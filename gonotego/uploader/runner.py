import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import leds
from gonotego.uploader import roam_uploader


def upload(note_events):
  roam_uploader.upload(note_events)


def main():
  print('Starting uploader.')
  note_events_queue = interprocess.get_note_events_queue()

  while True:

    note_events = []
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
