import keyboard

from gonotego.common import interprocess


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
    if event.name == 'delete':
      self.text = self.text[:-1]
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

  def wait(self):
    keyboard.wait()
