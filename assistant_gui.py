"""Jarvis GUI - Refactored version using modular structure."""

import os
import sys
import json
import queue
import threading
import time
import datetime
import re
import subprocess
import shutil

# GPU configuration
os.environ["OLLAMA_NUM_GPU"] = "1"
os.environ["OLLAMA_GPU_LAYERS"] = "999"

import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
import sounddevice as sd
import speech_recognition as sr
import requests
from kokoro_onnx import Kokoro
from PIL import ImageGrab

# Try importing optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    from diffusers import StableDiffusionPipeline
    HAS_DIFFUSERS = True
except ImportError:
    HAS_DIFFUSERS = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Import from our modules
from config import (
    OLLAMA_MODEL, OLLAMA_SECONDARY_MODEL, OLLAMA_LARGE_MODEL, OLLAMA_CODING_MODEL,
    VISION_MODEL, KOKORO_VOICE, KOKORO_VOICES, MAX_TTS_CHARS, INTERRUPTED_RESPONSE,
    WAKE_WORD, WAKE_WORD_ALIASES, WAKE_WORD_SIMILARITY_THRESHOLD,
    MIC_CALIBRATION_SECONDS, LISTEN_TIMEOUT_SECONDS, LISTEN_PHRASE_LIMIT_SECONDS,
    SAFETY_MODE_DEFAULT, FILE_PROTECTION_DEFAULT, SPEECH_SPEED_DEFAULT,
    THINKING_POWER_DEFAULT, SANDBOX_MODE_DEFAULT, VISION_VERIFICATION_DEFAULT,
    WEBSOCKET_ENABLED, API_ENABLED, DATABASE_ENABLED,
    ACTION_CONFIRMATION_ENABLED, ACTION_LOGGING_ENABLED,
    SANDBOX_NETWORK_ISOLATION, ROLLBACK_ENABLED,
    PLUGINS_DIR, IMAGE_MODEL_ID, SOUNDS_DIR, THEMES_DIR,
    MEMORY_FILE, CONVERSATION_HISTORY_FILE, SCREENSHOTS_JSON_FILE,
    PLUGINS_DIR, IMAGE_MODEL_ID
)

from core.memory import (
    load_memory, save_memory, add_memory_fact,
    load_personality, save_personality_trait,
    load_key_moments, load_autonomous_prompts,
    load_voice_commands, save_conversation_to_history
)

from core.ollama import (
    ask_ollama, ask_external_api, select_model_for_query,
    extract_thinking_content, check_ollama_running, start_ollama,
    unload_all_models, load_api_keys, is_coding_query, is_weather_query
)

from core.skills import handle_direct_query, is_weather_query, is_location_query
from core.pc_control import execute_pc_action, parse_pc_actions, take_screenshot
from ui.themes import load_themes, save_theme, get_theme_colors, apply_theme_to_widget


def get_python_exe() -> str:
    """Find the correct Python executable path."""
    python_exe = shutil.which("python")
    if python_exe:
        return python_exe
    python_exe = shutil.which("py")
    if python_exe:
        return python_exe
    return sys.executable


def load_plugins():
    """Load plugins from plugins directory."""
    plugins = {}
    if os.path.exists(PLUGINS_DIR):
        for filename in os.listdir(PLUGINS_DIR):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_name = filename[:-3]
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        plugin_name, os.path.join(PLUGINS_DIR, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    plugins[plugin_name] = module
                except Exception as e:
                    print(f"[Plugin warning] Failed to load {filename}: {e}")
    return plugins


def get_system_stats():
    """Get system RAM and VRAM stats."""
    if not HAS_PSUTIL:
        return "N/A"
    try:
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024**3)
        ram_total = ram.total / (1024**3)
        return f"RAM: {ram_used:.1f}/{ram_total:.1f}GB"
    except Exception:
        return "N/A"


def difflib_similarity(a: str, b: str) -> float:
    """Calculate string similarity using SequenceMatcher."""
    import difflib
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def is_similar_to_wake_word(text: str) -> bool:
    """Check if text is similar to wake word."""
    text = text.lower().strip()
    if not text:
        return False
    for alias in WAKE_WORD_ALIASES:
        if difflib_similarity(text, alias) >= WAKE_WORD_SIMILARITY_THRESHOLD:
            return True
    return False


def contains_wake_word(text: str) -> bool:
    """Check if text contains wake word or similar."""
    words = text.lower().split()
    return any(is_similar_to_wake_word(word) for word in words)


def should_interrupt(text: str) -> bool:
    """Check if voice input should interrupt current speech."""
    interrupt_keywords = ["stop", "cancel", "interrupt", "wait", "hold on", "pause"]
    lowered = text.lower()
    return any(keyword in lowered for keyword in interrupt_keywords)


def is_meaningful_voice_text(text: str) -> bool:
    """Filter out junk voice transcripts."""
    if not text or len(text) < 2:
        return False
    text = text.strip()
    if len(text) <= 1:
        return False
    meaningless = ["um", "uh", "hm", "mm", "ah", "oh", "er"]
    return text.lower() not in meaningless


def extract_query_after_wake_word(text: str) -> str:
    """Extract the query part after wake word."""
    lowered = text.lower()
    for alias in WAKE_WORD_ALIASES:
        if alias in lowered:
            idx = lowered.find(alias)
            after = text[idx + len(alias):].strip()
            after = re.sub(r'^[,.!?\s]+', '', after)
            return after
    return text


def prepare_tts_text(text: str, max_chars: int = MAX_TTS_CHARS) -> str:
    """Prepare text for TTS by normalizing and capping length."""
    text = text.replace("°C", " degrees Celsius")
    text = text.replace("°F", " degrees Fahrenheit")
    text = re.sub(r'https?://\S+', ' link ', text)
    if len(text) > max_chars:
        text = text[:max_chars-3] + "..."
    return text


def speak(engine, text: str, speaking_event, interrupt_event, log_func, voice, speed):
    """Speak text using Kokoro TTS."""
    if not text:
        return
    if speed is None:
        log_func("[TTS] Skipped (speed is None)")
        return
    if speaking_event.is_set():
        log_func("[TTS] Another speech in progress")
        return
    
    try:
        text = prepare_tts_text(text)
        if not text:
            return
        
        speaking_event.set()
        log_func(f"[TTS] Speaking: {text[:80]}...")
        
        try:
            samples = engine.speak(text, voice=voice)
            audio = samples / max(abs(samples).max(), 1e-6)
            audio = audio * 0.9
            
            if speed != 1.0 and speed is not None:
                import numpy as np
                # Simple speed adjustment by resampling
                indices = np.round(np.arange(0, len(audio), speed)).astype(int)
                indices = indices[indices < len(audio)]
                audio = audio[indices]
            
            sd.play(audio, 24000)
            
            # Wait while checking for interrupts
            while sd.get_stream().active:
                if interrupt_event.is_set():
                    sd.stop()
                    break
                time.sleep(0.1)
            
        except Exception as e:
            log_func(f"[TTS Error] {e}")
        finally:
            speaking_event.clear()
            
    except Exception as e:
        log_func(f"[TTS outer error] {e}")
        speaking_event.clear()


class JarvisGUI:
    """Main Jarvis GUI application."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")
        
        # Load configuration
        self.memory = load_memory()
        self.history = []
        self.input_queue = queue.Queue()
        self.pending_queue = queue.Queue()
        self.speaking_event = threading.Event()
        self.interrupt_event = threading.Event()
        self.state = {"active": False, "processing": False}
        
        # Settings from memory
        self.safety_mode = self.memory.get("safety_mode", SAFETY_MODE_DEFAULT)
        self.file_protection = self.memory.get("file_protection", FILE_PROTECTION_DEFAULT)
        self.speech_speed = self.memory.get("speech_speed", SPEECH_SPEED_DEFAULT)
        self.sandbox_mode = self.memory.get("sandbox_mode", SANDBOX_MODE_DEFAULT)
        self.vision_verification = self.memory.get("vision_verification", VISION_VERIFICATION_DEFAULT)
        self.personality = load_personality()
        self.autonomous_prompts = load_autonomous_prompts()
        self.autonomous_prompt_category = self.memory.get("autonomous_prompt_category", "proactive")
        self.plugins = load_plugins()
        self.voice_commands = load_voice_commands()
        self.themes = load_themes()
        self.current_theme = self.memory.get("current_theme", "dark")
        self.sound_effects_enabled = self.memory.get("sound_effects_enabled", False)
        self.mini_mode = self.memory.get("mini_mode", False)
        self.websocket_enabled = self.memory.get("websocket_enabled", WEBSOCKET_ENABLED)
        self.api_enabled = self.memory.get("api_enabled", API_ENABLED)
        self.database_enabled = self.memory.get("database_enabled", DATABASE_ENABLED)
        self.action_confirmation_enabled = self.memory.get("action_confirmation_enabled", ACTION_CONFIRMATION_ENABLED)
        self.action_logging_enabled = self.memory.get("action_logging_enabled", ACTION_LOGGING_ENABLED)
        self.sandbox_network_isolation = self.memory.get("sandbox_network_isolation", SANDBOX_NETWORK_ISOLATION)
        self.rollback_enabled = self.memory.get("rollback_enabled", ROLLBACK_ENABLED)
        self.thinking_power = self.memory.get("thinking_power", THINKING_POWER_DEFAULT)
        self.current_model = self.memory.get("current_model", OLLAMA_MODEL)
        
        # State
        self.thinking_panel_visible = False
        self.message_id = 0
        self.autonomous_mode = False
        self.autonomous_paused = False
        self.autonomous_error_count = 0
        self.voice_enabled = True
        self.engine = None
        self.recognizer = None
        self.microphone = None
        self.mic_device_index = None
        self.kokoro_voice = KOKORO_VOICE
        
        # Initialize
        self.select_microphone()
        self.setup_ui()
        self.initialize_jarvis()
    
    def select_microphone(self):
        """Select default microphone."""
        mics = sr.Microphone.list_microphone_names()
        if not mics:
            self.mic_device_index = None
            return
        # Default to index 1 (Steinberg UR22mkII) if available
        self.mic_device_index = 1 if len(mics) > 1 else 0
    
    def setup_ui(self):
        """Setup the user interface."""
        # Header
        header = tk.Frame(self.root, bg="#252526", height=50)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="JARVIS", font=("Arial", 16, "bold"),
                bg="#252526", fg="#00ff00").pack(side=tk.LEFT, padx=20, pady=10)
        
        self.status_label = tk.Label(header, text="Initializing...",
                                    font=("Arial", 10), bg="#252526", fg="#888888")
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Chat display
        self.chat_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 11), wrap=tk.WORD, state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg="#252526", height=30)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="",
                                    bg="#252526", fg="#00ff00",
                                    font=("Consolas", 9), anchor="w")
        self.status_label.pack(fill=tk.X, padx=5)
        self.update_status_bar()
        
        # Input area
        input_frame = tk.Frame(self.root, bg="#252526")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.input_entry = tk.Entry(input_frame, font=("Arial", 12),
                                   bg="#3c3c3c", fg="#d4d4d4", insertbackground="#00ff00")
        self.input_entry.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.input_entry.bind("<Return>", self.on_send)
        
        # Buttons
        button_frame = tk.Frame(input_frame, bg="#252526")
        button_frame.pack(fill=tk.X, padx=10)
        
        tk.Button(button_frame, text="Send", command=self.on_send,
                 bg="#0e639c", fg="white", font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=3)
        
        tk.Button(button_frame, text="📷 Shot", command=self.take_screenshot,
                 bg="#3c3c3c", fg="white").pack(side=tk.RIGHT, padx=3)
        
        tk.Button(button_frame, text="🎤 Voice", command=self.toggle_voice,
                 bg="#3c3c3c", fg="white").pack(side=tk.RIGHT, padx=3)
        
        # Additional buttons would go here...
        self.create_button_bar(button_frame)
    
    def create_button_bar(self, parent):
        """Create the full button bar."""
        buttons = [
            ("Think", self.toggle_thinking_panel),
            ("Safety", self.toggle_safety),
            ("Sandbox", self.toggle_sandbox_mode),
            ("Auto", self.toggle_autonomous_mode),
            ("Model", self.show_model_switcher),
        ]
        
        for text, command in buttons:
            tk.Button(parent, text=text, command=command,
                     bg="#3c3c3c", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
    
    def initialize_jarvis(self):
        """Initialize Jarvis engine and start threads."""
        # Initialize Kokoro TTS
        try:
            self.engine = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
        except Exception as e:
            print(f"[TTS init error] {e}")
            self.engine = None
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.6
        self.recognizer.non_speaking_duration = 0.35
        self.recognizer.phrase_threshold = 0.25
        
        # Start Ollama if not running
        if not check_ollama_running():
            start_ollama()
        
        # Start worker threads
        threading.Thread(target=self.listen_voice, daemon=True).start()
        threading.Thread(target=self.response_worker, daemon=True).start()
        self.process_queue()
        
        self.log("[Jarvis] Initialized and ready")
        self.update_status("Ready")
    
    def log(self, message):
        """Log a message to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def update_status(self, text):
        """Update status label."""
        self.status_label.config(text=text)
    
    def update_status_bar(self):
        """Update status bar with current settings."""
        status = [
            f"🛡️ Safety: {'ON' if self.safety_mode else 'OFF'}",
            f"🔒 Sandbox: {'ON' if self.sandbox_mode else 'OFF'}",
            f"🤖 Auto: {'ON' if self.autonomous_mode else 'OFF'}",
            f"💾 {get_system_stats()}"
        ]
        self.status_label.config(text=" | ".join(status))
    
    def on_send(self, event=None):
        """Handle send button or Enter key."""
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, tk.END)
            self.log(f"You (typed): {text}")
            self.input_queue.put(("text", text))
        return "break"
    
    def toggle_voice(self):
        """Toggle voice input."""
        self.voice_enabled = not self.voice_enabled
        self.log(f"[Voice] {'Enabled' if self.voice_enabled else 'Disabled'}")
    
    def toggle_safety(self):
        """Toggle safety mode."""
        self.safety_mode = not self.safety_mode
        self.memory["safety_mode"] = self.safety_mode
        save_memory(self.memory)
        self.log(f"[Safety] {'ON' if self.safety_mode else 'OFF'}")
    
    def toggle_sandbox_mode(self):
        """Toggle sandbox mode."""
        self.sandbox_mode = not self.sandbox_mode
        self.memory["sandbox_mode"] = self.sandbox_mode
        save_memory(self.memory)
        self.log(f"[Sandbox] {'ON' if self.sandbox_mode else 'OFF'}")
    
    def toggle_thinking_panel(self):
        """Toggle thinking panel visibility."""
        self.thinking_panel_visible = not self.thinking_panel_visible
        if self.thinking_panel_visible:
            self.show_thinking_window()
    
    def show_thinking_window(self):
        """Show the thinking process window."""
        if not hasattr(self, 'thinking_window') or not self.thinking_window.winfo_exists():
            self.thinking_window = tk.Toplevel(self.root)
            self.thinking_window.title("Thinking Process")
            self.thinking_window.geometry("600x400")
            self.thinking_window.configure(bg="#1e1e1e")
            
            self.thinking_text = scrolledtext.ScrolledText(
                self.thinking_window, bg="#1e1e1e", fg="#d4d4d4",
                font=("Consolas", 10), wrap=tk.WORD
            )
            self.thinking_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def append_thinking(self, text, pace=True):
        """Append text to thinking panel."""
        if hasattr(self, 'thinking_text'):
            self.thinking_text.insert(tk.END, text)
            self.thinking_text.see(tk.END)
    
    def toggle_autonomous_mode(self):
        """Toggle autonomous thinking mode."""
        self.autonomous_mode = not self.autonomous_mode
        if self.autonomous_mode:
            self.log("[Autonomous] Mode enabled")
            self.autonomous_error_count = 0
            threading.Thread(target=self.autonomous_thinking_loop, daemon=True).start()
        else:
            self.log("[Autonomous] Mode disabled")
        self.update_status_bar()
    
    def autonomous_thinking_loop(self):
        """Autonomous thinking loop."""
        while self.autonomous_mode:
            if self.autonomous_paused:
                time.sleep(1)
                continue
            
            if not self.state["processing"]:
                self.message_id += 1
                self.append_thinking(f"\n--- [Msg #{self.message_id}] Autonomous thinking ---\n")
                
                prompt = self.autonomous_prompts.get(self.autonomous_prompt_category, 
                                                   "Think about what you could do to help the user.")
                try:
                    response = ask_ollama(prompt, [], self.memory, None, 
                                        self.safety_mode, self.personality)
                    if response and response != "I can't reach my brain (Ollama)":
                        self.append_thinking(f"Thought: {response}\n")
                        self.log(f"[Autonomous] {response}")
                        self.autonomous_error_count = 0
                except Exception as e:
                    self.log(f"[Autonomous] Error: {e}")
                    self.autonomous_error_count += 1
                    if self.autonomous_error_count >= 3:
                        self.autonomous_paused = True
                        self.log("[Autonomous] Paused due to 3 consecutive errors")
            
            time.sleep(30)
    
    def show_model_switcher(self):
        """Show model switcher dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Model Switcher")
        dialog.geometry("400x300")
        dialog.configure(bg="#1e1e1e")
        
        models = [OLLAMA_MODEL, OLLAMA_SECONDARY_MODEL, OLLAMA_LARGE_MODEL, 
                 OLLAMA_CODING_MODEL, VISION_MODEL]
        model_var = tk.StringVar(value=self.current_model)
        
        for model in models:
            tk.Radiobutton(dialog, text=model, variable=model_var, value=model,
                          bg="#1e1e1e", fg="#d4d4d4", selectcolor="#3c3c3c").pack(anchor="w", padx=10, pady=2)
        
        def set_model():
            self.current_model = model_var.get()
            self.memory["current_model"] = self.current_model
            save_memory(self.memory)
            self.log(f"[Model] Switched to: {self.current_model}")
            dialog.destroy()
        
        tk.Button(dialog, text="Set Model", command=set_model,
                 bg="#3c3c3c", fg="white").pack(pady=10)
    
    def take_screenshot(self):
        """Take a screenshot."""
        path = take_screenshot()
        if path:
            self.log(f"[Screenshot] Saved: {path}")
        else:
            self.log("[Screenshot] Failed")
    
    def listen_voice(self):
        """Listen for voice input."""
        if self.mic_device_index is None:
            return
        
        while True:
            if not self.voice_enabled or self.speaking_event.is_set():
                time.sleep(0.02)
                continue
            
            self.update_status("Listening...")
            try:
                with sr.Microphone(device_index=self.mic_device_index) as source:
                    try:
                        audio = self.recognizer.listen(
                            source, timeout=LISTEN_TIMEOUT_SECONDS,
                            phrase_time_limit=LISTEN_PHRASE_LIMIT_SECONDS
                        )
                    except sr.WaitTimeoutError:
                        continue
                
                text = self.recognizer.recognize_whisper(audio, model="small", language="english")
                text = text.strip()
                
                if text and is_meaningful_voice_text(text):
                    self.log(f"[Voice] You said: {text}")
                    if self.speaking_event.is_set() and should_interrupt(text):
                        self.input_queue.put(("interrupt", text))
                    else:
                        self.input_queue.put(("voice", text))
                        
            except sr.UnknownValueError:
                continue
            except Exception as e:
                self.log(f"[Voice error] {e}")
            
            self.update_status("Ready")
    
    def response_worker(self):
        """Process responses from the pending queue."""
        while True:
            query = self.pending_queue.get()
            if query is None:
                self.state["processing"] = False
                return
            
            self.state["processing"] = True
            self.interrupt_event.clear()
            self.update_status("Processing...")
            
            # Try direct skills first
            response = handle_direct_query(query, self.memory)
            
            if response is None:
                # Route to LLM
                self.message_id += 1
                
                # Clear thinking box
                if hasattr(self, 'thinking_text'):
                    self.thinking_text.after(0, lambda: (
                        self.thinking_text.delete(1.0, tk.END),
                        self.thinking_text.insert(tk.END, f"--- [Msg #{self.message_id}] Processing ---\n\n")
                    ))
                
                # Chunk callback for streaming
                def update_thinking(chunk):
                    if hasattr(self, 'thinking_text'):
                        self.thinking_text.after(0, lambda c=chunk: (
                            self.thinking_text.insert("end", c),
                            self.thinking_text.see("end")
                        ))
                
                # Get API provider
                try:
                    api_keys = load_api_keys()
                    provider = api_keys.get("default_provider", "ollama")
                except:
                    provider = "ollama"
                
                # Select model
                selected_model = select_model_for_query(query)
                
                try:
                    if provider == "ollama":
                        self.log(f"[Model] Using {selected_model}")
                        response = ask_ollama(query, self.history, self.memory,
                                            self.interrupt_event, self.safety_mode,
                                            self.personality, chunk_callback=update_thinking,
                                            custom_model=selected_model)
                    else:
                        response = ask_external_api(query, self.history, self.memory,
                                                   self.interrupt_event, self.safety_mode,
                                                   self.personality)
                except Exception as e:
                    self.log(f"[Model Error] {e}")
                    response = "Sorry, I encountered an error processing your request."
                
                # Extract thinking content
                thinking_content, response = extract_thinking_content(response)
            
            self.state["processing"] = False
            self.update_status("Ready")
            
            if response == INTERRUPTED_RESPONSE:
                continue
            
            # Update history
            self.history.append({"role": "user", "content": query})
            self.history.append({"role": "assistant", "content": response})
            
            # Log response
            self.log(f"Jarvis: {response}")
            
            # Speak response
            speak(self.engine, response, self.speaking_event, self.interrupt_event,
                 self.log, self.kokoro_voice, self.speech_speed)
    
    def process_queue(self):
        """Process input queue."""
        try:
            source, text = self.input_queue.get(timeout=0.1)
        except queue.Empty:
            self.root.after(100, self.process_queue)
            return
        
        # Handle interrupt
        if source == "interrupt":
            self.interrupt_event.set()
            follow_up = extract_query_after_wake_word(text)
            if follow_up:
                self.state["active"] = True
        
        # Check for wake word
        if contains_wake_word(text) and not self.state["active"]:
            self.state["active"] = True
            query = extract_query_after_wake_word(text)
            if not query:
                speak(self.engine, "Yes?", self.speaking_event, self.interrupt_event,
                     self.log, self.kokoro_voice, self.speech_speed)
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
        
        # Handle exit commands
        if query.lower().strip() in ("goodbye", "go to sleep", "shut down", "exit"):
            self.interrupt_event.set()
            self.pending_queue.put(None)
            speak(self.engine, "Going offline. Call me when you need me.",
                 self.speaking_event, self.interrupt_event, self.log, self.kokoro_voice, self.speech_speed)
            self.root.after(2000, self.root.destroy)
            return
        
        # Handle processing state
        if self.state["processing"]:
            if source == "text" or contains_wake_word(text) or should_interrupt(text):
                self.interrupt_event.set()
                if query:
                    self.pending_queue.put(query)
            self.root.after(100, self.process_queue)
            return
        
        self.pending_queue.put(query)
        self.root.after(100, self.process_queue)
    
    def on_closing(self):
        """Handle window close."""
        self.log("[Shutdown] Unloading models...")
        unload_all_models()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Shutdown] Jarvis offline.")
