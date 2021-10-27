import time

import adafruit_dotstar
import board

from gonotego.common import events
from gonotego.common import status
from gonotego.leds import colors

Status = status.Status

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6


def main():
  dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

  while True:
    audio_recording = status.get(Status.AUDIO_RECORDING)
    text_last_keypress = status.get(Status.TEXT_LAST_KEYPRESS)
    time_since_keypress = time.time() - text_last_keypress
    transcription_active = status.get(Status.TRANSCRIPTION_ACTIVE)
    uploader_active = status.get(Status.UPLOADER_ACTIVE)

    led_colors = [colors.OFF, colors.OFF, colors.OFF]
    if audio_recording:
      led_colors[0] = colors.RED
    if time_since_keypress < 5:
      led_colors[1] = colors.ORANGE
      if time_since_keypress > 4:
        led_colors[1] = colors.brightness_adjusted(
            led_colors[1], (5 - time_since_keypress))
    if transcription_active:
      led_colors[1] = colors.GREEN
    if uploader_active:
      led_colors[2] = colors.BLUE

    for i in range(3):
      dots[i] = led_colors[i]
    dots.show()

    time.sleep(0.005)


if __name__ == '__main__':
  main()
