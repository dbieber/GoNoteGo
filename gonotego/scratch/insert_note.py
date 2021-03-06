import fire

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import status


def insert(text='test transcript', filepath=None):
  filepath = filepath or 'out/20210920-1632188898638.wav'
  note_events_queue = interprocess.get_note_events_queue()
  note_event = events.NoteEvent(text, filepath)
  note_events_queue.put(bytes(note_event))
  print(note_events_queue.size())
  return 'Success'


def insert_command(text='test transcript'):
  command_events_queue = interprocess.get_command_events_queue()
  command_event = events.CommandEvent(text)
  command_events_queue.put(bytes(command_event))
  print(command_events_queue.size())
  return 'Success'


def size():
  note_events_queue = interprocess.get_note_events_queue()
  print(note_events_queue.size())
  return 'Success'


def get_status():
  for key in list(status.Status):
    print(key, status.get(key))


if __name__ == '__main__':
  fire.Fire()
