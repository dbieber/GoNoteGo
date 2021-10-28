MAX_BRIGHTNESS = 0.1

# Colors are (G, B, R, A)
OFF = (0, 0, 0, 0.0)
RED = (0, 0, 255, MAX_BRIGHTNESS)
ORANGE = (90, 0, 255, MAX_BRIGHTNESS)
BLUE = (0, 255, 0, MAX_BRIGHTNESS)
GREEN = (255, 0, 0, MAX_BRIGHTNESS)


def brightness_adjusted(color, brightness):
  return (
      color[0], color[1], color[2],
      brightness * MAX_BRIGHTNESS
  )
