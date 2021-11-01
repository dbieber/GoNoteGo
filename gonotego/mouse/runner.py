import mouse
import sys
import time

from gonotego.common import status

Status = status.Status


def handle_mouse_event(event):
  sys.stdout.flush()
  if isinstance(event, mouse.MoveEvent):
    status.set(Status.MOUSE_LAST_MOVE, time.time())


def main():
  sys.stdout.flush()
  mouse.hook(handle_mouse_event)
  sys.stdout.flush()
  while True:
    time.sleep(5)
    sys.stdout.flush()

if __name__ == '__main__':
  main()
