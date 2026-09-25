"""
Example 2: Run a specialized Coder Subagent with automatic fallback.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.swarm import AgentSwarm

def main():
    swarm = AgentSwarm()
    
    task = (
        "Write a Python function with type hints and docstring that implements "
        "a sliding-window rate limiter using Redis and Lua script."
    )
    
    print("[*] Delegating task to Coder Subagent...")
    res = swarm.dispatch(task=task, role="coder")
    
    print("\n✅ Subagent Completed Task!")
    print(f"Model used: {res['model_used']}")
    print(f"Saved artifact: {res['artifact_file']}")
    print("\nResult preview:")
    print(res["content"][:400] + "...")

if __name__ == "__main__":
    main()
