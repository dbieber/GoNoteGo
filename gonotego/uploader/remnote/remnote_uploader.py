import os
import requests

from gonotego.common import events
from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader

CREATE_URL = 'https://api.remnote.io/api/v0/create'


def create_rem(text, edit_later, parent_id=None):
  data = dict(
      apiKey=secure_settings.REMNOTE_API_KEY,
      userId=secure_settings.REMNOTE_USER_ID,
      text=text,
      addToEditLater=edit_later,
      parentId=parent_id,
      isDocument=False,
  )
  response = requests.post(
      url=CREATE_URL,
      json=data)
  return response.json().get('remId')


class Uploader:

  def upload(self, note_events):
    if not secure_settings.REMNOTE_ROOT_REM:
      raise ValueError('Must provide REMNOTE_ROOT_REM')

    client = blob_uploader.make_client()
    for note_event in note_events:
      if note_event.action == events.SUBMIT:
        # Notes with audio should be checked for accuracy.
        edit_later = bool(note_event.audio_filepath)

        rem_id = create_rem(
            text=note_event.text,
            edit_later=edit_later,
            parent_id=secure_settings.REMNOTE_ROOT_REM)
        if note_event.audio_filepath and os.path.exists(note_event.audio_filepath):
          url = blob_uploader.upload_blob(note_event.audio_filepath, client)
          create_rem(url, edit_later=False, parent_id=rem_id)

  def handle_inactivity(self):
    pass

  def handle_disconnect(self):
    pass
