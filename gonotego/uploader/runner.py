import time

from gonotego.common import events
from gonotego.common import internet
from gonotego.common import interprocess
from gonotego.common import leds
from gonotego.common import status
from gonotego.uploader import roam_uploader

Status = status.Status


def make_uploader():
  note_taking_system = secure_settings.NOTE_TAKING_SYSTEM.lower()
  if note_taking_system == 'roam':
    uploader = roam_uploader.Uploader()
  else:
    raise ValueError('Unexpected NOTE_TAKING_SYSTEM in settings', note_taking_system)


def main():
  print('Starting uploader.')
  note_events_queue = interprocess.get_note_events_queue()
  uploader = make_uploader()
  status.set(Status.UPLOADER_READY, True)

  internet_available = True
  last_upload = None
  while True:

    # Don't even try uploading notes if we don't have a connection.
    internet.wait_for_internet(on_disconnect=uploader.handle_disconnect)

    note_events = []
    while note_events_queue.size() > 0:
      print('Note event received')
      note_event_bytes = note_events_queue.get()
      note_event = events.NoteEvent.from_bytes(note_event_bytes)
      note_events.append(note_event)

    if note_events:
      leds.blue(2)
      status.set(Status.UPLOADER_ACTIVE, True)
      uploader.upload(note_events)
      last_upload = time.time()
      print('Uploaded.')
      leds.off(2)
      status.set(Status.UPLOADER_ACTIVE, False)

    if last_upload and time.time() - last_upload > 600:
      # X minutes have passed since the last upload.
      uploader.handle_inactivity()

    time.sleep(1)


if __name__ == '__main__':
  main()
