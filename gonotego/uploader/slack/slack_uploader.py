"""Uploader for Slack workspace channels."""

import anthropic
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict

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
    self._message_timestamps: List[str] = []
    self._session_messages: List[Dict[str, str]] = []
    self._executor = ThreadPoolExecutor(max_workers=5)
    self._anthropic_client = None

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

  def _get_anthropic_client(self):
    """Get or create the Anthropic client."""
    if self._anthropic_client:
      return self._anthropic_client

    api_key = settings.get('ANTHROPIC_API_KEY')
    if api_key and api_key != '<ANTHROPIC_API_KEY>':
      self._anthropic_client = anthropic.Anthropic(api_key=api_key)
      return self._anthropic_client

    return None

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
      message_text = f":wip: {first_note}"
      response = self.client.chat_postMessage(
          channel=channel_id,
          text=message_text
      )
      self._thread_ts = response['ts']
      self._session_started = True
      self._message_timestamps = [response['ts']]
      self._session_messages = [{'ts': response['ts'], 'text': first_note}]

      # Schedule cleanup for first message
      self._executor.submit(self._cleanup_message_async, first_note, response['ts'])

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
      response = self.client.chat_postMessage(
          channel=channel_id,
          text=formatted_text,
          thread_ts=self._thread_ts
      )

      # Track the message
      self._message_timestamps.append(response['ts'])
      self._session_messages.append({'ts': response['ts'], 'text': text})

      # Schedule cleanup for this message
      self._executor.submit(self._cleanup_message_async, text, response['ts'])

      return True
    except SlackApiError as e:
      logger.error(f"Error sending note to thread: {e}")
      return False

  def _cleanup_message_async(self, original_text: str, message_ts: str):
    """Clean up a message using Claude in the background."""
    try:
      client = self._get_anthropic_client()
      if not client:
        logger.debug("Anthropic client not available, skipping cleanup")
        return

      # Call Claude to clean up the message
      prompt = f"""Clean up this voice-transcribed note to be clear and concise. Fix any transcription errors, grammar, and formatting. Keep the core meaning intact but make it more readable. Return only the cleaned text without any explanation or metadata.

Original text: {original_text}"""

      message = client.messages.create(
        model="claude-4-opus",
        max_tokens=5000,
        temperature=0.7,
        messages=[
          {"role": "user", "content": prompt}
        ]
      )

      cleaned_text = message.content[0].text.strip()

      # Update the message in Slack
      channel_id = self._get_channel_id()
      self._update_message(channel_id, message_ts, cleaned_text)

    except Exception as e:
      logger.error(f"Error cleaning up message: {e}")

  def _summarize_session_async(self):
    """Summarize the entire session using Claude Opus 4."""
    try:
      client = self._get_anthropic_client()
      if not client:
        logger.debug("Anthropic client not available, skipping summarization")
        return

      if not self._session_messages or not self._thread_ts:
        logger.debug("No messages to summarize")
        return

      # Compile all messages into a thread
      thread_text = "\n".join([msg['text'] for msg in self._session_messages])

      prompt = f"""Please provide a concise summary of this note-taking session. Identify the main topics, key points, and any action items. Format the summary clearly with bullet points where appropriate.

Session notes:
{thread_text}"""

      message = client.messages.create(
        model="claude-3-5-opus-20241022",
        max_tokens=1000,
        temperature=0.3,
        messages=[
          {"role": "user", "content": prompt}
        ]
      )

      summary = message.content[0].text.strip()

      # Update the top-level message with the summary
      channel_id = self._get_channel_id()
      original_text = self._session_messages[0]['text'] if self._session_messages else ""
      updated_text = f":memo: **Session Summary**\n\n{summary}\n\n---\n_Original first note: {original_text}_"

      self._update_message(channel_id, self._thread_ts, updated_text)

    except Exception as e:
      logger.error(f"Error summarizing session: {e}")

  def _update_message(self, channel_id: str, ts: str, new_text: str):
    """Update a Slack message with new text."""
    try:
      self.client.chat_update(
        channel=channel_id,
        ts=ts,
        text=new_text
      )
      logger.debug(f"Updated message {ts}")
    except SlackApiError as e:
      logger.error(f"Error updating message: {e}")

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
    # Schedule session summarization before clearing
    if self._session_started and self._session_messages:
      self._executor.submit(self._summarize_session_async)

    # Clear session state
    self._thread_ts = None
    self._session_started = False
    self._indent_level = 0
    self._message_timestamps = []
    self._session_messages = []

  def handle_inactivity(self) -> None:
    """Handle inactivity by ending the session and clearing client."""
    self.end_session()
    self._client = None
    self._anthropic_client = None

  def handle_disconnect(self) -> None:
    """Handle disconnection by ending the session and clearing client."""
    self.end_session()
    self._client = None
    self._anthropic_client = None

  def __del__(self):
    """Cleanup executor on deletion."""
    if hasattr(self, '_executor'):
      self._executor.shutdown(wait=False)