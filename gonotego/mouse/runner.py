import time
try:
  from pynput import mouse
  MOUSE_MODULE = 'pynput'
except ImportError:
  import mouse
  MOUSE_MODULE = 'mouse'
from gonotego.common import status

Status = status.Status


def handle_mouse_event(x, y):
  status.set(Status.PAUSED, True)
  status.set(Status.MOUSE_LAST_MOVE, time.time())


def main():
  if MOUSE_MODULE == 'pynput':
    with mouse.Listener(on_move=handle_mouse_event) as listener:
      listener.join()


if __name__ == '__main__':
  main()
