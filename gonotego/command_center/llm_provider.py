"""LLM provider module for different AI model providers.

This module handles creating completions and chat completions using different LLM
providers like OpenAI and Anthropic.
"""

import openai
import anthropic
from typing import List, Dict, Any, Optional

from gonotego.settings import settings
from gonotego.command_center import system_commands

def get_provider() -> str:
    """Get the configured LLM provider."""
    return settings.get('LLM_PROVIDER')

def has_openai_key() -> bool:
    """Check if OpenAI API key is configured."""
    api_key = settings.get('OPENAI_API_KEY')
    return api_key and api_key != '<OPENAI_API_KEY>'

def has_anthropic_key() -> bool:
    """Check if Anthropic API key is configured."""
    api_key = settings.get('ANTHROPIC_API_KEY')
    return api_key and api_key != '<ANTHROPIC_API_KEY>'

def create_completion(
    prompt: str,
    *,
    model: str = 'gpt-3.5-turbo-instruct',
    temperature: float = 0.7,
    max_tokens: int = 256,
    top_p: float = 1,
    frequency_penalty: float = 0,
    presence_penalty: float = 0,
    **kwargs
) -> Any:
    """Create a completion using the configured LLM provider."""
    provider = get_provider()
    
    if provider == 'openai':
        if not has_openai_key():
            system_commands.say("No OpenAI API key available")
            return None
            
        client = openai.OpenAI(api_key=settings.get('OPENAI_API_KEY'))
        response = client.completions.create(
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
    
    elif provider == 'anthropic':
        if not has_anthropic_key():
            system_commands.say("No Anthropic API key available")
            return None
            
        # Anthropic doesn't have an exact equivalent to completions API
        # So we'll use Claude's messages API instead with a single user prompt
        client = anthropic.Anthropic(api_key=settings.get('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            temperature=temperature,
            system="You are a helpful assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Return a response object that mimics OpenAI's structure
        # so we can access response.choices[0].text in the existing code
        class AnthropicCompletionChoice:
            def __init__(self, text):
                self.text = text
                
        class AnthropicCompletionResponse:
            def __init__(self, choices):
                self.choices = choices
                
        return AnthropicCompletionResponse([
            AnthropicCompletionChoice(response.content[0].text)
        ])
        
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

def chat_completion(
    messages: List[Dict[str, str]], 
    model: Optional[str] = None
) -> Any:
    """Create a chat completion using the configured LLM provider."""
    provider = get_provider()
    
    if provider == 'openai':
        if not has_openai_key():
            system_commands.say("No OpenAI API key available")
            return None
            
        if model is None:
            model = 'gpt-3.5-turbo'
            
        client = openai.OpenAI(api_key=settings.get('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response
    
    elif provider == 'anthropic':
        if not has_anthropic_key():
            system_commands.say("No Anthropic API key available")
            return None
            
        if model is None or model == 'claude-3-sonnet-20240229':
            claude_model = "claude-3-sonnet-20240229"
        else:
            # Default to Claude 3 Sonnet if no specific Claude model is specified
            claude_model = "claude-3-sonnet-20240229"
        
        # Extract system message if present
        system_message = "You are a helpful assistant."
        user_assistant_messages = []
        
        for message in messages:
            if message['role'] == 'system':
                system_message = message['content']
            else:
                user_assistant_messages.append(message)
        
        client = anthropic.Anthropic(api_key=settings.get('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model=claude_model,
            max_tokens=1024,
            system=system_message,
            messages=user_assistant_messages
        )
        
        # Return a response object that mimics OpenAI's structure
        class AnthropicMessage:
            def __init__(self, content):
                self.content = content
                
        class AnthropicChoice:
            def __init__(self, message):
                self.message = message
                
        class AnthropicChatResponse:
            def __init__(self, choices):
                self.choices = choices
                
        return AnthropicChatResponse([
            AnthropicChoice(AnthropicMessage(response.content[0].text))
        ])
        
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")