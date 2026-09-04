#!/usr/bin/env python3
"""
Orthos-iDart Deployment Script
================================
Validates environment, runs tests, and prepares the package for deployment.

Usage:
    python scripts/deploy.py [--skip-tests] [--env {dev,staging,prod}]
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deploy.log', encoding='utf-8'),
    ],
)
logger = logging.getLogger('deploy')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / '.venv'
PYTHON = VENV_DIR / ('Scripts' if sys.platform == 'win32' else 'bin') / 'python'
REQUIREMENTS = PROJECT_ROOT / 'requirements.txt'
TESTS_DIR = PROJECT_ROOT / 'tests'


def _run(cmd, cwd=None, check=True):
    logger.info('Running: %s', ' '.join(str(c) for c in cmd))
    result = subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT), stdout=sys.stdout, stderr=sys.stderr)
    if check and result.returncode != 0:
        logger.error('Command failed with exit code %d', result.returncode)
        sys.exit(result.returncode)
    return result.returncode


def check_python_version():
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        logger.error('Python 3.10+ required. Current: %d.%d', major, minor)
        sys.exit(1)
    logger.info('Python version: %d.%d OK', major, minor)


def ensure_venv():
    if not PYTHON.exists():
        logger.info('Creating virtual environment at %s', VENV_DIR)
        _run([sys.executable, '-m', 'venv', str(VENV_DIR)])
    else:
        logger.info('Virtual environment exists: %s OK', VENV_DIR)


def install_dependencies():
    logger.info('Installing dependencies...')
    _run([str(PYTHON), '-m', 'pip', 'install', '--upgrade', 'pip', '--quiet'])
    _run([str(PYTHON), '-m', 'pip', 'install', 'pytest', 'pytest-cov', 'pytest-asyncio', '--quiet'])
    if REQUIREMENTS.exists():
        _run([str(PYTHON), '-m', 'pip', 'install', '-r', str(REQUIREMENTS), '--quiet'])
    logger.info('Dependencies installed OK')


def run_tests(verbose=True):
    logger.info('Running test suite...')
    args = [str(PYTHON), '-m', 'pytest', str(TESTS_DIR)]
    if verbose:
        args.append('-v')
    args.extend(['--tb=short', '--no-header'])
    exit_code = _run(args, check=False)
    passed = exit_code == 0
    logger.info('Tests %s', 'PASSED OK' if passed else 'FAILED')
    return passed


def validate_package_structure():
    required = [
        PROJECT_ROOT / 'orthos' / '__init__.py',
        PROJECT_ROOT / 'orthos' / 'vm' / 'core.py',
        PROJECT_ROOT / 'orthos' / 'compiler' / 'lexer.py',
        PROJECT_ROOT / 'orthos' / 'idart' / 'cutter.py',
        PROJECT_ROOT / 'orthos' / 'annihilator' / 'faulhaber.py',
        PROJECT_ROOT / 'orthos' / 'storage' / 'tpx' / 'fallback_pure_python.py',
    ]
    missing = [p for p in required if not p.exists()]
    if missing:
        for p in missing:
            logger.error('Missing: %s', p)
        sys.exit(1)
    logger.info('Package structure validated OK (%d files)', len(required))


def main():
    parser = argparse.ArgumentParser(description='Orthos-iDart deployment script')
    parser.add_argument('--skip-tests', action='store_true')
    parser.add_argument('--env', choices=['dev', 'staging', 'prod'], default='dev')
    args = parser.parse_args()

    start = time.time()
    logger.info('Starting Orthos-iDart deployment (env=%s)', args.env)

    check_python_version()
    ensure_venv()
    install_dependencies()
    validate_package_structure()

    tests_passed = True
    if not args.skip_tests:
        tests_passed = run_tests()

    elapsed = time.time() - start
    logger.info('Deployment complete in %.2fs (tests=%s)', elapsed, 'OK' if tests_passed else 'FAILED')
    if not args.skip_tests and not tests_passed:
        sys.exit(1)


if __name__ == '__main__':
    main()
