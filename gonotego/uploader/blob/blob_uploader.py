import os

import dropbox

from gonotego.settings import settings


def make_client():
  # Handle case sensitivity for blob storage system
  blob_system = settings.get('BLOB_STORAGE_SYSTEM').lower() if settings.get('BLOB_STORAGE_SYSTEM') else ''
  if blob_system == 'dropbox':
    return dropbox.Dropbox(settings.get('DROPBOX_ACCESS_TOKEN'))


def upload_blob(filepath, client):
  """Uploads a blob, and returns a URL to that blob."""
  if not client:
    return ''

  if not os.path.exists(filepath):
    return ''
  dropbox_path = f'/{filepath}'
  with open(filepath, 'rb') as f:
    unused_file_metadata = client.files_upload(f.read(), dropbox_path)  # noqa
    link_metadata = client.sharing_create_shared_link(dropbox_path)
  return link_metadata.url.replace('www.', 'dl.').replace('?dl=0', '')
