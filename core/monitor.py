"""
OpenRouter Free Models Monitor.
Fetches, filters, ranks, and benchmarks all available zero-cost (:free) models.
"""

import time
import requests
from typing import List, Dict, Any, Optional
from config import OPENROUTER_BASE_URL, get_headers, PROXIES, DEFAULT_TIMEOUT


class OpenRouterMonitor:
    """Monitors live free models catalog on OpenRouter."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = get_headers(api_key)
        self.cached_models: List[Dict[str, Any]] = []
        self.last_fetch_time: float = 0.0

    def fetch_all_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch the full models list from OpenRouter API."""
        now = time.time()
        # Cache results for 5 minutes unless force_refresh is True
        if self.cached_models and not force_refresh and (now - self.last_fetch_time < 300):
            return self.cached_models

        url = f"{OPENROUTER_BASE_URL}/models"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                proxies=PROXIES if PROXIES else None,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            self.cached_models = data.get("data", [])
            self.last_fetch_time = now
            return self.cached_models
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch models from OpenRouter: {e}")

    def get_free_models(self, min_context: int = 0) -> List[Dict[str, Any]]:
        """
        Filter models to only include completely free tiers:
        - Model ID ends with ':free' OR
        - Both pricing.prompt and pricing.completion equal 0
        """
        all_models = self.fetch_all_models()
        free_models = []

        for m in all_models:
            model_id = m.get("id", "")
            pricing = m.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 1.0) or 0)
            completion_price = float(pricing.get("completion", 1.0) or 0)
            context_len = m.get("context_length", 0) or 0

            is_free = (
                model_id.endswith(":free") or
                (prompt_price == 0.0 and completion_price == 0.0)
            )

            if is_free and context_len >= min_context:
                free_models.append({
                    "id": model_id,
                    "name": m.get("name", model_id),
                    "context_length": context_len,
                    "description": m.get("description", ""),
                    "architecture": m.get("architecture", {}),
                    "top_provider": m.get("top_provider", {}),
                    "per_request_limits": m.get("per_request_limits", {})
                })

        # Sort by context length descending (largest context first)
        free_models.sort(key=lambda x: x["context_length"], reverse=True)
        return free_models

    def benchmark_model(self, model_id: str, test_prompt: str = "Reply with 'OK'") -> Dict[str, Any]:
        """Send a lightweight probe request to measure latency and verify availability."""
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": test_prompt}],
            "max_tokens": 10
        }

        t0 = time.time()
        try:
            res = requests.post(
                url,
                headers=self.headers,
                json=payload,
                proxies=PROXIES if PROXIES else None,
                timeout=15
            )
            latency = time.time() - t0

            if res.status_code == 200:
                return {
                    "model_id": model_id,
                    "status": "ONLINE",
                    "latency_sec": round(latency, 2),
                    "error": None
                }
            elif res.status_code == 429:
                return {
                    "model_id": model_id,
                    "status": "RATE_LIMITED",
                    "latency_sec": round(latency, 2),
                    "error": "Rate limit exceeded (429)"
                }
            else:
                return {
                    "model_id": model_id,
                    "status": "ERROR",
                    "latency_sec": round(latency, 2),
                    "error": f"HTTP {res.status_code}: {res.text[:100]}"
                }
        except Exception as e:
            return {
                "model_id": model_id,
                "status": "OFFLINE",
                "latency_sec": round(time.time() - t0, 2),
                "error": str(e)
            }
