import http


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
