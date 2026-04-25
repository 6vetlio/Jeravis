"""PC control and action execution for Jarvis."""

import os
import re
import subprocess
import time
from config import SANDBOX_NETWORK_ISOLATION


def parse_pc_actions(text: str):
    """Parse PC actions from response text."""
    pattern = r'\[PC_ACTION\]:(.*?)(?=\[PC_ACTION\]:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches if match.strip()]


def execute_powershell_command(command: str, timeout=30, sandbox_network=False):
    """Execute a PowerShell command safely."""
    try:
        # Build PowerShell arguments
        ps_args = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        
        # If sandbox network isolation is enabled, we would need to run in a restricted environment
        # For now, we just log the restriction
        if sandbox_network and SANDBOX_NETWORK_ISOLATION:
            print(f"[Sandbox] Network isolation would restrict: {command[:50]}...")
        
        result = subprocess.run(
            ["powershell.exe"] + ps_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode != 0 and error:
            return f"Error: {error}"
        return output if output else "Command executed successfully."
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Execution error: {str(e)}"


def execute_pc_action(action_text: str, sandbox_mode=False, file_protection=True, 
                     log_callback=None, vision_verification=False):
    """Execute a PC action with safety checks."""
    if sandbox_mode:
        if log_callback:
            log_callback(f"[Sandbox] Would execute: {action_text}")
        return f"[Sandbox] Action simulated: {action_text}"
    
    # File protection check
    if file_protection:
        dangerous_patterns = [
            r'\brm\s+-rf\b', r'\bformat\s+[a-zA-Z]:', r'\bdel\s+/[fqs]',
            r'\berase\b', r'\bremove-item\s+-recurse\s+-force',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, action_text, re.IGNORECASE):
                if log_callback:
                    log_callback(f"[File Protection] Blocked dangerous action: {action_text}")
                return f"[Blocked] Dangerous file operation detected: {action_text}"
    
    # Execute the command
    result = execute_powershell_command(action_text)
    if log_callback:
        log_callback(f"[PC Action] Executed: {action_text[:50]}...")
    return result


def process_response(response: str, memory: dict, speak_fn, interrupt_event=None,
                    safety_mode=True, file_protection=True, sandbox_mode=False,
                    vision_verification=False, log_callback=None):
    """Process response and execute any PC actions."""
    if interrupt_event is not None and interrupt_event.is_set():
        return
    
    # Check for image generation requests
    if "[IMAGE_GEN]:" in response:
        idx = response.index("[IMAGE_GEN]:")
        prompt = response[idx + len("[IMAGE_GEN]:"):].strip()
        if log_callback:
            log_callback(f"[Image] Generation requested: {prompt}")
        # Image generation would be handled here
        return
    
    # Parse and execute PC actions
    actions = parse_pc_actions(response)
    if actions:
        for action in actions:
            if interrupt_event is not None and interrupt_event.is_set():
                return
            
            result = execute_pc_action(
                action, 
                sandbox_mode=sandbox_mode,
                file_protection=file_protection,
                log_callback=log_callback,
                vision_verification=vision_verification
            )
            
            if log_callback:
                log_callback(f"[PC Action Result] {result[:200]}...")
    
    # Speak the response (without PC action tags)
    clean_response = re.sub(r'\[PC_ACTION\]:.*?($|\[)', '', response, flags=re.DOTALL).strip()
    if clean_response:
        speak_fn(clean_response)


def take_screenshot():
    """Take a screenshot and save it."""
    try:
        from PIL import ImageGrab
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            f"screenshot_{timestamp}.png"
        )
        screenshot = ImageGrab.grab()
        screenshot.save(screenshot_path)
        return screenshot_path
    except Exception as e:
        print(f"[Screenshot] Error: {e}")
        return None


def analyze_image_with_vision(image_path: str, query: str = "Describe this image"):
    """Analyze an image using the vision model."""
    from core.ollama import ask_ollama, VISION_MODEL
    # This would use the vision model to analyze the image
    # Implementation depends on how images are passed to Ollama
    return f"[Vision] Analyzing {image_path} with query: {query}"
