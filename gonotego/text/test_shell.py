"""Tests for the text shell's keyboard handling."""
import sys
import types
from unittest import mock

# The real keyboard module needs root and input devices; stub it before
# importing the shell.
fake_keyboard = types.ModuleType('keyboard')
fake_keyboard.pressed = set()
fake_keyboard.is_pressed = lambda key: key in fake_keyboard.pressed
fake_keyboard.on_press = lambda callback: None
sys.modules['keyboard'] = fake_keyboard

from gonotego.text import shell  # noqa: E402


class FakeEvent:

  def __init__(self, name):
    self.name = name


def make_shell():
  with mock.patch.object(shell.interprocess, 'get_command_events_queue', mock.MagicMock()), \
       mock.patch.object(shell.interprocess, 'get_note_events_queue', mock.MagicMock()), \
       mock.patch.object(shell.interprocess, 'get_note_events_session_queue', mock.MagicMock()):
    s = shell.Shell()
  s.command_event_queue = mock.MagicMock()
  s.note_events_queue = mock.MagicMock()
  s.note_events_session_queue = mock.MagicMock()
  return s


def press(s, name, pressed=()):
  fake_keyboard.pressed = set(pressed)
  try:
    s.on_press(FakeEvent(name))
  finally:
    fake_keyboard.pressed = set()


def test_cmd_shift_digit_switches_profile(fake_redis):
  s = make_shell()
  press(s, '2', pressed={'shift', 'cmd'})
  s.command_event_queue.put.assert_called_once_with(b'use profile 2')
  assert s.text == ''


def test_windows_key_counts_as_cmd(fake_redis):
  s = make_shell()
  press(s, '3', pressed={'shift', 'windows'})
  s.command_event_queue.put.assert_called_once_with(b'use profile 3')


def test_shift_digit_without_cmd_still_types_symbol(fake_redis):
  s = make_shell()
  press(s, '2', pressed={'shift'})
  assert s.text == '@'
  s.command_event_queue.put.assert_not_called()


def test_plain_digit_types_digit(fake_redis):
  s = make_shell()
  press(s, '2')
  assert s.text == '2'
  s.command_event_queue.put.assert_not_called()
