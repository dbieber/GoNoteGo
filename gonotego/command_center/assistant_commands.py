"""Assistant commands. Commands for using the AI assistant."""

from gonotego.command_center import note_commands
from gonotego.command_center import registry
from gonotego.command_center import system_commands
from gonotego.command_center import llm_provider
from gonotego.common import events
from gonotego.common import interprocess
from gonotego.settings import settings

register_command = registry.register_command


# Use the LLM provider module for completions and chat completions
create_completion = llm_provider.create_completion
chat_completion = llm_provider.chat_completion


@register_command('ask {}')
@register_command('q {}')
def ask(prompt):
  response = create_completion(prompt)
  response_text = response.choices[0].text
  system_commands.speak(response_text)
  note_commands.add_note(prompt)
  note_commands.add_indented_note(f'{response_text} #[[AI Response]]')
  return response_text


@register_command('aix')
@register_command('aix {}')
def ask_with_context(prompt=None):
  messages = get_messages(prompt=prompt)
  texts = [message['content'] for message in messages]
  extended_prompt = '\n'.join(texts) + '\n'
  response = create_completion(extended_prompt)

  response_text = response.choices[0].text
  response_text = response_text.lstrip()

  system_commands.speak(response_text)
  if prompt:
    note_commands.add_note(prompt)
  note_commands.add_indented_note(f'{response_text} #[[AI Response]]')
  return response_text


@register_command('ai3')
@register_command('ai3 {}')
def chat_with_context3(prompt=None):
  return chat_with_context(prompt=prompt, model='gpt-3.5-turbo')


@register_command('ai')
@register_command('ai {}')
def chat_with_context_default(prompt=None):
  """Use the default AI model based on the configured provider."""
  provider = llm_provider.get_provider()
  if provider == 'openai':
    model = 'gpt-4'
  else:  # anthropic
    model = 'claude-3-sonnet-20240229'
  return chat_with_context(prompt=prompt, model=model)


@register_command('ai4')
@register_command('ai4 {}')
def chat_with_context4(prompt=None):
  return chat_with_context(prompt=prompt, model='gpt-4')


@register_command('sonnet37')
@register_command('sonnet37 {}')
def chat_with_context_sonnet(prompt=None):
  if not llm_provider.has_anthropic_key():
    system_commands.say("No Anthropic API key available")
    return None
  return chat_with_context(prompt=prompt, model='claude-3-sonnet-20240229')


@register_command('gpt4')
@register_command('gpt4 {}')
def chat_with_context_gpt4(prompt=None):
  if not llm_provider.has_openai_key():
    system_commands.say("No OpenAI API key available")
    return None
  return chat_with_context(prompt=prompt, model='gpt-4')


def chat_with_context(prompt=None, model='gpt-3.5-turbo'):
  messages = get_messages(prompt=prompt)
  messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
  response = chat_completion(messages)
  response_text = response.choices[0].message.content

  system_commands.speak(response_text)
  if prompt:
    note_commands.add_note(prompt)
  note_commands.add_indented_note(f'{response_text} #[[AI Response]]')
  return response_text


@register_command('set_llm openai')
def set_llm_openai():
  """Set the LLM provider to OpenAI."""
  settings.set('LLM_PROVIDER', 'openai')
  system_commands.say("LLM provider set to OpenAI")
  if not llm_provider.has_openai_key():
    system_commands.say("Warning: No OpenAI API key configured")


@register_command('set_llm anthropic')
def set_llm_anthropic():
  """Set the LLM provider to Anthropic."""
  settings.set('LLM_PROVIDER', 'anthropic')
  system_commands.say("LLM provider set to Anthropic")
  if not llm_provider.has_anthropic_key():
    system_commands.say("Warning: No Anthropic API key configured")


@register_command('llm_status')
def llm_status():
  """Show the current LLM provider and API key status."""
  provider = llm_provider.get_provider()
  has_openai = llm_provider.has_openai_key()
  has_anthropic = llm_provider.has_anthropic_key()
  
  status_msg = f"Current LLM provider: {provider}\n"
  status_msg += f"OpenAI API key: {'configured' if has_openai else 'not configured'}\n"
  status_msg += f"Anthropic API key: {'configured' if has_anthropic else 'not configured'}"
  
  system_commands.speak(status_msg)
  note_commands.add_note(status_msg)


def get_messages(prompt=None):
  note_events_session_queue = interprocess.get_note_events_session_queue()
  note_event_bytes_list = note_events_session_queue.peek_all()
  note_events = [
      events.NoteEvent.from_bytes(note_event_bytes)
      for note_event_bytes in note_event_bytes_list
  ]

  indent = 0
  messages = []
  for note_event in note_events:
    if note_event.action == events.SUBMIT:
      text = note_event.text
      if ' #[[AI Response]]' in text:
        role = 'assistant'
        text = text.replace(' #[[AI Response]]', '')
      else:
        role = 'user'
      messages.append({'role': role, 'content': text})
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
    messages.append({'role': 'user', 'content': prompt})
  return messages
