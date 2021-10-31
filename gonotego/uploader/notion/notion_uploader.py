from datetime import datetime
import os
import requests

from gonotego.settings import secure_settings
from gonotego.uploader.blob import blob_uploader


PAGES_URL = 'https://api.notion.com/v1/pages'
APPEND_CHILD_URL_FORMAT = 'https://api.notion.com/v1/blocks/{block_id}/children'


def create_page(title):
  return requests.post(
      url=PAGES_URL,
      json=dict(
          parent={'database_id': secure_settings.NOTION_DATABASE_ID},
          properties={
              'Name': {'title': [{'text': {'content': title}}]},
          }
      ),
      headers={
          'Authorization': f'Bearer {secure_settings.NOTION_INTEGRATION_TOKEN}',
          'Notion-Version': '2021-08-16',
      },
  )


def make_text_block(text):
  return {
      'object': 'block',
      'type': 'paragraph',
      'paragraph': {
          'text': [{ 'type': 'text', 'text': {'content': text}}],
      },
  }


def make_audio_block(url):
  return {
      'object': 'block',
      'type': 'file',
      'file': {
          'type': 'external',
          'external': {'url': url},
      },
  }


def append_notes(blocks, page_id):
  children = []
  return requests.patch(
      url=APPEND_CHILD_URL_FORMAT.format(block_id=page_id),
      json=dict(children=blocks),
      headers={
          'Authorization': f'Bearer {secure_settings.NOTION_INTEGRATION_TOKEN}',
          'Notion-Version': '2021-08-16',
      },
  )


def now_as_title():
  now = datetime.now()
  return now.strftime('%B %d, %Y at %H:%M')


class Uploader:

  def __init__(self):
    self.current_page_id = None

  def upload(self, note_events):
    if self.current_page_id is None:
      response = create_page(now_as_title())
      self.current_page_id = response.json().get('id')

    client = blob_uploader.make_client()
    blocks = []
    for note_event in note_events:
      text = note_event.text.strip()
      blocks.append(make_text_block(text))
      if note_event.audio_filepath and os.path.exists(note_event.audio_filepath):
        url = blob_uploader.upload_blob(note_event.audio_filepath, client)
        blocks.append(make_audio_block(url))
    append_notes(blocks, page_id=self.current_page_id)

  def handle_inactivity(self):
    self.current_page_id = None

  def handle_disconnect(self):
    self.current_page_id = None
