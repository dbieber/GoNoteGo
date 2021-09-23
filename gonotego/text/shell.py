import keyboard
import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import leds
from gonotego.common import status

Status = status.Status

shift_characters = {
    '1': '!',
    '2': '@',
    '3': '#',
    '4': '$',
    '5': '%',
    '6': '^',
    '7': '&',
    '8': '*',
    '9': '(',
    '0': ')',
    '-': '_',
    '=': '+',
    '[': '{',
    ']': '}',
    '\\': '|',
    '`': '~',
    ';': ':',
    "'": '"',
    ',': '<',
    '.': '>',
    '/': '?',
}


class Shell:

  def __init__(self):
    self.queue = interprocess.get_text_events_queue()
    self.text = ''
  
  def start(self):
    keyboard.on_press(self.on_press)

  def on_press(self, event):
    leds.orange(1)
    status.set(Status.TEXT_LAST_KEYPRESS, time.time())
    if event.name == 'delete':
      self.text = self.text[:-1]
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        self.text = ''
    elif event.name == 'enter':
      print(self.text)
      text_event = events.TextEvent(self.text)
      self.queue.put(bytes(text_event))
      self.text = ''
    elif event.name == 'space':
      self.text += ' '
    elif len(event.name) == 1:
      character = event.name
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        character = shift_characters.get(character, character.upper())
      self.text += character
    leds.off(1)

  def wait(self):
    keyboard.wait()
