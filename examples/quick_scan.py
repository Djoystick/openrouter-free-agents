"""
Example 1: Quick Scan & Filter OpenRouter Free Models.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.monitor import OpenRouterMonitor

def main():
    monitor = OpenRouterMonitor()
    print("[*] Querying OpenRouter live catalog for :free models...")
    
    free_models = monitor.get_free_models(min_context=16000)
    print(f"[+] Found {len(free_models)} models with >= 16k context window:\n")
    
    for idx, m in enumerate(free_models[:10], 1):
        name = m["name"]
        m_id = m["id"]
        ctx = m["context_length"]
        print(f"{idx:2d}. {name} ({m_id})")
        print(f"    Context Length: {ctx:,} tokens")

if __name__ == "__main__":
    main()
