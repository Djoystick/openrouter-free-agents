"""
Configuration loader for OpenRouter Free Agents Swarm.
Reads settings from .env file or environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
APP_NAME = os.getenv("APP_NAME", "OpenRouter Free Agents Swarm")
APP_REFERER = os.getenv("APP_REFERER", "https://github.com/openrouter-free-agents")
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "90"))

# Proxy configuration
HTTP_PROXY = os.getenv("HTTP_PROXY", "").strip()
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "").strip()

PROXIES = {}
if HTTP_PROXY:
    PROXIES["http"] = HTTP_PROXY
if HTTPS_PROXY:
    PROXIES["https"] = HTTPS_PROXY

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def get_headers(api_key: str = None) -> dict:
    """Return authorization and client identification headers for OpenRouter API."""
    key = api_key or OPENROUTER_API_KEY
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": APP_REFERER,
        "X-Title": APP_NAME,
        "User-Agent": "OpenRouter-Free-Agents-Swarm/1.0"
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers
