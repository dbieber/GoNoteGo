import keyboard
import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import status
from gonotego.settings import secure_settings

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


def get_timestamp():
  return time.time()


class Shell:

  def __init__(self):
    self.command_event_queue = interprocess.get_command_events_queue()
    self.note_events_queue = interprocess.get_note_events_queue()
    self.text = ''
    self.last_press = None

  def start(self):
    keyboard.on_press(self.on_press)

  def on_press(self, event):
    self.last_press = time.time()
    status.set(Status.TEXT_LAST_KEYPRESS, self.last_press)
    print(event)
    if keyboard.is_pressed(secure_settings.HOTKEY):
      # Ignore presses while the hotkey is pressed.
      return
    elif event.name == 'tab':
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        # Shift-Tab
        note_event = events.NoteEvent(
            text=None,
            action=events.UNINDENT,
            audio_filepath=None,
            timestamp=get_timestamp())
        self.note_events_queue.put(bytes(note_event))
      else:
        # Tab
        note_event = events.NoteEvent(
            text=None,
            action=events.INDENT,
            audio_filepath=None,
            timestamp=get_timestamp())
        self.note_events_queue.put(bytes(note_event))
    elif event.name == 'delete':
      if self.text == '':
        note_event = events.NoteEvent(
            text=None,
            action=events.CLEAR_EMPTY,
            audio_filepath=None,
            timestamp=get_timestamp())
        self.note_events_queue.put(bytes(note_event))
      self.text = self.text[:-1]
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        self.text = ''
    elif event.name == 'enter':
      # Write both a text event (for the command center)
      # and a note event (for the uploader).
      if self.text == '':
        note_event = events.NoteEvent(
            text=None,
            action=events.ENTER_EMPTY,
            audio_filepath=None,
            timestamp=get_timestamp())
        self.note_events_queue.put(bytes(note_event))
      elif self.text.strip().startswith(':'):
        command_event = events.CommandEvent(command_text=self.text.strip()[1:])
        self.command_event_queue.put(bytes(command_event))
        self.text = ''
      else:
        self.submit_note()
    elif event.name == 'space':
      self.text += ' '
    elif len(event.name) == 1:
      character = event.name
      if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
        character = shift_characters.get(character, character.upper())
      self.text += character

  def submit_note(self):
    if self.text:
      note_event = events.NoteEvent(
          text=self.text,
          action=events.SUBMIT,
          audio_filepath=None,
          timestamp=get_timestamp())
      self.note_events_queue.put(bytes(note_event))
      # Reset the text buffer.
      self.text = ''

  def handle_inactivity(self):
    self.submit_note()

  def wait(self):
    while True:
      time.sleep(5)

      # If 3 minutes elapse, submit the buffer as a note and clear it.
      if self.last_press and time.time() - self.last_press > 180:
        self.last_press = None
        self.handle_inactivity()
