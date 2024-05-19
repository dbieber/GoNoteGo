try:
  import board
  from digitalio import DigitalInOut, Direction, Pull
except:
  print('Unable to import board and digitalio.')
  board = None
import keyboard

from gonotego.settings import settings


if board is not None:
  # The "onboard button" is the physical button on the Voice Bonnet.
  onboard_button = DigitalInOut(board.D17)
  onboard_button.direction = Direction.INPUT
  onboard_button.pull = Pull.UP

  # The "red button" is the handheld round one that's really satisfying to push.
  red_button = DigitalInOut(board.D27)
  red_button.direction = Direction.INPUT
  red_button.pull = Pull.UP
else:
  onboard_button = None
  red_button = None


def is_pressed():
  if onboard_button is not None:
    button_pressed = (
        not onboard_button.value
        or not red_button.value
    )
  else:
    button_pressed = False
  audio_hotkey_pressed = False
  try:
    audio_hotkey_pressed = keyboard.is_pressed(settings.get("HOTKEY"))
  except:
    pass
  return audio_hotkey_pressed or button_pressed
