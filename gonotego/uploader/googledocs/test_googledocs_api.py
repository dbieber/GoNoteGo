import pytest

from gonotego.uploader.googledocs import googledocs_api as api


class FakeResponse:

  def __init__(self, status_code=200, json_data=None, text=''):
    self.status_code = status_code
    self._json = json_data if json_data is not None else {}
    self.text = text
    self.content = b'x' if (json_data is not None or text) else b''

  def json(self):
    return self._json


class FakeSession:

  def __init__(self, responses):
    self.responses = list(responses)
    self.calls = []

  def request(self, method, url, **kwargs):
    self.calls.append({'method': method, 'url': url, **kwargs})
    response = self.responses.pop(0)
    if isinstance(response, Exception):
      raise response
    return response


def make_client(responses):
  session = FakeSession(responses)
  return api.GoogleDocsClient(session=session), session


def test_find_doc_builds_query_and_returns_id():
  client, session = make_client([FakeResponse(json_data={'files': [{'id': 'doc1'}]})])
  assert client.find_doc('September 2026') == 'doc1'
  call = session.calls[0]
  assert call['method'] == 'GET' and call['url'] == api.DRIVE_FILES_URL
  q = call['params']['q']
  assert "name = 'September 2026'" in q
  assert f"mimeType = '{api.DOC_MIME}'" in q
  assert 'trashed = false' in q


def test_find_doc_returns_none_when_absent():
  client, _ = make_client([FakeResponse(json_data={'files': []})])
  assert client.find_doc('Nope') is None


def test_find_doc_escapes_apostrophe():
  client, session = make_client([FakeResponse(json_data={'files': []})])
  client.find_doc("Andrea's Notes")
  assert "name = 'Andrea\\'s Notes'" in session.calls[0]['params']['q']


def test_create_doc_without_share():
  client, session = make_client([FakeResponse(json_data={'id': 'newdoc'})])
  assert client.create_doc('September 2026') == 'newdoc'
  call = session.calls[0]
  assert call['method'] == 'POST' and call['url'] == api.DRIVE_FILES_URL
  assert call['json'] == {'name': 'September 2026', 'mimeType': api.DOC_MIME}


def test_create_doc_with_folder_and_share():
  client, session = make_client([
      FakeResponse(json_data={'id': 'newdoc'}),  # create
      FakeResponse(json_data={'id': 'perm1'}),   # share
  ])
  assert client.create_doc('Sept', folder_id='folder1', share_email='a@b.com') == 'newdoc'
  create, share = session.calls
  assert create['json']['parents'] == ['folder1']
  assert share['url'] == f'{api.DRIVE_FILES_URL}/newdoc/permissions'
  assert share['json'] == {'type': 'user', 'role': 'writer', 'emailAddress': 'a@b.com'}
  assert share['params']['sendNotificationEmail'] == 'false'


def test_get_or_create_uses_existing():
  client, session = make_client([FakeResponse(json_data={'files': [{'id': 'existing'}]})])
  assert client.get_or_create_month_doc('Sept', share_email='a@b.com') == 'existing'
  assert len(session.calls) == 1  # only the find; no create, no share


def test_get_or_create_creates_when_missing():
  client, session = make_client([
      FakeResponse(json_data={'files': []}),      # find -> none
      FakeResponse(json_data={'id': 'created'}),  # create
      FakeResponse(json_data={'id': 'perm'}),     # share
  ])
  assert client.get_or_create_month_doc('Sept', share_email='a@b.com') == 'created'
  assert [c['method'] for c in session.calls] == ['GET', 'POST', 'POST']


def test_batch_update_posts_requests():
  client, session = make_client([FakeResponse(json_data={'documentId': 'd'})])
  reqs = [{'insertText': {'location': {'index': 1}, 'text': 'hi'}}]
  client.batch_update('doc1', reqs)
  call = session.calls[0]
  assert call['url'] == f'{api.DOCS_URL}/doc1:batchUpdate'
  assert call['json'] == {'requests': reqs}


def test_batch_update_noop_on_empty():
  client, session = make_client([])
  assert client.batch_update('doc1', []) == {}
  assert session.calls == []


def test_error_raised_on_non_2xx():
  client, _ = make_client([FakeResponse(status_code=403, text='forbidden')])
  with pytest.raises(api.GoogleDocsError, match='403'):
    client.get_document('doc1')


def test_default_credentials_path_prefers_env(monkeypatch):
  monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/creds.json')
  assert api.default_credentials_path() == '/tmp/creds.json'
  monkeypatch.delenv('GOOGLE_APPLICATION_CREDENTIALS', raising=False)
  assert api.default_credentials_path() == api.DEFAULT_CREDENTIALS_PATH
