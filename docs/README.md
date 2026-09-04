# Orthos-iDart Documentation

## Overview

**Orthos-iDart** is a High-Performance Python Execution Engine that automatically analyzes and optimizes Python code through 5 phases without requiring any code changes.

---

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd Orthos-iDart

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run all tests
pytest tests/ -v --timeout=30

# 5. Run benchmark
python scripts/benchmark.py

# 6. Deploy
python scripts/deploy.py --env dev
```

---

## Architecture

```
orthos/
+-- __init__.py          # Main entry point, ignite()
+-- bootstrapper.py      # sys.meta_path import hook
+-- nexus/               # Phase 0: Fast-path pre-filter
|   +-- bridge.py        # NexusBridge - security firewall
+-- compiler/            # Lexer, Parser, Codegen
|   +-- lexer.py         # OrthosLexer, TokenType
|   +-- parser.py        # OrthosParser
|   +-- codegen.py       # OrthosCodeGenerator
|   +-- packer.py        # BytecodePacker (CRC32, wire format)
|   +-- analysis/
|       +-- scope.py           # ScopeAnalyzer
|       +-- cfg.py             # CFGBuilder, CFG
|       +-- complexity_gate.py # ComplexityAnalyzer
|       +-- verification_cache.py # VerificationCache
+-- vm/                  # VM execution engine
|   +-- core.py          # OrthosVM, VMState, Register, Instruction
|   +-- loader.py        # OrthosLoader (.oxb files)
+-- idart/               # Optimization
|   +-- cutter.py        # IDartCutter (topological graph cutting)
|   +-- demand_tracer.py # DemandTracer (backward demand tracing)
|   +-- express_tunnel.py # ExpressTunnel (zero-copy)
+-- annihilator/         # Mathematical transforms
|   +-- faulhaber.py     # FaulhaberEngine (O(N)->O(1))
|   +-- companion_matrix.py # CompanionMatrixEngine (recurrences)
|   +-- dp_collapser.py  # DPCollapser (dynamic programming)
|   +-- diophantine.py   # DiophantineSolver (integer equations)
|   +-- simplex.py       # SimplexOptimizer (linear programming)
|   +-- cost_model.py    # CostModel (performance estimation)
+-- safety/              # Safety & security
|   +-- taint_analyzer.py # TaintAnalyzer
|   +-- circuit_breaker.py # CircuitBreaker
+-- storage/tpx/
    +-- fallback_pure_python.py # TPXStoragePurePython
```

---

## Optimization Pipeline

| Phase | Component | Purpose |
|-------|-----------|---------|
| 0 | Nexus (NexusBridge) | Fast-path pre-filter, bottleneck detection |
| 1-2 | Compiler Analysis | Safety gates, scope management, complexity |
| 3 | iDart (IDartCutter) | Topological graph cutting, zero-copy spans |
| 4 | Annihilator | Mathematical transforms (O(N) -> O(1)) |
| 5 | VM / Execution | Bytecode emission and execution |

---

## Core Principles

- **Zero-Dependency**: Core is 100% pure Python
- **Zero-Regression**: Never breaks existing code behavior
- **Graceful Fallback**: Always has a fallback path
- **Automatic Optimization**: No manual code changes required

---

## Testing

```bash
# Run all tests
pytest tests/ -v --timeout=30

# Run specific module
pytest tests/vm/ -v

# Run with coverage
pytest tests/ --cov=orthos --cov-report=html

# Run performance benchmarks
python scripts/benchmark.py --iterations 1000
```

---

## Configuration

Copy .env.example to .env and configure:

```bash
cp .env.example .env
```

Key settings:
- ORTHOS_VM_REGISTERS - Number of VM registers (default: 256)
- ORTHOS_LOG_LEVEL - Logging level (DEBUG/INFO/WARNING/ERROR)
- ORTHOS_STORAGE_BACKEND - Storage backend type

See .env.example for all available options.
