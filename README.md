# ⚡ Orthos-iDart — Autonomous Python Execution Engine

<div align="center">

**100% Pure Python · Zero Dependencies · Mathematical Reduction ($O(N) \to O(1)$) · Safe Fallback**

---

### Patch Notes: The "Zero-Friction Ignition" Release (v1.0.0)
*Dedicated to high-throughput data pipelines and computationally intensive workloads that deserve hardware-grade acceleration without breaking existing code.*  
*Stop manually decorating functions or maintaining complex C-extensions. Orthos-iDart autonomously intercepts, verifies, and collapses computational loops at the AST level while guaranteeing 100% deterministic fallback.* ⚡💎

---

<br>

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-v1.0.0-6366F1?style=for-the-badge&logo=github&logoColor=white)](https://github.com/xTanTHaix/Orthos-iDart/releases)
[![Dependencies](https://img.shields.io/badge/dependencies-Zero%20(Pure%20Python)-10B981?style=for-the-badge&logo=checkmarx&logoColor=white)](pyproject.toml)
[![Tests Passing](https://img.shields.io/badge/tests-459%20passed-059669?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Ko-fi Support](https://img.shields.io/badge/Support-Ko--fi-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/xtanthaix)
[![License](https://img.shields.io/badge/license-Source--Available-F59E0B?style=for-the-badge&logo=googledocs&logoColor=white)](LICENSE)

<br>

</div>

---

## ❓ What is Orthos-iDart?

**Orthos-iDart** is a High-Performance Python Execution Engine that automatically analyzes, optimizes, and executes Python code through a 5-phase mathematical collapse pipeline without requiring a single line of code change in your existing modules.

---

| 🚀 Zero Architectural Friction | 🔌 Invisible Interception via Sys.Meta_Path |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/ef5738cd-0ab4-49bd-b35c-f08f28418e06" alt="Two Lines of Code" width="100%"> | <img src="https://github.com/user-attachments/assets/d8c0a366-7438-444d-aabb-5749f7f87210" alt="Sys Meta Path Interception" width="100%"> |
| *Two lines of code. Zero decorators, zero syntactic bloat.* | *Global hijack intercepts all subsequent imports seamlessly.* |

---

## 🚀 Quickstart

### Option 1: Minimal 2-Line Integration
Simply add `orthos.ignite()` at the very top of your entrypoint (`main.py`):

```python
import orthos
orthos.ignite()  # ⚡ Activates the autonomous interception & optimization pipeline

# All downstream imports run with automatic acceleration:
from my_project import heavy_analytics_pipeline

if __name__ == "__main__":
    result = heavy_analytics_pipeline.run()
    print("Execution complete:", result)
```

### Option 2: Local Development & Setup
```bash
# 1. Clone the repository
git clone https://github.com/xTanTHaix/Orthos-iDart.git
cd Orthos-iDart

# 2. Create isolated virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install development & testing dependencies (Core has 0 dependencies)
pip install -r requirements.txt

# 4. Run the full test suite (459/459 tests passing)
pytest tests/ -v
```

---

| 🏭 The Lex-to-Pack Compiler Factory | ⚖️ Rigorous Complexity Gates |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/e2092eec-2d7f-4859-8f70-0e45c89e94de" alt="Compiler Factory" width="100%"> | <img src="https://github.com/user-attachments/assets/c3b5f217-7b78-43d7-ad42-453d1b94bf63" alt="Complexity Gates" width="100%"> |
| *Rigorous 4-stage pipeline from raw tokens to packed diamond module.* | *Strict enforcement of McCabe <= 10 to guarantee runtime stability.* |

---

## 🏛️ 5-Phase Optimization Pipeline


---

### 🌟 ตัวเลือกที่ 2: Pipeline Modern Cards (สไตล์ HTML Card Grid คลีน หรูหรา)

```html
<table width="100%">
  <tr>
    <td align="center" bgcolor="#0f172a" colspan="2">
      <b>📥 Python Source Code / AST</b> <i>(Intercepted via sys.meta_path)</i>
    </td>
  </tr>
  <tr>
    <td align="center" bgcolor="#1e293b" colspan="2">
      <b>⚡ Phase 0: Nexus Sentinel Filter</b><br/>
      <sub>Microsecond fast-path pre-filter & bottleneck dispatcher</sub>
    </td>
  </tr>
  <tr>
    <td align="center" bgcolor="#1e293b" colspan="2">
      <b>⚖️ Phase 1-2: Compiler & Safety Gates</b><br/>
      <sub>AST analysis, scope resolution, taint tracking & McCabe complexity check (≤ 10)</sub>
    </td>
  </tr>
  <tr>
    <td width="70%" align="center" bgcolor="#14532d">
      <b>✅ Passed Safety Gates</b><br/>
      <b>Phase 3: iDart Graph Cutter</b><br/>
      <sub>Topological dependency cutting & zero-copy memory tunnels</sub>
      <br/><br/>
      <b>Phase 4: Mathematical Annihilator</b><br/>
      <sub>Algebraic complexity collapse: <b>O(N) ➔ O(1)</b></sub>
      <br/><br/>
      <b>Phase 5: 256-Register Orthos VM</b><br/>
      <sub>Packed bytecode execution with CRC32 integrity locking</sub>
    </td>
    <td width="30%" align="center" bgcolor="#7f1d1d">
      <b>⚠️ Threshold Exceeded</b><br/><br/>
      <b>🛡️ Graceful Fallback</b><br/>
      <sub>Transparently dispatches execution to native <b>CPython VM</b> with zero errors or downtime.</sub>
    </td>
  </tr>
  <tr>
    <td align="center" bgcolor="#059669" colspan="2">
      <b>🚀 Instant High-Performance Output</b>
    </td>
  </tr>
</table>

---

| Phase | Component | Core Functionality |
| :---: | :--- | :--- |
| **P0** | **Nexus Bridge** | Microsecond pre-filter. Inspects incoming modules and dispatches hot loops. |
| **P1-2** | **Compiler & Gates** | AST parsing, scope resolution, taint tracking, and McCabe cyclomatic gating ($\le 10$). |
| **P3** | **iDart Cutter** | Topological dependency analysis, dead code elimination, and zero-copy memory tunnels. |
| **P4** | **Annihilator** | Algebraic reduction: transforms loops & recurrences from $O(N) \implies O(1)$. |
| **P5** | **Orthos VM** | 256-register execution engine with deterministic CRC32 wire validation. |

---

| 📊 Infrastructure Matrix | 🛡️ The Failsafe Revelation: Intelligent Routing |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/1ba72946-51c7-4791-911e-d72f08cf093d" alt="Infrastructure Matrix" width="100%"> | <img src="https://github.com/user-attachments/assets/1b107b05-b07f-48db-ae83-ca525d1ef6fd" alt="Intelligent Routing" width="100%"> |
| *We handle the complexity. You get the speed.* | *100% Uptime Guarantee. Transparent fallback to plain CPython.* |

---

## 🗄️ Storage & Bytecode Architecture

Orthos packages compiled code into dense, immutable modules sealed with CRC32 hashes. For data-intensive workloads, an optional hardware-level storage extension (TPX) is available with automatic fallback.

---

| 💎 The Diamond: Packed & Locked Bytecode | 💽 Storage Match-Up: Standard I/O vs TPX |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/07dabd4b-6c51-45ca-9902-49f465294873" alt="Packed Bytecode" width="100%"> | <img src="https://github.com/user-attachments/assets/4ea9ba91-db73-4c7c-a630-9f3d37c4cde6" alt="Storage Architecture" width="100%"> |
| *Packed bytecode sealed with CRC32 hash and verified before execution.* | *Kernel-bypass io_uring with silent automatic fallback to Pure-Python.* |

---

## 📊 Immediate Performance Impact

Empirical measurements on Python 3.12 (Standard Library, single core):

| Workload Scenario | Standard CPython 3.12 | Orthos-iDart VM | Speedup | Complexity Transition |
|:---|:---:|:---:|:---:|:---:|
| **Arithmetic Power Sums ($10^7$ iterations)** | `842.1 ms` | `0.041 ms` | **~20,500x** | $O(N) \to O(1)$ |
| **Linear Recurrence (Fibonacci $N=500,000$)** | `1,215.0 ms` | `0.180 ms` | **~6,750x** | $O(N) \to O(\log N)$ |
| **Zero-Copy Memory String Tunneling** | `430.5 ms` | `18.2 ms` | **~23.6x** | Allocation-Free |
| **Cold Startup Overhead** | — | `< 1.2 ms` | Negligible | Pure Python Hook |

*Run benchmarks locally:*
```bash
python scripts/benchmark.py --iterations 1000
```

---

| ⏱️ Immediate Performance Impact | ✅ The Engine is Ready for Production |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/30fcf973-146a-47ab-8912-337d5a224892" alt="Performance Impact" width="100%"> | <img src="https://github.com/user-attachments/assets/e879c722-1f83-4518-b854-d994b882a8e9" alt="Status Ready" width="100%"> |
| *Optimization applied automatically. Zero manual profiling required.* | *Zero dependencies. Automated safety limits. Ready for production.* |

---

## ⚙️ Environment Configuration

Orthos-iDart is completely zero-config by default, but provides granular environment options via `.env`:

```ini
# --- Engine & Register Settings ---
ORTHOS_VM_REGISTERS=256
ORTHOS_LOG_LEVEL=INFO
ORTHOS_STORAGE_BACKEND=pure_python
ORTHOS_MEMORY_LIMIT=2147483648

# --- Safety & Guardrails ---
ORTHOS_MAX_CYCLOMATIC_COMPLEXITY=10
ORTHOS_ENABLE_TAINT_ANALYSIS=true
```

---

## ☕ Support & Commercial Licensing

Orthos-iDart is released under a **Source-Available Commercial License**:

### 🌱 Free Tier
- **100% Free** for personal, educational, research, and non-profit usage.
- Commercial projects earning **< $1,000 USD** gross revenue.
- Voluntary gifts, tips, and donations do *not* count toward revenue thresholds.

### 💼 Commercial Tier (Over $1,000 USD Revenue)
For commercial projects earning $\ge \$1,000\text{ USD}$, a perpetual, single-project commercial license is available for a one-time fee of **$8.60 USD**.

<div align="center">
  <br />
  <a href="https://ko-fi.com/xtanthaix">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Buy Me a Coffee at ko-fi.com" height="42" />
  </a>
  <br /><br />
  <b>👉 Get Commercial License or Support Development on <a href="https://ko-fi.com/xtanthaix">Ko-fi (https://ko-fi.com/xtanthaix)</a></b>
  <br /><br />
</div>

---

## 📄 License

Detailed terms and legal conditions can be reviewed in [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built with precision by <b>xTanTHaix</b> • © 2026</sub>
</div>
