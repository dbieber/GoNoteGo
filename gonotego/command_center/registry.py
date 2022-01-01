from typing import Callable, Pattern, Text, Tuple

import dataclasses
import re

COMMANDS = []


@dataclasses.dataclass
class Command(object):
  name: Text
  func: Callable
  regex: Pattern
  requirements: Tuple[Text]

  def execute_if_match(self, text, resources):
    match = self.regex.match(text)
    if match:
      args = match.groups()

      kwargs = {}
      for requirement in self.requirements:
        kwargs[requirement] = resources[requirement]

      self.func(*args, **kwargs)
      return True
    return False


def register_command(pattern, **params):
  def command_decorator(func):
    regex_str = '^' + pattern.replace('{}', '(.*)') + '$'
    regex = re.compile(regex_str)
    name = params.pop('name', func.__name__)
    requirements = params.pop('requirements', ())

    command = Command(
        name=name,
        func=func,
        regex=regex,
        requirements=requirements,
    )
    COMMANDS.append(command)

    return func
  return command_decorator
