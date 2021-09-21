import fire

from gonotego.common import events
from gonotego.common import interprocess

def insert():
  note_events_queue = interprocess.get_note_events_queue()
  note_event = events.NoteEvent('Test transcript', 'out/20210920-1632188898638.wav')
  note_events_queue.put(bytes(note_event))


if __name__ == '__main__':
  fire.Fire()
