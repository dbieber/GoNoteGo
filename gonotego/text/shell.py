import keyboard
import platform
try:
  import pyperclip
except:
  print('Cannot import pyperclip')
import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import status
from gonotego.settings import settings

Status = status.Status

MINUS = chr(8722)
assert MINUS == '−'  # This is a unicode minus sign, not an ordinary hyphen.
MAC_LEFT_SHIFT = 56

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
    '-': '_',  # Ordinary hyphen. ord(x) == 45.
    MINUS: '_',  # The kind typed on the Raspberry Pi. ord(x) == 8722.
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

character_substitutions = {
    MINUS: '-',  # Replace unicode minus with ordinary hyphens.
}


def get_timestamp():
  return time.time()


def is_shift_pressed():
  if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'):
    return True
  if platform.system() == 'Darwin':
    if keyboard.is_pressed(MAC_LEFT_SHIFT):
      return True
  return False


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
    try:
      if keyboard.is_pressed(settings.get('HOTKEY')):
        # Ignore presses while the hotkey is pressed.
        return
    except ValueError:
      # If HOTKEY is not a valid key, continue.
      pass
    try:
      if keyboard.is_pressed(settings.get('PAUSE_HOTKEY')):
        # Toggle the paused status.
        paused = status.get(Status.PAUSED)
        status.set(Status.PAUSED, not paused)
        # Ignore presses while the hotkey is pressed.
        return
    except ValueError:
      # If PAUSE_HOTKEY is not a valid key, continue.
      pass

    if status.get(Status.PAUSED):
      # Don't collect key presses while paused.
      return

    if event.name == 'tab':
      if is_shift_pressed():
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
    elif event.name == 'delete' or event.name == 'backspace':
      if self.text == '':
        note_event = events.NoteEvent(
            text=None,
            action=events.CLEAR_EMPTY,
            audio_filepath=None,
            timestamp=get_timestamp())
        self.note_events_queue.put(bytes(note_event))
      self.text = self.text[:-1]
      if is_shift_pressed():
        self.text = ''
    elif event.name == 'v' and keyboard.is_pressed('cmd'):
      # If on Mac, paste into the buffer.
      if platform.system() == 'Darwin':
        clipboard = pyperclip.paste()
        self.text += clipboard
    elif event.name == 'enter':
      if is_shift_pressed():
        note_event = events.NoteEvent(
            text=None,
            action=events.END_SESSION,
            audio_filepath=None,
            timestamp=get_timestamp())
        self.note_events_queue.put(bytes(note_event))
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
      if character in character_substitutions:
        character = character_substitutions[character]
      if is_shift_pressed():
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
