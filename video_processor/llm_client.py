"""
llm_client.py

Wrapper for calling the Ollama chat completion API (Claude Opus 4).
"""
import os
import sys
import requests
import time
import random

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
    Supported backends: Ollama (default), Anthropic Cloud, OpenAI.
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
                stream=True,
            )
            # Handle streaming response
            completion = ""
            stop_reason = None
            for chunk in response:
                if hasattr(chunk, 'completion'):
                    completion += chunk.completion
                if hasattr(chunk, 'stop_reason'):
                    stop_reason = chunk.stop_reason
            
            # Check for token limit issues
            was_truncated = False
            if stop_reason == 'max_tokens':
                print(f"** ERROR: Output truncated due to OUTPUT token limit ({max_tokens} tokens reached)", file=sys.stderr)
                was_truncated = True
            
            # Debug logging for output
            if debug:
                output_length = len(completion)
                estimated_output_tokens = output_length // 4
                print(f"__ LLM Debug: Output length: {output_length} chars (~{estimated_output_tokens} tokens)", file=sys.stderr)
                if stop_reason:
                    print(f"__ LLM Debug: Stop reason: {stop_reason}", file=sys.stderr)
            
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
                    stream=True,
                )
                # Handle streaming Messages API response
                try:
                    text = ''
                    stop_reason = None
                    for chunk in resp_msg:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            text += chunk.delta.text
                        elif hasattr(chunk, 'message') and hasattr(chunk.message, 'stop_reason'):
                            stop_reason = chunk.message.stop_reason
                        elif hasattr(chunk, 'stop_reason'):
                            stop_reason = chunk.stop_reason
                    
                    # Check for token limit issues in Messages API
                    was_truncated = False
                    if stop_reason == 'max_tokens':
                        print(f"** ERROR: Output truncated due to OUTPUT token limit ({max_tokens} tokens reached)", file=sys.stderr)
                        was_truncated = True
                    
                    # Debug logging for Messages API output
                    if debug:
                        output_length = len(text)
                        estimated_output_tokens = output_length // 4
                        print(f"__ LLM Debug: Output length: {output_length} chars (~{estimated_output_tokens} tokens)", file=sys.stderr)
                        if stop_reason:
                            print(f"__ LLM Debug: Stop reason: {stop_reason}", file=sys.stderr)
                    
                    return text, was_truncated
                except Exception:
                    return str(resp_msg), False
            raise

    if backend == 'openai':
        # OpenAI API implementation
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY is not set')
        
        # Get base URL from config or use default
        # Load config similar to how config.py does it
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        
        # Load config from project-local config.toml if it exists
        config = {}
        from pathlib import Path
        config_path = Path.cwd() / "config.toml"
        if config_path.exists():
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
        
        base_url = config.get('openai_base_url', 'https://api.openai.com/v1')
        
        # Use API key from config if available, otherwise use environment variable
        config_api_key = config.get('openai_api_key')
        if config_api_key:
            api_key = config_api_key
        
        use_responses_api = model.startswith("gpt-5")
        if use_responses_api:
            url = f"{base_url}/responses"
            payload = {
                'model': model,
                'input': prompt,
                'max_output_tokens': max_tokens,
                'temperature': temperature,
            }
        else:
            url = f"{base_url}/chat/completions"
            payload = {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
            }
            # Some newer models (like o4-mini, o3) have specific requirements
            if model.startswith(('o3-', 'o4-')):
                payload['max_completion_tokens'] = max_tokens
                # These models only support temperature=1 (default)
                if temperature != 1.0:
                    if debug:
                        print(f"__ LLM Debug: Model {model} only supports temperature=1, ignoring temperature={temperature}", file=sys.stderr)
            else:
                payload['max_tokens'] = max_tokens
                payload['temperature'] = temperature
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Retry logic for OpenAI API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [500, 502, 503, 504] and attempt < max_retries - 1:
                    # Server errors - retry with exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    if debug:
                        print(f"__ LLM Debug: Server error {e.response.status_code}, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                else:
                    # Client errors or max retries reached - format error message
                    if e.response.status_code == 401:
                        raise RuntimeError("** OpenAI API key is invalid or expired")
                    elif e.response.status_code == 429:
                        raise RuntimeError("** OpenAI API rate limit exceeded")
                    elif e.response.status_code == 404:
                        raise RuntimeError(f"** OpenAI model '{model}' not found or not available")
                    else:
                        try:
                            error_data = e.response.json()
                            error_msg = error_data.get('error', {}).get('message', str(e))
                            raise RuntimeError(f"** OpenAI API error: {error_msg}")
                        except:
                            raise RuntimeError(f"** OpenAI API error: {e}")
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    # Network errors - retry with exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    if debug:
                        print(f"__ LLM Debug: Network error, retrying in {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                else:
                    # Max retries reached
                    raise RuntimeError(f"** OpenAI API connection failed after {max_retries} attempts: {e}")
            except Exception as e:
                # Other exceptions (JSON parsing, etc.)
                err = str(e)
                if 'token' in err.lower() and ('limit' in err.lower() or 'exceeded' in err.lower()):
                    raise RuntimeError(f"** Token limit exceeded: {err}. Consider reducing transcript length or increasing token limit.")
                raise RuntimeError(f"** OpenAI API error: {err}")
        else:
            # This should not happen, but just in case
            raise RuntimeError("** OpenAI API call failed after all retry attempts")
            
        if use_responses_api:
            # Extract response content from Responses API
            parts = []
            for item in data.get('output', []):
                if item.get('type') == 'message':
                    for c in item.get('content', []):
                        if c.get('type') == 'output_text':
                            parts.append(c.get('text', ''))
            content = "".join(parts).strip()
            if not content:
                # Fallbacks for unexpected shapes
                content = data.get('output_text', '') or data.get('text', '')
            
            # Check for truncation / incomplete response
            was_truncated = False
            if data.get('status') == 'incomplete' or data.get('incomplete_details'):
                print("** ERROR: Output truncated or incomplete (Responses API)", file=sys.stderr)
                was_truncated = True
            
            if debug:
                usage = data.get('usage', {})
                print(f"__ LLM Debug: OpenAI usage: {usage}", file=sys.stderr)
                print(f"__ LLM Debug: Output length: {len(content)} chars", file=sys.stderr)
                print(f"__ LLM Debug: Status: {data.get('status')}", file=sys.stderr)
            
            return content, was_truncated
        
        # Extract response content (Chat Completions)
        content = data['choices'][0]['message']['content']
        
        # Check for truncation
        was_truncated = False
        finish_reason = data['choices'][0].get('finish_reason', '')
        if finish_reason == 'length':
            # For reasoning models, check if completion tokens were used for reasoning
            usage = data.get('usage', {})
            completion_details = usage.get('completion_tokens_details', {})
            reasoning_tokens = completion_details.get('reasoning_tokens', 0)
            if reasoning_tokens > 0:
                print(f"** ERROR: Output truncated due to reasoning token limit ({reasoning_tokens} reasoning tokens used)", file=sys.stderr)
            else:
                print(f"** ERROR: Output truncated due to OUTPUT token limit ({max_tokens} tokens reached)", file=sys.stderr)
            was_truncated = True
        
        # Debug logging for OpenAI output
        if debug:
            usage = data.get('usage', {})
            print(f"__ LLM Debug: OpenAI usage: {usage}", file=sys.stderr)
            output_length = len(content)
            print(f"__ LLM Debug: Output length: {output_length} chars", file=sys.stderr)
            print(f"__ LLM Debug: Finish reason: {finish_reason}", file=sys.stderr)
        
        return content, was_truncated

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
