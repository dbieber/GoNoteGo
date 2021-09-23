import time

from gonotego.common import events
from gonotego.common import interprocess
from gonotego.command_center import commands  # pylint: disable=unused-import
from gonotego.command_center import scheduler
from gonotego.command_center import registry


class Executor:

  def __init__(self, **resources):
    self.resources = resources

  def execute(self, text):
    for command in registry.COMMANDS:
      executed = command.execute_if_match(text, self.resources)
      if executed:
        break


def main():
  print('Starting command center.')
  text_events_queue = interprocess.get_text_events_queue()

  executor = Executor(scheduler=scheduler.Scheduler())
  scheduler.executor_singleton = executor
  while True:
    while text_events_queue.size() > 0:
      text_event_bytes = text_events_queue.get()
      text_event = events.TextEvent.from_bytes(text_event_bytes)
      text = text_event.text
      if text.startswith(':'):
        executor.execute(text[1:])
    time.sleep(1)


if __name__ == '__main__':
  main()
