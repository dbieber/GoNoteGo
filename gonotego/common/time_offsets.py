"""Support for an 'alleged time' offset while offline.

Go Note Go devices have no realtime clock, so after a flight or a stretch
offline the system clock can be wrong. ':xtime <time>' records the offset
between the alleged current time and the system clock. From then on, note
events carry both the raw clock timestamp and the offset (see
events.NoteEvent). ':rxtime [hours]' retroactively applies the current
offset to recently captured, not-yet-uploaded notes.
"""

from datetime import datetime
from datetime import timedelta
import time

import parsedatetime

from gonotego.common import events
from gonotego.common import interprocess

TIME_OFFSET_KEY = 'GoNoteGo:time_offset'


def get_offset():
  """Returns the current time offset in seconds (0.0 when none is set)."""
  try:
    r = interprocess.get_redis_client()
    value = r.get(TIME_OFFSET_KEY)
    return float(value) if value is not None else 0.0
  except Exception:
    # Note capture must keep working even if redis is unavailable.
    return 0.0


def set_offset(offset_seconds):
  r = interprocess.get_redis_client()
  r.set(TIME_OFFSET_KEY, repr(float(offset_seconds)))


def clear_offset():
  r = interprocess.get_redis_client()
  r.delete(TIME_OFFSET_KEY)


def compute_offset(alleged_dt, now=None):
  """Returns the seconds to add to the system clock so it reads alleged_dt."""
  now = now if now is not None else time.time()
  return alleged_dt.timestamp() - now


PARSED_TIME_ONLY = 2


def parse_alleged_time(time_str, now=None):
  """Parses a natural-language time string; returns a datetime or None."""
  calendar = parsedatetime.Calendar()
  now_dt = datetime.fromtimestamp(now) if now is not None else datetime.now()
  dt, parse_status = calendar.parseDT(time_str, sourceTime=now_dt)
  if not parse_status:
    return None
  if parse_status == PARSED_TIME_ONLY:
    # A bare clock time ("3:30pm") always parses as today, which can be far
    # in the past or future. For correcting a wrong clock, the intended
    # moment is the occurrence of that clock time nearest to now.
    while dt - now_dt > timedelta(hours=12):
      dt -= timedelta(days=1)
    while now_dt - dt > timedelta(hours=12):
      dt += timedelta(days=1)
  return dt


def describe_offset(offset_seconds):
  """Formats an offset in seconds as e.g. '+2h05m00s' or '-0h30m00s'."""
  sign = '+' if offset_seconds >= 0 else '-'
  remainder = abs(int(round(offset_seconds)))
  hours, remainder = divmod(remainder, 3600)
  minutes, seconds = divmod(remainder, 60)
  return f'{sign}{hours}h{minutes:02}m{seconds:02}s'


def boot_timestamp():
  """Returns the system-clock timestamp of the last boot, or None."""
  try:
    with open('/proc/uptime') as f:
      uptime_seconds = float(f.read().split()[0])
    return time.time() - uptime_seconds
  except (OSError, ValueError, IndexError):
    return None


def update_note_event_bytes(note_event_bytes, offset, cutoff):
  """Returns updated event bytes carrying `offset` if the event is at/after `cutoff`.

  Returns None (leave unchanged) for events before the cutoff or without a
  timestamp.
  """
  note_event = events.NoteEvent.from_bytes(note_event_bytes)
  if note_event.timestamp is None or note_event.timestamp < cutoff:
    return None
  note_event.offset = offset
  return bytes(note_event)


def apply_offset_retroactively(offset, cutoff, queues=None):
  """Rewrites pending note events captured at/after `cutoff` to carry `offset`.

  Only events still waiting in the queues (not yet uploaded) are rewritten.
  Returns the number of events updated in the main note events queue.
  """
  if queues is None:
    queues = (
        interprocess.get_note_events_queue(),
        interprocess.get_note_events_session_queue(),
    )
  counts = []
  for queue in queues:
    counts.append(queue.update_items(
        lambda note_event_bytes: update_note_event_bytes(note_event_bytes, offset, cutoff)))
  return counts[0] if counts else 0
