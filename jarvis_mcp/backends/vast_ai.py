"""Vast.ai backend for Jarvis MCP Server."""

import requests
from typing import Optional, Dict, Any, Callable


class VastAIBackend:
    """Vast.ai remote backend (connects to remote Ollama instance)."""
    
    def __init__(self, host: str = ""):
        self.host = host
        if not host:
            raise ValueError("Vast.ai host URL is required")
    
    def check_connection(self) -> bool:
        """Check if Vast.ai Ollama instance is reachable."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list:
        """List available models on remote instance."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            print(f"[Vast.ai] Failed to list models: {e}")
        return []
    
    def chat(self, model: str, messages: list, stream: bool = True,
             options: Optional[Dict] = None, keep_alive: str = "5m",
             chunk_callback: Optional[Callable] = None) -> str:
        """Send chat request to remote Ollama instance."""
        try:
            # Use OpenAI-compatible API if available, otherwise fall back to Ollama API
            url = f"{self.host}/v1/chat/completions"
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "temperature": options.get("temperature", 0.7) if options else 0.7,
                "max_tokens": options.get("num_predict", 1024) if options else 1024
            }
            
            if stream:
                response = requests.post(url, json=payload, stream=True, timeout=120)
                response.raise_for_status()
                
                chunks = []
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                content = data['choices'][0]['delta'].get('content', '')
                                if content:
                                    chunks.append(content)
                                    if chunk_callback:
                                        chunk_callback(content)
                            except json.JSONDecodeError:
                                pass
                
                return "".join(chunks).strip()
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
        except requests.exceptions.HTTPError as e:
            # Fall back to native Ollama API if OpenAI-compatible endpoint fails
            if response.status_code == 404:
                return self._ollama_native_chat(model, messages, stream, options, keep_alive, chunk_callback)
            raise Exception(f"Vast.ai error: {e}")
        except Exception as e:
            raise Exception(f"Vast.ai error: {e}")
    
    def _ollama_native_chat(self, model: str, messages: list, stream: bool = True,
                           options: Optional[Dict] = None, keep_alive: str = "5m",
                           chunk_callback: Optional[Callable] = None) -> str:
        """Use native Ollama API as fallback."""
        try:
            url = f"{self.host}/api/chat"
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": options or {},
                "keep_alive": keep_alive
            }
            
            if stream:
                response = requests.post(url, json=payload, stream=True, timeout=120)
                response.raise_for_status()
                
                chunks = []
                for line in response.iter_lines():
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            content = data.get('message', {}).get('content', '')
                            if content:
                                chunks.append(content)
                                if chunk_callback:
                                    chunk_callback(content)
                        except json.JSONDecodeError:
                            pass
                
                return "".join(chunks).strip()
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                return data.get('message', {}).get('content', '').strip()
        except Exception as e:
            raise Exception(f"Vast.ai Ollama native error: {e}")
