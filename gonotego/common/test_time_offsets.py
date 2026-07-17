from datetime import datetime
import unittest
from unittest import mock

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import time_offsets


def make_note_event_bytes(text, timestamp, offset=0.0):
  return bytes(events.NoteEvent(
      text=text,
      action=events.SUBMIT,
      audio_filepath=None,
      timestamp=timestamp,
      offset=offset))


class TimeOffsetsTest(unittest.TestCase):

  def test_compute_offset(self):
    now = datetime(2026, 7, 16, 12, 0, 0).timestamp()
    alleged = datetime(2026, 7, 16, 15, 30, 0)
    self.assertEqual(time_offsets.compute_offset(alleged, now=now), 3.5 * 60 * 60)

  def test_compute_offset_negative(self):
    now = datetime(2026, 7, 16, 12, 0, 0).timestamp()
    alleged = datetime(2026, 7, 16, 11, 0, 0)
    self.assertEqual(time_offsets.compute_offset(alleged, now=now), -60 * 60)

  def test_parse_alleged_time(self):
    now = datetime(2026, 7, 16, 8, 0, 0).timestamp()
    dt = time_offsets.parse_alleged_time('3:30pm', now=now)
    self.assertIsNotNone(dt)
    self.assertEqual((dt.hour, dt.minute), (15, 30))

  def test_parse_alleged_time_snaps_to_nearest_occurrence(self):
    # At 8pm, ':xtime 1:00am' means 1am tonight (5h ahead), not 1am this
    # morning (19h ago).
    now = datetime(2026, 7, 16, 20, 0, 0).timestamp()
    dt = time_offsets.parse_alleged_time('1:00am', now=now)
    self.assertEqual(dt, datetime(2026, 7, 17, 1, 0, 0))

    # At 3am, ':xtime 11:00pm' means 11pm yesterday (4h ago).
    now = datetime(2026, 7, 16, 3, 0, 0).timestamp()
    dt = time_offsets.parse_alleged_time('11:00pm', now=now)
    self.assertEqual(dt, datetime(2026, 7, 15, 23, 0, 0))

  def test_parse_alleged_time_with_explicit_date_is_not_snapped(self):
    now = datetime(2026, 7, 16, 20, 0, 0).timestamp()
    dt = time_offsets.parse_alleged_time('july 20 3pm', now=now)
    self.assertEqual(dt, datetime(2026, 7, 20, 15, 0, 0))

  def test_parse_alleged_time_unparseable(self):
    now = datetime(2026, 7, 16, 8, 0, 0).timestamp()
    self.assertIsNone(time_offsets.parse_alleged_time('gobbledygook@#$', now=now))

  def test_describe_offset(self):
    self.assertEqual(time_offsets.describe_offset(3.5 * 60 * 60), '+3h30m00s')
    self.assertEqual(time_offsets.describe_offset(-90), '-0h01m30s')
    self.assertEqual(time_offsets.describe_offset(0), '+0h00m00s')

  def test_update_note_event_bytes_within_window(self):
    note_event_bytes = make_note_event_bytes('recent', timestamp=1000.0)
    updated = time_offsets.update_note_event_bytes(note_event_bytes, offset=120.0, cutoff=500.0)
    self.assertIsNotNone(updated)
    event = events.NoteEvent.from_bytes(updated)
    self.assertEqual(event.offset, 120.0)
    self.assertEqual(event.effective_timestamp, 1120.0)
    self.assertEqual(event.text, 'recent')

  def test_update_note_event_bytes_before_cutoff(self):
    note_event_bytes = make_note_event_bytes('old', timestamp=100.0)
    self.assertIsNone(
        time_offsets.update_note_event_bytes(note_event_bytes, offset=120.0, cutoff=500.0))

  def test_apply_offset_retroactively_rewrites_pending_events(self):
    values = [
        make_note_event_bytes('before cutoff', timestamp=100.0),
        make_note_event_bytes('after cutoff', timestamp=1000.0),
        make_note_event_bytes('also after', timestamp=2000.0),
    ]
    r = mock.MagicMock()
    r.lrange.return_value = list(values)
    with mock.patch.object(interprocess, 'get_redis_client', return_value=r):
      queue = interprocess.InterprocessQueue('test_queue')
      updated = time_offsets.apply_offset_retroactively(60.0, cutoff=500.0, queues=[queue])

    self.assertEqual(updated, 2)
    lset_calls = r.lset.call_args_list
    self.assertEqual(len(lset_calls), 2)
    # The event before the cutoff (index 0) is untouched.
    self.assertEqual([call.args[1] for call in lset_calls], [1, 2])
    for call in lset_calls:
      event = events.NoteEvent.from_bytes(call.args[2])
      self.assertEqual(event.offset, 60.0)

  def test_apply_offset_retroactively_already_offset_events_are_updated(self):
    values = [make_note_event_bytes('note', timestamp=1000.0, offset=30.0)]
    r = mock.MagicMock()
    r.lrange.return_value = list(values)
    with mock.patch.object(interprocess, 'get_redis_client', return_value=r):
      queue = interprocess.InterprocessQueue('test_queue')
      updated = time_offsets.apply_offset_retroactively(60.0, cutoff=500.0, queues=[queue])
    self.assertEqual(updated, 1)
    event = events.NoteEvent.from_bytes(r.lset.call_args.args[2])
    self.assertEqual(event.offset, 60.0)

  def test_update_items_no_changes(self):
    r = mock.MagicMock()
    r.lrange.return_value = [b'a', b'b']
    with mock.patch.object(interprocess, 'get_redis_client', return_value=r):
      queue = interprocess.InterprocessQueue('test_queue')
      updated = queue.update_items(lambda value: None)
    self.assertEqual(updated, 0)
    r.lset.assert_not_called()


if __name__ == '__main__':
  unittest.main()
