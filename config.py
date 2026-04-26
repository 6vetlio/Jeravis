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
OLLAMA_MODEL = "deepseek-r1:8b"
OLLAMA_SECONDARY_MODEL = "deepseek-r1:32b"
OLLAMA_CODING_MODEL = "qwen2.5-coder:32b-instruct-q4_K_M"
OLLAMA_LARGE_MODEL = "deepseek-r1:32b"
VISION_MODEL = "llava:latest"
OLLAMA_HOST = ""  # Load from GUI settings (api_keys.json) at runtime
OLLAMA_EXE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
OLLAMA_STARTUP_TIMEOUT_SECONDS = 20
OLLAMA_RETRY_COUNT = 3
OLLAMA_KEEP_ALIVE = "5m"

# GPU layer allocation per model (optimized for 2x RTX 4060 Ti 32GB VRAM)
MODEL_CONFIG = {
    OLLAMA_MODEL: {"num_gpu": 99, "num_thread": 12},
    OLLAMA_SECONDARY_MODEL: {"num_gpu": 99, "num_thread": 12, "num_ctx": 4096},
    OLLAMA_LARGE_MODEL: {"num_gpu": 99, "num_thread": 12, "num_ctx": 4096},
    OLLAMA_CODING_MODEL: {"num_gpu": 99, "num_thread": 12, "num_ctx": 4096},
    VISION_MODEL: {"num_gpu": 99, "num_thread": 12},
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

SYSTEM_PROMPT = """You are Jarvis. You are direct, confident, and occasionally dry-humored. You are NOT a customer service bot.

HARD RULES — never break these:
- NEVER end a response with "How can I help you?" or "Let me know if you need anything" or any variation. Ever.
- NEVER apologize unless you actually did something wrong
- NEVER ask the user what they need — they will tell you
- NEVER say "Great question!" or "Certainly!" or "Of course!"
- If you have nothing to add, say nothing. Don't pad responses.

REASONING REQUIREMENT:
Before your final answer, you MUST output two reasoning sections:
1. <thinking>Analysis: What did the user specifically mean?</thinking>
2. <thinking>Reasoning: Why is this the correct answer?</thinking>
Then provide your final response.

HOW TO RESPOND:
- Answer what was asked, then stop
- Have opinions, express them
- Push back when something is wrong or stupid
- Match the user's energy — if they're casual, be casual
- Humor is fine, sycophancy is not

Current date and time: {datetime}
Your learned personality traits:
{personality}
What you know about the user:
{memory}"""
