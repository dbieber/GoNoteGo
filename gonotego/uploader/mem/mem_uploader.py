import os
import requests

from gonotego.common import events
from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader


CREATE_URL = 'https://api.mem.ai/v0/mems'


def upload_mem(text, is_read=True):
  return requests.post(
      url=CREATE_URL,
      json=dict(
          content=text,
          isRead=is_read,
      ),
      headers=dict(Authorization=f'ApiAccessToken {secure_settings.MEM_API_KEY}')
  )


class Uploader:

  def upload(self, note_events):
    client = blob_uploader.make_client()
    for note_event in note_events:
      if note_event.action == events.SUBMIT:
        text = note_event.text.strip()
        if note_event.audio_filepath and os.path.exists(note_event.audio_filepath):
          is_read = False  # Notes with audio should be checked for accuracy.
          url = blob_uploader.upload_blob(note_event.audio_filepath, client)
          text = f'{text} #transcription ({url})'
        else:
          is_read = True
        upload_mem(text, is_read=is_read)

  def handle_inactivity(self):
    pass

  def handle_disconnect(self):
    pass
