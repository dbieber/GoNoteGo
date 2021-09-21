import time

from gonotego.common import events
from gonotego.common import interprocess

# Colors are (G, B, R, A)


def off(ids=None):
  set((0, 0, 0, 0.0), ids=ids)


def red(ids=None):
  set((0, 0, 255, 1.0), ids=ids)


def blue(ids=None):
  set((0, 255, 0, 1.0), ids=ids)


def green(ids=None):
  set((255, 0, 0, 1.0), ids=ids)


def set(color, ids=None):
  led_events_queue = interprocess.get_led_events_queue()  

  if ids is None:
    ids = range(3)
  elif isinstance(ids, int):
    ids = [ids]
  led_event = events.LEDEvent(
      color=color,
      ids=tuple(ids)
  )
  led_events_queue.put(bytes(led_event))
