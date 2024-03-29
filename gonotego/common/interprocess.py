import redis


def get_redis_client():
  return redis.Redis(host='localhost', port=6379, db=0)


class InterprocessQueue:

  def __init__(self, key):
    self.key = key
    self.r = get_redis_client()
    self.index = 0

  def put(self, value):
    self.r.set(f'{self.key}:latest', value)
    return self.r.rpush(self.key, value)

  def get(self):
    """Gets the next item in the queue. Does not remove it from the queue."""
    value = self.r.lindex(self.key, self.index)
    if value is not None:
      self.index += 1
    return value

  def peek_all(self):
    return self.r.lrange(self.key, self.index, -1)

  def commit(self, value):
    """Removes the next item in the queue, asserting it matches the provided value.

    To ensure each item is processed, use the following pattern.
    1. value = queue.get()
    2. process(value)
    3. queue.commit(value)

    This can still result in an item being processed or partially processed multiple times,
    but importantly it guarantees each item is processed.

    Args:
      value: The expected value for the leftmost item in the queue.
    """
    if value is None:
      return

    pop_value = self.r.lpop(self.key)
    self.index -= 1
    assert self.index >= 0
    assert value == pop_value

  def size(self):
    return self.r.llen(self.key) - self.index

  def latest(self):
    return self.r.get(f'{self.key}:latest')

  def clear(self):
    self.r.delete(self.key)


def get_audio_events_queue():
  return InterprocessQueue('audio_events_queue')


def get_command_events_queue():
  return InterprocessQueue('command_events_queue')


def get_note_events_queue():
  return InterprocessQueue('note_events_queue')


def get_note_events_session_queue():
  return InterprocessQueue('note_events_session_queue')
