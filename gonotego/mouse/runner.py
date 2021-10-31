import mouse
import sys
import time

from gonotego.common import status

Status = status.Status


def handle_mouse_event(event):
  print(event)
  sys.stdout.flush()
  if isinstance(event, mouse.MoveEvent):
    status.set(Status.MOUSE_LAST_MOVE, time.time())


def main():
  print('prehook')
  sys.stdout.flush()
  mouse.hook(handle_mouse_event)
  print('posthook')
  sys.stdout.flush()
  while True:
    time.sleep(5)
    print('sleep')
    sys.stdout.flush()

if __name__ == '__main__':
  main()
