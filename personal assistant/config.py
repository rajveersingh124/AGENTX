"""
Configuration module for AGENTX.
Manages environment variables, LLM provider settings, and credentials safely.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Base directory for the AGENTX application
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables from .env
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Default LLM configurations (Groq API endpoints and popular models)
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DB_PATH = BASE_DIR / "agentx.db"

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

def get_api_key() -> str:
    """Retrieve API key from env or empty string."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    key = os.getenv("LLM_API_KEY", "").strip()
    # Check if placeholder
    if key.lower().startswith("your_") or key == "":
        return ""
    return key

def get_base_url() -> str:
    """Retrieve base URL for OpenAI-compatible client."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL

def get_model() -> str:
    """Retrieve selected LLM model."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

def is_demo_mode() -> bool:
    """Returns True if no valid API key is configured."""
    key = get_api_key()
    return len(key) < 8

def mask_api_key(key: str) -> str:
    """Safely mask an API key for display purposes."""
    if not key or len(key) < 8:
        return "Not Configured (Demo Mode)"
    return f"{key[:4]}...{key[-4:]}"

def save_config(api_key: str, base_url: str = DEFAULT_BASE_URL, model: str = DEFAULT_MODEL) -> bool:
    """Save configuration to .env file safely."""
    try:
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        
        set_key(str(ENV_PATH), "LLM_API_KEY", api_key.strip())
        set_key(str(ENV_PATH), "LLM_BASE_URL", base_url.strip())
        set_key(str(ENV_PATH), "LLM_MODEL", model.strip())
        
        # Reload environment
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def test_api_connection(api_key: str, base_url: str, model: str) -> tuple[bool, str]:
    """Test the LLM API connection with a lightweight prompt."""
    if not api_key or len(api_key) < 8:
        return False, "API key is empty or too short."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=12.0)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Respond with the single word 'CONNECTED'."}],
            max_tokens=10,
            temperature=0.1
        )
        msg = response.choices[0].message.content.strip()
        return True, f"Successfully connected to {model}! Response: {msg}"
    except Exception as err:
        return False, f"Connection failed: {str(err)}"

