import unittest
from gonotego.common import events


class EventsTest(unittest.TestCase):

  def test_audio_event(self):
    event = events.AudioEvent(
        action=events.AUDIO_DONE,
        filepath='/tmp/audio')
    event_bytes = bytes(event)
    event2 = events.AudioEvent.from_bytes(event_bytes)
    self.assertEqual(event, event2)

  def test_command_event(self):
    event = events.CommandEvent(
        command_text='time')
    event_bytes = bytes(event)
    event2 = events.CommandEvent.from_bytes(event_bytes)
    self.assertEqual(event, event2)

  def test_note_event(self):
    event = events.NoteEvent(
        text='Example note.',
        action=events.SUBMIT,
        audio_filepath='/tmp/audio',
        timestamp=None)
    event_bytes = bytes(event)
    event2 = events.NoteEvent.from_bytes(event_bytes)
    self.assertEqual(event, event2)

  def test_note_event_with_offset(self):
    event = events.NoteEvent(
        text='Example note.',
        action=events.SUBMIT,
        audio_filepath='/tmp/audio',
        timestamp=1000.0,
        offset=3600.0)
    event_bytes = bytes(event)
    event2 = events.NoteEvent.from_bytes(event_bytes)
    self.assertEqual(event, event2)
    self.assertEqual(event2.effective_timestamp, 4600.0)

  def test_note_event_from_bytes_without_offset(self):
    # Events serialized before the offset field existed still deserialize.
    event_bytes = b'{"text": "Old note.", "action": "submit", "audio_filepath": null, "timestamp": 1000.0}'
    event = events.NoteEvent.from_bytes(event_bytes)
    self.assertEqual(event.offset, 0.0)
    self.assertEqual(event.effective_timestamp, 1000.0)

  def test_led_event(self):
    event = events.LEDEvent(
        color=[0, 0, 0],
        ids=[0])
    event_bytes = bytes(event)
    event2 = events.LEDEvent.from_bytes(event_bytes)
    self.assertEqual(event, event2)
