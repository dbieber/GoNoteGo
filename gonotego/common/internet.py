import http.client
import time

from gonotego.common import status

Status = status.Status

# Endpoints that are known to return HTTP 204 with an empty body.
# Captive portals (hotel wifi login pages, etc.) intercept requests and answer
# with their own page -- typically a 200 or a redirect with a body. Requiring
# an exact 204-with-no-content response distinguishes real internet access
# from a captive portal that is merely accepting TCP connections.
CONNECTIVITY_CHECK_ENDPOINTS = (
    ('connectivitycheck.gstatic.com', '/generate_204'),
    ('clients3.google.com', '/generate_204'),
)


def check_endpoint(host, path, timeout=2):
  """Checks a single connectivity-check endpoint for a genuine 204 response."""
  connection = http.client.HTTPConnection(host, timeout=timeout)
  try:
    connection.request('GET', path)
    response = connection.getresponse()
    body = response.read()
    return response.status == 204 and not body
  except Exception:
    return False
  finally:
    connection.close()


def is_internet_available():
  """Determines if we are connected to the Internet.

  Returns True only if a known endpoint returns its expected no-content
  response, so a captive portal doesn't count as having internet.
  """
  for host, path in CONNECTIVITY_CHECK_ENDPOINTS:
    if check_endpoint(host, path):
      return True
  return False


def wait_for_internet(on_disconnect=None):
  first = True
  while not is_internet_available():
    if first:
      print('No internet connection available. Sleeping.')
      status.set(Status.INTERNET_AVAILABLE, False)
      first = False
      if on_disconnect is not None:
        on_disconnect()
    time.sleep(60)
  if not first:
    print('Internet connection restored.')
  status.set(Status.INTERNET_AVAILABLE, True)
