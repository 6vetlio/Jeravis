# Jarvis - Local AI Voice Assistant

A local AI voice assistant powered by Ollama, Kokoro TTS, and Whisper voice input. Jarvis runs entirely on your local machine with no cloud dependencies for core functionality.

## Features

- **Local AI**: Powered by Ollama's `qwen2.5:7b` model
- **Voice Input**: Whisper-based speech recognition via SpeechRecognition
- **Voice Output**: Kokoro TTS with `af_heart` voice
- **Direct Skills**: Weather (wttr.in) and location (ipinfo.io) lookups without LLM routing
- **Persistent Memory**: Remembers facts across sessions via `memory.json`
- **PC Control**: PowerShell subprocess for local computer control
- **Interruptible**: Can be interrupted mid-speech with voice commands
- **Fuzzy Wake Word**: Supports aliases like "Dioris" for wake-word detection
- **Conversationally Persistent**: Non-prompt-based, keeps conversation flowing

## Requirements

- Python 3.11
- Ollama with `qwen2.5:7b` model installed
- Windows (PowerShell for PC control)
- Microphone (device index 1 configured for Steinberg UR22mkII)

## Installation

1. Install Ollama: https://ollama.com
2. Pull the required model:
   ```powershell
   ollama pull qwen2.5:7b
   ```
3. Install Python dependencies:
   ```powershell
   pip install ollama kokoro-onnx sounddevice SpeechRecognition requests pyperclip pillow
   ```
4. Download Kokoro TTS models (not included in repository due to size):
   - Download `kokoro-v1.0.onnx` (~325MB) and `voices-v1.0.bin` (~28MB)
   - Place both files in the same directory as `assistant.py`
   - Model source: https://github.com/remsky/Kokoro-FastAPI

## Usage

### CLI Version (No GUI)
Run Jarvis in the terminal:
```powershell
py -3.11 C:\Users\svet\Documents\GitHub\Жаравиз\assistant.py
```

### GUI Version
Run Jarvis with a graphical interface:
```powershell
py -3.11 C:\Users\svet\Documents\GitHub\Жаравиз\assistant_gui.py
```

The GUI includes:
- Conversation history display
- Text input field with Enter to send
- Voice enable/disable toggle button
- Status indicator (Ready, Listening, Processing)
- Dark theme interface
- Copy log button (copies conversation to clipboard)
- Screenshot button (captures screen to file)

**Note:** The current model (qwen2.5:7b) does not support vision. Screenshots are saved to files but not analyzed. For full vision capabilities like Gemini, you would need a vision-capable model like llava from Ollama.

Activate Jarvis by saying **"Jarvis"** or using the fuzzy aliases:
- "Jervis"
- "Jarves"
- "Jarviss"
- "Dioris" (common misrecognition)

You can also type messages directly without the wake word.

## Direct Skills

Jarvis bypasses the LLM for certain queries for faster, more accurate responses:

### Weather
- Ask: "What's the weather?" or "Jarvis what's the weather in London?"
- Uses wttr.in API with 4-second timeout
- Returns current conditions with temperature and feels-like

### Location
- Ask: "Where am I?" or "Jarvis what's my location?"
- Uses ipinfo.io API with 4-second timeout
- Returns city, region, country, coordinates, and timezone

## PC Control

Jarvis can execute PowerShell commands on your local machine. Prefix commands with `[PC_ACTION]:`:

```
Jarvis: [PC_ACTION]: Get-Process
```

## Configuration

Key constants in `assistant.py`:

```python
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_KEEP_ALIVE = "30m"  # Keep model warm for faster follow-ups
MIC_CALIBRATION_SECONDS = 0.6
LISTEN_TIMEOUT_SECONDS = 6
LISTEN_PHRASE_LIMIT_SECONDS = 16
MAX_TTS_CHARS = 280  # Cap spoken output to avoid Kokoro crashes
WAKE_WORD = "jarvis"
WAKE_WORD_SIMILARITY_THRESHOLD = 0.72
```

## Voice Input Tuning

SpeechRecognition thresholds configured for natural conversation flow:

```python
recognizer.pause_threshold = 0.6
recognizer.non_speaking_duration = 0.35
recognizer.phrase_threshold = 0.25
```

These values reduce premature cutoffs while maintaining responsiveness.

## Robustness Features

### Ollama Error Handling
- Automatic Ollama startup if not running
- Retry logic (3 attempts) for failed requests
- Specific error messages for missing model vs connection issues
- Model warmup on startup for faster first response

### Voice Input Filtering
- Ignores junk transcripts (single characters, non-meaningful input)
- Fuzzy wake-word matching handles common misrecognitions
- Voice listener pauses while TTS is speaking

### TTS Safety
- `prepare_tts_text()` caps output length to avoid phoneme limit crashes
- TTS exceptions caught gracefully without crashing response worker
- Weather text normalization fixes encoding artifacts (e.g., `Â°C` → `degrees Celsius`)
- Country code expansion (e.g., `nl` → `Netherlands`)

### Memory Protection
- `normalize_memory()` protects against malformed `memory.json`
- UTF-8 read/write for memory file
- Graceful handling of missing/corrupted memory

### Clean Shutdown
- KeyboardInterrupt handling without traceback
- Proper thread cleanup

## Memory System

Jarvis stores facts in `memory.json`:

```json
{
  "facts": [],
  "conversation_count": 0
}
```

Facts are included in the system prompt and referenced naturally in conversation.

## System Prompt Behavior

Jarvis is configured to:
- Be witty, direct, confident, and occasionally dry-humoured
- Avoid generic chatbot limitation disclaimers
- Use `[PC_ACTION]` only for explicit local PC actions
- Reply in English by default unless asked otherwise
- Remember and reference facts naturally

## Troubleshooting

### "Can't find my brain" Error
- Ensure Ollama is running: check if `ollama.exe` is accessible
- Verify `qwen2.5:7b` model is installed: `ollama pull qwen2.5:7b`
- Check Ollama is accessible at `http://127.0.0.1:11434`

### Voice Cutoffs
- If Jarvis cuts you off too early, the thresholds can be adjusted:
  - Increase `LISTEN_PHRASE_LIMIT_SECONDS` (currently 16)
  - Increase `pause_threshold` (currently 0.6)
  - Increase `non_speaking_duration` (currently 0.35)

### TTS Crashes
- Long responses are automatically truncated to `MAX_TTS_CHARS` (280)
- If TTS still crashes, reduce `MAX_TTS_CHARS` further

### Wake Word Not Detected
- Try the fuzzy aliases: "Jervis", "Jarves", "Jarviss", "Dioris"
- If needed, lower `WAKE_WORD_SIMILARITY_THRESHOLD` (currently 0.72)

### Weather/Location Not Working
- Check internet connectivity (wttr.in and ipinfo.io require network)
- Verify API services are accessible (no blocking)
- Check timeout settings: `WEATHER_TIMEOUT_SECONDS = 4`, `LOCATION_TIMEOUT_SECONDS = 4`

## Hardware Context

Tested on:
- Windows with RTX 4070 (12GB VRAM) and 32GB RAM
- Microphone: Steinberg UR22mkII (device index 1)
- Ollama executable path: `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`

## Development History

### Initial Setup
- Basic Ollama integration with `qwen2.5:7b`
- Kokoro TTS with `af_heart` voice
- Whisper voice input via SpeechRecognition
- PowerShell subprocess for PC control
- Persistent memory via `memory.json`

### Latency Reduction
- Removed repeated per-loop microphone recalibration
- Mic now calibrates once at startup
- Tuned SpeechRecognition thresholds for faster end-of-speech detection
- Added `OLLAMA_KEEP_ALIVE = "30m"` and background warmup
- Avoids saying 'Yes?' when the same utterance already contains the full request

### Direct Skills
- Added direct weather skill using `wttr.in` via `requests`
- Added direct location skill using `ipinfo.io`
- Bypasses LLM for faster, more accurate responses

### Conversation Persistence
- Refactored main loop into persistent conversation mode
- Background response worker with interrupt support
- `speaking_event` and `interrupt_event` for TTS and input coordination
- Streaming Ollama responses with keep-alive

### Wake Word Hardening
- Fuzzy wake-word detection using `difflib.SequenceMatcher`
- Aliases: "jarvis", "jervis", "jarves", "jarviss", "dioris"
- Similarity threshold: 0.72

### Robustness Improvements
- `normalize_memory()` protects against malformed `memory.json`
- Resilient Ollama startup with retries
- `ask_ollama()` retries instead of failing on first exception
- Safer Ollama response parsing via `extract_ollama_content()`
- Specific error messages for missing model vs connection issues
- UTF-8 memory file read/write
- Clean KeyboardInterrupt handling

### Stream Assembly Fix
- Fixed streamed Ollama response assembly by preserving chunk spacing
- Previously words were smashed together without spaces

### TTS Safety
- Added `prepare_tts_text()` and `MAX_TTS_CHARS` to cap spoken output
- Prevents Kokoro phoneme limit crashes
- `speak()` now catches TTS exceptions instead of crashing response worker
- Weather text normalization fixes encoding artifacts
- Country code expansion for natural speech

### Voice Input Filtering
- Added `is_meaningful_voice_text()` to ignore junk transcripts
- Filters single-character and non-meaningful recognitions
- Wake-word matching still supports fuzzy aliases

### Voice Timing Tune
- Increased `LISTEN_PHRASE_LIMIT_SECONDS` from 12 to 16
- Relaxed speech-end thresholds: `pause_threshold=0.6`, `non_speaking_duration=0.35`, `phrase_threshold=0.25`
- Reduces premature voice cutoffs

## License

Personal project for local AI assistant development.
