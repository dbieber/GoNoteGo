"""Uploader for Slack workspace channels."""

import logging
import threading
from typing import List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from gonotego.command_center import assistant_commands
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
    self._session_notes: List[str] = []

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
      self._session_notes = [first_note]  # Start collecting notes for the session
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

      # Start a background thread to clean up typos
      if response and 'ts' in response:
        message_ts = response['ts']
        self._start_typo_correction_thread(text, channel_id, message_ts, indent_level)

      # Add to session notes for later summarization
      self._session_notes.append(text)

      return True
    except SlackApiError as e:
      logger.error(f"Error sending note to thread: {e}")
      return False

  def _start_typo_correction_thread(self, text: str, channel_id: str, message_ts: str, indent_level: int) -> None:
    """Start a background thread to correct typos in the note."""
    thread = threading.Thread(
        target=self._correct_typos_and_update,
        args=(text, channel_id, message_ts, indent_level),
        daemon=True
    )
    thread.start()

  def _correct_typos_and_update(self, text: str, channel_id: str, message_ts: str, indent_level: int) -> None:
    """Correct typos in the text and update the Slack message."""
    try:
      # Create a prompt for the LLM to correct typos but preserve character
      messages = [
          {"role": "system", "content": "You are a helpful assistant that corrects obvious typos in text. "
                                       "Only fix clear typos that don't convey character or information. "
                                       "Leave expressions that convey personality or uncertainty (like 'Hmm...', "
                                       "'Errr', or informal shortenings) intact. Return ONLY the corrected text "
                                       "with no explanations or additional commentary."},
          {"role": "user", "content": f"Correct obvious typos in this text, but preserve the character and style: {text}"}
      ]

      # Get the corrected text from the LLM
      response = assistant_commands.chat_completion(messages)
      corrected_text = response.choices[0].message.content.strip()

      # Only update if there were changes and the message isn't empty
      if corrected_text and corrected_text != text:
        # Format the text based on indentation
        formatted_text = corrected_text
        if indent_level > 0:
          bullet = "•"
          indentation = "  " * (indent_level - 1)
          formatted_text = f"{indentation}{bullet} {corrected_text}"

        # Update the message in Slack
        self.client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=formatted_text
        )
        logger.debug(f"Updated message with typo corrections: '{text}' -> '{corrected_text}'")
    except Exception as e:
      logger.error(f"Error in typo correction thread: {e}")
      # Do not propagate the exception as this is a background task

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
    # Start the summarization thread if we have a valid session with notes
    if self._session_started and self._thread_ts and self._session_notes:
      channel_id = self._get_channel_id()
      self._start_session_summary_thread(
          channel_id,
          self._thread_ts,
          self._session_notes.copy()
      )

    # Reset session state
    self._thread_ts = None
    self._session_started = False
    self._indent_level = 0
    self._session_notes = []

  def _start_session_summary_thread(self, channel_id: str, message_ts: str, session_notes: List[str]) -> None:
    """Start a background thread to summarize the session and update the top message."""
    thread = threading.Thread(
        target=self._summarize_session_and_update,
        args=(channel_id, message_ts, session_notes),
        daemon=True
    )
    thread.start()

  def _summarize_session_and_update(self, channel_id: str, message_ts: str, session_notes: List[str]) -> None:
    """Summarize the session and update the top-level message."""
    try:
      # Create a prompt for the LLM to summarize the session
      all_notes = "\n".join(session_notes)
      messages = [
          {"role": "system", "content": "You are a helpful assistant that creates concise summaries. "
                                      "Your summary should capture the key points and insights. "
                                      "After your summary, on a separate line, include an importance rating "
                                      "(Low/Medium/High), estimated reading time, and relevant #tags."},
          {"role": "user", "content": f"Here's a note-taking session. Please summarize it and provide metadata:\n\n{all_notes}"}
      ]

      # Get the summary from the LLM
      response = assistant_commands.chat_completion(messages)
      summary = response.choices[0].message.content.strip()

      # Update the top-level message in Slack
      first_note = session_notes[0] if session_notes else ""
      updated_message = f"{first_note}\n\n{summary}\n\n:keyboard: Go Note Go thread."

      # Update the message in Slack
      self.client.chat_update(
          channel=channel_id,
          ts=message_ts,
          text=updated_message
      )
      logger.debug("Updated top-level message with session summary")
    except Exception as e:
      logger.error(f"Error in session summarization thread: {e}")
      # Do not propagate the exception as this is a background task

  def handle_inactivity(self) -> None:
    """Handle inactivity by ending the session and clearing client."""
    self._client = None
    self.end_session()

  def handle_disconnect(self) -> None:
    """Handle disconnection by ending the session and clearing client."""
    self._client = None
    self.end_session()
