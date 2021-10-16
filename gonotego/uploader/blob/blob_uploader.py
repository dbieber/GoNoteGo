import dropbox

from gonotego.settings import secure_settings


def make_client():
  return dropbox.Dropbox(secure_settings.DROPBOX_ACCESS_TOKEN)


def upload_blob(filepath, client):
  """Uploads a blob, and returns a URL to that blob."""
  dropbox_path = f'/{filepath}'
  with open(filepath, 'rb') as f:
    unused_file_metadata = client.files_upload(f.read(), dropbox_path)
    link_metadata = client.sharing_create_shared_link(dropbox_path)
  return link_metadata.url.replace('www.', 'dl.').replace('?dl=0', '')
