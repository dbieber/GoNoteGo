"""Twitter commands.

To use the Twitter uploader, run:
:set uploader twitter
or equivalently,
:twitter

To switch to a different Twitter account, run:
:set twitter-user <username>
or equivalently,
:twitter user <username>

Run the following to log in:
:twitter auth
or
:twitter auth <email address>

This will send you a URL where you can log in to Twitter and get a pin code.
Run the following to finish logging in:
:twitter pin <pin>
"""

from gonotego.common import status
from gonotego.command_center import registry

register_command = registry.register_command

Status = status.Status


@register_command('twitter')
def twitter():
  pass
