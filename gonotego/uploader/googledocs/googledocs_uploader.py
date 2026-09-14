"""Uploads notes to Google Docs, one document per month.

Layout inside each month's doc:

  September 2026                         <- the document's title (one per month)

  Monday, September 8th, 2026            <- day heading (Heading 1)
    6:30 AM                              <- session timestamp (Heading 2)
      - a note                           <- bulleted, nested by indent level
      - another note
        - an indented note
    7:14 AM
      - a later session's note

A new day heading is written when the day changes, and a new timestamp heading
when a session starts (after an END_SESSION, inactivity, or a restart). Notes are
a bulleted list nested by the tab/indent level, matching how they were typed.

Auth is a Google service account (see googledocs_api). Settings:
  GOOGLE_DOCS_CREDENTIALS: path to the service-account JSON (optional; defaults
    to GOOGLE_APPLICATION_CREDENTIALS or /home/pi/secrets/google_credentials.json).
  GOOGLE_DOCS_SHARE_EMAIL: email to share each new month's doc with (e.g. yours).
  GOOGLE_DOCS_FOLDER_ID: Drive folder id to create the month docs in (optional).
  GOOGLE_DOCS_TITLE_FORMAT: strftime for the month doc title (default '%B %Y').
"""
from datetime import datetime

from gonotego.common import events
from gonotego.settings import settings
from gonotego.uploader.googledocs import googledocs_api

DAY_STYLE = 'HEADING_1'
SESSION_STYLE = 'HEADING_2'
BULLET_PRESET = 'BULLET_DISC_CIRCLE_SQUARE'
DEFAULT_TITLE_FORMAT = 'Go Note Go Notes - %B %Y'


def clip(x, a, b):
  return max(a, min(x, b))


def ordinal_suffix(day):
  if 3 < day < 21:
    return 'th'
  return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


def day_title(dt):
  """e.g. 'Monday, September 8th, 2026'."""
  return f'{dt.strftime("%A, %B")} {dt.day}{ordinal_suffix(dt.day)}, {dt.year}'


def session_title(dt):
  """e.g. '6:30 AM' (no leading zero on the hour)."""
  return f'{dt.hour % 12 or 12}:{dt.minute:02d} {"AM" if dt.hour < 12 else "PM"}'


def month_title(dt):
  fmt = _setting('GOOGLE_DOCS_TITLE_FORMAT') or DEFAULT_TITLE_FORMAT
  return dt.strftime(fmt)


def note_datetime(note_event):
  """The note's effective time (clock + alleged-time offset), or now if unknown."""
  timestamp = note_event.effective_timestamp if note_event is not None else None
  return datetime.fromtimestamp(timestamp) if timestamp else datetime.now()


def _setting(key):
  """Returns a configured setting value, or None if unset or a '<PLACEHOLDER>'."""
  value = settings.get(key, None)
  if not value:
    return None
  if isinstance(value, str) and value.startswith('<') and value.endswith('>'):
    return None
  return value


def doc_end_index(document):
  """The index just past the document body, where new content is appended."""
  content = document.get('body', {}).get('content', [])
  return content[-1]['endIndex'] if content else 1


def _paragraph_text(element):
  runs = element.get('paragraph', {}).get('elements', [])
  return ''.join(run.get('textRun', {}).get('content', '') for run in runs)


def last_day_heading(document):
  """The text of the last Heading-1 (day) paragraph in the doc, or None."""
  last = None
  for element in document.get('body', {}).get('content', []):
    paragraph = element.get('paragraph')
    if paragraph and paragraph.get('paragraphStyle', {}).get('namedStyleType') == DAY_STYLE:
      last = _paragraph_text(element).strip()
  return last


class Uploader:

  def __init__(self, client=None):
    self._client = client
    self.indent_level = 0
    self.last_indent_level = -1
    self.session_started = False
    self.current_day = None
    self._month_doc = None  # (month_title, doc_id)

  def get_client(self):
    if self._client is None:
      self._client = googledocs_api.GoogleDocsClient(
          credentials_path=_setting('GOOGLE_DOCS_CREDENTIALS'))
    return self._client

  def month_doc_id(self, dt):
    """Finds or creates the doc for dt's month, caching within the month."""
    title = month_title(dt)
    if self._month_doc is None or self._month_doc[0] != title:
      doc_id = self.get_client().get_or_create_month_doc(
          title,
          folder_id=_setting('GOOGLE_DOCS_FOLDER_ID'),
          share_email=_setting('GOOGLE_DOCS_SHARE_EMAIL'))
      self._month_doc = (title, doc_id)
      self.current_day = None  # new/unknown doc; re-learn the last day from it
    return self._month_doc[1]

  def upload(self, note_events):
    """Appends the note events to the current month's doc. Returns True on success."""
    try:
      self._upload(note_events)
    except googledocs_api.GoogleDocsError as e:
      print(f'Google Docs upload failed: {e}')
      return False
    except Exception as e:  # noqa: BLE001 - keep notes queued on any failure
      print(f'Google Docs upload error: {e!r}')
      return False
    return True

  def _upload(self, note_events):
    submits = [e for e in note_events if e.action == events.SUBMIT and e.text.strip()]
    if not submits:
      self._apply_structural(note_events)
      return

    client = self.get_client()
    doc_id = self.month_doc_id(note_datetime(submits[0]))
    document = client.get_document(doc_id)
    insert_index = max(1, doc_end_index(document) - 1)
    if self.current_day is None:
      self.current_day = last_day_heading(document)

    parts = []
    paragraphs = []  # (start_offset, end_offset, kind)
    pos = 0

    def emit(text, kind):
      nonlocal pos
      start = pos
      parts.append(text)
      pos += len(text)
      paragraphs.append((start, pos, kind))

    for note_event in note_events:
      action = note_event.action
      if action == events.INDENT:
        self.indent_level = clip(self.indent_level + 1, 0, self.last_indent_level + 1)
      elif action == events.UNINDENT:
        self.indent_level = clip(self.indent_level - 1, 0, self.last_indent_level + 1)
      elif action == events.CLEAR_EMPTY:
        self.indent_level = 0
      elif action == events.ENTER_EMPTY:
        self.indent_level = clip(self.indent_level - 1, 0, self.last_indent_level + 1)
      elif action == events.END_SESSION:
        self.end_session()
      elif action == events.SUBMIT:
        text = note_event.text.strip()
        if not text:
          continue
        dt = note_datetime(note_event)
        day = day_title(dt)
        if day != self.current_day:
          emit(day + '\n', 'day')
          self.current_day = day
          self.session_started = False
        if not self.session_started:
          emit(session_title(dt) + '\n', 'session')
          self.session_started = True
        emit('\t' * self.indent_level + text + '\n', 'note')
        self.last_indent_level = self.indent_level

    if not paragraphs:
      return
    requests = self._build_requests(insert_index, ''.join(parts), paragraphs)
    client.batch_update(doc_id, requests)

  def _build_requests(self, insert_index, blob, paragraphs):
    """One insert of the whole blob, then paragraph styles and bullets.

    Style/bullet requests are ordered high-index-to-low so that bullet creation
    (which consumes leading tabs and shifts following indices) never invalidates
    an earlier request's range within the same batch.
    """
    requests = [{'insertText': {
        'location': {'index': insert_index}, 'text': blob}}]
    # Optionally force a single font across the whole insert (headings + notes).
    # Without GOOGLE_DOCS_FONT set, Google Docs' default two-font styling is kept
    # (Trebuchet MS headings, Arial body). Applied before the bullet requests
    # below, which shift indices by removing tabs; a text-style change has no
    # length effect, so this range stays valid.
    font = _setting('GOOGLE_DOCS_FONT')
    if font:
      requests.append({'updateTextStyle': {
          'range': {'startIndex': insert_index, 'endIndex': insert_index + len(blob)},
          'textStyle': {'weightedFontFamily': {'fontFamily': font}},
          'fields': 'weightedFontFamily'}})
    styling = []  # (start_index, request)
    i = 0
    n = len(paragraphs)
    while i < n:
      start, end, kind = paragraphs[i]
      if kind in ('day', 'session'):
        style = DAY_STYLE if kind == 'day' else SESSION_STYLE
        styling.append((insert_index + start, {'updateParagraphStyle': {
            'range': {'startIndex': insert_index + start, 'endIndex': insert_index + end},
            'paragraphStyle': {'namedStyleType': style},
            'fields': 'namedStyleType'}}))
        i += 1
      else:  # a maximal run of note paragraphs becomes one bulleted list
        group_start = start
        j = i
        while j < n and paragraphs[j][2] == 'note':
          j += 1
        group_end = paragraphs[j - 1][1]
        styling.append((insert_index + group_start, {'createParagraphBullets': {
            'range': {'startIndex': insert_index + group_start,
                      'endIndex': insert_index + group_end},
            'bulletPreset': BULLET_PRESET}}))
        i = j
    styling.sort(key=lambda item: item[0], reverse=True)
    requests.extend(request for _, request in styling)
    return requests

  def _apply_structural(self, note_events):
    """Updates indent/session state for a batch that has no writable notes."""
    for note_event in note_events:
      action = note_event.action
      if action == events.INDENT:
        self.indent_level = clip(self.indent_level + 1, 0, self.last_indent_level + 1)
      elif action == events.UNINDENT:
        self.indent_level = clip(self.indent_level - 1, 0, self.last_indent_level + 1)
      elif action == events.CLEAR_EMPTY:
        self.indent_level = 0
      elif action == events.ENTER_EMPTY:
        self.indent_level = clip(self.indent_level - 1, 0, self.last_indent_level + 1)
      elif action == events.END_SESSION:
        self.end_session()

  def handle_inactivity(self):
    self.end_session()

  def handle_disconnect(self):
    self.end_session()

  def end_session(self):
    self.session_started = False
    self.indent_level = 0
    self.last_indent_level = -1
