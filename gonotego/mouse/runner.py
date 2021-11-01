import mouse
import time

from gonotego.common import status

Status = status.Status


def handle_mouse_event(event):
  if isinstance(event, mouse.MoveEvent):
    status.set(Status.MOUSE_LAST_MOVE, time.time())


def main():
  mouse.hook(handle_mouse_event)
  while True:
    time.sleep(5)

if __name__ == '__main__':
  main()
