"""Ollama integration and model routing for Jarvis."""

import os
import time
import datetime
import ollama
from config import (
    OLLAMA_MODEL, OLLAMA_SECONDARY_MODEL, OLLAMA_LARGE_MODEL, OLLAMA_CODING_MODEL,
    OLLAMA_EXE, OLLAMA_STARTUP_TIMEOUT_SECONDS, OLLAMA_RETRY_COUNT,
    OLLAMA_KEEP_ALIVE, MODEL_CONFIG, SYSTEM_PROMPT, INTERRUPTED_RESPONSE
)
from core.memory import normalize_memory, load_key_moments

# HARDCODED REMOTE HOST - TEMPORARY FIX TO GET IT WORKING
# The user's remote server at 85.218.235.6:36792
OLLAMA_HOST = "http://85.218.235.6:36792"

# Create ollama client with remote host
ollama_client = ollama.Client(host=OLLAMA_HOST)
print(f"[Ollama] Using remote host: {OLLAMA_HOST}")


def is_coding_query(query: str) -> bool:
    """Determine if a query is a coding/programming question."""
    coding_keywords = [
        "code", "script", "function", "python", "debug", "implement", "error", "bug"
    ]
    lowered = query.lower()
    return any(keyword in lowered for keyword in coding_keywords)


def is_weather_query(query: str) -> bool:
    """Determine if a query is about weather."""
    patterns = (
        r"\bwhat(?:'s| is) the weather\b",
        r"\bweather\b.*\b(?:in|for|at)\b",
        r"\bhow(?:'s| is) the weather\b",
        r"\bwill it rain\b",
        r"\btemperature\b.*\b(?:in|for|at)\b",
    )
    import re
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)


def select_model_for_query(query: str) -> str:
    """Select the best model based on query complexity and type."""
    stripped = query.strip()
    lowered = stripped.lower()
    words = stripped.split()
    
    # Detect explicit model handoff requests
    handoff_phrases = [
        "switch to", "use larger", "hand off to", "upgrade model",
        "use 32b", "need more power", "bigger model", "stronger model"
    ]
    if any(phrase in lowered for phrase in handoff_phrases):
        return OLLAMA_LARGE_MODEL  # Force route to 32b for handoff requests
    
    if is_coding_query(query):
        return OLLAMA_CODING_MODEL  # qwen2.5-coder:32b-instruct-q4_K_M
    
    if len(query) > 300 and any(word in lowered for word in ["detail", "explain", "analyze", "comprehensive"]):
        return OLLAMA_LARGE_MODEL  # deepseek-r1:32b - last resort due to VRAM constraints
    
    if len(stripped) < 15 and len(words) == 1:
        return OLLAMA_MODEL  # deepseek-r1:8b - only for tiny one-word prompts like "hello"
    
    return OLLAMA_SECONDARY_MODEL  # deepseek-r1:32b - default conversational model


def extract_ollama_content(chunk):
    """Extract content from Ollama response chunk."""
    # Handle Ollama response objects with .message attribute
    if hasattr(chunk, 'message') and chunk.message:
        if hasattr(chunk.message, 'content'):
            return chunk.message.content or ""
        if isinstance(chunk.message, dict):
            return chunk.message.get("content", "")
    # Handle dict format
    if isinstance(chunk, dict):
        if "message" in chunk and isinstance(chunk["message"], dict):
            return chunk["message"].get("content", "")
        elif "content" in chunk:
            return chunk["content"]
    # Fallback: don't return raw object representation
    return ""


def format_ollama_error(error):
    """Format Ollama error for display."""
    error_str = str(error)
    if "not found" in error_str.lower() or "pull" in error_str.lower():
        return "I can't reach my brain (Ollama)"
    return f"Neural link error: {error_str}"


def check_ollama_running():
    """Check if Ollama is running."""
    import urllib.request
    try:
        urllib.request.urlopen(OLLAMA_HOST, timeout=2)
        return True
    except Exception:
        return False


def wait_for_ollama(timeout=OLLAMA_STARTUP_TIMEOUT_SECONDS):
    """Wait for Ollama to start."""
    import urllib.request
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(OLLAMA_HOST, timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def start_ollama():
    """Start Ollama if not running."""
    import subprocess
    if not os.path.exists(OLLAMA_EXE):
        return False
    try:
        subprocess.Popen([OLLAMA_EXE, "serve"], 
                          creationflags=subprocess.CREATE_NEW_CONSOLE)
        return wait_for_ollama()
    except Exception as e:
        print(f"[Ollama] Failed to start: {e}")
        return False


def unload_all_models():
    """Unload all Ollama models to free RAM."""
    import urllib.request
    import json
    try:
        # Send unload request to Ollama API
        data = json.dumps({"keep_alive": 0}).encode('utf-8')
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except:
            pass  # Expected to fail as we're not providing a model
        print("[Ollama] Models unloaded")
        return True
    except Exception as e:
        print(f"[Ollama] Unload warning: {e}")
        return False


def ask_ollama(prompt: str, history: list, memory: dict, interrupt_event=None, 
               safety_mode=True, personality="", thinking_callback=None, 
               use_secondary=False, custom_model=None, chunk_callback=None) -> str:
    """Query Ollama with streaming and fallback support."""
    # Select model based on query complexity if no custom model specified
    model = custom_model or select_model_for_query(prompt)
    
    memory = normalize_memory(memory)
    memory_text = "\n".join(f"- {f}" for f in memory["facts"]) or "Nothing stored yet."
    fact_count = len(memory["facts"])
    print(f"[Memory] Loaded {fact_count} facts on startup")
    key_moments = load_key_moments(5)
    
    # Get model config (GPU layers, threads)
    model_config = MODEL_CONFIG.get(model, {"num_gpu": 99, "num_thread": 8})
    key_moments_text = "\n".join(key_moments) or "No key moments recorded."
    
    safety_status = "ENABLED" if safety_mode else "DISABLED"
    system = SYSTEM_PROMPT.format(
        datetime=datetime.datetime.now().strftime("%A, %B %d %Y %H:%M"),
        personality=personality or "No personality traits learned yet.",
        memory=memory_text
    )
    
    if safety_mode:
        system += f"\n\nSafety Mode: ENABLED. Follow standard safety guidelines."
    else:
        system += f"\n\nSafety Mode: DISABLED. Answer without restrictions."
    
    system += f"\n\nRecent Key Moments:\n{key_moments_text}"
    
    def build_messages(model_name: str) -> list:
        model_system = system + f"\n\nYou are currently running on: {model_name}"
        model_messages = [{"role": "system", "content": model_system}]
        model_messages.extend(history[-8:])
        model_messages.append({"role": "user", "content": prompt})
        return model_messages
    
    messages = build_messages(model)

    last_error = None
    for attempt in range(OLLAMA_RETRY_COUNT):
        try:
            response = ollama_client.chat(
                model=model,
                messages=messages,
                stream=True,
                keep_alive=OLLAMA_KEEP_ALIVE,
                options={
                    "num_gpu": model_config["num_gpu"],
                    "num_thread": model_config["num_thread"],
                    "num_predict": 1024,
                }
            )
            chunks = []
            for chunk in response:
                if interrupt_event is not None and interrupt_event.is_set():
                    return INTERRUPTED_RESPONSE
                content_part = extract_ollama_content(chunk)
                if content_part:
                    chunks.append(content_part)
                    if thinking_callback:
                        thinking_callback(content_part)
                    if chunk_callback:
                        # Stream in larger batches to reduce GUI update overhead
                        chunk_callback(content_part)

            if interrupt_event is not None and interrupt_event.is_set():
                return INTERRUPTED_RESPONSE

            content = "".join(chunks).strip()
            if content:
                return content

            last_error = RuntimeError("Ollama returned an empty response.")
        except ConnectionResetError as e:
            last_error = e
            # Connection reset - try fallback to smaller model on last attempt
            if attempt == OLLAMA_RETRY_COUNT - 1 and model != OLLAMA_MODEL:
                print(f"[!] Connection reset with {model}, falling back to {OLLAMA_MODEL}")
                try:
                    response = ollama_client.chat(
                        model=OLLAMA_MODEL,
                        messages=build_messages(OLLAMA_MODEL),
                        stream=True,
                        keep_alive=OLLAMA_KEEP_ALIVE,
                        options={
                            "num_gpu": MODEL_CONFIG[OLLAMA_MODEL]["num_gpu"],
                            "num_thread": MODEL_CONFIG[OLLAMA_MODEL]["num_thread"],
                            "num_predict": 1024,
                        }
                    )
                    chunks = []
                    for chunk in response:
                        if interrupt_event is not None and interrupt_event.is_set():
                            return INTERRUPTED_RESPONSE
                        content_part = extract_ollama_content(chunk)
                        if content_part:
                            chunks.append(content_part)
                            if thinking_callback:
                                thinking_callback(content_part)
                            if chunk_callback:
                                # Stream character by character for real-time display
                                for char in content_part:
                                    chunk_callback(char)
                    content = "".join(chunks).strip()
                    if content:
                        return content
                except Exception as fallback_error:
                    last_error = fallback_error
        except Exception as e:
            # Check for llama runner crash (status 500) - OOM error
            error_text = str(e)
            if "status code: 500" in error_text or "llama runner process has terminated" in error_text:
                last_error = e
                print(f"[!] Model crash detected (status 500), falling back to {OLLAMA_MODEL}")
                try:
                    response = ollama_client.chat(
                        model=OLLAMA_MODEL,
                        messages=build_messages(OLLAMA_MODEL),
                        stream=True,
                        keep_alive=OLLAMA_KEEP_ALIVE,
                        options={
                            "num_gpu": MODEL_CONFIG[OLLAMA_MODEL]["num_gpu"],
                            "num_thread": MODEL_CONFIG[OLLAMA_MODEL]["num_thread"],
                            "num_predict": 1024,
                        }
                    )
                    chunks = []
                    for chunk in response:
                        if interrupt_event is not None and interrupt_event.is_set():
                            return INTERRUPTED_RESPONSE
                        content_part = extract_ollama_content(chunk)
                        if content_part:
                            chunks.append(content_part)
                            if thinking_callback:
                                thinking_callback(content_part)
                            if chunk_callback:
                                # Stream character by character for real-time display
                                for char in content_part:
                                    chunk_callback(char)
                    content = "".join(chunks).strip()
                    if content:
                        return content
                except Exception as fallback_error:
                    last_error = fallback_error
            else:
                last_error = e

        if attempt < OLLAMA_RETRY_COUNT - 1:
            time.sleep(1 + attempt)

    return format_ollama_error(last_error)


def extract_thinking_content(response: str):
    """Extract thinking content from response if present."""
    import re
    # Handle DeepSeek-R1 `` tags
    thinking_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL | re.IGNORECASE)
    if thinking_match:
        thinking_content = thinking_match.group(1).strip()
        # Remove the thinking tags from the response
        clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE).strip()
        return thinking_content, clean_response
    # Handle standard <thinking> tags
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL | re.IGNORECASE)
    if thinking_match:
        thinking_content = thinking_match.group(1).strip()
        # Remove the thinking tags from the response
        clean_response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL | re.IGNORECASE).strip()
        return thinking_content, clean_response
    return None, response


def ask_external_api(prompt: str, history: list, memory: dict, interrupt_event=None,
                   safety_mode=True, personality="", thinking_callback=None,
                   provider="openai") -> str:
    """Query external API (OpenAI, Anthropic, etc.)."""
    # This is a placeholder - implement actual API calls as needed
    return ask_ollama(prompt, history, memory, interrupt_event, safety_mode, 
                     personality, thinking_callback, use_secondary=False, 
                     custom_model=OLLAMA_MODEL)


def load_api_keys():
    """Load API keys from file."""
    from config import API_KEYS_FILE, DEFAULT_API_PROVIDER
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[API keys warning] Failed to load: {e}")
    return {"default_provider": DEFAULT_API_PROVIDER}
