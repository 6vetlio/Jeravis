import os
import json
import datetime
import difflib
import re
import subprocess
import threading
import queue
import time
import sys

import tkinter as tk
from tkinter import scrolledtext, ttk
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False
try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import ollama
import requests
from kokoro_onnx import Kokoro

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_EXE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
OLLAMA_STARTUP_TIMEOUT_SECONDS = 20
OLLAMA_RETRY_COUNT = 3
OLLAMA_KEEP_ALIVE = "30m"
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

SYSTEM_PROMPT = """You are Jarvis, a highly intelligent and loyal AI assistant.
You assist your user — a Bulgarian developer working on VR and game development projects in Unity.
You are witty, direct, confident, and occasionally dry-humoured. You never waffle.
You remember things the user tells you and refer back to them naturally.
You can control the user's PC, answer questions, write code, and manage tasks.
Keep responses concise unless detail is explicitly needed.
Answer like Jarvis, not a generic chatbot.
Do not volunteer limitations unless a live lookup or action actually failed.
Use [PC_ACTION] only for explicit local PC actions. Do not use [PC_ACTION] for weather, location, or normal question answering.
Reply in English by default unless the user clearly asks for another language.
When asked to do something on the PC, prefix your action with [PC_ACTION]: followed by a PowerShell command.
Current date and time: {datetime}
What you know about the user:
{memory}"""


def normalize_memory(memory):
    if not isinstance(memory, dict):
        return {"facts": [], "conversation_count": 0}

    normalized = dict(memory)
    facts = normalized.get("facts")
    if not isinstance(facts, list):
        facts = []

    conversation_count = normalized.get("conversation_count", 0)
    try:
        conversation_count = int(conversation_count)
    except (TypeError, ValueError):
        conversation_count = 0

    normalized["facts"] = [str(fact) for fact in facts if str(fact).strip()]
    normalized["conversation_count"] = max(0, conversation_count)
    return normalized


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return normalize_memory(json.load(f))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"[Memory warning] Failed to load memory: {e}")
    return {"facts": [], "conversation_count": 0}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(normalize_memory(memory), f, indent=2, ensure_ascii=False)


def add_memory_fact(fact: str, memory: dict):
    facts = memory.setdefault("facts", [])
    if not isinstance(facts, list):
        memory["facts"] = []
        facts = memory["facts"]
    if fact not in facts:
        facts.append(fact)
        save_memory(memory)


def execute_pc_action(command: str):
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip() or result.stderr.strip() or "Done."
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error: {e}"


def find_wake_word_span(text: str):
    for match in re.finditer(r"[A-Za-z']+", text):
        token = match.group(0).lower()
        for alias in WAKE_WORD_ALIASES:
            if token == alias:
                return match.start(), match.end()
            similarity = difflib.SequenceMatcher(None, token, alias).ratio()
            if similarity >= WAKE_WORD_SIMILARITY_THRESHOLD:
                return match.start(), match.end()
    return None


def contains_wake_word(text: str) -> bool:
    return find_wake_word_span(text) is not None


def is_meaningful_voice_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False

    if contains_wake_word(stripped):
        return True

    alnum_count = sum(1 for char in stripped if char.isalnum())
    ascii_letter_count = sum(1 for char in stripped if char.isascii() and char.isalpha())

    if alnum_count < 2:
        return False

    if ascii_letter_count == 0 and len(stripped) <= 3:
        return False

    return True


def should_interrupt(text: str) -> bool:
    lowered = text.lower().strip()
    if contains_wake_word(text):
        return True
    return any(phrase in lowered for phrase in ("stop", "cancel", "wait", "hold on", "quiet"))


def extract_query_after_wake_word(text: str) -> str:
    span = find_wake_word_span(text)
    if span is None:
        return ""
    return text[span[1]:].strip(" ,.")


def prepare_tts_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= MAX_TTS_CHARS:
        return compact

    truncated = compact[:MAX_TTS_CHARS].rsplit(" ", 1)[0].strip()
    if not truncated:
        truncated = compact[:MAX_TTS_CHARS].strip()
    return f"{truncated}..."


def speak(engine: Kokoro, text: str, speaking_event=None, interrupt_event=None, log_callback=None):
    clean = text
    if "[PC_ACTION]:" in text:
        clean = text[:text.index("[PC_ACTION]:")].strip()
    if not clean:
        return
    spoken_text = prepare_tts_text(clean)
    if speaking_event is not None:
        speaking_event.set()
    try:
        if log_callback:
            log_callback(f"\nJarvis: {clean}")
        else:
            print(f"\nJarvis: {clean}")
        samples, sample_rate = engine.create(spoken_text, voice="af_heart", speed=1.0, lang="en-us")
        sd.play(samples, sample_rate)
        while True:
            if interrupt_event is not None and interrupt_event.is_set():
                sd.stop()
                break
            stream = sd.get_stream()
            if stream is None or not stream.active:
                break
            time.sleep(0.05)
    except Exception as e:
        if log_callback:
            log_callback(f"[TTS error: {e}]")
        else:
            print(f"[TTS error: {e}]")
    finally:
        if speaking_event is not None:
            speaking_event.clear()


def is_weather_query(query: str) -> bool:
    return bool(re.search(r"\b(weather|forecast|temperature|rain|raining|snow|snowing|sunny|windy)\b", query, re.IGNORECASE))


def is_location_query(query: str) -> bool:
    patterns = (
        r"\bwhere am i\b",
        r"\bwhat(?:'s| is) my location\b",
        r"\bcurrent location\b",
        r"\bmy location\b",
        r"\bwhere are we\b",
    )
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)


def extract_weather_location(query: str) -> str:
    match = re.search(r"\b(?:in|for|at)\s+(.+)$", query, re.IGNORECASE)
    if not match:
        return ""

    location = match.group(1).strip(" ?!.,")
    location = re.sub(r"\b(right now|today|now|please)\b$", "", location, flags=re.IGNORECASE).strip(" ,.")
    return location


def get_weather_response(query: str) -> str | None:
    if not is_weather_query(query):
        return None

    location = extract_weather_location(query)
    location_path = requests.utils.quote(location) if location else ""

    try:
        response = requests.get(
            f"https://wttr.in/{location_path}",
            params={"format": "%l: %t, %C, feels like %f"},
            headers={"User-Agent": "Jarvis"},
            timeout=WEATHER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        weather_text = normalize_weather_text(response.text.strip())
        if not weather_text:
            raise ValueError("Weather service returned an empty response.")
        return f"Right now, {weather_text}."
    except Exception as e:
        target = location.title() if location else "your area"
        return f"I couldn't fetch the live weather for {target} right now. Error: {e}"


def get_location_response(query: str) -> str | None:
    if not is_location_query(query):
        return None

    try:
        response = requests.get(
            "https://ipinfo.io/json",
            headers={"User-Agent": "Jarvis"},
            timeout=LOCATION_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        city = (data.get("city") or "").strip()
        region = (data.get("region") or "").strip()
        country = (data.get("country") or "").strip()
        loc = (data.get("loc") or "").strip()
        timezone = (data.get("timezone") or "").strip()

        place_parts = [part for part in (city, region, country) if part]
        place = ", ".join(place_parts) if place_parts else "an unknown location"

        details = []
        if loc:
            details.append(f"coordinates {loc}")
        if timezone:
            details.append(f"timezone {timezone}")

        if details:
            return f"You appear to be in {place}, with {' and '.join(details)}."
        return f"You appear to be in {place}."
    except Exception as e:
        return f"I couldn't determine your current location right now. Error: {e}"


def expand_country_code(country: str) -> str:
    mapping = {
        "nl": "Netherlands",
        "bg": "Bulgaria",
        "uk": "United Kingdom",
        "gb": "United Kingdom",
        "us": "United States",
        "de": "Germany",
        "fr": "France",
    }
    stripped = country.strip()
    if not stripped:
        return stripped
    return mapping.get(stripped.lower(), stripped.upper() if len(stripped) == 2 else stripped)


def normalize_weather_text(weather_text: str) -> str:
    cleaned = weather_text.replace("Â°", "°")
    cleaned = re.sub(r"\b([A-Za-z\- ]+),\s*([A-Za-z\- ]+),\s*([A-Za-z]{2})\b", lambda m: f"{m.group(1).title()}, {m.group(2).title()}, {expand_country_code(m.group(3))}", cleaned)
    cleaned = re.sub(r"\b([+-]?\d+)°C\b", r"\1 degrees Celsius", cleaned)
    cleaned = re.sub(r"\b([+-]?\d+)°F\b", r"\1 degrees Fahrenheit", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned


def handle_direct_query(query: str, memory: dict) -> str | None:
    del memory
    weather_response = get_weather_response(query)
    if weather_response is not None:
        return weather_response
    location_response = get_location_response(query)
    if location_response is not None:
        return location_response
    return None


def check_ollama_running():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


def wait_for_ollama(timeout_seconds: int = OLLAMA_STARTUP_TIMEOUT_SECONDS) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if check_ollama_running():
            return True
        time.sleep(1)
    return False


def start_ollama_if_needed() -> bool:
    if check_ollama_running():
        return True

    if not OLLAMA_EXE or not os.path.exists(OLLAMA_EXE):
        print(f"[!] Ollama executable not found: {OLLAMA_EXE}")
        return False

    print("[!] Ollama is not running. Starting it...")
    try:
        subprocess.Popen(
            [OLLAMA_EXE, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except OSError as e:
        print(f"[!] Failed to start Ollama: {e}")
        return False

    if wait_for_ollama():
        return True

    print("[!] Ollama did not become ready in time.")
    return False


def warm_ollama_model():
    try:
        ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Reply with: ready"}],
            options={"num_predict": 1},
            keep_alive=OLLAMA_KEEP_ALIVE,
        )
    except Exception as e:
        print(f"[Brain warmup warning] {e}")


def extract_ollama_content(response) -> str:
    if isinstance(response, dict):
        message = response.get("message", {})
        if isinstance(message, dict):
            content = message.get("content") or ""
            return content if isinstance(content, str) else ""

    message = getattr(response, "message", None)
    if message is not None:
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content

    return ""


def format_ollama_error(error: Exception) -> str:
    error_text = str(error).strip() or error.__class__.__name__
    lowered = error_text.lower()

    if OLLAMA_MODEL.lower() in lowered and "not found" in lowered:
        return f"I found Ollama, but my {OLLAMA_MODEL} brain is missing. Run: ollama pull {OLLAMA_MODEL}"

    if "connection refused" in lowered or "failed to connect" in lowered or "timed out" in lowered:
        return "Ollama isn't responding yet. Give me a second and try again."

    return f"I'm having trouble reaching my brain right now. Error: {error_text}"


def ask_ollama(prompt: str, history: list, memory: dict, interrupt_event=None) -> str:
    memory = normalize_memory(memory)
    memory_text = "\n".join(f"- {f}" for f in memory["facts"]) or "Nothing stored yet."
    system = SYSTEM_PROMPT.format(
        datetime=datetime.datetime.now().strftime("%A, %B %d %Y %H:%M"),
        memory=memory_text
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": prompt})

    last_error = RuntimeError("Ollama returned an empty response.")

    for attempt in range(OLLAMA_RETRY_COUNT):
        try:
            if not check_ollama_running() and not start_ollama_if_needed():
                last_error = RuntimeError("Ollama is not running.")
                break

            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                stream=True,
                keep_alive=OLLAMA_KEEP_ALIVE,
            )
            chunks = []
            for chunk in response:
                if interrupt_event is not None and interrupt_event.is_set():
                    return INTERRUPTED_RESPONSE
                content_part = extract_ollama_content(chunk)
                if content_part:
                    chunks.append(content_part)

            if interrupt_event is not None and interrupt_event.is_set():
                return INTERRUPTED_RESPONSE

            content = "".join(chunks).strip()
            if content:
                return content

            last_error = RuntimeError("Ollama returned an empty response.")
        except Exception as e:
            last_error = e

        if attempt < OLLAMA_RETRY_COUNT - 1:
            time.sleep(1 + attempt)

    return format_ollama_error(last_error)


def process_response(response: str, memory: dict, speak_fn, interrupt_event=None):
    if interrupt_event is not None and interrupt_event.is_set():
        return

    if "[PC_ACTION]:" in response:
        idx = response.index("[PC_ACTION]:")
        before = response[:idx].strip()
        command_part = response[idx + len("[PC_ACTION]:"):].strip()
        command = command_part.split("\n")[0].strip()

        if before:
            speak_fn(before)

        if interrupt_event is not None and interrupt_event.is_set():
            return

        print(f"\n[Executing: {command}]")
        result = execute_pc_action(command)
        print(f"[Result: {result}]")

        if result and len(result) < 300:
            speak_fn(f"Done. {result}")
        else:
            speak_fn("Done.")
    else:
        speak_fn(response)

    lines = response.lower()
    if "remember" in lines or "don't forget" in lines or "my name is" in lines:
        add_memory_fact(response[:120], memory)


class JarvisGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("Jarvis - AI Assistant")
            self.root.geometry("800x600")
            self.root.configure(bg="#1e1e1e")

            self.memory = load_memory()
            self.history = []
            self.input_queue = queue.Queue()
            self.pending_queue = queue.Queue()
            self.speaking_event = threading.Event()
            self.interrupt_event = threading.Event()
            self.state = {"active": False, "processing": False}
            self.engine = None
            self.recognizer = None
            self.microphone = None
            self.mic_device_index = None
            self.debug_log = []

            self.select_microphone()
            self.setup_ui()
            self.initialize_jarvis()
        except Exception as e:
            print(f"[!] GUI initialization error: {e}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to exit...")
            sys.exit(1)

    def select_microphone(self):
        print("=" * 50)
        print("  JARVIS - Microphone Selection")
        print("=" * 50)
        print("\nAvailable microphones:")
        
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            print("[!] No microphones found. Voice input will be disabled.")
            self.mic_device_index = None
            input("\nPress Enter to continue...")
            return

        for i, mic_name in enumerate(mics):
            print(f"  [{i}] {mic_name}")

        print("\n" + "=" * 50)
        while True:
            try:
                selection = input(f"Select microphone (0-{len(mics)-1}): ").strip()
                if not selection:
                    print("[!] No selection. Voice input will be disabled.")
                    self.mic_device_index = None
                    break
                index = int(selection)
                if 0 <= index < len(mics):
                    self.mic_device_index = index
                    print(f"[Selected] {mics[index]}")
                    break
                else:
                    print(f"[!] Invalid selection. Please enter a number between 0 and {len(mics)-1}.")
            except ValueError:
                print("[!] Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n[!] Cancelled. Voice input will be disabled.")
                self.mic_device_index = None
                break

        print("=" * 50)
        print()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#252526", height=50)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="JARVIS", font=("Arial", 16, "bold"), 
                         bg="#252526", fg="#00ff00")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Status indicator
        self.status_label = tk.Label(header, text="Initializing...", 
                                    font=("Arial", 10), bg="#252526", fg="#888888")
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # Conversation area
        self.chat_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, 
            bg="#1e1e1e", 
            fg="#d4d4d4", 
            font=("Consolas", 11),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Input area
        input_frame = tk.Frame(self.root, bg="#252526", height=80)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.input_entry = tk.Entry(
            input_frame, 
            font=("Arial", 12),
            bg="#3c3c3c", 
            fg="#d4d4d4",
            insertbackground="#00ff00"
        )
        self.input_entry.pack(fill=tk.X, padx=10, pady=10)
        self.input_entry.bind("<Return>", self.on_send)

        send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.on_send,
            bg="#0e639c",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        send_button.pack(side=tk.RIGHT, padx=10, pady=10)

        copy_button = tk.Button(
            input_frame,
            text="📋 Copy Log",
            command=self.copy_log,
            bg="#3c3c3c",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT
        )
        copy_button.pack(side=tk.RIGHT, padx=5, pady=10)

        screenshot_button = tk.Button(
            input_frame,
            text="📷 Screenshot",
            command=self.take_screenshot,
            bg="#3c3c3c",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT
        )
        screenshot_button.pack(side=tk.RIGHT, padx=5, pady=10)

        # Voice control button
        self.voice_button = tk.Button(
            input_frame,
            text="🎤 Voice",
            command=self.toggle_voice,
            bg="#3c3c3c",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT
        )
        self.voice_button.pack(side=tk.RIGHT, padx=5, pady=10)

        self.voice_enabled = True

    def initialize_jarvis(self):
        try:
            self.log("=" * 50)
            self.log("  JARVIS - Initialising...")
            self.log("=" * 50)

            ollama_ready = start_ollama_if_needed()
            if not ollama_ready:
                self.log("[!] Continuing without a live Ollama connection. The first request will retry automatically.")
            else:
                threading.Thread(target=warm_ollama_model, daemon=True).start()

            self.log("[TTS] Loading Kokoro voice engine...")
            _dir = os.path.dirname(os.path.abspath(__file__))
            self.engine = Kokoro(os.path.join(_dir, "kokoro-v1.0.onnx"), os.path.join(_dir, "voices-v1.0.bin"))

            self.recognizer = sr.Recognizer()
            if self.mic_device_index is not None:
                try:
                    self.microphone = sr.Microphone(device_index=self.mic_device_index)
                    self.log(f"[Mic] Using device index {self.mic_device_index}")
                    self.recognizer.dynamic_energy_threshold = True
                    self.recognizer.pause_threshold = 0.6
                    self.recognizer.non_speaking_duration = 0.35
                    self.recognizer.phrase_threshold = 0.25

                    self.log("[Mic] Calibrating...")
                    try:
                        with self.microphone as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=MIC_CALIBRATION_SECONDS)
                        self.log("[Mic] Calibration complete")
                    except Exception as e:
                        self.log(f"[Mic warning] Calibration failed: {e}")
                        self.log("[Mic] Using default settings")
                except Exception as e:
                    self.log(f"[Mic error] Failed to initialize microphone device index {self.mic_device_index}: {e}")
                    self.log("[Mic] Voice input will be disabled")
                    self.microphone = None
                    self.voice_enabled = False
                    self.voice_button.config(bg="#8b0000", text="🔇 No Mic")
            else:
                self.log("[Mic] Voice input disabled (no microphone selected)")
                self.microphone = None
                self.voice_enabled = False
                self.voice_button.config(bg="#8b0000", text="🔇 No Mic")

            self.memory["conversation_count"] = self.memory.get("conversation_count", 0) + 1
            save_memory(self.memory)

            self.log(f"\n[Ready] Say or type '{WAKE_WORD.upper()}' to activate.")
            self.log("[Tip]   You can also just type your message directly and press Enter.")

            self.update_status("Ready")

            speak(self.engine, "Jarvis online. Ready when you are.", self.speaking_event, self.interrupt_event, self.log)

            if self.mic_device_index is not None:
                voice_thread = threading.Thread(target=self.listen_voice, daemon=True)
                voice_thread.start()
            else:
                self.voice_enabled = False
                self.voice_button.config(bg="#8b0000", text="🔇 No Mic")

            worker_thread = threading.Thread(target=self.response_worker, daemon=True)
            worker_thread.start()

            self.root.after(100, self.process_queue)

        except Exception as e:
            self.log(f"[!] Initialization error: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.log("[!] Jarvis failed to start. Check the error above.")
            input("\nPress Enter to exit...")

    def log(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.debug_log.append(message)
        if len(self.debug_log) > 1000:
            self.debug_log = self.debug_log[-1000:]

    def copy_log(self):
        if not HAS_PYPERCLIP:
            self.log("[Clipboard] pyperclip not installed. Install with: pip install pyperclip")
            self.auto_copy_debug_to_file()
            return

        log_text = "\n".join(self.debug_log)
        pyperclip.copy(log_text)
        self.log("[Clipboard] Conversation log copied to clipboard")
        self.auto_copy_debug_to_file()

    def auto_copy_debug_to_file(self):
        debug_file = os.path.join(os.path.dirname(__file__), "debug_log.txt")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.debug_log))

    def take_screenshot(self):
        if not HAS_PIL:
            self.log("[Screenshot] PIL not installed. Install with: pip install pillow")
            return

        try:
            screenshot = ImageGrab.grab()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(os.path.dirname(__file__), f"screenshot_{timestamp}.png")
            screenshot.save(screenshot_path)
            self.log(f"[Screenshot] Saved to {screenshot_path}")
            self.log("[Tip] To analyze screenshots, you'll need a vision-capable model like llava")
        except Exception as e:
            self.log(f"[Screenshot error: {e}")

    def update_status(self, status):
        self.status_label.config(text=status)

    def on_send(self, event=None):
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, tk.END)
            self.log(f"You (typed): {text}")
            self.input_queue.put(("text", text))
        if event:
            return "break"

    def toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        if self.voice_enabled:
            self.voice_button.config(bg="#3c3c3c", text="🎤 Voice")
            self.log("[Voice] Enabled")
        else:
            self.voice_button.config(bg="#8b0000", text="🔇 Muted")
            self.log("[Voice] Disabled")

    def listen_voice(self):
        if self.mic_device_index is None:
            return

        mic_error_count = 0
        while True:
            if not self.voice_enabled or self.speaking_event.is_set():
                time.sleep(0.02)
                continue

            self.update_status("Listening...")
            try:
                mic = sr.Microphone(device_index=self.mic_device_index)
                with mic as source:
                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=LISTEN_TIMEOUT_SECONDS,
                            phrase_time_limit=LISTEN_PHRASE_LIMIT_SECONDS
                        )
                    except sr.WaitTimeoutError:
                        continue

                try:
                    text = self.recognizer.recognize_whisper(audio, model="base", language="english")
                    text = text.strip()
                    if text:
                        self.log(f"[Voice] You said: {text}")
                        if self.speaking_event.is_set() and should_interrupt(text):
                            self.input_queue.put(("interrupt", text))
                            continue
                        if not is_meaningful_voice_text(text):
                            continue
                        self.input_queue.put(("voice", text))
                        mic_error_count = 0
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    mic_error_count += 1
                    if mic_error_count < 3:
                        self.log(f"[Whisper error: {e}")
                    else:
                        self.log("[Whisper] Too many errors, pausing voice input for 10 seconds")
                        time.sleep(10)
                        mic_error_count = 0
                    continue
            except Exception as e:
                mic_error_count += 1
                if mic_error_count < 3:
                    self.log(f"[Mic error: {e}")
                else:
                    self.log("[Mic] Too many errors, pausing voice input for 10 seconds")
                    time.sleep(10)
                    mic_error_count = 0
                time.sleep(1)

            self.update_status("Ready")

    def response_worker(self):
        while True:
            query = self.pending_queue.get()
            if query is None:
                self.state["processing"] = False
                return

            self.state["processing"] = True
            self.interrupt_event.clear()
            self.update_status("Processing...")

            response = handle_direct_query(query, self.memory)
            if response is None:
                response = ask_ollama(query, self.history, self.memory, self.interrupt_event)

            if response == INTERRUPTED_RESPONSE:
                self.state["processing"] = False
                self.update_status("Ready")
                continue

            self.history.append({"role": "user", "content": query})
            self.history.append({"role": "assistant", "content": response})
            process_response(response, self.memory, lambda t: speak(self.engine, t, self.speaking_event, self.interrupt_event, self.log), self.interrupt_event)
            self.state["processing"] = False
            self.update_status("Ready")

    def process_queue(self):
        try:
            source, text = self.input_queue.get(timeout=0.1)
        except queue.Empty:
            self.root.after(100, self.process_queue)
            return

        normalized_text = text.lower()

        if source == "text":
            self.log(f"You (typed): {text}")

        if source == "interrupt":
            self.interrupt_event.set()
            follow_up_query = extract_query_after_wake_word(text)
            if follow_up_query:
                self.state["active"] = True
                self.pending_queue.put(follow_up_query)
            self.root.after(100, self.process_queue)
            return

        if contains_wake_word(text) and not self.state["active"]:
            self.state["active"] = True
            query = extract_query_after_wake_word(text)
            if not query:
                if not self.state["processing"]:
                    speak(self.engine, "Yes?", self.speaking_event, self.interrupt_event, self.log)
                self.root.after(100, self.process_queue)
                return
        elif not self.state["active"]:
            if source == "text":
                self.state["active"] = True
                query = text
            else:
                self.root.after(100, self.process_queue)
                return
        else:
            query = extract_query_after_wake_word(text) if contains_wake_word(text) else text

        normalized_query = query.lower().strip()

        if normalized_query in ("goodbye", "go to sleep", "shut down", "exit"):
            self.interrupt_event.set()
            self.pending_queue.put(None)
            speak(self.engine, "Going offline. Call me when you need me.", self.speaking_event, self.log)
            self.root.after(2000, self.root.destroy)
            return

        if self.state["processing"]:
            if source == "text" or contains_wake_word(text) or should_interrupt(text):
                self.interrupt_event.set()
                if query:
                    self.pending_queue.put(query)
            self.root.after(100, self.process_queue)
            return

        self.pending_queue.put(query)
        self.root.after(100, self.process_queue)


def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Shutdown] Jarvis offline.")
