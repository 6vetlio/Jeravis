"""Configuration management for Jarvis MCP Server."""

import os
import json
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "backend": "ollama",
    "ollama_host": "http://127.0.0.1:11434",
    "lm_studio_host": "http://127.0.0.1:1234",
    "vast_ai_host": "",
    "models": {
        "default": "deepseek-r1:32b",
        "coding": "qwen2.5-coder:32b-instruct-q4_K_M",
        "tiny": "deepseek-r1:8b"
    },
    "memory_enabled": True,
    "personality_enabled": True,
    "pc_control_enabled": True,
    "safety_mode": True,
    "sandbox_mode": False,
    "thinking_visibility": True,
    "keep_alive": "5m",
    "retry_count": 3
}

# File paths
CONFIG_DIR = Path.home() / ".jarvis_mcp"
CONFIG_FILE = CONFIG_DIR / "config.json"
MEMORY_FILE = CONFIG_DIR / "memory.json"
PERSONALITY_FILE = CONFIG_DIR / "personality.txt"
CONVERSATION_HISTORY_FILE = CONFIG_DIR / "conversation_history.txt"


def load_config() -> dict:
    """Load configuration from file or use defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Config] Failed to load config, using defaults: {e}")
            return DEFAULT_CONFIG.copy()
    
    # Save default config if it doesn't exist
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def get_config_value(key: str, default=None):
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value):
    """Set a specific configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)
