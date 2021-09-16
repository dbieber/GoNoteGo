import redis


def get_redis_client():
  return redis.Redis(host='localhost', port=6379, db=0)


class InterprocessQueue:

  def __init__(self, key):
    self.key = key
    self.r = get_redis_client()

  def put(self, value):
    return self.r.rpush(self.key, value)

  def get(self):
    return self.r.lpop(self.key)

  def size(self):
    return self.r.llen(self.key)


def get_audio_events_queue():
  return InterprocessQueue('audio_events_queue')


def get_text_events_queue():
  return InterprocessQueue('text_events_queue')


def get_note_events_queue():
  return InterprocessQueue('note_events_queue')
