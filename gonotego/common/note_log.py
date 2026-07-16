"""Durable local log of every note event.

Every note event is appended to a local JSONL file at capture time, before
any transcription or upload happens. These files are the local source of
truth if anything downstream goes wrong (captive portal, uploader bug,
crash): a note that made it into the log is never lost silently.

Log files are only ever deleted by `cleanup`, which (a) never touches files
younger than MAX_AGE_DAYS (~6 months) and (b) doesn't delete anything at all
unless the disk is under real pressure.
"""

from datetime import datetime
import json
import os
import shutil
import time

NOTE_LOG_DIR = os.path.join('out', 'note_log')

# Local copies are kept for at least ~6 months no matter what.
MAX_AGE_DAYS = 183

# Old files are only cleaned up when free disk space drops below this.
MIN_FREE_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB

# Only files Go Note Go itself writes are eligible for cleanup.
CLEANUP_SUFFIXES = ('.wav', '.txt', '.jsonl')


def log(note_event):
  """Appends a note event to the durable local log. Never raises."""
  try:
    os.makedirs(NOTE_LOG_DIR, exist_ok=True)
    timestamp = note_event.timestamp
    dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
    filepath = os.path.join(NOTE_LOG_DIR, dt.strftime('%Y-%m-%d') + '.jsonl')
    offset = getattr(note_event, 'offset', 0.0) or 0.0
    effective_dt = datetime.fromtimestamp(timestamp + offset) if timestamp else dt
    entry = {
        'text': note_event.text,
        'action': note_event.action,
        'audio_filepath': note_event.audio_filepath,
        'timestamp': timestamp,
        'time': dt.isoformat(),
        'offset': offset,
        'effective_time': effective_dt.isoformat(),
    }
    with open(filepath, 'a') as f:
      f.write(json.dumps(entry) + '\n')
    return filepath
  except Exception as e:
    # Writing to the log must never prevent a note from being captured.
    print(f'Failed to write note event to note log: {e!r}')
    return None


def cleanup(directory='out', max_age_days=MAX_AGE_DAYS, min_free_bytes=MIN_FREE_BYTES):
  """Deletes old local note copies, but only under real disk pressure.

  Never deletes anything newer than max_age_days. Never deletes anything at
  all unless free disk space is below min_free_bytes. Deletes oldest files
  first and stops as soon as enough space is free.

  Returns the list of deleted filepaths.
  """
  try:
    free = shutil.disk_usage(directory).free
  except OSError:
    return []
  if free >= min_free_bytes:
    return []

  now = time.time()
  max_age_seconds = max_age_days * 24 * 60 * 60
  candidates = []
  for dirpath, unused_dirnames, filenames in os.walk(directory):
    for filename in filenames:
      if not filename.endswith(CLEANUP_SUFFIXES):
        continue
      filepath = os.path.join(dirpath, filename)
      try:
        mtime = os.path.getmtime(filepath)
        size = os.path.getsize(filepath)
      except OSError:
        continue
      if now - mtime > max_age_seconds:
        candidates.append((mtime, filepath, size))

  candidates.sort()
  deleted = []
  for unused_mtime, filepath, size in candidates:
    if free >= min_free_bytes:
      break
    try:
      os.remove(filepath)
    except OSError:
      continue
    free += size
    deleted.append(filepath)
  return deleted
