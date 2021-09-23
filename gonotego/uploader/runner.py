import time

from gonotego.common import events
from gonotego.common import internet
from gonotego.common import interprocess
from gonotego.common import leds
from gonotego.common import status
from gonotego.uploader import roam_uploader

Status = status.Status


def main():
  print('Starting uploader.')
  text_events_queue = interprocess.get_text_events_queue()
  note_events_queue = interprocess.get_note_events_queue()
  uploader = roam_uploader.Uploader()
  status.set(Status.UPLOADER_READY, True)

  internet_available = True
  last_upload = None
  while True:

    # Don't even try uploading notes if we don't have a connection.
    internet.wait_for_internet(on_disconnect=uploader.close_browser)

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
      status.set(Status.UPLOADER_ACTIVE, True)
      uploader.upload(note_events)
      last_upload = time.time()
      print('Uploaded.')
      leds.off(2)
      status.set(Status.UPLOADER_ACTIVE, False)

    if last_upload and time.time() - last_upload > 600:
      # X minutes have passed since the last upload.
      uploader.close_browser()

    time.sleep(1)


if __name__ == '__main__':
  main()
