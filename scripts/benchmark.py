#!/usr/bin/env python3
"""
Orthos-iDart Performance Benchmark Script
==========================================
Measures performance of key Orthos components and reports results.

Usage:
    python scripts/benchmark.py [--iterations N] [--output {text,json}]
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def measure(func: Callable, iterations: int = 100, warmup: int = 5) -> dict[str, float]:
    """Measure execution time of a callable over multiple iterations."""
    for _ in range(warmup):
        try:
            func()
        except Exception:
            pass

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            func()
        except Exception:
            pass
        times.append((time.perf_counter() - t0) * 1000)

    return {
        'min_ms': min(times),
        'max_ms': max(times),
        'avg_ms': statistics.mean(times),
        'median_ms': statistics.median(times),
        'stdev_ms': statistics.stdev(times) if len(times) > 1 else 0.0,
        'throughput_ops_per_sec': iterations / (statistics.mean(times) / 1000),
        'iterations': iterations,
    }


def bench_vm(iterations: int) -> dict[str, Any]:
    """Benchmark VM initialization and basic execution."""
    from orthos.vm.core import OrthosVM
    import struct

    # Pre-build a tiny HALT bytecode
    bytecode = struct.pack('>4B', 0x00, 0, 0, 0)

    def _run():
        vm = OrthosVM(bytecode=bytecode)
        vm.execute()

    return measure(_run, iterations)


def bench_faulhaber(iterations: int) -> dict[str, Any]:
    """Benchmark Faulhaber O(1) polynomial summation."""
    from orthos.annihilator.faulhaber import FaulhaberEngine
    engine = FaulhaberEngine()

    def _run():
        engine.compute_sum(power=3, n=10000)

    return measure(_run, iterations)


def bench_storage(iterations: int) -> dict[str, Any]:
    """Benchmark TPX storage store/retrieve cycle."""
    from orthos.storage.tpx.fallback_pure_python import TPXStoragePurePython
    storage = TPXStoragePurePython()

    counter = [0]

    def _run():
        k = f'bench_key_{counter[0]}'
        counter[0] += 1
        storage.store(k, b'benchmark_payload_' + str(counter[0]).encode())
        storage.retrieve(k)

    return measure(_run, iterations)


def bench_lexer(iterations: int) -> dict[str, Any]:
    """Benchmark Orthos lexer on a representative snippet."""
    from orthos.compiler.lexer import OrthosLexer

    source = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

for i in range(10):
    result = fibonacci(i)
"""

    def _run():
        lexer = OrthosLexer(source)
        lexer.tokenize()

    return measure(_run, iterations)


def format_result(name: str, result: dict[str, Any]) -> str:
    return (
        f"  {name:<35} "
        f"avg={result['avg_ms']:8.3f}ms  "
        f"min={result['min_ms']:8.3f}ms  "
        f"max={result['max_ms']:8.3f}ms  "
        f"throughput={result['throughput_ops_per_sec']:,.1f} ops/s"
    )


BENCHMARKS: dict[str, Callable] = {
    'VM Init + HALT': bench_vm,
    'Faulhaber sum(k^3, n=10000)': bench_faulhaber,
    'TPX Storage store+retrieve': bench_storage,
    'Lexer tokenize': bench_lexer,
}


def main() -> None:
    parser = argparse.ArgumentParser(description='Orthos-iDart performance benchmark')
    parser.add_argument('--iterations', '-n', type=int, default=100, help='Iterations per benchmark (default: 100)')
    parser.add_argument('--output', choices=['text', 'json'], default='text')
    args = parser.parse_args()

    print('=' * 80)
    print('ORTHOS-IDART PERFORMANCE BENCHMARK')
    print('=' * 80)
    print(f'Iterations per benchmark: {args.iterations}')
    print()

    results: dict[str, Any] = {}
    for name, bench_fn in BENCHMARKS.items():
        print(f'  Running: {name}...', end='', flush=True)
        try:
            result = bench_fn(args.iterations)
            results[name] = result
            print(f'\r{format_result(name, result)}')
        except Exception as exc:
            print(f'\r  {name:<35} ERROR: {exc}')
            results[name] = {'error': str(exc)}

    print()
    print('=' * 80)
    print('BENCHMARK COMPLETE')
    print('=' * 80)

    if args.output == 'json':
        output_path = PROJECT_ROOT / 'benchmark_results.json'
        with open(output_path, 'w', encoding='utf-8') as fh:
            json.dump(results, fh, indent=2)
        print(f'Results written to: {output_path}')


if __name__ == '__main__':
    main()
