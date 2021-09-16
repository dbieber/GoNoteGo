import keyboard

from gonotego.common import interprocess
from gonotego.text import shell


def main():
  s = shell.Shell()
  s.start()


if __name__ == '__main__':
  main()
