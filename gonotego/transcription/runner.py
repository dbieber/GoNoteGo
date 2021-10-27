import time

from gonotego.common import events
from gonotego.common import internet
from gonotego.common import interprocess
from gonotego.common import leds
from gonotego.common import status
from gonotego.transcription import transcriber

Status = status.Status


def main():
  print('Starting transcription.')
  audio_events_queue = interprocess.get_audio_events_queue()
  command_events_queue = interprocess.get_command_events_queue()
  note_events_queue = interprocess.get_note_events_queue()

  t = transcriber.Transcriber()
  status.set(Status.TRANSCRIPTION_READY, True)
  while True:
    audio_event_bytes = audio_events_queue.get()

    if audio_event_bytes is not None:
      print(f'Event received: {audio_event_bytes}')

      # Don't even try transcribing if we don't have a connection.
      internet.wait_for_internet()

      event = events.AudioEvent.from_bytes(audio_event_bytes)
      if event.action == events.AUDIO_DONE:
        status.set(Status.TRANSCRIPTION_ACTIVE, True)
        leds.green(1)
        transcript = t.transcribe(event.filepath)
        text_filepath = event.filepath.replace('.wav', '.txt')
        with open(text_filepath, 'w') as f:
          f.write(transcript)
        print(transcript)
        note_event = events.NoteEvent(transcript, event.filepath)
        note_events_queue.put(bytes(note_event))

        # Audio commands:
        for trigger in ['go go', 'GoGo', 'Go-Go']:
          extended_trigger = f'{trigger} '
          if transcript.lower().startswith(extended_trigger.lower()):
            command_text = transcript[len(extended_trigger):] + ':'
            command_event = events.CommandEvent(command_text)
            command_events_queue.put(bytes(command_event))

        leds.off(1)
        status.set(Status.TRANSCRIPTION_ACTIVE, False)
    audio_events_queue.commit(audio_event_bytes)

    time.sleep(3)


if __name__ == '__main__':
  main()
