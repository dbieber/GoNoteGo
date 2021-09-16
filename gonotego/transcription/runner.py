import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.transcription import transcriber


def main():
  print('Starting transcription.')
  audio_events_queue = interprocess.get_audio_events_queue()
  note_events_queue = interprocess.get_note_events_queue()

  t = transcriber.Transcriber()
  while True:
    audio_event_bytes = audio_events_queue.get()

    if audio_event_bytes is not None:
      print(f'Event received: {audio_event_bytes}')
      event = events.AudioEvent.from_bytes(audio_event_bytes)
      if event.action == events.AUDIO_DONE:
        transcript = t.transcribe(event.filepath)
        text_filepath = event.filepath.replace('.wav', '.txt')
        with open(text_filepath, 'w') as f:
          f.write(transcript)
        note_event = events.NoteEvent(transcript, event.filepath)
        note_events_queue.put(bytes(note_event))

    time.sleep(3)


if __name__ == '__main__':
  main()
