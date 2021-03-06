import http.client
import time

from gonotego.common import status

Status = status.Status


def is_internet_available(url='www.google.com'):
  """Determines if we are connected to the Internet."""
  connection = http.client.HTTPConnection(url, timeout=2)
  try:
    connection.request('HEAD', '/')
    connection.close()
    return True
  except:
    connection.close()
    return False


def wait_for_internet(url='www.google.com', on_disconnect=None):
  first = True
  while not is_internet_available(url):
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
