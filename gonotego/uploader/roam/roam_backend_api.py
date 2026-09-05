"""Client for the Roam Research backend API.

Talks to Roam over HTTPS instead of driving Roam in a browser. Roam's web app
sits behind a bot-verification challenge that headless browsers on the Pi fail,
so the browser-based uploader can no longer reach the graph; the backend API
has no such check.

Create a token in Roam under Settings > Graph > API tokens (edit access), then
run ":set ROAM_API_TOKEN <token>" on Go Note Go or add it to secure_settings.

Reference: https://github.com/Roam-Research/backend-sdks
Docs: https://roamresearch.com/#/app/developer-documentation/page/bmYYKQ4vf
"""
import random
import re
import string
import time

import requests

BASE_URL = 'https://api.roamresearch.com'
UID_ALPHABET = string.ascii_letters + string.digits + '-_'
UID_LENGTH = 9
PEER_RE = re.compile(r'https://(peer-\d+)[^:/]*:(\d+)')
MAX_REDIRECTS = 5
RETRY_DELAY_SECONDS = 3

PAGE_UID_QUERY = """
[:find ?uid
 :in $ ?title
 :where
 [?page :node/title ?title]
 [?page :block/uid ?uid]]
"""

BLOCK_ON_PAGE_QUERY = """
[:find ?uid
 :in $ ?page-uid ?string
 :where
 [?page :block/uid ?page-uid]
 [?block :block/page ?page]
 [?block :block/string ?string]
 [?block :block/uid ?uid]]
"""


class RoamAPIError(Exception):
  """The Roam backend API rejected a request or could not be reached."""


class RoamNotReadyError(RoamAPIError):
  """The graph is still starting up on Roam's side; the request can be retried."""


def generate_uid():
  """Returns a new random block uid in Roam's 9-character format."""
  return ''.join(random.choice(UID_ALPHABET) for _ in range(UID_LENGTH))


def ordinal_suffix(day):
  """Returns 'st', 'nd', 'rd', or 'th' for a day of the month."""
  if 3 < day < 21:
    return 'th'
  return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


def daily_note_title(dt):
  """Returns the title Roam uses for the Daily Notes page of a date, e.g. 'September 5th, 2026'."""
  return f'{dt.strftime("%B")} {dt.day}{ordinal_suffix(dt.day)}, {dt.year}'


def daily_note_uid(dt):
  """Returns the uid Roam uses for the Daily Notes page of a date, e.g. '09-05-2026'."""
  return dt.strftime('%m-%d-%Y')


def normalize_graph_name(graph):
  """Strips the 'app/' prefix the browser uploader accepts in ROAM_GRAPH."""
  if graph.startswith('app/'):
    return graph[len('app/'):]
  return graph


class RoamBackendClient:
  """A minimal client for Roam's q and write endpoints."""

  def __init__(self, token, graph, session=None, timeout=60, retries=3):
    if not token:
      raise ValueError('A Roam API token is required.')
    self._token = token
    self.graph = normalize_graph_name(graph)
    self._session = session or requests.Session()
    self._timeout = timeout
    self._retries = retries
    # Roam redirects the first request to a graph-specific peer; we remember it.
    self._base_url = BASE_URL

  def _headers(self):
    return {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'Authorization': f'Bearer {self._token}',
        'x-authorization': f'Bearer {self._token}',
    }

  def _call_once(self, endpoint, body):
    for _ in range(MAX_REDIRECTS):
      url = f'{self._base_url}/api/graph/{self.graph}/{endpoint}'
      response = self._session.post(
          url, headers=self._headers(), json=body,
          allow_redirects=False, timeout=self._timeout)
      if response.is_redirect or response.is_permanent_redirect:
        location = response.headers.get('Location', '')
        match = PEER_RE.search(location)
        if not match:
          raise RoamAPIError(f'Unexpected redirect from Roam API: {location!r}')
        peer, port = match.groups()
        self._base_url = f'https://{peer}.api.roamresearch.com:{port}'
        continue
      break
    else:
      raise RoamAPIError('Too many redirects from the Roam API.')

    if response.status_code == 401:
      raise RoamAPIError('Roam API token is invalid or lacks permission for this graph.')
    if response.status_code == 503:
      raise RoamNotReadyError('Roam graph is not ready yet; retry in a few seconds.')
    if not response.ok:
      raise RoamAPIError(f'Roam API error (HTTP {response.status_code}): {response.text[:500]}')
    return response

  def call(self, endpoint, body):
    """POSTs body to the graph's endpoint ('q', 'pull', or 'write') and returns the response.

    Retries transient failures (connection problems, graph not ready) a few times.
    Raises RoamAPIError if the request ultimately fails.
    """
    attempt = 0
    while True:
      try:
        return self._call_once(endpoint, body)
      except (requests.RequestException, RoamNotReadyError) as e:
        attempt += 1
        if attempt > self._retries:
          if isinstance(e, RoamAPIError):
            raise
          raise RoamAPIError(f'Could not reach the Roam API: {e!r}') from e
        print(f'Roam API request failed ({e!r}); retrying in {RETRY_DELAY_SECONDS}s.')
        time.sleep(RETRY_DELAY_SECONDS)

  def q(self, query, args=None):
    """Runs a datalog query and returns its result rows."""
    body = {'query': query}
    if args is not None:
      body['args'] = list(args)
    return self.call('q', body).json()['result']

  def write(self, body):
    return self.call('write', body)

  def get_page_uid(self, title):
    """Returns the uid of the page with this title, or None if it doesn't exist."""
    results = self.q(PAGE_UID_QUERY, [title])
    return results[0][0] if results else None

  def create_page(self, title, uid=None):
    """Creates a page and returns its uid."""
    page = {'title': title}
    if uid:
      page['uid'] = uid
    self.write({'action': 'create-page', 'page': page})
    return uid or self.get_page_uid(title)

  def get_or_create_page(self, title, uid=None):
    return self.get_page_uid(title) or self.create_page(title, uid=uid)

  def get_block_on_page_uid(self, page_uid, text):
    """Returns the uid of a block anywhere on the page with exactly this text, or None."""
    results = self.q(BLOCK_ON_PAGE_QUERY, [page_uid, text])
    return results[0][0] if results else None

  def create_block(self, parent_uid, text, order='last', uid=None):
    """Creates a child block under parent_uid and returns the new block's uid.

    order is an integer position or 'last'.
    """
    uid = uid or generate_uid()
    self.write({
        'action': 'create-block',
        'location': {'parent-uid': parent_uid, 'order': order},
        'block': {'string': text, 'uid': uid},
    })
    return uid

  def get_or_create_block_on_page(self, page_uid, text, order='last'):
    return self.get_block_on_page_uid(page_uid, text) or self.create_block(page_uid, text, order=order)
