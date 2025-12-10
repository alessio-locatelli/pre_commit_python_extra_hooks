#!/usr/bin/env python3
"""Benchmark script to measure pre-commit hook performance.

Usage:
    python benchmark.py [--iterations=5] [--clear-cache]

This script measures:
- First run performance (cold cache)
- Incremental run performance (warm cache)
- Per-hook breakdown
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

HOOKS = [
    "forbid-vars",
    "validate-function-name",
    "check-redundant-super-init",
    "fix-misplaced-comments",
    "fix-excessive-blank-lines",
]

CACHE_DIR = Path(".cache/pre_commit_hooks")


def clear_cache() -> None:
    """Clear the cache directory."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        print(f"✓ Cleared cache: {CACHE_DIR}")


def get_test_files() -> list[str]:
    """Get all Python test files."""
    test_files = list(Path("tests").rglob("*.py"))
    src_files = list(Path("src").rglob("*.py"))
    return [str(f) for f in test_files + src_files]


def run_hook(hook_name: str, files: list[str]) -> dict[str, Any]:
    """Run a single hook and measure time.

    Returns:
        Dict with timing and result info
    """
    start = time.perf_counter()
    result = subprocess.run(
        ["python", "-m", f"pre_commit_hooks.{hook_name.replace('-', '_')}", *files],
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start

    return {
        "hook": hook_name,
        "elapsed_ms": elapsed * 1000,
        "return_code": result.returncode,
        "files_checked": len(files),
    }


def benchmark_iteration(files: list[str], label: str) -> dict[str, Any]:
    """Run all hooks once and collect timing data."""
    print(f"\n{'=' * 60}")
    print(f"{label}")
    print(f"{'=' * 60}")

    results = []
    total_start = time.perf_counter()

    for hook in HOOKS:
        result = run_hook(hook, files)
        results.append(result)
        print(
            f"  {hook:30s} {result['elapsed_ms']:8.2f} ms "
            f"({result['files_checked']} files)"
        )

    total_elapsed = time.perf_counter() - total_start

    print(f"{'-' * 60}")
    print(f"  {'Total':30s} {total_elapsed * 1000:8.2f} ms")

    return {
        "label": label,
        "total_ms": total_elapsed * 1000,
        "hooks": results,
    }


def main() -> None:
    """Run benchmark suite."""
    parser = argparse.ArgumentParser(description="Benchmark pre-commit hooks")
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations for each run type (default: 3)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache before starting",
    )
    args = parser.parse_args()

    print("Pre-commit Hooks Performance Benchmark")
    print("=" * 60)

    # Get test files
    files = get_test_files()
    print(f"\nTest files: {len(files)} Python files")

    # Clear cache if requested
    if args.clear_cache:
        clear_cache()

    all_results: list[dict[str, Any]] = []

    # Run cold cache benchmarks
    print("\n\n📊 COLD CACHE (First Run) Benchmarks")
    print("=" * 60)
    cold_results = []
    for i in range(args.iterations):
        clear_cache()
        result = benchmark_iteration(files, f"Cold run {i + 1}/{args.iterations}")
        cold_results.append(result)
        all_results.append(result)

    # Run warm cache benchmarks
    print("\n\n📊 WARM CACHE (Incremental Run) Benchmarks")
    print("=" * 60)
    warm_results = []
    for i in range(args.iterations):
        result = benchmark_iteration(files, f"Warm run {i + 1}/{args.iterations}")
        warm_results.append(result)
        all_results.append(result)

    # Calculate averages
    print("\n\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)

    cold_avg = sum(r["total_ms"] for r in cold_results) / len(cold_results)
    warm_avg = sum(r["total_ms"] for r in warm_results) / len(warm_results)

    print(f"\nCold cache (first run):      {cold_avg:8.2f} ms")
    print(f"Warm cache (incremental):    {warm_avg:8.2f} ms")
    print(f"Cache speedup:               {(1 - warm_avg / cold_avg) * 100:7.1f}%")

    # Per-hook averages
    print("\n" + "-" * 60)
    print("Per-hook averages (cold cache):")
    print("-" * 60)

    for hook in HOOKS:
        hook_times = [
            next(h["elapsed_ms"] for h in r["hooks"] if h["hook"] == hook)
            for r in cold_results
        ]
        avg_time = sum(hook_times) / len(hook_times)
        print(f"  {hook:30s} {avg_time:8.2f} ms")

    print("\n" + "-" * 60)
    print("Per-hook averages (warm cache):")
    print("-" * 60)

    for hook in HOOKS:
        hook_times = [
            next(h["elapsed_ms"] for h in r["hooks"] if h["hook"] == hook)
            for r in warm_results
        ]
        avg_time = sum(hook_times) / len(hook_times)
        cold_time = sum(
            next(h["elapsed_ms"] for h in r["hooks"] if h["hook"] == hook)
            for r in cold_results
        ) / len(cold_results)
        speedup = (1 - avg_time / cold_time) * 100 if cold_time > 0 else 0
        print(f"  {hook:30s} {avg_time:8.2f} ms ({speedup:+6.1f}%)")


if __name__ == "__main__":
    main()
