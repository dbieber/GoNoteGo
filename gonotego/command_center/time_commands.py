"""Commands for correcting note timestamps when the system clock is wrong.

Go Note Go has no realtime clock, so after a flight (or a long stretch
offline) the system clock can be off. These commands manage an
'alleged time' offset:

  :xtime 3:30pm   -- declare what time it really is. Future notes carry both
                     the raw clock time and the offset to the alleged time.
  :xtime          -- say the current alleged time and offset.
  :xtime clear    -- clear the offset.
  :rxtime 4       -- retroactively apply the current offset to the last
                     4 hours of not-yet-uploaded notes.
  :rxtime         -- same, reaching back to the last boot.
"""

from datetime import datetime
import time

from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.common import time_offsets

register_command = registry.register_command

CLEAR_WORDS = ('clear', 'off', 'reset', 'none')


@register_command('xtime {}')
def set_alleged_time(time_str):
  """Sets the alleged time, recording its offset from the system clock."""
  time_str = time_str.strip()
  if time_str.lower() in CLEAR_WORDS:
    time_offsets.clear_offset()
    system_commands.say('time offset cleared')
    return
  alleged_dt = time_offsets.parse_alleged_time(time_str)
  if alleged_dt is None:
    system_commands.say(f'could not parse time {time_str}')
    return
  offset = time_offsets.compute_offset(alleged_dt)
  time_offsets.set_offset(offset)
  say_alleged_time(prefix=f'offset {time_offsets.describe_offset(offset)}. ')


@register_command('xtime')
def say_alleged_time(prefix=''):
  """Says the current alleged time and offset."""
  offset = time_offsets.get_offset()
  alleged = datetime.fromtimestamp(time.time() + offset)
  time_str = alleged.strftime('%A %l:%M %p').strip()
  system_commands.say(f'{prefix}alleged time {time_str}')


@register_command('rxtime {}')
def apply_offset_to_recent_notes(hours_str):
  """Retroactively applies the offset to the last N hours of pending notes."""
  hours_str = hours_str.strip()
  try:
    hours = float(hours_str)
  except ValueError:
    system_commands.say(f'could not parse hours {hours_str}')
    return
  cutoff = time.time() - hours * 60 * 60
  apply_offset_since(cutoff)


@register_command('rxtime')
def apply_offset_to_notes_since_boot():
  """Retroactively applies the offset to pending notes since the last boot."""
  cutoff = time_offsets.boot_timestamp()
  if cutoff is None:
    system_commands.say('could not determine boot time')
    return
  apply_offset_since(cutoff)


def apply_offset_since(cutoff):
  offset = time_offsets.get_offset()
  updated = time_offsets.apply_offset_retroactively(offset, cutoff)
  system_commands.say(
      f'applied offset {time_offsets.describe_offset(offset)} to {updated} pending notes')
