from gonotego.text import shell


def main():
  s = shell.Shell()
  s.start()
  s.wait()


if __name__ == '__main__':
  main()
