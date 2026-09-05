from datetime import datetime

import pytest
import requests

from gonotego.uploader.roam import roam_backend_api as api


class FakeResponse:

  def __init__(self, status_code=200, json_data=None, headers=None, text=''):
    self.status_code = status_code
    self._json = json_data if json_data is not None else {}
    self.headers = headers or {}
    self.text = text
    has_location = 'Location' in self.headers
    self.is_redirect = has_location and status_code in (301, 302, 303, 307, 308)
    self.is_permanent_redirect = has_location and status_code in (301, 308)
    self.ok = status_code < 400

  def json(self):
    return self._json


class FakeSession:

  def __init__(self, responses):
    self.responses = list(responses)
    self.calls = []

  def post(self, url, headers=None, json=None, allow_redirects=True, timeout=None):
    self.calls.append({'url': url, 'headers': headers, 'json': json, 'allow_redirects': allow_redirects})
    response = self.responses.pop(0)
    if isinstance(response, Exception):
      raise response
    return response


REDIRECT = FakeResponse(308, headers={'Location': 'https://peer-24.api.roamresearch.com:3001/api/graph/g/q'})


def make_client(responses, **kwargs):
  session = FakeSession(responses)
  client = api.RoamBackendClient(token='tok', graph='g', session=session, **kwargs)
  return client, session


def test_follows_peer_redirect_and_remembers_peer():
  client, session = make_client([REDIRECT, FakeResponse(json_data={'result': [['abc']]}), FakeResponse(json_data={'result': []})])

  assert client.q('[:find ?x]', ['arg']) == [['abc']]
  assert client.q('[:find ?x]') == []

  assert session.calls[0]['url'] == 'https://api.roamresearch.com/api/graph/g/q'
  assert session.calls[1]['url'] == 'https://peer-24.api.roamresearch.com:3001/api/graph/g/q'
  assert session.calls[2]['url'] == 'https://peer-24.api.roamresearch.com:3001/api/graph/g/q'
  assert session.calls[0]['json'] == {'query': '[:find ?x]', 'args': ['arg']}
  assert session.calls[2]['json'] == {'query': '[:find ?x]'}
  for call in session.calls:
    assert call['allow_redirects'] is False
    assert call['headers']['Authorization'] == 'Bearer tok'
    assert call['headers']['x-authorization'] == 'Bearer tok'


def test_unexpected_redirect_raises():
  client, _ = make_client([FakeResponse(308, headers={'Location': 'https://elsewhere.example.com/'})])
  with pytest.raises(api.RoamAPIError):
    client.q('[:find ?x]')


def test_invalid_token_raises():
  client, _ = make_client([FakeResponse(401)])
  with pytest.raises(api.RoamAPIError, match='token'):
    client.q('[:find ?x]')


def test_bad_request_includes_server_message():
  client, _ = make_client([FakeResponse(400, text='{"message":"nope"}')])
  with pytest.raises(api.RoamAPIError, match='nope'):
    client.write({'action': 'create-block'})


def test_not_ready_is_retried(monkeypatch):
  monkeypatch.setattr(api.time, 'sleep', lambda seconds: None)
  client, session = make_client([FakeResponse(503), FakeResponse(json_data={'result': [['uid']]})], retries=1)
  assert client.q('[:find ?x]') == [['uid']]
  assert len(session.calls) == 2


def test_connection_error_is_wrapped(monkeypatch):
  monkeypatch.setattr(api.time, 'sleep', lambda seconds: None)
  client, _ = make_client([requests.ConnectionError('down'), requests.ConnectionError('down')], retries=1)
  with pytest.raises(api.RoamAPIError, match='Could not reach'):
    client.q('[:find ?x]')


def test_get_page_uid():
  client, _ = make_client([FakeResponse(json_data={'result': [['09-05-2026']]}), FakeResponse(json_data={'result': []})])
  assert client.get_page_uid('September 5th, 2026') == '09-05-2026'
  assert client.get_page_uid('Missing') is None


def test_get_or_create_page_creates_with_uid():
  client, session = make_client([FakeResponse(json_data={'result': []}), FakeResponse()])
  assert client.get_or_create_page('September 5th, 2026', uid='09-05-2026') == '09-05-2026'
  assert session.calls[1]['url'].endswith('/api/graph/g/write')
  assert session.calls[1]['json'] == {'action': 'create-page', 'page': {'title': 'September 5th, 2026', 'uid': '09-05-2026'}}


def test_create_block_generates_uid_and_appends_last():
  client, session = make_client([FakeResponse()])
  uid = client.create_block('parent', 'hello')
  assert len(uid) == api.UID_LENGTH
  assert set(uid) <= set(api.UID_ALPHABET)
  assert session.calls[0]['json'] == {
      'action': 'create-block',
      'location': {'parent-uid': 'parent', 'order': 'last'},
      'block': {'string': 'hello', 'uid': uid},
  }


def test_get_or_create_block_on_page_reuses_existing():
  client, session = make_client([FakeResponse(json_data={'result': [['existing']]})])
  assert client.get_or_create_block_on_page('page', '[[Go Note Go Notes]]:') == 'existing'
  assert len(session.calls) == 1
  assert session.calls[0]['json']['args'] == ['page', '[[Go Note Go Notes]]:']


def test_requires_token():
  with pytest.raises(ValueError):
    api.RoamBackendClient(token='', graph='g')


@pytest.mark.parametrize('day, expected', [
    (1, 'September 1st, 2026'), (2, 'September 2nd, 2026'), (3, 'September 3rd, 2026'),
    (4, 'September 4th, 2026'), (11, 'September 11th, 2026'), (12, 'September 12th, 2026'),
    (13, 'September 13th, 2026'), (21, 'September 21st, 2026'), (22, 'September 22nd, 2026'),
    (23, 'September 23rd, 2026'), (30, 'September 30th, 2026'),
])
def test_daily_note_title(day, expected):
  assert api.daily_note_title(datetime(2026, 9, day, 6, 30)) == expected


def test_daily_note_title_31st():
  assert api.daily_note_title(datetime(2026, 1, 31)) == 'January 31st, 2026'


def test_daily_note_uid():
  assert api.daily_note_uid(datetime(2026, 9, 5)) == '09-05-2026'


def test_normalize_graph_name():
  assert api.normalize_graph_name('app/playground') == 'playground'
  assert api.normalize_graph_name('playground') == 'playground'
