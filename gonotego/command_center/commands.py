"""The module imports all other command modules.

It also defines some miscellaneous commands itself.
"""

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.command_center import assistant_commands  # noqa: unused-import
from gonotego.command_center import note_commands  # noqa: unused-import
from gonotego.command_center import settings_commands  # noqa: unused-import
from gonotego.command_center import system_commands  # noqa: unused-import
from gonotego.command_center import twitter_commands  # noqa: unused-import
from gonotego.command_center import registry

register_command = registry.register_command


@register_command('r')
@register_command('read')
def read_latest():
  note_events_queue = interprocess.get_note_events_queue()
  note_event_bytes = note_events_queue.latest()
  note_event = events.NoteEvent.from_bytes(note_event_bytes)
  system_commands.say(note_event.text)
