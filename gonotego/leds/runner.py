import time

import adafruit_dotstar
import board

from gonotego.common import events
from gonotego.common import interprocess


DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6


def main():
  dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

  led_events_queue = interprocess.get_led_events_queue()
  colors = [
      (0, 0, 0),
      (0, 0, 0),
      (0, 0, 0),
  ]
  while True:
    while led_events_queue.size() > 0:
      led_event_bytes = led_events_queue.get()
      led_event = events.LEDEvent.from_bytes(led_event_bytes)

      for i in led_event.ids:
        colors[i] = led_event.color
      for i in range(3):
        dots[i] = colors[i]
      dots.show()
      time.sleep(0.005)
    time.sleep(0.05)


if __name__ == '__main__':
  main()
