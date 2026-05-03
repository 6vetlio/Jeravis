"""Jarvis MCP Server - Extract Jarvis functionality for Windsurf/Cursor."""

from .config import load_config, save_config
from .server import JarvisMCPServer

__version__ = "0.1.0"
__all__ = ["load_config", "save_config", "JarvisMCPServer"]
