from datetime import datetime
import keyboard
import subprocess
import time

from gonotego.audio import audiolistener


def make_filepath():
  now = datetime.now()
  date_str = now.strftime('%Y%m%d')
  milliseconds = int(round(time.time() * 1000))
  return f'out/{date_str}-{milliseconds}.wav'


def main():
  listener = audiolistener.AudioListener()

  last_filepath = None
  last_pressed = False
  last_press_time = None
  hold_triggered = False
  press_time = None
  while True:
    pressed = keyboard.is_pressed('r')
    newly_pressed = pressed and not last_pressed
    still_pressed = pressed and last_pressed

    now = time.time()
    if newly_pressed:
      last_press_time = press_time
      press_time = now
      hold_triggered = False
    if still_pressed:
      press_duration = now - press_time

    if listener.recording and listener.silence_length() > 3:
      print('Three seconds of silence. Stopping. {filepath}')
      listener.stop()
      last_filepath = filepath

    if pressed and not listener.recording:
      filepath = make_filepath()
      print(f'Start recording. {filepath}')
      listener.record(filepath)
    elif newly_pressed and listener.recording:
      print(f'Stop recording. {filepath}')
      listener.stop()
      last_filepath = filepath
    elif still_pressed and press_duration > 1 and not hold_triggered:
      hold_triggered = True
      print('Held down for 1 second. Cancel and read back.')
      listener.stop()
      subprocess.call(['rm', filepath])
      subprocess.call(['afplay', last_filepath])

    if newly_pressed and last_press_time and press_time - last_press_time < 0.5:
      print('Double pressed. Cancel.')
      subprocess.call(['rm', filepath])

    last_pressed = pressed
    time.sleep(0.01)


if __name__ == '__main__':
  main()
