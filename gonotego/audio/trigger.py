try:
  import board
  from digitalio import DigitalInOut, Direction, Pull
except:
  print('Unable to import board and digitalio.')
  board = None
import keyboard

from gonotego.settings import secure_settings


if board is not None:
  button = DigitalInOut(board.D17)
  button.direction = Direction.INPUT
  button.pull = Pull.UP
else:
  button = None


def is_pressed():
  if button is not None:
    button_pressed = not button.value
  else:
    button_pressed = False
  return (
      keyboard.is_pressed(secure_settings.HOTKEY)
      or button_pressed
  )
