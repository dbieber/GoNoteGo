import requests

from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader


URL = 'https://api.notion.com/v1/pages'
APPEND_CHILD_URL_FORMAT = 'https://api.notion.com/v1/blocks/{block_id}/children'


def upload_note(text, is_read=True):
  return requests.post(
      url=URL,
      json=dict(
          parent={'type': 'page_id', 'page_id': page_id},
          isRead=is_read,
      ),
      headers=dict(Authorization=f'Bearer {secure_settings.MEM_API_KEY}')
  )


class Uploader:

  def upload(self, note_events):
    client = blob_uploader.make_client()
    for note_event in note_events:
      text = note_event.text.strip()
      if note_event.audio_filepath:
        is_read = False  # Notes with audio should be checked for accuracy.
        url = blob_uploader.upload_blob(note_event.audio_filepath, client)
        text = f'{text} #transcription ({url})'
      else:
        is_read = True
      upload_note(text, is_read=is_read)

  def handle_inactivity(self):
    pass

  def handle_disconnect(self):
    pass
