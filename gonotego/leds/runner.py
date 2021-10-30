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
    leds_setting = status.get(Status.LEDS_SETTING)

    led_colors = [colors.OFF, colors.OFF, colors.OFF]

    if leds_setting == 'low':
      if audio_recording:
        led_colors[0] = colors.brightness_adjusted(colors.RED, 0.5)
      if time_since_keypress < 4:
        led_colors[1] = colors.brightness_adjusted(colors.ORANGE, 0.5)

    elif leds_setting != 'off':
      if audio_recording:
        led_colors[0] = colors.RED
      if time_since_keypress < 4:
        led_colors[1] = colors.ORANGE
        if time_since_keypress > 3:
          led_colors[1] = colors.brightness_adjusted(colors.ORANGE, 0.5)
      if transcription_active:
        led_colors[1] = colors.GREEN
      if uploader_active:
        led_colors[2] = colors.BLUE

    for i in range(3):
      dots[i] = led_colors[i]
    dots.show()

    time.sleep(0.05)


if __name__ == '__main__':
  main()
