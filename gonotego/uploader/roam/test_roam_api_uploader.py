from datetime import datetime

from gonotego.common import events
from gonotego.uploader.blob import blob_uploader
from gonotego.uploader.roam import roam_api_uploader
from gonotego.uploader.roam import roam_backend_api


class FakeClient:
  """Records the tree of pages and blocks the uploader asks for."""

  def __init__(self):
    self.pages = {}  # title -> uid
    self.page_uids = {}  # title -> uid passed at creation
    self.blocks = []  # (parent_uid, text, uid)
    self.blocks_on_page = {}  # (page_uid, text) -> uid
    self.count = 0
    self.fail = False

  def get_or_create_page(self, title, uid=None):
    if title not in self.pages:
      self.pages[title] = uid or f'page{len(self.pages)}'
      self.page_uids[title] = uid
    return self.pages[title]

  def get_or_create_block_on_page(self, page_uid, text, order='last'):
    key = (page_uid, text)
    if key not in self.blocks_on_page:
      self.blocks_on_page[key] = self.create_block(page_uid, text, order=order)
    return self.blocks_on_page[key]

  def create_block(self, parent_uid, text, order='last', uid=None):
    if self.fail:
      raise roam_backend_api.RoamAPIError('boom')
    self.count += 1
    uid = uid or f'b{self.count}'
    self.blocks.append((parent_uid, text, uid))
    return uid

  def children(self, parent_uid):
    return [text for parent, text, _ in self.blocks if parent == parent_uid]

  def uid_of(self, text):
    return next(uid for _, t, uid in self.blocks if t == text)


TS = datetime(2026, 9, 5, 6, 30).timestamp()


def note(action, text='', audio_filepath='', timestamp=TS):
  return events.NoteEvent(text=text, action=action, audio_filepath=audio_filepath, timestamp=timestamp)


def test_upload_builds_daily_note_structure():
  client = FakeClient()
  uploader = roam_api_uploader.Uploader(client=client)

  ok = uploader.upload([
      note(events.SUBMIT, 'first'),
      note(events.SUBMIT, 'second'),
      note(events.INDENT),
      note(events.SUBMIT, 'nested under second'),
      note(events.UNINDENT),
      note(events.SUBMIT, 'third'),
      note(events.END_SESSION),
      note(events.SUBMIT, 'new session note', timestamp=datetime(2026, 9, 5, 7, 14).timestamp()),
  ])

  assert ok is True
  assert client.pages == {'September 5th, 2026': '09-05-2026'}
  assert client.page_uids['September 5th, 2026'] == '09-05-2026'
  assert client.children('09-05-2026') == ['[[Go Note Go Notes]]:']
  section_uid = client.uid_of('[[Go Note Go Notes]]:')
  assert client.children(section_uid) == ['06:30 AM', '07:14 AM']
  first_session = client.uid_of('06:30 AM')
  assert client.children(first_session) == ['first', 'second', 'third']
  assert client.children(client.uid_of('second')) == ['nested under second']
  assert client.children(client.uid_of('07:14 AM')) == ['new session note']


def test_enter_empty_pops_stack_and_clear_empty_clears_it():
  client = FakeClient()
  uploader = roam_api_uploader.Uploader(client=client)
  uploader.upload([
      note(events.SUBMIT, 'a'),
      note(events.INDENT),
      note(events.SUBMIT, 'a1'),
      note(events.INDENT),
      note(events.SUBMIT, 'a1x'),
      note(events.ENTER_EMPTY),
      note(events.SUBMIT, 'a2'),
      note(events.CLEAR_EMPTY),
      note(events.SUBMIT, 'b'),
  ])
  session = client.uid_of('06:30 AM')
  assert client.children(session) == ['a', 'b']
  assert client.children(client.uid_of('a')) == ['a1', 'a2']
  assert client.children(client.uid_of('a1')) == ['a1x']


def test_session_persists_across_uploads_until_ended():
  client = FakeClient()
  uploader = roam_api_uploader.Uploader(client=client)
  assert uploader.upload([note(events.SUBMIT, 'one')])
  assert uploader.upload([note(events.SUBMIT, 'two')])
  uploader.handle_inactivity()
  assert uploader.upload([note(events.SUBMIT, 'three')])
  section_uid = client.uid_of('[[Go Note Go Notes]]:')
  assert len(client.children(section_uid)) == 2
  assert client.children(client.uid_of('one')) == []
  assert client.children(client.blocks[1][2]) == ['one', 'two']


def test_api_error_returns_false_so_notes_stay_queued():
  client = FakeClient()
  client.fail = True
  uploader = roam_api_uploader.Uploader(client=client)
  assert uploader.upload([note(events.SUBMIT, 'one')]) is False


def test_audio_notes_get_tag_and_embed(monkeypatch, tmp_path):
  audio = tmp_path / 'clip.wav'
  audio.write_bytes(b'RIFF')
  monkeypatch.setattr(blob_uploader, 'make_client', lambda: object())
  monkeypatch.setattr(blob_uploader, 'upload_blob', lambda filepath, client: 'https://dl.example.com/clip.wav')
  client = FakeClient()
  uploader = roam_api_uploader.Uploader(client=client)

  assert uploader.upload([note(events.SUBMIT, 'spoken note', audio_filepath=str(audio))])

  session = client.uid_of('06:30 AM')
  assert client.children(session) == ['spoken note #[[unverified transcription]]']
  note_uid = client.uid_of('spoken note #[[unverified transcription]]')
  assert client.children(note_uid) == ['{{audio: https://dl.example.com/clip.wav}}']


def test_note_datetime_uses_effective_timestamp():
  event = note(events.SUBMIT, 'x')
  event.offset = 3600.0
  assert roam_api_uploader.note_datetime(event) == datetime(2026, 9, 5, 7, 30)
