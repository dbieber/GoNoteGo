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
    print(f'Executing: {text}')
    for command in registry.COMMANDS:
      executed = command.execute_if_match(text, self.resources)
      if executed:
        break


def main():
  print('Starting command center.')
  command_events_queue = interprocess.get_command_events_queue()

  executor = Executor(scheduler=scheduler.Scheduler())
  scheduler.executor_singleton = executor
  while True:
    while command_events_queue.size() > 0:
      # We commit the item before executing the command.
      # So, if the command fails, it will not be re-executed.
      command_event_bytes = command_events_queue.get()
      command_events_queue.commit(command_event_bytes)

      command_event = events.CommandEvent.from_bytes(command_event_bytes)
      command_text = command_event.command_text
      executor.execute(command_text)
    time.sleep(1)


if __name__ == '__main__':
  main()
