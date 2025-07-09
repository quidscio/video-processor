"""
llm_client.py

Wrapper for calling the Ollama chat completion API (Claude Opus 4).
"""
import os
import sys
import requests

from .config import OLLAMA_URL, BACKEND as CONFIG_BACKEND

def load_template(name: str) -> str:
    """
    Load a prompt template from the prompts/ directory.
    """
    base = os.path.dirname(__file__)
    path = os.path.join(base, 'prompts', name)
    with open(path, encoding='utf-8') as f:
        return f.read()

def chat(prompt: str, model: str = 'claude-opus-4', temperature: float = 0.0, debug: bool = False, max_tokens: int = 10000) -> tuple[str, bool]:
    """
    Send a user prompt to the selected LLM backend and return the content.
    Supported backends: Ollama (default), Anthropic Cloud.
    The backend is selected via the project config or LLM_BACKEND env var.
    
    Returns:
        tuple[str, bool]: (response_content, was_truncated)
    """
    # Select LLM backend (CLI env override, then project config)
    backend = os.getenv('LLM_BACKEND', CONFIG_BACKEND).lower()
    
    # Debug logging for token usage
    if debug:
        prompt_length = len(prompt)
        # Rough token estimation (1 token ≈ 4 characters)
        estimated_input_tokens = prompt_length // 4
        print(f"__ LLM Debug: Input length: {prompt_length} chars (~{estimated_input_tokens} tokens)", file=sys.stderr)
    
    if backend == 'anthropic':
        try:
            from anthropic import Client, HUMAN_PROMPT, AI_PROMPT
        except ModuleNotFoundError:
            raise RuntimeError(
                "Anthropic SDK is not installed; please install with `pip install anthropic>=0.3.0`"
            )

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise RuntimeError('ANTHROPIC_API_KEY is not set')
        try:
            client = Client(api_key=api_key)
        except TypeError:
            client = Client()
        full_prompt = HUMAN_PROMPT + prompt + AI_PROMPT
        try:
            response = client.completions.create(
                model=model,
                prompt=full_prompt,
                temperature=temperature,
                max_tokens_to_sample=max_tokens,
            )
            # Check for token limit issues
            completion = response.completion
            was_truncated = False
            if hasattr(response, 'stop_reason') and response.stop_reason == 'max_tokens':
                print(f"** ERROR: Output truncated due to OUTPUT token limit ({max_tokens} tokens reached)", file=sys.stderr)
                was_truncated = True
            
            # Debug logging for output
            if debug:
                output_length = len(completion)
                estimated_output_tokens = output_length // 4
                print(f"__ LLM Debug: Output length: {output_length} chars (~{estimated_output_tokens} tokens)", file=sys.stderr)
                if hasattr(response, 'stop_reason'):
                    print(f"__ LLM Debug: Stop reason: {response.stop_reason}", file=sys.stderr)
            
            return completion, was_truncated
        except Exception as e:
            err = str(e)
            # Check for token limit errors
            if 'token' in err.lower() and ('limit' in err.lower() or 'exceeded' in err.lower()):
                raise RuntimeError(f"Token limit exceeded: {err}. Consider reducing transcript length or increasing token limit.")
            # Fallback to the Anthropic Messages API for models that no longer support Completions
            if 'Please use the Messages API instead' in err:
                messages_payload = [{'role': 'user', 'content': prompt}]
                resp_msg = client.messages.create(
                    model=model,
                    messages=messages_payload,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                # Extract and concatenate text blocks from the response
                try:
                    blocks = resp_msg.content
                    text = ''
                    for block in blocks:
                        # Each block has .text for text content
                        if hasattr(block, 'text'):
                            text += block.text
                    
                    # Check for token limit issues in Messages API
                    was_truncated = False
                    if hasattr(resp_msg, 'stop_reason') and resp_msg.stop_reason == 'max_tokens':
                        print(f"** ERROR: Output truncated due to OUTPUT token limit ({max_tokens} tokens reached)", file=sys.stderr)
                        was_truncated = True
                    
                    # Debug logging for Messages API output
                    if debug:
                        output_length = len(text)
                        estimated_output_tokens = output_length // 4
                        print(f"__ LLM Debug: Output length: {output_length} chars (~{estimated_output_tokens} tokens)", file=sys.stderr)
                        if hasattr(resp_msg, 'stop_reason'):
                            print(f"__ LLM Debug: Stop reason: {resp_msg.stop_reason}", file=sys.stderr)
                    
                    return text, was_truncated
                except Exception:
                    return str(resp_msg), False
            raise

    # Default to Ollama HTTP API
    url = f"{OLLAMA_URL}/v1/chat/completions"
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': temperature,
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data['choices'][0]['message']['content'], False
    except Exception:
        raise RuntimeError(f"Unexpected response format from LLM: {data}")