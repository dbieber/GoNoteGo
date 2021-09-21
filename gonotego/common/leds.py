import time
import board
import adafruit_dotstar

DOTSTAR_DATA = board.D5
DOTSTAR_CLOCK = board.D6

dots = adafruit_dotstar.DotStar(DOTSTAR_CLOCK, DOTSTAR_DATA, 3, brightness=0.2)

# Colors are (G, B, R, A)

def wheel(pos):
  # Input a value 0 to 255 to get a color value.
  # The colours are a transition r - g - b - back to r.
  if pos < 0 or pos > 255:
    return (0, 0, 0)
  if pos < 85:
    return (255 - pos * 3, pos * 3, 0)
  if pos < 170:
    pos -= 85
    return (0, 255 - pos * 3, pos * 3)
  pos -= 170
  return (pos * 3, 0, 255 - pos * 3)


def off(ids=None):
  set((0, 0, 0, 0.0))


def red(ids=None):
  set((0, 0, 255, 1.0))


def blue(ids=None):
  set((0, 255, 0, 1.0))


def green(ids=None):
  set((255, 0, 0, 1.0))


def set(color, ids=None):
  if ids is None:
    ids = range(3)
  elif isinstance(ids, int):
    ids = [ids]
  for i in ids:
    dots[i] = color
  dots.show()


def example():
  while True:
    for j in range(255):
      for i in range(3):
        rc_index = (i * 256 // 3) + j * 5
        dots[i] = wheel(rc_index & 255)
      dots.show()
      time.sleep(0.01)
