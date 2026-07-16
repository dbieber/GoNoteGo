import time

from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.common import events
from gonotego.common import interprocess
from gonotego.common import note_log
from gonotego.common import time_offsets


register_command = registry.register_command


def get_timestamp():
  return time.time()


def put_note_event(note_event):
  """Logs a note event locally and enqueues it for the uploader."""
  note_event.offset = time_offsets.get_offset()
  note_log.log(note_event)
  interprocess.get_note_events_queue().put(bytes(note_event))
  interprocess.get_note_events_session_queue().put(bytes(note_event))


@register_command('note {}')
def add_note(text):
  note_event = events.NoteEvent(
      text=text,
      action=events.SUBMIT,
      audio_filepath=None,
      timestamp=get_timestamp())
  put_note_event(note_event)


@register_command('subnote {}')
def add_indented_note(text):
  # Indent
  note_event = events.NoteEvent(
      text=None,
      action=events.INDENT,
      audio_filepath=None,
      timestamp=get_timestamp())
  put_note_event(note_event)

  # The note
  note_event = events.NoteEvent(
      text=text,
      action=events.SUBMIT,
      audio_filepath=None,
      timestamp=get_timestamp())
  put_note_event(note_event)

  # Dedent
  note_event = events.NoteEvent(
      text=None,
      action=events.UNINDENT,
      audio_filepath=None,
      timestamp=get_timestamp())
  put_note_event(note_event)


@register_command('todo {}')
def add_todo(text):
  # TODO(dbieber): This syntax is Roam Research specific.
  return add_note(f'{{{{[[TODO]]}}}} {text}')


@register_command('pending')
def get_pending_note_count():
  note_events_queue = interprocess.get_note_events_queue()
  size = note_events_queue.size()
  size_str = str(size)
  system_commands.say(size_str)
  return size
