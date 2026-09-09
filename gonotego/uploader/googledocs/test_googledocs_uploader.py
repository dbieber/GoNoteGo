from datetime import datetime

import pytest

from gonotego.common import events
from gonotego.uploader.googledocs import googledocs_api
from gonotego.uploader.googledocs import googledocs_uploader as gd


@pytest.fixture(autouse=True)
def stub_settings(monkeypatch):
  """Keep the uploader off Redis: settings come from this dict (default None)."""
  store = {}
  monkeypatch.setattr(gd.settings, 'get', lambda key, default=None: store.get(key, default))
  return store


class FakeClient:

  def __init__(self):
    self.docs = {}            # title -> doc_id
    self.created = []         # (title, folder_id, share_email)
    self.doc_state = {}       # doc_id -> {'end_index', 'last_day'}
    self.batches = []         # (doc_id, requests)
    self.get_or_create_calls = 0
    self.fail = False

  def get_or_create_month_doc(self, name, folder_id=None, share_email=None):
    self.get_or_create_calls += 1
    if name not in self.docs:
      doc_id = f'doc:{name}'
      self.docs[name] = doc_id
      self.created.append((name, folder_id, share_email))
      self.doc_state[doc_id] = {'end_index': 2, 'last_day': None}
    return self.docs[name]

  def set_existing_day(self, doc_id, day_text):
    self.doc_state.setdefault(doc_id, {'end_index': 2, 'last_day': None})
    self.doc_state[doc_id]['last_day'] = day_text

  def get_document(self, doc_id):
    state = self.doc_state.setdefault(doc_id, {'end_index': 2, 'last_day': None})
    content = [{'endIndex': 1}]
    if state['last_day']:
      content.append({
          'endIndex': 1 + len(state['last_day']) + 1,
          'paragraph': {
              'paragraphStyle': {'namedStyleType': gd.DAY_STYLE},
              'elements': [{'textRun': {'content': state['last_day'] + '\n'}}]}})
    content.append({'endIndex': state['end_index'],
                    'paragraph': {'elements': [{'textRun': {'content': ''}}]}})
    return {'body': {'content': content}}

  def batch_update(self, doc_id, requests):
    if self.fail:
      raise googledocs_api.GoogleDocsError('boom')
    self.batches.append((doc_id, requests))
    inserted = sum(len(r['insertText']['text']) for r in requests if 'insertText' in r)
    self.doc_state[doc_id]['end_index'] += inserted
    return {}


def note(action, text='', timestamp=None):
  ts = timestamp if timestamp is not None else datetime(2026, 9, 8, 6, 30).timestamp()
  return events.NoteEvent(text=text, action=action, audio_filepath='', timestamp=ts)


def insert_text(requests):
  return requests[0]['insertText']['text']


def request_kinds(requests):
  kinds = []
  for r in requests:
    if 'insertText' in r:
      kinds.append('insert')
    elif 'createParagraphBullets' in r:
      kinds.append('bullets')
    elif 'updateParagraphStyle' in r:
      kinds.append(r['updateParagraphStyle']['paragraphStyle']['namedStyleType'])
  return kinds


def test_single_session_layout():
  client = FakeClient()
  up = gd.Uploader(client=client)
  ts = datetime(2026, 9, 8, 6, 30).timestamp()
  ok = up.upload([note(events.SUBMIT, 'first', ts), note(events.SUBMIT, 'second', ts)])

  assert ok is True
  assert client.created == [('September 2026', None, None)]
  doc_id, requests = client.batches[0]
  assert doc_id == 'doc:September 2026'
  day = gd.day_title(datetime(2026, 9, 8, 6, 30))
  session = gd.session_title(datetime(2026, 9, 8, 6, 30))
  assert insert_text(requests) == f'{day}\n{session}\nfirst\nsecond\n'
  # insert first, then styling high-index-to-low: notes bullets, session H2, day H1.
  assert request_kinds(requests) == ['insert', 'bullets', gd.SESSION_STYLE, gd.DAY_STYLE]


def test_session_and_day_headings_get_styles_over_correct_ranges():
  client = FakeClient()
  up = gd.Uploader(client=client)
  up.upload([note(events.SUBMIT, 'hello')])
  _, requests = client.batches[0]
  day = gd.day_title(datetime(2026, 9, 8, 6, 30))
  session = gd.session_title(datetime(2026, 9, 8, 6, 30))
  insert_index = 1  # end_index(2) - 1
  by_type = {request_kinds([r])[0]: r for r in requests[1:]}
  day_range = by_type[gd.DAY_STYLE]['updateParagraphStyle']['range']
  assert day_range == {'startIndex': insert_index, 'endIndex': insert_index + len(day) + 1}
  session_start = insert_index + len(day) + 1
  session_range = by_type[gd.SESSION_STYLE]['updateParagraphStyle']['range']
  assert session_range == {'startIndex': session_start,
                           'endIndex': session_start + len(session) + 1}
  bullets_range = by_type['bullets']['createParagraphBullets']['range']
  assert bullets_range['startIndex'] == session_range['endIndex']


def test_indentation_uses_tabs_and_one_bullet_group():
  client = FakeClient()
  up = gd.Uploader(client=client)
  up.upload([
      note(events.SUBMIT, 'a'),
      note(events.INDENT),
      note(events.SUBMIT, 'a1'),
      note(events.INDENT),
      note(events.SUBMIT, 'a1x'),
      note(events.UNINDENT),
      note(events.SUBMIT, 'a2'),
  ])
  _, requests = client.batches[0]
  text = insert_text(requests)
  assert '\na\n' in text
  assert '\n\ta1\n' in text
  assert '\n\t\ta1x\n' in text
  assert '\n\ta2\n' in text
  # A single contiguous run of notes -> exactly one bullets request.
  assert request_kinds(requests).count('bullets') == 1


def test_new_session_same_day_no_duplicate_day_heading():
  client = FakeClient()
  up = gd.Uploader(client=client)
  t1 = datetime(2026, 9, 8, 6, 30).timestamp()
  t2 = datetime(2026, 9, 8, 7, 14).timestamp()
  up.upload([note(events.SUBMIT, 'one', t1), note(events.END_SESSION, timestamp=t1),
             note(events.SUBMIT, 'two', t2)])
  _, requests = client.batches[0]
  kinds = request_kinds(requests)
  assert kinds.count(gd.DAY_STYLE) == 1      # one day heading
  assert kinds.count(gd.SESSION_STYLE) == 2  # two session timestamps
  text = insert_text(requests)
  assert gd.session_title(datetime(2026, 9, 8, 6, 30)) in text
  assert gd.session_title(datetime(2026, 9, 8, 7, 14)) in text


def test_day_rollover_adds_new_day_heading():
  client = FakeClient()
  up = gd.Uploader(client=client)
  t1 = datetime(2026, 9, 8, 23, 55).timestamp()
  t2 = datetime(2026, 9, 9, 0, 5).timestamp()
  up.upload([note(events.SUBMIT, 'late', t1), note(events.SUBMIT, 'early', t2)])
  _, requests = client.batches[0]
  assert request_kinds(requests).count(gd.DAY_STYLE) == 2


def test_existing_day_heading_in_doc_is_not_repeated():
  client = FakeClient()
  up = gd.Uploader(client=client)
  today = gd.day_title(datetime(2026, 9, 8, 6, 30))
  # Pre-create the month doc and mark today's heading already present.
  doc_id = client.get_or_create_month_doc('September 2026')
  client.set_existing_day(doc_id, today)
  up.upload([note(events.SUBMIT, 'x')])
  _, requests = client.batches[0]
  assert gd.DAY_STYLE not in request_kinds(requests)     # no new day heading
  assert gd.SESSION_STYLE in request_kinds(requests)     # but a session heading


def test_month_doc_cached_across_uploads():
  client = FakeClient()
  up = gd.Uploader(client=client)
  up.upload([note(events.SUBMIT, 'one')])
  up.upload([note(events.SUBMIT, 'two')])
  assert client.get_or_create_calls == 1  # same month -> resolved once
  assert len(client.batches) == 2


def test_folder_and_share_settings_passed(stub_settings):
  stub_settings['GOOGLE_DOCS_FOLDER_ID'] = 'folderX'
  stub_settings['GOOGLE_DOCS_SHARE_EMAIL'] = 'andrea@example.com'
  client = FakeClient()
  gd.Uploader(client=client).upload([note(events.SUBMIT, 'x')])
  assert client.created == [('September 2026', 'folderX', 'andrea@example.com')]


def test_placeholder_settings_treated_as_unset(stub_settings):
  stub_settings['GOOGLE_DOCS_SHARE_EMAIL'] = '<GOOGLE_DOCS_SHARE_EMAIL>'
  client = FakeClient()
  gd.Uploader(client=client).upload([note(events.SUBMIT, 'x')])
  assert client.created == [('September 2026', None, None)]


def test_custom_title_format(stub_settings):
  stub_settings['GOOGLE_DOCS_TITLE_FORMAT'] = 'GNG %Y-%m'
  client = FakeClient()
  gd.Uploader(client=client).upload([note(events.SUBMIT, 'x')])
  assert client.created[0][0] == 'GNG 2026-09'


def test_empty_submits_skipped():
  client = FakeClient()
  up = gd.Uploader(client=client)
  assert up.upload([note(events.SUBMIT, '   ')]) is True
  assert client.batches == []  # nothing to write, no doc touched


def test_upload_returns_false_on_api_error():
  client = FakeClient()
  client.fail = True
  assert gd.Uploader(client=client).upload([note(events.SUBMIT, 'x')]) is False


def test_session_title_formatting():
  assert gd.session_title(datetime(2026, 9, 8, 6, 30)) == '6:30 AM'
  assert gd.session_title(datetime(2026, 9, 8, 0, 5)) == '12:05 AM'
  assert gd.session_title(datetime(2026, 9, 8, 13, 9)) == '1:09 PM'
  assert gd.session_title(datetime(2026, 9, 8, 12, 0)) == '12:00 PM'


@pytest.mark.parametrize('day, expected_suffix', [
    (1, 'st'), (2, 'nd'), (3, 'rd'), (4, 'th'), (11, 'th'), (12, 'th'),
    (13, 'th'), (21, 'st'), (22, 'nd'), (23, 'rd'), (31, 'st')])
def test_day_title_ordinals(day, expected_suffix):
  title = gd.day_title(datetime(2026, 1, day, 9, 0))
  assert title.endswith(f'{day}{expected_suffix}, 2026')
