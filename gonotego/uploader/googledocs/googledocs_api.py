"""Client for the Google Docs and Drive REST APIs used by the Google Docs uploader.

Auth can be either of two credential kinds, both pointed to by
GOOGLE_DOCS_CREDENTIALS (falling back to the GOOGLE_APPLICATION_CREDENTIALS env
var, then /home/pi/secrets/google_credentials.json):

  - A **service account** key (JSON with "type": "service_account"). Docs are
    created and owned by the service account, then shared with GOOGLE_DOCS_SHARE_EMAIL.
  - A **user OAuth token** (an "authorized user" JSON with a refresh_token,
    produced by scripts/authorize_googledocs.py). Docs are created in and owned
    by that Google user's own Drive. Use this to write into someone's own Drive,
    since a service account cannot own files in a consumer Gmail Drive.

The uploader keeps one Google Doc per month. This client finds that doc by name
or creates it, optionally placing it in a Drive folder, then appends content.

Scopes: documents (edit docs) and drive.file (create/find/share only the files
this app makes). drive.file is deliberately narrow: only docs this app created
are visible to it, not the rest of anyone's Drive.
"""
import json
import os

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file',
]
DEFAULT_CREDENTIALS_PATH = '/home/pi/secrets/google_credentials.json'
DRIVE_FILES_URL = 'https://www.googleapis.com/drive/v3/files'
DOCS_URL = 'https://docs.googleapis.com/v1/documents'
DOC_MIME = 'application/vnd.google-apps.document'


class GoogleDocsError(Exception):
  """A Google Docs or Drive API request failed or could not be made."""


def default_credentials_path():
  return os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or DEFAULT_CREDENTIALS_PATH


def load_credentials(path):
  """Loads Google credentials from a service-account key or a user OAuth token.

  Detects the kind by the JSON contents: a service-account key has
  "type": "service_account"; anything else is treated as an authorized-user
  token (with a refresh_token) that authenticates as a specific Google user so
  the docs live in that user's own Drive.
  """
  with open(path) as f:
    info = json.load(f)
  if info.get('type') == 'service_account':
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
  from google.oauth2.credentials import Credentials
  return Credentials.from_authorized_user_info(info, scopes=SCOPES)


def _escape_query_value(value):
  """Escapes a value for use inside a Drive query string literal."""
  return value.replace('\\', '\\\\').replace("'", "\\'")


class GoogleDocsClient:
  """A minimal client for the Drive files endpoints and the Docs endpoints."""

  def __init__(self, session=None, credentials_path=None, timeout=60):
    self._session = session
    self._credentials_path = credentials_path
    self._timeout = timeout

  def session(self):
    """Returns an authorized requests session, building it from the SA creds once."""
    if self._session is None:
      from google.auth.transport.requests import AuthorizedSession
      path = self._credentials_path or default_credentials_path()
      self._session = AuthorizedSession(load_credentials(path))
    return self._session

  def _request(self, method, url, **kwargs):
    kwargs.setdefault('timeout', self._timeout)
    response = self.session().request(method, url, **kwargs)
    if response.status_code // 100 != 2:
      raise GoogleDocsError(
          f'{method} {url} -> HTTP {response.status_code}: {response.text[:400]}')
    if response.content:
      return response.json()
    return {}

  def find_doc(self, name):
    """Returns the id of a Google Doc with exactly this name, or None."""
    query = (f"name = '{_escape_query_value(name)}' and "
             f"mimeType = '{DOC_MIME}' and trashed = false")
    data = self._request(
        'GET', DRIVE_FILES_URL,
        params={'q': query, 'fields': 'files(id,name)', 'pageSize': 1})
    files = data.get('files', [])
    return files[0]['id'] if files else None

  def create_doc(self, name, folder_id=None, share_email=None):
    """Creates a Google Doc, optionally in a folder and shared with an email."""
    metadata = {'name': name, 'mimeType': DOC_MIME}
    if folder_id:
      metadata['parents'] = [folder_id]
    data = self._request(
        'POST', DRIVE_FILES_URL, params={'fields': 'id'}, json=metadata)
    doc_id = data['id']
    if share_email:
      self.share(doc_id, share_email)
    return doc_id

  def share(self, doc_id, email, role='writer'):
    """Grants a user access to a doc without sending a notification email."""
    self._request(
        'POST', f'{DRIVE_FILES_URL}/{doc_id}/permissions',
        params={'sendNotificationEmail': 'false'},
        json={'type': 'user', 'role': role, 'emailAddress': email})

  def get_or_create_month_doc(self, name, folder_id=None, share_email=None):
    """Returns the id of the doc named `name`, creating and sharing it if absent."""
    return self.find_doc(name) or self.create_doc(
        name, folder_id=folder_id, share_email=share_email)

  def get_document(self, doc_id):
    """Fetches the document structure (used to find the append point and last day)."""
    return self._request('GET', f'{DOCS_URL}/{doc_id}')

  def batch_update(self, doc_id, requests):
    """Applies a list of Docs API requests in one batch."""
    if not requests:
      return {}
    return self._request(
        'POST', f'{DOCS_URL}/{doc_id}:batchUpdate', json={'requests': requests})
