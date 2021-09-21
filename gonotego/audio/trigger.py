import board
from digitalio import DigitalInOut, Direction, Pull
import keyboard

from gonotego.settings import secure_settings


button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP


def is_pressed():
  return (
      keyboard.is_pressed(secure_settings.HOTKEY)
      or not button.value
  )
