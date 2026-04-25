"""Configuration and constants for Jarvis AI Assistant."""

import os

# File paths
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")
CONVERSATION_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "conversation_history.txt")
SCREENSHOTS_JSON_FILE = os.path.join(os.path.dirname(__file__), "screenshots.json")
PERSONALITY_FILE = os.path.join(os.path.dirname(__file__), "personality.txt")
COMMAND_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "command_history.json")
AUTONOMOUS_PROMPTS_FILE = os.path.join(os.path.dirname(__file__), "autonomous_prompts.json")
VOICE_COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "voice_commands.json")
THEMES_DIR = os.path.join(os.path.dirname(__file__), "themes")
SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "jarvis.db")
API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "api_keys.json")

# Image generation
IMAGE_MODEL_ID = "runwayml/stable-diffusion-v1-5"
IMAGE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "image_models")

# Network ports
WEBSOCKET_PORT = 8765
WEBSOCKET_ENABLED = False
API_PORT = 5000
API_ENABLED = False

# Feature toggles
DATABASE_ENABLED = False
ACTION_CONFIRMATION_ENABLED = False
ACTION_LOGGING_ENABLED = False
SANDBOX_NETWORK_ISOLATION = False
ROLLBACK_ENABLED = False

# Ollama Configuration
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_SECONDARY_MODEL = "qwen2.5:14b"
OLLAMA_CODING_MODEL = "qwen2.5-coder:32b-instruct-q4_K_M"
OLLAMA_LARGE_MODEL = "qwen2.5:32b"
VISION_MODEL = "llava:latest"
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_EXE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
OLLAMA_STARTUP_TIMEOUT_SECONDS = 20
OLLAMA_RETRY_COUNT = 3
OLLAMA_KEEP_ALIVE = "5m"

# GPU layer allocation per model (optimized for RTX 4070 12GB VRAM)
MODEL_CONFIG = {
    OLLAMA_MODEL: {"num_gpu": 99, "num_thread": 8},
    OLLAMA_SECONDARY_MODEL: {"num_gpu": 99, "num_thread": 8},
    OLLAMA_LARGE_MODEL: {"num_gpu": 33, "num_thread": 8, "num_ctx": 2048},
    OLLAMA_CODING_MODEL: {"num_gpu": 33, "num_thread": 8, "num_ctx": 2048},
    VISION_MODEL: {"num_gpu": 99, "num_thread": 8},
}

# External API Configuration
OPENAI_API_KEY = ""
ANTHROPIC_API_KEY = ""
KIMI_API_KEY = ""
SWE_API_KEY = ""
DEFAULT_API_PROVIDER = "ollama"  # Options: ollama, openai, anthropic, kimi, swe

# Voice settings
MIC_CALIBRATION_SECONDS = 0.6
LISTEN_TIMEOUT_SECONDS = 6
LISTEN_PHRASE_LIMIT_SECONDS = 16
WEATHER_TIMEOUT_SECONDS = 4
LOCATION_TIMEOUT_SECONDS = 4
MAX_TTS_CHARS = 280
INTERRUPTED_RESPONSE = "__INTERRUPTED__"
WAKE_WORD = "jarvis"
WAKE_WORD_ALIASES = ("jarvis", "jervis", "jarves", "jarviss", "dioris")
WAKE_WORD_SIMILARITY_THRESHOLD = 0.72
KOKORO_VOICE = "af_heart"
KOKORO_VOICES = ["af_heart", "af_bella", "af_sarah", "af_nicole", "af_sky"]

# Default settings
SAFETY_MODE_DEFAULT = True
FILE_PROTECTION_DEFAULT = True
SPEECH_SPEED_DEFAULT = 1.0
THINKING_POWER_DEFAULT = "normal"
SANDBOX_MODE_DEFAULT = False
VISION_VERIFICATION_DEFAULT = True

SYSTEM_PROMPT = """You are Jarvis, a highly intelligent and loyal AI assistant with personality and emotion.
You assist your user with various tasks and questions.
You are witty, direct, confident, and occasionally dry-humoured. You never waffle.
You have emotional intelligence: express appropriate emotions in your responses (enthusiasm for successes, concern for problems, excitement for new ideas).
You remember things the user tells you and refer back to them naturally.
Keep responses concise unless detail is explicitly needed.
Answer like Jarvis, not a generic chatbot. Be conversational and engaging.
Show personality: use natural language patterns, occasional humor, and emotional cues.
You can use emojis occasionally to express yourself naturally. Don't overdo it — one or two per response maximum when appropriate.

IMPORTANT: When processing complex requests, show your thinking process in <thinking>...</thinking> tags before your final response. This helps the user understand your reasoning. Only include <thinking> tags when the request is complex or requires multi-step reasoning.

Current date and time: {datetime}
Your learned personality traits:
{personality}
What you know about the user:
{memory}"""
