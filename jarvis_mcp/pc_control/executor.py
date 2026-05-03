"""PC control executor for Jarvis MCP Server."""

import subprocess
import re
from typing import Optional, Callable


class PCControlExecutor:
    """Execute PC commands with safety checks."""
    
    def __init__(self, safety_mode: bool = True, sandbox_mode: bool = False):
        self.safety_mode = safety_mode
        self.sandbox_mode = sandbox_mode
    
    def execute(self, command: str, log_callback: Optional[Callable] = None) -> str:
        """Execute a PowerShell command."""
        if self.sandbox_mode:
            if log_callback:
                log_callback(f"[Sandbox] Simulated: {command}")
            return f"[SANDBOX] Command simulated (not executed): {command}"
        
        if self.safety_mode:
            if self._is_dangerous(command):
                if log_callback:
                    log_callback(f"[Safety] Blocked dangerous command: {command}")
                return "I cannot execute that command for safety reasons."
        
        try:
            command = command.strip()
            command = re.sub(r"(\w)(powershell\.exe)", r"\1 \2", command)
            command = re.sub(r"(Start-Process)(\w)", r"\1 \2", command)
            command = command.strip("`")
            
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout.strip() or result.stderr.strip() or "Command executed."
            
            if log_callback:
                log_callback(f"[PC Action] Executed: {command[:50]}...")
            
            return output
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except Exception as e:
            return f"Error: {e}"
    
    def _is_dangerous(self, command: str) -> bool:
        """Check if command is dangerous."""
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"del\s+/s\s+/q",
            r"format\s+c:",
            r"shutdown\s+/s",
            r"wipefs",
            r"dd\s+if=/dev/zero"
        ]
        lowered = command.lower()
        return any(re.search(pattern, lowered) for pattern in dangerous_patterns)
    
    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot and save it."""
        try:
            from PIL import ImageGrab
            from datetime import datetime
            from pathlib import Path
            
            screenshot_dir = Path.home() / ".jarvis_mcp" / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = screenshot_dir / f"screenshot_{timestamp}.png"
            
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            return str(screenshot_path)
        except Exception as e:
            print(f"[Screenshot] Error: {e}")
            return None
