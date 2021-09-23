from gonotego.common import status
from gonotego.text import shell

Status = status.Status


def main():
  s = shell.Shell()
  s.start()
  status.set(Status.TEXT_READY, True)
  s.wait()


if __name__ == '__main__':
  main()
