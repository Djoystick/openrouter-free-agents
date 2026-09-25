#!/usr/bin/env python3
"""
CLI entry point for OpenRouter Free Agents Swarm.
"""

import sys
import argparse
from core.monitor import OpenRouterMonitor
from core.swarm import AgentSwarm
from core.roles import ROLE_PRESETS

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


def print_banner():
    title = "OpenRouter Free Agents"
    desc = "Resilient LLM router with automatic 429 failover"
    if HAS_RICH:
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]\n[dim]{desc}[/dim]", expand=False))
    else:
        print("=" * 55)
        print(f"{title}\n{desc}")
        print("=" * 55)


def cmd_scan(args):
    print("[*] Fetching active free models from OpenRouter...")
    monitor = OpenRouterMonitor()
    try:
        free_models = monitor.get_free_models(min_context=args.min_context)
    except Exception as e:
        print(f"[!] Error fetching models: {e}")
        return

    print(f"\n✅ Discovered {len(free_models)} completely free models:\n")

    if HAS_RICH:
        table = Table(title="OpenRouter Free Models Catalog")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Model ID", style="bold green")
        table.add_column("Context Window", justify="right", style="yellow")
        table.add_column("Architecture", style="dim")

        for idx, m in enumerate(free_models[:args.limit], 1):
            arch = m.get("architecture", {}).get("modality", "text")
            ctx = f"{m['context_length']:,}"
            table.add_row(str(idx), m["id"], ctx, arch)
        console.print(table)
    else:
        for idx, m in enumerate(free_models[:args.limit], 1):
            print(f"{idx:2d}. {m['id']:<45} | Context: {m['context_length']:,}")


def cmd_benchmark(args):
    print("[*] Benchmarking top free models for latency and availability...")
    monitor = OpenRouterMonitor()
    models = monitor.get_free_models()[:args.limit]

    results = []
    for m in models:
        m_id = m["id"]
        print(f"[*] Testing {m_id}...")
        res = monitor.benchmark_model(m_id)
        results.append(res)

    print("\n📊 Benchmark Results:")
    if HAS_RICH:
        table = Table(title="Latency Benchmark")
        table.add_column("Model ID", style="bold")
        table.add_column("Status", style="cyan")
        table.add_column("Latency (s)", justify="right")
        table.add_column("Notes", style="dim")

        for r in results:
            status_style = "green" if r["status"] == "ONLINE" else "red"
            table.add_row(
                r["model_id"],
                f"[{status_style}]{r['status']}[/{status_style}]",
                str(r["latency_sec"]),
                r["error"] or "OK"
            )
        console.print(table)
    else:
        for r in results:
            print(f"- {r['model_id']:<45} | {r['status']} | {r['latency_sec']}s | {r['error'] or 'OK'}")


def cmd_run(args):
    swarm = AgentSwarm()
    print(f"\n[*] Dispatching task to subagent [role: {args.role}]...")
    try:
        res = swarm.dispatch(
            task=args.task,
            role=args.role,
            preferred_model=args.model
        )
        print(f"\n🎉 Task Completed Successfully!")
        print(f"👉 Model: {res['model_used']}")
        print(f"📁 Output Saved: {res['artifact_file']}\n")
        print("--- Output Preview ---")
        print(res['content'][:600] + ("..." if len(res['content']) > 600 else ""))
    except Exception as e:
        print(f"\n[!] Execution failed: {e}")


def cmd_pipeline(args):
    swarm = AgentSwarm()
    roles = args.roles.split(",") if args.roles else ["architect", "coder", "security"]
    print(f"\n[*] Launching Multi-Agent Pipeline: {' -> '.join(roles)}...")
    try:
        results = swarm.pipeline(task=args.task, pipeline_roles=roles)
        print(f"\n🎉 Full Pipeline Completed! ({len(results)} stages)")
        for idx, r in enumerate(results, 1):
            print(f"  Stage {idx} ({r['role']}): {r['model_used']} -> {r['artifact_file']}")
    except Exception as e:
        print(f"\n[!] Pipeline failed: {e}")


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="OpenRouter Free Agents Swarm CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan and list active free models on OpenRouter")
    p_scan.add_argument("--min-context", type=int, default=0, help="Minimum context length")
    p_scan.add_argument("--limit", type=int, default=20, help="Max models to show")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Benchmark top free models for latency")
    p_bench.add_argument("--limit", type=int, default=5, help="Number of models to test")

    # run
    p_run = subparsers.add_parser("run", help="Dispatch a task to a specialized subagent")
    p_run.add_argument("--role", default="coder", choices=list(ROLE_PRESETS.keys()), help="Subagent role")
    p_run.add_argument("--task", required=True, help="Task description or prompt")
    p_run.add_argument("--model", default=None, help="Explicit preferred model")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run a sequential multi-agent pipeline")
    p_pipe.add_argument("--task", required=True, help="Epic task description")
    p_pipe.add_argument("--roles", default="architect,coder,security", help="Comma-separated roles")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
