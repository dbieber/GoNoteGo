"""Uploads notes to Roam Research through the Roam backend API.

Produces the same structure as the browser-based uploader (roam_uploader.py):

  Daily Notes page for the note's date
    - [[Go Note Go Notes]]:
      - 06:30 AM                (one block per writing session)
        - a note
        - another note
          - an indented note

Unlike the browser uploader this needs no Firefox and no Roam password, and it
is unaffected by the bot-verification challenge in front of Roam's web app.
It is used whenever ROAM_API_TOKEN is set.
"""
from datetime import datetime
import os

from gonotego.common import events
from gonotego.settings import settings
from gonotego.uploader.blob import blob_uploader
from gonotego.uploader.roam import roam_backend_api

SECTION_TITLE = '[[Go Note Go Notes]]:'
UNVERIFIED_TAG = '#[[unverified transcription]]'


def note_datetime(note_event):
  """The note's effective time (clock + alleged-time offset), or now if unknown."""
  timestamp = note_event.effective_timestamp if note_event is not None else None
  return datetime.fromtimestamp(timestamp) if timestamp else datetime.now()


class Uploader:

  def __init__(self, client=None):
    self._client = client
    self.session_uid = None
    self.last_note_uid = None
    self.stack = []

  def get_client(self):
    if self._client is None:
      self._client = roam_backend_api.RoamBackendClient(
          token=settings.get('ROAM_API_TOKEN'),
          graph=settings.get('ROAM_GRAPH'))
    return self._client

  def new_session(self, note_event):
    """Creates the block that this writing session's notes are nested under."""
    client = self.get_client()
    dt = note_datetime(note_event)
    title = roam_backend_api.daily_note_title(dt)
    page_uid = client.get_or_create_page(title, uid=roam_backend_api.daily_note_uid(dt))
    section_uid = client.get_or_create_block_on_page(page_uid, SECTION_TITLE)
    self.session_uid = client.create_block(section_uid, dt.strftime('%H:%M %p'))
    print(f'Started session (({self.session_uid})) on "{title}"')

  def upload(self, note_events):
    """Uploads the note events. Returns True on success, False if a request failed."""
    try:
      self._upload(note_events)
    except roam_backend_api.RoamAPIError as e:
      print(f'Roam API upload failed: {e}')
      return False
    return True

  def _upload(self, note_events):
    client = self.get_client()
    blob_client = None
    for note_event in note_events:
      if note_event.action == events.INDENT:
        # When you press tab, that adds your most-recent note to a stack.
        if self.last_note_uid and self.last_note_uid not in self.stack:
          self.stack.append(self.last_note_uid)
      elif note_event.action == events.UNINDENT:
        # When you shift-tab, that pops from the stack.
        if self.stack:
          self.stack.pop()
      elif note_event.action == events.CLEAR_EMPTY:
        # When you shift-delete from an empty note, that clears the stack.
        self.stack = []
      elif note_event.action == events.ENTER_EMPTY:
        # When you submit from an empty note, that pops from the stack.
        if self.stack:
          self.stack.pop()
      elif note_event.action == events.END_SESSION:
        self.end_session()
      elif note_event.action == events.SUBMIT:
        if self.session_uid is None:
          self.new_session(note_event)
        text = note_event.text.strip()
        has_audio = bool(note_event.audio_filepath) and os.path.exists(note_event.audio_filepath)
        if has_audio:
          text = f'{text} {UNVERIFIED_TAG}'
        parent_uid = self.stack[-1] if self.stack else self.session_uid
        block_uid = client.create_block(parent_uid, text)
        self.last_note_uid = block_uid
        print(f'Inserted: "{text}" at block (({block_uid}))')
        if has_audio:
          if blob_client is None:
            blob_client = blob_uploader.make_client()
          embed_url = blob_uploader.upload_blob(note_event.audio_filepath, blob_client)
          if embed_url:
            embed_text = '{{audio: ' + embed_url + '}}'
            print(f'Audio embed: {embed_text}')
            client.create_block(block_uid, embed_text)

  def handle_inactivity(self):
    self.end_session()

  def handle_disconnect(self):
    self.end_session()

  def end_session(self):
    self.session_uid = None
    self.last_note_uid = None
    self.stack = []
