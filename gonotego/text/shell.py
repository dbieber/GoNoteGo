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
    '-': '_',  # Ordinary minus sign. ord(x) == 45.
    '−': '_',  # The kind typed on the Raspberry Pi. ord(x) == 8722.
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
    self.command_event_queue = interprocess.get_command_events_queue()
    self.note_event_queue = interprocess.get_note_events_queue()
    self.text = ''

  def start(self):
    keyboard.on_press(self.on_press)

  def on_press(self, event):
    status.set(Status.TEXT_LAST_KEYPRESS, time.time())
    if event.name == 'delete':
      self.text = self.text[:-1]
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        self.text = ''
    elif event.name == 'enter':
      # Write both a text event (for the command center)
      # and a note event (for the uploader).
      if self.text.strip().startswith(':'):
        command_event = events.CommandEvent(command_text=self.text.strip()[1:])
        self.command_event_queue.put(bytes(command_event))
      note_event = events.NoteEvent(text=self.text, audio_filepath=None)
      self.note_event_queue.put(bytes(note_event))
      # Reset the text buffer.
      self.text = ''
    elif event.name == 'space':
      self.text += ' '
    elif len(event.name) == 1:
      character = event.name
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        character = shift_characters.get(character, character.upper())
      self.text += character

  def wait(self):
    keyboard.wait()
