import time

from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.common import events
from gonotego.common import interprocess


register_command = registry.register_command


def get_timestamp():
  return time.time()


@register_command('note {}')
def add_note(text):
  note_events_queue = interprocess.get_note_events_queue()
  note_events_session_queue = interprocess.get_note_events_session_queue()

  note_event = events.NoteEvent(
      text=text,
      action=events.SUBMIT,
      audio_filepath=None,
      timestamp=get_timestamp())
  note_events_queue.put(bytes(note_event))
  note_events_session_queue.put(bytes(note_event))


@register_command('subnote {}')
def add_indented_note(text):
  note_events_queue = interprocess.get_note_events_queue()
  note_events_session_queue = interprocess.get_note_events_session_queue()

  # Indent
  note_event = events.NoteEvent(
      text=None,
      action=events.INDENT,
      audio_filepath=None,
      timestamp=get_timestamp())
  note_events_queue.put(bytes(note_event))
  note_events_session_queue.put(bytes(note_event))

  # The note
  note_event = events.NoteEvent(
      text=text,
      action=events.SUBMIT,
      audio_filepath=None,
      timestamp=get_timestamp())
  note_events_queue.put(bytes(note_event))
  note_events_session_queue.put(bytes(note_event))

  # Dedent
  note_event = events.NoteEvent(
      text=None,
      action=events.UNINDENT,
      audio_filepath=None,
      timestamp=get_timestamp())
  note_events_queue.put(bytes(note_event))
  note_events_session_queue.put(bytes(note_event))


@register_command('pending')
def get_pending_note_count():
  note_events_queue = interprocess.get_note_events_queue()
  size = note_events_queue.size()
  system_commands.say(size)
  return size
