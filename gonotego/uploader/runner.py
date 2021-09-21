import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import leds
from gonotego.uploader import internet
from gonotego.uploader import roam_uploader


def upload(note_events):
  roam_uploader.upload(note_events)


def main():
  print('Starting uploader.')
  text_events_queue = interprocess.get_text_events_queue()
  note_events_queue = interprocess.get_note_events_queue()

  internet_available = True
  while True:

    # Don't even try uploading notes if we don't have a connection.
    if not internet.is_internet_available():
      if internet_available:
        print('No internet connection available. Sleeping')
      time.sleep(60)
      internet_available = False
      continue
    if not internet_available:
      print('Internet connection restored.')
    internet_available = True

    note_events = []
    while text_events_queue.size() > 0:
      print('Text event received. Converting to note event.')
      text_event_bytes = text_events_queue.get()
      text_event = events.TextEvent.from_bytes(text_event_bytes)
      note_event = events.NoteEvent(text_event.text, audio_filepath=None)
      note_events.append(note_event)

    while note_events_queue.size() > 0:
      print('Note event received')
      note_event_bytes = note_events_queue.get()
      note_event = events.NoteEvent.from_bytes(note_event_bytes)
      note_events.append(note_event)

    if note_events:
      leds.blue(2)
      upload(note_events)
      print('Uploaded.')
      leds.off(2)

    time.sleep(1)


if __name__ == '__main__':
  main()
