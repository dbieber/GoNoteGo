import random
import time

import twython

from gonotego.common import events
from gonotego.settings import settings


def _tweet(client, text, tweet_id=None):
  # Assumes text is < 280 characters.
  # If tweet_id is None, tweets a non-reply tweet.
  # If tweet_id is not None, tweets a reply tweet.
  return client.update_status(
      status=text, in_reply_to_status_id=tweet_id)


def _tweet_thread(client, texts, tweet_id=None):
  # Assume each text is < 280 characters.
  # If tweet_id is None, tweets a non-reply tweet thread.
  # If tweet_id is not None, tweets a reply tweet thread.
  tweets = []
  for text in texts:
    if not tweets:
      tweet = _tweet(client, text, tweet_id=tweet_id)
    else:
      time.sleep(random.random())
      tweet = _tweet(
          client, text, tweet_id=tweets[-1]['id_str'])
    tweets.append(tweet)
  return tweets


def split_to_tweets(text, delimiter=None, limit=280):
  texts = []
  if delimiter and delimiter in text:
    # Presence of delimiter forces splitting into a new tweet.
    for t in text.split(delimiter):
      texts.extend(split_to_tweets(t, delimiter=None, limit=limit))
    return texts
  spacers = ['\n\n\n', '\n\n', '\n', ' ']
  preferred_breaks = ['.', '!', '?', ';', ',', '-', '+', '*', '&', ')']
  while len(text) > limit:
    for spacer in spacers + preferred_breaks:
      try:
        index = text[:limit].rindex(spacer)
        end_index = index
        start_index = index + len(spacer)
        if spacer in preferred_breaks:
          end_index += len(spacer)
        texts.append(text[:end_index])
        text = text[start_index:]
        break
      except ValueError:
        pass
    else:
      # None of the spacers matched.
      texts.append(text[:limit])
      text = text[limit:]

  if text:
    texts.append(text)
  return texts


def send(client, text, tweet_id=None):
  texts = split_to_tweets(text)
  return _tweet_thread(client, texts, tweet_id)


def get_oauth_tokens():
  user_id = settings.get('twitter.user_id')
  oauth_token = settings.get(f'twitter.user_ids.{user_id}.oauth_token')
  oauth_token_secret = settings.get(f'twitter.user_ids.{user_id}.oauth_token_secret')

  # TODO(dbieber): Add fallback to settings:
  # settings.get('TWITTER_ACCESS_TOKEN')
  # settings.get('TWITTER_ACCESS_TOKEN_SECRET')

  return oauth_token, oauth_token_secret


class Uploader:

  def __init__(self):
    self._client = None
    self.last_tweet_id = None

  @property
  def client(self):
    if self._client:
      return self._client
    oauth_token, oauth_token_secret = get_oauth_tokens()
    self._client = twython.Twython(
        settings.get('TWITTER_API_KEY'),
        settings.get('TWITTER_API_SECRET'),
        oauth_token,
        oauth_token_secret)
    return self._client

  def upload(self, note_events):
    client = self.client
    for note_event in note_events:
      if note_event.action == events.SUBMIT:
        text = note_event.text.strip()
        tweets = send(client, text, self.last_tweet_id)
        self.last_tweet_id = tweets[-1]['id_str']
      elif note_event.action == events.END_SESSION:
        self.end_session()

  def handle_inactivity(self):
    self._client = None
    self.end_session()

  def handle_disconnect(self):
    self._client = None
    self.end_session()

  def end_session(self):
    self.last_tweet_id = None
