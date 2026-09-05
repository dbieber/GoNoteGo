from gonotego.uploader import runner


def test_is_configured():
  assert runner.is_configured('roam-graph-token-abc')
  assert not runner.is_configured('')
  assert not runner.is_configured(None)
  assert not runner.is_configured('<ROAM_API_TOKEN>')
