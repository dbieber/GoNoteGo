import requests

from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader


CREATE_URL = 'https://api.remnote.io/api/v0/create'


def create_rem(text, edit_later, parent_id=None):
  response = requests.post(
      url=CREATE_URL,
      data=dict(
          apiKey=secure_settings.REMNOTE_API_KEY,
          userId=secure_settings.REMNOTE_USER_ID,
          text=text,
          addToEditLater=edit_later,
          parentId=parent_id,
          source='Go Note Go',
      ),
  )
  try:
    return response.json().get('remId')
  except:
    pass


class Uploader:

  def upload(self, note_events):
    client = blob_uploader.make_client()
    for note_event in note_events:
      # Notes with audio should be checked for accuracy.
      edit_later = bool(note_event.audio_filepath)
      rem_id = create_rem(note_event.text, edit_later)
      if note_event.audio_filepath:
        url = blob_uploader.upload_blob(note_event.audio_filepath, client)
        audio_rem_id = create_rem(url, edit_later=False, parent_id=rem_id)


  def handle_inactivity(self):
    pass

  def handle_disconnect(self):
    pass
