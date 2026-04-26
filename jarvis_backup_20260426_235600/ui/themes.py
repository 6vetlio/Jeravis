"""Theme management for Jarvis UI."""

import os
import json
from config import THEMES_DIR


def load_themes():
    """Load available themes from themes directory."""
    themes = {
        "dark": {
            "name": "Dark",
            "bg": "#1e1e1e",
            "fg": "#d4d4d4",
            "accent": "#00ff00",
            "button_bg": "#3c3c3c",
            "button_fg": "white",
            "header_bg": "#252526",
            "chat_bg": "#1e1e1e",
            "input_bg": "#3c3c3c",
            "status_bg": "#252526"
        },
        "light": {
            "name": "Light",
            "bg": "#f0f0f0",
            "fg": "#333333",
            "accent": "#0066cc",
            "button_bg": "#e0e0e0",
            "button_fg": "#333333",
            "header_bg": "#e8e8e8",
            "chat_bg": "#ffffff",
            "input_bg": "#ffffff",
            "status_bg": "#e8e8e8"
        },
        "cyberpunk": {
            "name": "Cyberpunk",
            "bg": "#0a0a0f",
            "fg": "#00ffff",
            "accent": "#ff00ff",
            "button_bg": "#1a1a2e",
            "button_fg": "#00ffff",
            "header_bg": "#16162a",
            "chat_bg": "#0a0a0f",
            "input_bg": "#1a1a2e",
            "status_bg": "#16162a"
        }
    }
    
    # Load custom themes from themes directory
    if os.path.exists(THEMES_DIR):
        for filename in os.listdir(THEMES_DIR):
            if filename.endswith('.json'):
                theme_name = filename[:-5]
                try:
                    with open(os.path.join(THEMES_DIR, filename), 'r', encoding='utf-8') as f:
                        custom_theme = json.load(f)
                        themes[theme_name] = custom_theme
                except (OSError, json.JSONDecodeError) as e:
                    print(f"[Theme warning] Failed to load {filename}: {e}")
    
    return themes


def save_theme(theme_name: str, theme_data: dict):
    """Save a custom theme to file."""
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)
    
    theme_path = os.path.join(THEMES_DIR, f"{theme_name}.json")
    try:
        with open(theme_path, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, indent=2)
        return True
    except OSError as e:
        print(f"[Theme error] Failed to save theme: {e}")
        return False


def apply_theme_to_widget(widget, theme, is_ttk=False):
    """Apply theme colors to a widget."""
    if is_ttk:
        # TTK styles would be configured here
        pass
    else:
        try:
            if hasattr(widget, 'config'):
                widget.config(bg=theme.get('bg', '#1e1e1e'))
        except tk.TclError:
            pass  # Some widgets don't support bg config


def get_theme_colors(theme_name: str, themes: dict):
    """Get color scheme for a theme."""
    return themes.get(theme_name, themes.get('dark', {}))
