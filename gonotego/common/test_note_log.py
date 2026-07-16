import json
import os
import tempfile
import time
import unittest
from unittest import mock

from gonotego.common import events
from gonotego.common import note_log


class NoteLogTest(unittest.TestCase):

  def setUp(self):
    self.tempdir = tempfile.TemporaryDirectory()
    self.addCleanup(self.tempdir.cleanup)

  def make_note_event(self, text='Example note.', timestamp=None):
    return events.NoteEvent(
        text=text,
        action=events.SUBMIT,
        audio_filepath=None,
        timestamp=timestamp if timestamp is not None else time.time())

  def test_log_writes_note_event(self):
    log_dir = os.path.join(self.tempdir.name, 'note_log')
    note_event = self.make_note_event(text='A note to keep.')
    with mock.patch.object(note_log, 'NOTE_LOG_DIR', log_dir):
      filepath = note_log.log(note_event)
    self.assertIsNotNone(filepath)
    with open(filepath) as f:
      entry = json.loads(f.read())
    self.assertEqual(entry['text'], 'A note to keep.')
    self.assertEqual(entry['action'], events.SUBMIT)
    self.assertEqual(entry['timestamp'], note_event.timestamp)

  def test_log_appends_multiple_events(self):
    log_dir = os.path.join(self.tempdir.name, 'note_log')
    timestamp = time.time()
    with mock.patch.object(note_log, 'NOTE_LOG_DIR', log_dir):
      filepath = note_log.log(self.make_note_event(text='one', timestamp=timestamp))
      note_log.log(self.make_note_event(text='two', timestamp=timestamp))
    with open(filepath) as f:
      lines = f.read().splitlines()
    self.assertEqual([json.loads(line)['text'] for line in lines], ['one', 'two'])

  def test_log_never_raises(self):
    # Even with an unwritable log directory, capturing a note must not raise.
    log_dir = os.path.join(self.tempdir.name, 'not-a-dir')
    with open(log_dir, 'w') as f:
      f.write('a file where the directory should be')
    with mock.patch.object(note_log, 'NOTE_LOG_DIR', log_dir):
      self.assertIsNone(note_log.log(self.make_note_event()))

  def write_file(self, name, age_days, content=b'x' * 1024):
    filepath = os.path.join(self.tempdir.name, name)
    with open(filepath, 'wb') as f:
      f.write(content)
    old_time = time.time() - age_days * 24 * 60 * 60
    os.utime(filepath, (old_time, old_time))
    return filepath

  def test_cleanup_is_noop_without_disk_pressure(self):
    self.write_file('ancient.wav', age_days=400)
    usage = mock.MagicMock(free=note_log.MIN_FREE_BYTES * 10)
    with mock.patch.object(note_log.shutil, 'disk_usage', return_value=usage):
      deleted = note_log.cleanup(directory=self.tempdir.name)
    self.assertEqual(deleted, [])

  def test_cleanup_never_deletes_recent_files(self):
    recent = self.write_file('recent.wav', age_days=30)
    five_months = self.write_file('five-months.jsonl', age_days=150)
    usage = mock.MagicMock(free=0)
    with mock.patch.object(note_log.shutil, 'disk_usage', return_value=usage):
      deleted = note_log.cleanup(directory=self.tempdir.name)
    self.assertEqual(deleted, [])
    self.assertTrue(os.path.exists(recent))
    self.assertTrue(os.path.exists(five_months))

  def test_cleanup_deletes_old_files_under_disk_pressure(self):
    old_wav = self.write_file('old.wav', age_days=400)
    old_log = self.write_file('old.jsonl', age_days=250)
    recent = self.write_file('recent.wav', age_days=10)
    usage = mock.MagicMock(free=0)
    with mock.patch.object(note_log.shutil, 'disk_usage', return_value=usage):
      deleted = note_log.cleanup(directory=self.tempdir.name)
    self.assertEqual(sorted(deleted), sorted([old_wav, old_log]))
    self.assertFalse(os.path.exists(old_wav))
    self.assertFalse(os.path.exists(old_log))
    self.assertTrue(os.path.exists(recent))

  def test_cleanup_stops_once_enough_space_is_free(self):
    # Oldest file is deleted first; once free space recovers, deletion stops.
    oldest = self.write_file('oldest.wav', age_days=500, content=b'x' * 4096)
    newer = self.write_file('newer.wav', age_days=300, content=b'x' * 4096)
    usage = mock.MagicMock(free=0)
    with mock.patch.object(note_log.shutil, 'disk_usage', return_value=usage):
      deleted = note_log.cleanup(directory=self.tempdir.name, min_free_bytes=1024)
    self.assertEqual(deleted, [oldest])
    self.assertTrue(os.path.exists(newer))

  def test_cleanup_ignores_foreign_file_types(self):
    precious = self.write_file('precious.db', age_days=500)
    usage = mock.MagicMock(free=0)
    with mock.patch.object(note_log.shutil, 'disk_usage', return_value=usage):
      deleted = note_log.cleanup(directory=self.tempdir.name)
    self.assertEqual(deleted, [])
    self.assertTrue(os.path.exists(precious))


if __name__ == '__main__':
  unittest.main()
