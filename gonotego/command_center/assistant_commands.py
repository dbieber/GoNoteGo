"""Assistant commands. Commands for using the AI assistant."""

import openai

from gonotego.command_center import note_commands
from gonotego.command_center import registry
from gonotego.command_center import system_commands
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
def ask(prompt):
  response = create_completion(prompt)
  text = response['choices'][0].text
  system_commands.say(text)
  note_commands.add_note(prompt)
  note_commands.add_indented_note(text)
  return text
