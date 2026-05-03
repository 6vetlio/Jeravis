"""Ollama backend for Jarvis MCP Server."""

import ollama
import requests
from typing import Optional, Dict, Any, Callable


class OllamaBackend:
    """Ollama model backend."""
    
    def __init__(self, host: str = "http://127.0.0.1:11434"):
        self.host = host
        self.client = ollama.Client(host=host)
    
    def check_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list:
        """List available models."""
        try:
            response = self.client.list()
            return [model['name'] for model in response.get('models', [])]
        except Exception as e:
            print(f"[Ollama] Failed to list models: {e}")
            return []
    
    def chat(self, model: str, messages: list, stream: bool = True, 
             options: Optional[Dict] = None, keep_alive: str = "5m",
             chunk_callback: Optional[Callable] = None) -> str:
        """Send chat request to Ollama."""
        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                stream=stream,
                keep_alive=keep_alive,
                options=options or {}
            )
            
            chunks = []
            if stream:
                for chunk in response:
                    content = self._extract_content(chunk)
                    if content:
                        chunks.append(content)
                        if chunk_callback:
                            chunk_callback(content)
            else:
                content = self._extract_content(response)
                if content:
                    chunks.append(content)
            
            return "".join(chunks).strip()
        except Exception as e:
            raise Exception(f"Ollama error: {e}")
    
    def _extract_content(self, chunk) -> str:
        """Extract content from Ollama response chunk."""
        if hasattr(chunk, 'message') and chunk.message:
            if hasattr(chunk.message, 'content'):
                return chunk.message.content or ""
            if isinstance(chunk.message, dict):
                return chunk.message.get("content", "")
        if isinstance(chunk, dict):
            if "message" in chunk and isinstance(chunk["message"], dict):
                return chunk["message"].get("content", "")
            elif "content" in chunk:
                return chunk["content"]
        return ""
