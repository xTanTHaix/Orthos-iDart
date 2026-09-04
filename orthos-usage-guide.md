# How to Use Orthos (Usage Guide v1.0)

This guide explains how to install and run the Orthos system in a real project. It is based on the *Orthos Master Technical Blueprint — Unified Edition v1.0*.

---

## 1. Basic Setup (Minimum Setup)

These 2 lines are enough for general use:

```python
import orthos
orthos.ignite()
```

- `import orthos` — loads the core package, which automatically registers `bootstrapper.py` with Python's `sys.meta_path`
- `orthos.ignite()` — starts up the entire system. After this line, the rest of the project's code **can be written as plain, ordinary Python — no need to import anything extra on a per-function basis**, because the system will intercept it and route it through the pipeline (Nexus → Verification → iDart → Annihilator → VM) automatically behind the scenes

Where to place it: near the top of the entry-point file (e.g. `main.py` or the project's `__init__.py`), before importing any of the project's own modules

```python
# main.py
import orthos
orthos.ignite()

# Normal project code — nothing else needs to change
from my_project import heavy_math_module
heavy_math_module.run()
```

---

## 2. Enabling the Storage Extension (TPX) — Opt-in Only

If the project does tensor/large-data serialization work and needs hardware-level speed, pass the `storage` argument:

```python
import orthos
orthos.ignite(storage="tpx")
```

Behavior:
- If the machine's kernel supports `io_uring` and a C-extension compiler helper is available → TPX runs at full capacity (kernel-bypass I/O)
- If the machine doesn't support it → the system **automatically falls back to the Pure-Python storage backend**, with no code changes and no error

You don't need to specify this argument unless you're specifically working with tensors/large data — it's fine to leave it at the default.

---

## 3. Using `.orth` Files (If Any)

If part of the project is written in Orthos's own language (`.orth`) instead of plain Python, once `orthos.ignite()` has been called, `.orth` files can be imported just like normal Python modules immediately, with no extra special syntax needed:

```python
import orthos
orthos.ignite()

import my_module   # my_module.orth is loaded automatically via bootstrapper.py
```

---

## 4. Full Usage Example

```python
# main.py
import orthos
orthos.ignite(storage="tpx")   # Enables TPX if the machine supports it, otherwise falls back automatically

import numpy_style_math   # Module with heavy computational loops
import data_pipeline       # Module that passes strings across functions a lot

if __name__ == "__main__":
    result = numpy_style_math.run_heavy_loop(n=10_000_000)
    print(result)
```

Nothing else needs to be done inside `numpy_style_math.py` or `data_pipeline.py` — Orthos will analyze and speed things up automatically based on its safety conditions (McCabe Cyclomatic Gate, Taint Analysis, etc.). If any part of the code is too complex or has side effects beyond the threshold, the system will automatically route it to run on plain CPython instead — there's no scenario where enabling Orthos causes the code to fail to run or break.

---

## 5. Frequently Asked Questions (FAQ)

**Q: Do I need to change my existing project code?**
A: No. As long as you add `import orthos` + `orthos.ignite()` before importing your other modules, your existing Python code behaves exactly the same — the only difference is that it runs faster in the parts the system has analyzed as safe and reducible.

**Q: Will it break if the machine doesn't have `io_uring` or a C compiler?**
A: No. The system has Graceful Fallback at every point (Progressive Compilation Plugin, TPX Storage) — if the hardware/OS isn't supported, it automatically falls back to running 100% Pure Python.

**Q: Do I need to call `ignite()` in every file?**
A: No. Calling it once at the program's entry point is enough, because `bootstrapper.py` registers itself in `sys.meta_path`, which affects every subsequent import in the same process.

**Q: Are there any external dependencies I need to install?**
A: None — Orthos's core is always 100% Pure Python, Zero-Dependency. Add-ons like TPX are opt-in and already have built-in fallback.
