import unittest
from unittest import mock

from gonotego.common import internet


def make_connection(status=204, body=b''):
  """Creates a mock http.client.HTTPConnection whose response is fixed."""
  connection = mock.MagicMock()
  response = mock.MagicMock()
  response.status = status
  response.read.return_value = body
  connection.getresponse.return_value = response
  return connection


class InternetTest(unittest.TestCase):

  def test_genuine_204_counts_as_internet(self):
    connection = make_connection(status=204, body=b'')
    with mock.patch.object(internet.http.client, 'HTTPConnection', return_value=connection):
      self.assertTrue(internet.is_internet_available())

  def test_captive_portal_login_page_is_not_internet(self):
    # A captive portal accepts the connection but answers with its own page.
    connection = make_connection(status=200, body=b'<html>Hotel wifi login</html>')
    with mock.patch.object(internet.http.client, 'HTTPConnection', return_value=connection):
      self.assertFalse(internet.is_internet_available())

  def test_captive_portal_redirect_is_not_internet(self):
    connection = make_connection(status=302, body=b'')
    with mock.patch.object(internet.http.client, 'HTTPConnection', return_value=connection):
      self.assertFalse(internet.is_internet_available())

  def test_204_with_unexpected_body_is_not_internet(self):
    connection = make_connection(status=204, body=b'unexpected')
    with mock.patch.object(internet.http.client, 'HTTPConnection', return_value=connection):
      self.assertFalse(internet.is_internet_available())

  def test_connection_error_is_not_internet(self):
    connection = mock.MagicMock()
    connection.request.side_effect = OSError('no route to host')
    with mock.patch.object(internet.http.client, 'HTTPConnection', return_value=connection):
      self.assertFalse(internet.is_internet_available())

  def test_second_endpoint_can_confirm_internet(self):
    # If the first endpoint is unreachable but the second returns a genuine
    # 204, we are online.
    bad = mock.MagicMock()
    bad.request.side_effect = OSError('no route to host')
    good = make_connection(status=204, body=b'')
    with mock.patch.object(internet.http.client, 'HTTPConnection', side_effect=[bad, good]):
      self.assertTrue(internet.is_internet_available())


if __name__ == '__main__':
  unittest.main()
