import sys
import time

from gonotego.common import events
from gonotego.common import internet
from gonotego.common import interprocess
from gonotego.common import status
from gonotego.settings import settings
from gonotego.uploader.email import email_uploader
from gonotego.uploader.ideaflow import ideaflow_uploader
from gonotego.uploader.remnote import remnote_uploader
from gonotego.uploader.roam import roam_uploader
from gonotego.uploader.mem import mem_uploader
from gonotego.uploader.notion import notion_uploader
from gonotego.uploader.slack import slack_uploader
from gonotego.uploader.twitter import twitter_uploader

Status = status.Status


def print_configuration_help():
  """Print helpful message when NOTE_TAKING_SYSTEM is not configured."""
  print("NOTE_TAKING_SYSTEM is not configured. Please set it using ':set NOTE_TAKING_SYSTEM [system]'")
  print("Example: ':set NOTE_TAKING_SYSTEM roam'")


def is_unconfigured(note_taking_system):
  """Check if the note taking system is unconfigured."""
  return note_taking_system == '<note_taking_system>' or note_taking_system == ''


def make_uploader(note_taking_system):
  if note_taking_system == 'email':
    return email_uploader.Uploader()
  elif note_taking_system == 'ideaflow':
    return ideaflow_uploader.Uploader()
  elif note_taking_system == 'remnote':
    return remnote_uploader.Uploader()
  elif note_taking_system == 'roam':
    return roam_uploader.Uploader()
  elif note_taking_system == 'mem':
    return mem_uploader.Uploader()
  elif note_taking_system == 'notion':
    return notion_uploader.Uploader()
  elif note_taking_system == 'slack':
    return slack_uploader.Uploader()
  elif note_taking_system == 'twitter':
    return twitter_uploader.Uploader()
  else:
    raise ValueError('Unexpected NOTE_TAKING_SYSTEM in settings', note_taking_system)


def main():
  print('Starting uploader.')
  note_events_queue = interprocess.get_note_events_queue()
  note_taking_system = settings.get('NOTE_TAKING_SYSTEM').lower()

  # Check if note taking system is still using the default unconfigured value
  if is_unconfigured(note_taking_system):
    print_configuration_help()
    return

  try:
    uploader = make_uploader(note_taking_system)
  except ValueError as e:
    print(e, file=sys.stderr)
    return
  status.set(Status.UPLOADER_READY, True)

  last_upload = None
  while True:

    # Don't even try uploading notes if we don't have a connection.
    internet.wait_for_internet(on_disconnect=uploader.handle_disconnect)

    note_taking_system_setting = settings.get('NOTE_TAKING_SYSTEM').lower()
    if note_taking_system_setting != note_taking_system:
      note_taking_system = note_taking_system_setting

      # Check if note taking system is using the default unconfigured value after a change
      if is_unconfigured(note_taking_system):
        print_configuration_help()
        continue

      uploader = make_uploader(note_taking_system)

    note_event_bytes_list = []
    note_events = []
    while note_events_queue.size() > 0:
      print('Note event received')
      note_event_bytes = note_events_queue.get()
      note_event_bytes_list.append(note_event_bytes)
      note_event = events.NoteEvent.from_bytes(note_event_bytes)
      note_events.append(note_event)

    if note_events:
      status.set(Status.UPLOADER_ACTIVE, True)
      # TODO(dbieber): Allow uploader to yield note events as it finishes them.
      # So that if it fails midway, we can still mark the completed events as done.
      upload_successful = uploader.upload(note_events)
      if upload_successful:
        last_upload = time.time()
        print('Uploaded.')
      else:
        print('Upload unsuccessful.')

      status.set(Status.UPLOADER_ACTIVE, False)
      if upload_successful:
        for note_event_bytes in note_event_bytes_list:
          note_events_queue.commit(note_event_bytes)

    if last_upload and time.time() - last_upload > 600:
      # X minutes have passed since the last upload.
      uploader.handle_inactivity()

    time.sleep(1)


if __name__ == '__main__':
  main()
