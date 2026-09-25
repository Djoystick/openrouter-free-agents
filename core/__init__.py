"""
Core package for OpenRouter Free Agents Swarm.
"""

from .monitor import OpenRouterMonitor
from .swarm import AgentSwarm
from .roles import ROLE_PRESETS

__all__ = ["OpenRouterMonitor", "AgentSwarm", "ROLE_PRESETS"]
