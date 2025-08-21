"""Uploader for Slack workspace channels."""

import anthropic
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, TypedDict

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from gonotego.common import events
from gonotego.settings import settings

logger = logging.getLogger(__name__)


class SessionState(TypedDict):
  """State for a single Slack session."""
  thread_ts: str
  channel_id: str
  cleaned_reply_ts: str
  raw_reply_ts: str
  session_messages: List[Dict[str, str]]
  cleaned_messages: Dict[str, str]
  last_summary: str
  is_active: bool


class Uploader:
  """Uploader implementation for Slack."""

  def __init__(self):
    self._client: Optional[WebClient] = None
    self._channel_id: Optional[str] = None
    self._indent_level: int = 0
    self._executor = ThreadPoolExecutor(max_workers=5)
    self._anthropic_client = None

    # Current session state
    self._current_session: Optional[SessionState] = None

    # Summary debouncing and version tracking
    self._summary_timer: Optional[threading.Timer] = None
    self._summary_request_version: int = 0
    self._latest_summary_version: int = 0
    self._is_waiting_for_summary: bool = False

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

    try:
      # Create the header message
      header_text = f":wip: {first_note}"
      header_response = self.client.chat_postMessage(
          channel=channel_id,
          text=header_text
      )
      thread_ts = header_response['ts']

      # Create the first reply (cleaned content - initially raw)
      cleaned_reply_response = self.client.chat_postMessage(
          channel=channel_id,
          text=first_note,
          thread_ts=thread_ts
      )
      cleaned_reply_ts = cleaned_reply_response['ts']

      # Create the second reply (raw content)
      raw_reply_response = self.client.chat_postMessage(
          channel=channel_id,
          text=first_note,
          thread_ts=thread_ts
      )
      raw_reply_ts = raw_reply_response['ts']

      # Create session state
      self._current_session = SessionState(
          thread_ts=thread_ts,
          channel_id=channel_id,
          cleaned_reply_ts=cleaned_reply_ts,
          raw_reply_ts=raw_reply_ts,
          session_messages=[{'ts': header_response['ts'], 'text': first_note}],
          cleaned_messages={},
          last_summary=first_note,
          is_active=True
      )

      # Initialize tracking
      self._summary_request_version = 0
      self._latest_summary_version = 0
      self._is_waiting_for_summary = False

      # Schedule cleanup for the first message
      self._executor.submit(self._cleanup_message_async, first_note,
                           header_response['ts'], self._current_session)

      return True
    except SlackApiError as e:
      logger.error(f"Error starting session: {e}")
      return False

  def _request_summary_smart(self):
    """Request a summary with smart debouncing."""
    if not self._current_session:
      return

    if not self._is_waiting_for_summary:
      # Not waiting, send request immediately
      self._is_waiting_for_summary = True
      self._summary_request_version += 1
      version = self._summary_request_version
      self._executor.submit(self._summarize_session_async, version, self._current_session)

      # Set timer to reset waiting flag
      self._summary_timer = threading.Timer(0.5, self._reset_summary_waiting)
      self._summary_timer.start()
    else:
      # Already waiting, cancel existing timer and set new one
      if self._summary_timer:
        self._summary_timer.cancel()

      # Set new timer to send request after 0.5s
      self._summary_timer = threading.Timer(0.5, self._send_summary_request)
      self._summary_timer.start()

  def _reset_summary_waiting(self):
    """Reset the waiting flag after debounce period."""
    self._is_waiting_for_summary = False

  def _send_summary_request(self):
    """Send a summary request after debounce period."""
    self._is_waiting_for_summary = False
    if not self._current_session:
      return
    self._summary_request_version += 1
    version = self._summary_request_version
    self._executor.submit(self._summarize_session_async, version, self._current_session)

  def _update_replies(self, session: SessionState):
    """Update both reply messages with current content."""
    if not session['thread_ts'] or not session['cleaned_reply_ts'] or not session['raw_reply_ts']:
      return

    # Compile cleaned content (use cleaned version if available, else raw)
    cleaned_content_parts = []
    for msg in session['session_messages']:
      ts = msg['ts']
      text = msg['text']
      # Use cleaned version if available
      if ts in session['cleaned_messages']:
        cleaned_content_parts.append(session['cleaned_messages'][ts])
      else:
        cleaned_content_parts.append(text)

    cleaned_content = '\n'.join(cleaned_content_parts)

    # Compile raw content
    raw_content = '\n'.join([msg['text'] for msg in session['session_messages']])

    # Update cleaned reply
    try:
      self.client.chat_update(
        channel=session['channel_id'],
        ts=session['cleaned_reply_ts'],
        text=cleaned_content
      )
    except SlackApiError as e:
      logger.error(f"Error updating cleaned reply: {e}")

    # Update raw reply
    try:
      self.client.chat_update(
        channel=session['channel_id'],
        ts=session['raw_reply_ts'],
        text=raw_content
      )
    except SlackApiError as e:
      logger.error(f"Error updating raw reply: {e}")

  def _send_note_to_thread(self, text: str, indent_level: int = 0) -> bool:
    """Add a note to the session and update reply messages."""
    if not self._current_session:
      logger.error("Trying to send to thread but no session exists")
      return False

    # Format the text based on indentation
    formatted_text = text
    if indent_level > 0:
      # Add bullet and proper indentation
      bullet = "•"
      indentation = "  " * (indent_level - 1)
      formatted_text = f"{indentation}{bullet} {text}"

    # Generate a unique timestamp for this message
    msg_ts = str(time.time())

    # Track the message in current session
    self._current_session['session_messages'].append({'ts': msg_ts, 'text': formatted_text})

    # Update header to add :thread: if this is the second message
    if len(self._current_session['session_messages']) == 2:
      try:
        header_text = f":wip: {self._current_session['last_summary']} :thread:"
        self._update_message(self._current_session['channel_id'],
                           self._current_session['thread_ts'], header_text)
      except SlackApiError as e:
        logger.error(f"Error updating header with thread indicator: {e}")

    # Update both reply messages
    self._update_replies(self._current_session)

    # Schedule cleanup for this message
    self._executor.submit(self._cleanup_message_async, formatted_text, msg_ts,
                         self._current_session)

    # Request summary with smart debouncing
    self._request_summary_smart()

    return True

  def _cleanup_message_async(self, original_text: str, message_ts: str,
                            session: SessionState):
    """Clean up a message using Claude in the background."""
    try:
      client = self._get_anthropic_client()
      if not client:
        logger.debug("Anthropic client not available, skipping cleanup")
        return

      # Call Claude to clean up the message
      prompt = f"""Clean up this message. Fix any obvious typographic issues, but keep any stylistic choices that convey emotion, tone, or emphasis. Only clean up typos that were unintentional mistakes. Output the full cleaned text without any explanation or metadata. If you cannot clean the text, state it unchanged.

Original text: {original_text}"""

      message = client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=5000,
        temperature=0.7,
        messages=[
          {"role": "user", "content": prompt}
        ]
      )

      cleaned_text = message.content[0].text.strip()
      logger.debug(f"Cleaned text: {cleaned_text}")

      # Store the cleaned message in session
      session['cleaned_messages'][message_ts] = cleaned_text

      # Update the cleaned reply message
      self._update_replies(session)

    except Exception as e:
      logger.error(f"Error cleaning up message: {e}")

  def _summarize_session_async(self, version: int, session: SessionState):
    """Summarize the entire session using Claude Opus 4."""
    try:
      client = self._get_anthropic_client()
      if not client:
        logger.debug("Anthropic client not available, skipping summarization")
        return

      if not session['session_messages']:
        logger.debug("No messages to summarize")
        return

      # Compile all messages into a thread
      thread_text = "\n".join([msg['text'] for msg in session['session_messages']])

      prompt = f"""Please provide a concise one-line summary of this note-taking session. Be very brief and focus on the main topic or purpose.

Session notes:
{thread_text}"""

      message = client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=200,
        temperature=0.7,
        messages=[
          {"role": "user", "content": prompt}
        ]
      )

      summary = message.content[0].text.strip()

      # Only update if this version is the latest
      if version >= self._latest_summary_version:
        self._latest_summary_version = version
        session['last_summary'] = summary

        # Determine status indicators
        has_thread = len(session['session_messages']) > 1
        thread_indicator = " :thread:" if has_thread else ""

        # Only add :wip: if this session is still active
        wip_indicator = ":wip: " if session['is_active'] else ""
        header_text = f"{wip_indicator}{summary}{thread_indicator}"
        self._update_message(session['channel_id'], session['thread_ts'], header_text)

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
        if not self._current_session:
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
    if self._current_session:
      try:
        # Mark session as inactive
        self._current_session['is_active'] = False

        # Cancel any pending summary timer
        if self._summary_timer:
          self._summary_timer.cancel()

        # Request final summary (will see is_active=False and not add :wip:)
        if self._current_session['session_messages']:
          self._summary_request_version += 1
          self._executor.submit(self._summarize_session_async,
                              self._summary_request_version,
                              self._current_session)

        # Update header to remove :wip: immediately
        has_thread = len(self._current_session['session_messages']) > 1
        thread_indicator = " :thread:" if has_thread else ""
        header_text = f"{self._current_session['last_summary']}{thread_indicator}"
        self._update_message(self._current_session['channel_id'],
                           self._current_session['thread_ts'],
                           header_text)

      except Exception as e:
        logger.error(f"Error finalizing session: {e}")

    # Clear session state
    self._current_session = None
    self._indent_level = 0
    self._summary_request_version = 0
    self._latest_summary_version = 0
    self._is_waiting_for_summary = False
    if self._summary_timer:
      self._summary_timer.cancel()
      self._summary_timer = None

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
    """Cleanup executor and timer on deletion."""
    self._executor.shutdown(wait=False)
    self._summary_timer.cancel()