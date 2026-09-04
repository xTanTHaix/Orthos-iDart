#!/usr/bin/env python3
"""
Orthos-iDart Test Runner Script
=================================
Runs the full test suite with coverage reporting and summary statistics.

Usage:
    python scripts/run_tests.py [--module MODULE] [--cov] [--html]
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = PROJECT_ROOT / '.venv' / ('Scripts' if sys.platform == 'win32' else 'bin') / 'python'
TESTS_DIR = PROJECT_ROOT / 'tests'


def run_tests(module=None, coverage=False, html_report=False, verbose=True, fail_fast=False):
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [python, '-m', 'pytest']

    if module:
        cmd.append(str(TESTS_DIR / module))
    else:
        cmd.append(str(TESTS_DIR))

    if verbose:
        cmd.append('-v')
    cmd.extend(['--tb=short', '--no-header'])

    if fail_fast:
        cmd.append('-x')

    if coverage:
        cmd.extend(['--cov=orthos', '--cov-report=term-missing'])
        if html_report:
            cmd.append('--cov-report=html:coverage_report')

    print('=' * 60)
    print('ORTHOS-IDART TEST RUNNER')
    print('=' * 60)
    print(f'Command: {" ".join(cmd)}')
    print()

    start = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.time() - start

    print()
    print('=' * 60)
    print(f'Test run completed in {elapsed:.2f}s')
    print(f'Exit code: {result.returncode}')
    if coverage and html_report and result.returncode == 0:
        report_path = PROJECT_ROOT / 'coverage_report' / 'index.html'
        print(f'Coverage report: {report_path}')
    print('=' * 60)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Orthos-iDart test runner')
    parser.add_argument('--module', help='Run tests only in specific module (e.g. vm, compiler, idart)')
    parser.add_argument('--cov', action='store_true', help='Enable coverage reporting')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    args = parser.parse_args()

    exit_code = run_tests(
        module=args.module,
        coverage=args.cov,
        html_report=args.html,
        verbose=not args.quiet,
        fail_fast=args.fail_fast,
    )
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
