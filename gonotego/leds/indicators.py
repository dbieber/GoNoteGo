"""A library for setting the num lock and caps lock indicator LEDs on the keyboard."""
import struct
import time
import os

NUM_LOCK = 0x00
CAPS_LOCK = 0x01

LED_EVENT = 0x11


def set(device_path='/dev/input/by-id/usb-_Raspberry_Pi_Internal_Keyboard-event-kbd', led_id=NUM_LOCK, state=0):
  """Sets the specified led (num lock or caps lock) to the specified state (on or off).

  Args:
    device_path: The path to the keyboard input device with the LEDs. The default value
      is for a Raspberry Pi 400.
    led_id: One of NUM_LOCK or CAPS_LOCK, indicating which light's status to modify.
    state: 0 indicates off, while 1 indicates on.
  """
  fd = os.open(device_path, os.O_WRONLY)
  now = time.time()
  now_seconds = int(now)
  now_microseconds = int((now - now_seconds) * 1e6)
  data = struct.pack('@llHHI', now_seconds, now_microseconds, LED_EVENT, led_id, state)
  os.write(fd, data)
