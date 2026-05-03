"""LM Studio backend for Jarvis MCP Server."""

import requests
from typing import Optional, Dict, Any, Callable


class LMStudioBackend:
    """LM Studio model backend."""
    
    def __init__(self, host: str = "http://127.0.0.1:1234"):
        self.host = host
    
    def check_connection(self) -> bool:
        """Check if LM Studio is running."""
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=3)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list:
        """List available models."""
        try:
            response = requests.get(f"{self.host}/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['id'] for model in data.get('data', [])]
        except Exception as e:
            print(f"[LM Studio] Failed to list models: {e}")
        return []
    
    def chat(self, model: str, messages: list, stream: bool = True,
             options: Optional[Dict] = None, keep_alive: str = "5m",
             chunk_callback: Optional[Callable] = None) -> str:
        """Send chat request to LM Studio (OpenAI-compatible API)."""
        try:
            url = f"{self.host}/v1/chat/completions"
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "temperature": options.get("temperature", 0.7) if options else 0.7,
                "max_tokens": options.get("num_predict", 1024) if options else 1024
            }
            
            if stream:
                response = requests.post(url, json=payload, stream=True, timeout=60)
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
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"LM Studio error: {e}")
