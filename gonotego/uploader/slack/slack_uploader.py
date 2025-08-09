"""Uploader for Slack workspace channels."""

import logging
from typing import List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from gonotego.common import events
from gonotego.settings import settings

logger = logging.getLogger(__name__)


class Uploader:
  """Uploader implementation for Slack."""

  def __init__(self):
    self._client: Optional[WebClient] = None
    self._channel_id: Optional[str] = None
    self._thread_ts: Optional[str] = None
    self._session_started: bool = False
    self._indent_level: int = 0

  @property
  def client(self) -> WebClient:
    """Get or create the Slack WebClient."""
    if self._client:
      return self._client

    # Get token from settings
    token = settings.get('SLACK_API_TOKEN')
    if not token:
      logger.error("Missing Slack API token in settings")
      raise ValueError("Missing Slack API token in settings")

    # Initialize the client
    self._client = WebClient(token=token)
    return self._client

  def _get_channel_id(self) -> str:
    """Get the channel ID for the configured channel name."""
    if self._channel_id:
      return self._channel_id

    channel_id = settings.get('SLACK_CHANNEL_ID')
    if channel_id is not None:
      self._channel_id = channel_id
      return self._channel_id

    channel_name = settings.get('SLACK_CHANNEL')
    if not channel_name:
      logger.error("Missing Slack channel name in settings")
      raise ValueError("Missing Slack channel name in settings")

    # Try to find the channel in the workspace
    try:
      result = self.client.conversations_list()
      for channel in result['channels']:
        if channel['name'] == channel_name:
          self._channel_id = channel['id']
          return self._channel_id
    except SlackApiError as e:
      logger.error(f"Error fetching channels: {e}")
      raise

    logger.error(f"Channel {channel_name} not found in workspace")
    raise ValueError(f"Channel {channel_name} not found in workspace")

  def _start_session(self, first_note: str) -> bool:
    """Start a new session thread in the configured Slack channel."""
    channel_id = self._get_channel_id()

    # Create the initial message with the note content
    try:
      message_text = f"{first_note}\n\n:keyboard: Go Note Go thread."
      response = self.client.chat_postMessage(
          channel=channel_id,
          text=message_text
      )
      self._thread_ts = response['ts']
      self._session_started = True
      return True
    except SlackApiError as e:
      logger.error(f"Error starting session: {e}")
      return False

  def _send_note_to_thread(self, text: str, indent_level: int = 0) -> bool:
    """Send a note as a reply in the current thread."""
    if not self._thread_ts:
      logger.error("Trying to send to thread but no thread exists")
      return False

    channel_id = self._get_channel_id()

    # Format the text based on indentation
    formatted_text = text
    if indent_level > 0:
      # Add bullet and proper indentation
      bullet = "•"
      indentation = "  " * (indent_level - 1)
      formatted_text = f"{indentation}{bullet} {text}"

    try:
      self.client.chat_postMessage(
          channel=channel_id,
          text=formatted_text,
          thread_ts=self._thread_ts
      )
      return True
    except SlackApiError as e:
      logger.error(f"Error sending note to thread: {e}")
      return False

  def upload(self, note_events: List[events.NoteEvent]) -> bool:
    """Upload note events to Slack.

    Args:
      note_events: List of NoteEvent objects.

    Returns:
      bool: True if upload successful, False otherwise.
    """
    for note_event in note_events:
      # Handle indent/unindent events to track indentation level
      if note_event.action == events.INDENT:
        self._indent_level += 1
        continue
      elif note_event.action == events.UNINDENT:
        self._indent_level = max(0, self._indent_level - 1)
        continue
      elif note_event.action == events.CLEAR_EMPTY:
        self._indent_level = 0
        continue
      elif note_event.action == events.ENTER_EMPTY:
        # When you submit from an empty note, that pops from the stack.
        self._indent_level = max(0, self._indent_level - 1)
      elif note_event.action == events.SUBMIT:
        text = note_event.text.strip()

        # Skip empty notes
        if not text:
          continue

        # Start a new session for the first note
        if not self._session_started:
          success = self._start_session(text)
        else:
          # Send as a reply to the thread with proper indentation
          success = self._send_note_to_thread(text, self._indent_level)

        if not success:
          logger.error("Failed to upload note to Slack")
          return False

      elif note_event.action == events.END_SESSION:
        self.end_session()

    return True

  def end_session(self) -> None:
    """End the current session."""
    self._thread_ts = None
    self._session_started = False
    self._indent_level = 0

  def handle_inactivity(self) -> None:
    """Handle inactivity by ending the session and clearing client."""
    self._client = None
    self.end_session()

  def handle_disconnect(self) -> None:
    """Handle disconnection by ending the session and clearing client."""
    self._client = None
    self.end_session()
