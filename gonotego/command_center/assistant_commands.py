"""Assistant commands. Commands for using the AI assistant."""

import openai

from gonotego.command_center import note_commands
from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.common import events
from gonotego.common import interprocess
from gonotego.settings import settings

register_command = registry.register_command

openai.api_key = settings.get('OPENAI_API_KEY')


def create_completion(
    prompt,
    *,
    model='text-davinci-003',
    temperature=0.7,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    **kwargs
):
  response = openai.Completion.create(
      model=model,
      prompt=prompt,
      temperature=temperature,
      max_tokens=max_tokens,
      top_p=top_p,
      frequency_penalty=frequency_penalty,
      presence_penalty=presence_penalty,
      **kwargs
  )
  return response


@register_command('ask {}')
@register_command('q {}')
def ask(prompt):
  response = create_completion(prompt)
  response_text = response['choices'][0].text
  system_commands.say(response_text)
  note_commands.add_note(prompt)
  note_commands.add_indented_note(f'{response_text} #[[AI Response]]')
  return response_text


@register_command('ai')
@register_command('ai {}')
def ask_with_context(prompt=None):
  note_events_session_queue = interprocess.get_note_events_session_queue()
  note_event_bytes_list = note_events_session_queue.peek_all()
  note_events = [
      events.NoteEvent.from_bytes(note_event_bytes)
      for note_event_bytes in note_event_bytes_list
  ]

  indent = 0
  texts = []
  for note_event in note_events:
    if note_event.action == events.SUBMIT:
      text = note_event.text
      text = text.replace(' #[[AI Response]]', '')
      texts.append(text)
    elif note_event.action == events.INDENT:
      indent += 1
    elif note_event.action == events.UNINDENT:
      indent = max(0, indent - 1)
    elif note_event.action == events.CLEAR_EMPTY:
      indent = 0
    elif note_event.action == events.ENTER_EMPTY:
      indent = max(0, indent - 1)
    else:
      raise ValueError('Unexpected event action', note_event)
  del indent  # Unused.

  if prompt:
    texts.append(prompt)
  extended_prompt = '\n'.join(texts) + '\n'
  response = create_completion(extended_prompt)

  response_text = response['choices'][0].text
  response_text = response_text.lstrip()

  system_commands.say(response_text)
  if prompt:
    note_commands.add_note(prompt)
  note_commands.add_indented_note(f'{response_text} #[[AI Response]]')
  return response_text
