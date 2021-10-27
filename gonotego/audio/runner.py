from absl import logging

from datetime import datetime
import subprocess
import time

from gonotego.audio import audiolistener
from gonotego.audio import trigger
from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import status

Status = status.Status


def make_filepath():
  now = datetime.now()
  date_str = now.strftime('%Y%m%d')
  milliseconds = int(round(time.time() * 1000))
  return f'out/{date_str}-{milliseconds}.wav'


def enqueue_recording(queue, filepath):
  event = events.AudioEvent(events.AUDIO_DONE, filepath)
  queue.put(bytes(event))


def main():
  logging.info('Starting logging for audio listener')
  print('Starting audio listener.')
  listener = audiolistener.AudioListener()
  audio_events_queue = interprocess.get_audio_events_queue()
  status.set(Status.AUDIO_READY, True)

  filepath = None
  last_filepath = None
  last_pressed = False
  last_press_time = None
  hold_triggered = False
  press_time = None

  # Wait until not pressed before starting.
  while trigger.is_pressed():
    time.sleep(0.01)

  print('Starting audio trigger loop.')
  while True:
    pressed = trigger.is_pressed()
    newly_pressed = pressed and not last_pressed
    still_pressed = pressed and last_pressed

    now = time.time()
    if newly_pressed:
      last_press_time = press_time
      press_time = now
      hold_triggered = False
    if still_pressed:
      press_duration = now - press_time

    # Three seconds of silence.
    if listener.recording and listener.silence_length() > 3:
      logging.info(f'Three seconds of silence. Stopping. {filepath}')
      print(f'Three seconds of silence. Stopping. {filepath}')
      listener.stop()
      status.set(Status.AUDIO_RECORDING, listener.recording)
      enqueue_recording(audio_events_queue, filepath)
      last_filepath = filepath
      filepath = None

    # Double press.
    elif newly_pressed and last_press_time and press_time - last_press_time < 0.5:
      if listener.recording:
        # We just started recording with the first push. Now we're going to stop.
        listener.stop()
        status.set(Status.AUDIO_RECORDING, listener.recording)
        subprocess.call(['rm', filepath])
        filepath = None
      else:
        # We stopped recording with the first push. Let's delete it.
        subprocess.call(['rm', last_filepath])

      logging.info('Double pressed. Cancel.')
      print('Double pressed. Cancel.')

    elif newly_pressed and not listener.recording:
      # Start a recording by press.
      filepath = make_filepath()
      logging.info(f'Start recording. {filepath}')
      print(f'Start recording. {filepath}')
      listener.record(filepath)
      status.set(Status.AUDIO_RECORDING, listener.recording)
    elif newly_pressed and listener.recording:
      # Stop a recording by press.
      logging.info(f'Stop recording. {filepath}')
      print(f'Stop recording. {filepath}')
      listener.stop()
      status.set(Status.AUDIO_RECORDING, listener.recording)
      # TODO(dbieber): Should wait to make sure it's not a double press.
      enqueue_recording(audio_events_queue, filepath)
      last_filepath = filepath
      filepath = None
    elif still_pressed and press_duration > 1 and not hold_triggered:
      hold_triggered = True
      logging.info('Held down for 1 second. Cancel and read back.')
      print('Held down for 1 second. Cancel and read back.')
      if listener.recording:
        listener.stop()
        status.set(Status.AUDIO_RECORDING, listener.recording)
        subprocess.call(['rm', filepath])
        filepath = None
      subprocess.call(['afplay', last_filepath])

    last_pressed = pressed
    time.sleep(0.01)


if __name__ == '__main__':
  main()
