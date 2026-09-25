"""
Multi-Agent Swarm Orchestrator with resilient fallback chain.
Dispatches tasks to role-specialized subagents using OpenRouter free models.
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import OPENROUTER_BASE_URL, get_headers, PROXIES, DEFAULT_TIMEOUT
from .roles import ROLE_PRESETS
from .monitor import OpenRouterMonitor


class AgentSwarm:
    """Orchestrates autonomous subagents powered by zero-cost OpenRouter models."""

    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[str] = None):
        self.api_key = api_key
        self.headers = get_headers(api_key)
        self.monitor = OpenRouterMonitor(api_key)
        self.output_dir = Path(output_dir or (Path(__file__).resolve().parent.parent / "outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def dispatch(
        self,
        task: str,
        role: str = "general",
        preferred_model: Optional[str] = None,
        context_data: Optional[str] = None,
        max_retries_per_model: int = 2
    ) -> Dict[str, Any]:
        """
        Dispatch a task to a specialized subagent with automatic fallback.
        If a model is rate-limited (429) or fails, the orchestrator automatically
        routes the prompt to the next available free model.
        """
        role_config = ROLE_PRESETS.get(role, ROLE_PRESETS["general"])
        system_prompt = role_config["system_prompt"]
        temperature = role_config.get("temperature", 0.2)

        # Build fallback model chain
        candidate_models: List[str] = []
        if preferred_model:
            candidate_models.append(preferred_model)
        for m in role_config.get("preferred_models", []):
            if m not in candidate_models:
                candidate_models.append(m)

        # Append top free models discovered by the monitor as deep safety net
        try:
            live_free = self.monitor.get_free_models(min_context=8000)
            for m in live_free:
                m_id = m["id"]
                if m_id not in candidate_models:
                    candidate_models.append(m_id)
        except Exception:
            pass

        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        if context_data:
            messages.append({
                "role": "user",
                "content": f"### Context and Project Background:\n{context_data}"
            })
        messages.append({"role": "user", "content": task})

        execution_log = []
        final_content = None
        successful_model = None

        url = f"{OPENROUTER_BASE_URL}/chat/completions"

        for model_id in candidate_models:
            print(f"[*] Trying model: {model_id} (Role: {role})...")
            model_success = False

            for attempt in range(1, max_retries_per_model + 1):
                payload = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 4096
                }

                t0 = time.time()
                try:
                    res = requests.post(
                        url,
                        headers=self.headers,
                        json=payload,
                        proxies=PROXIES if PROXIES else None,
                        timeout=DEFAULT_TIMEOUT
                    )
                    latency = round(time.time() - t0, 2)

                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            final_content = choices[0]["message"].get("content", "")
                            successful_model = model_id
                            execution_log.append({
                                "model": model_id,
                                "status": "SUCCESS",
                                "latency_sec": latency,
                                "attempt": attempt
                            })
                            model_success = True
                            break
                        else:
                            execution_log.append({
                                "model": model_id,
                                "status": "EMPTY_CHOICES",
                                "details": str(data),
                                "latency_sec": latency
                            })
                    elif res.status_code == 429:
                        print(f"    [!] Rate-limit (429) on {model_id}. Switching...")
                        execution_log.append({
                            "model": model_id,
                            "status": "RATE_LIMITED_429",
                            "latency_sec": latency
                        })
                        break  # Don't retry same model on 429, jump to next candidate
                    else:
                        execution_log.append({
                            "model": model_id,
                            "status": f"HTTP_{res.status_code}",
                            "error": res.text[:200],
                            "latency_sec": latency
                        })
                        time.sleep(2)
                except Exception as err:
                    execution_log.append({
                        "model": model_id,
                        "status": "EXCEPTION",
                        "error": str(err),
                        "latency_sec": round(time.time() - t0, 2)
                    })
                    time.sleep(2)

            if model_success:
                break

        if not final_content:
            raise RuntimeError(
                f"Swarm failed to obtain result after attempting {len(candidate_models)} models. "
                f"Log: {execution_log}"
            )

        # Save artifact to output directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_role = role.replace("/", "_")
        filename = f"{timestamp}_{safe_role}.md"
        artifact_path = self.output_dir / filename

        artifact_header = (
            f"# Subagent Artifact: {role_config['title']}\n"
            f"> **Model Used:** `{successful_model}` | **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"---\n\n"
        )
        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(artifact_header + final_content)

        return {
            "ok": True,
            "role": role,
            "model_used": successful_model,
            "artifact_file": str(artifact_path),
            "content": final_content,
            "execution_log": execution_log
        }

    def pipeline(self, task: str, pipeline_roles: List[str] = None) -> List[Dict[str, Any]]:
        """
        Execute a sequential multi-agent pipeline where each subagent
        builds upon the output of the previous agent.
        Default pipeline: Architect -> Coder -> Security Reviewer.
        """
        if not pipeline_roles:
            pipeline_roles = ["architect", "coder", "security"]

        results = []
        accumulated_context = f"Initial Task:\n{task}\n\n"

        for role in pipeline_roles:
            print(f"\n==========================================")
            print(f"🚀 Running Pipeline Stage: {role.upper()}")
            print(f"==========================================")
            step_res = self.dispatch(
                task=task,
                role=role,
                context_data=accumulated_context
            )
            results.append(step_res)
            accumulated_context += (
                f"\n### Output from {role.upper()} ({step_res['model_used']}):\n"
                f"{step_res['content']}\n\n"
            )

        return results
