"""Twitter commands.

To use the Twitter uploader, run:
:set uploader twitter
or equivalently,
:twitter

To switch to a different Twitter account, run:
:set twitter_user <username>
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

import twython

from gonotego.common import status
from gonotego.command_center import registry
from gonotego.settings import settings

register_command = registry.register_command

Status = status.Status


@register_command('twitter')
def twitter():
  settings.set('NOTE_TAKING_SYSTEM', 'twitter')


@register_command('twitter user')
def get_twitter_user():
  system_commands.say(settings.get('twitter.screen_name'))


@register_command('twitter user {}')
def set_twitter_user(screen_name):
  settings.set('twitter.screen_name', screen_name)
  user_id = settings.get(f'twitter.screen_names.{screen_name}.user_id')
  settings.set('twitter.user_id', user_id)


@register_command('twitter auth')
def start_auth():
  api_key = settings.get('TWITTER_API_KEY')
  secret_key = settings.get('TWITTER_API_SECRET')
  client = twython.Twython(api_key, secret_key)
  auth = client.get_authentication_tokens(callback_url='oob')
  oauth_token = auth['oauth_token']
  oauth_token_secret = auth['oauth_token_secret']
  auth_url = auth['auth_url']
  settings.set('twitter.oauth_token', oauth_token)
  settings.set('twitter.oauth_token_secret', oauth_token_secret)
  # TODO(dbieber): If there's a screen, open auth_url.
  with open('auth_url', 'w') as f:
    f.write(auth_url)
  print(auth_url)
  return auth_url


# # TODO(dbieber): Support email commands.
# @register_command('twitter auth {}')
# def start_auth_with_email(email):
#   auth_url = start_auth()
#   email_commands.send_email(
#       recipient=email, sender='Go Note Go', subject='Connect Go Note Go with Twitter',
#       message=f"""You requested to connect your Twitter account to your Go Note Go.

# You can do so at this link:
# {auth_url}

# Once you authorize Go Note Go to connect to your Twitter account, run the following on your Go Note Go:
# :twitter pin <pin>

# If you did not request to connect your Twitter account to your Go Note Go, you can safely ignore this email.
# """)


@register_command('twitter pin {}')
def complete_auth(pin):
  api_key = settings.get('TWITTER_API_KEY')
  secret_key = settings.get('TWITTER_API_SECRET')
  oauth_token = settings.get('twitter.oauth_token')
  oauth_token_secret = settings.get('twitter.oauth_token_secret')
  client = twython.Twython(api_key, secret_key, oauth_token, oauth_token_secret)
  auth = client.get_authorized_tokens(pin)

  oauth_token = auth['oauth_token']
  oauth_token_secret = auth['oauth_token_secret']
  user_id = auth['user_id']
  screen_name = auth['screen_name']

  settings.set('twitter.user_id', user_id)
  settings.set('twitter.screen_name', screen_name)
  settings.set(f'twitter.screen_names.{screen_name}.user_id', user_id)
  settings.set(f'twitter.user_ids.{user_id}.oauth_token', oauth_token)
  settings.set(f'twitter.user_ids.{user_id}.oauth_token_secret', oauth_token_secret)
