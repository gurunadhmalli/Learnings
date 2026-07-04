# 0. Setup & Tooling — Complete Deep-Dive Guide

This is the companion reference for **Section 0** of [`python_full_syllabus.md`](python_full_syllabus.md).
Every bullet from that section is explained here in full: what it is, why it exists, how it works
under the hood, and runnable code/commands. Commands are shown for **Windows (PowerShell)** first
since that's the primary environment, with macOS/Linux equivalents noted where they differ.

---

## Table of Contents

1. [The Big Picture: What Happens When You Run Python](#1-the-big-picture)
2. [Installing Python](#2-installing-python)
3. [Verifying Your Install](#3-verifying-your-install)
4. [Python 2 vs 3 & EOL Policy](#4-python-2-vs-3--eol-policy)
5. [`python` vs `python3` vs `py` Launcher](#5-python-vs-python3-vs-py-launcher)
6. [Interpreter Command-Line Flags](#6-interpreter-command-line-flags)
7. [Virtual Environments](#7-virtual-environments)
8. [Package Managers](#8-package-managers)
9. [pip Fundamentals](#9-pip-fundamentals)
10. [`requirements.txt` vs `pyproject.toml`](#10-requirementstxt-vs-pyprojecttoml)
11. [pip Configuration Files & Private Indices](#11-pip-configuration-files--private-indices)
12. [Interactive Shells](#12-interactive-shells)
13. [IDEs & Editors](#13-ides--editors)
14. [Running Scripts](#14-running-scripts)
15. [Environment Variables](#15-environment-variables)
16. [`.env` Files & python-dotenv](#16-env-files--python-dotenv)
17. [`.pyc` Files & `__pycache__`](#17-pyc-files--__pycache__)
18. [Python Implementations](#18-python-implementations)
19. [`.gitignore` Essentials](#19-gitignore-essentials)
20. [Troubleshooting Cheat Sheet](#20-troubleshooting-cheat-sheet)
21. [Quick-Start Checklist](#21-quick-start-checklist)

---

## 1. The Big Picture

Before installing anything, it helps to know what you're installing. "Python" is really three things
bundled together: an **interpreter** (the program that runs your code), a **standard library**
(bundled modules), and **tooling** (pip, venv, etc.).

```
 your_script.py
      │
      │  1. Parsing
      ▼
 ┌─────────────┐      ┌───────────────┐      ┌────────────────┐
 │   Source    │ ───► │      AST      │ ───► │    Bytecode     │
 │   (text)    │      │ (syntax tree) │      │  (.pyc, in      │
 │             │      │               │      │  __pycache__)   │
 └─────────────┘      └───────────────┘      └────────┬────────┘
                                                        │ 2. Execution
                                                        ▼
                                             ┌──────────────────────┐
                                             │  Python Virtual       │
                                             │  Machine (PVM)        │
                                             │  — a bytecode         │
                                             │  interpreter loop     │
                                             │  written in C         │
                                             │  (this is "CPython")  │
                                             └──────────────────────┘
```

Everything in this section — installers, launchers, virtual envs, package managers — exists to
manage **which interpreter runs**, **which packages it can see**, and **how you invoke it**. Keep
that framing in mind; it's the thread that ties all these tools together.

---

## 2. Installing Python

There are three common ways to get a Python interpreter on your machine. They solve different
problems — pick based on whether you need *one* version, *many* versions, or a *data-science stack*.

### 2.1 CPython from python.org (the reference implementation)

- Download the installer from python.org and run it.
- On Windows, **check "Add python.exe to PATH"** during install — this is the #1 source of
  "`python` is not recognized" errors later.
- This gives you exactly one Python version, installed system-wide (or per-user).

```powershell
# After install, confirm it's on PATH
python --version
```

### 2.2 pyenv / pyenv-win (multiple versions, switchable per project)

`pyenv` solves: *"I need Python 3.9 for project A and 3.12 for project B, on the same machine."*
It installs multiple Python versions side-by-side under its own directory and switches which one
is "active" via shims on your PATH — it never touches your system Python.

```powershell
# Windows: pyenv-win (install via pip, scoop, or git)
pyenv install 3.12.4
pyenv install 3.9.19
pyenv global 3.12.4        # default version everywhere
pyenv local 3.9.19          # pins THIS folder to 3.9.19 (writes .python-version)
pyenv versions               # list installed versions
```

```
Without pyenv:                 With pyenv:
┌────────────────┐            ┌─────────────────────────────┐
│ One system      │            │ ~/.pyenv/versions/           │
│ python.exe      │            │   ├── 3.9.19/                │
│ (whatever the   │            │   ├── 3.11.9/                │
│ installer put   │            │   └── 3.12.4/                │
│ there)          │            │                               │
└────────────────┘            │ project_A/.python-version    │
                                │   → "3.9.19"                 │
                                │ project_B/.python-version    │
                                │   → "3.12.4"                 │
                                └─────────────────────────────┘
```

### 2.3 conda / miniconda (data-science stacks, non-Python deps included)

`conda` solves a different problem than pyenv: it manages Python **and** non-Python dependencies
(C libraries, CUDA, compiled numerical packages) as a single environment, which matters heavily for
data science / ML stacks where `pip`-installed wheels aren't always enough.

```powershell
conda create -n myenv python=3.12
conda activate myenv
conda install numpy pandas scikit-learn
```

| Tool | Solves | Manages non-Python deps? | Typical user |
|---|---|---|---|
| python.org installer | "I just need Python" | No | Beginners, single-version use |
| pyenv / pyenv-win | Multiple Python versions per project | No | Multi-project developers |
| conda / miniconda | Python + native/scientific libs | **Yes** | Data science / ML |

---

## 3. Verifying Your Install

Always confirm the interpreter and its package manager are correctly on PATH before doing anything
else:

```powershell
python --version          # e.g. Python 3.12.4
pip --version             # confirms pip is tied to that same interpreter
where python               # Windows: shows every python.exe found on PATH, in resolution order
python -c "import sys; print(sys.executable)"   # the exact binary actually running
```

```bash
# macOS/Linux equivalents
python3 --version
pip3 --version
which python3
```

If `where python` lists multiple entries, the **first one wins** — this is a common source of
"I installed a new version but the old one still runs" confusion.

---

## 4. Python 2 vs 3 & EOL Policy

- Python 2 reached **End of Life on January 1, 2020** — no security patches since. Any Python 2 code
  you encounter today is legacy and should be migrated (tools: `2to3`, `six` for a transition shim).
- Key breaking changes in Python 3: `print` is a function not a statement, `/` is true division by
  default (`//` for floor division), strings are Unicode by default (`str` vs Python 2's byte
  `str`/`unicode` split), `range()` returns a lazy iterator instead of a list.
- Python 3 itself follows a **yearly release cycle** (3.10, 3.11, 3.12, 3.13, …) with each version
  getting ~5 years of support (2 years of bugfixes + security-only after that). Always check
  [the official EOL schedule] before choosing a version for a long-lived production project.
- Rule of thumb: **use the latest stable minor version minus one** for new projects — it has had
  time to stabilize in the ecosystem (third-party packages catch up) while still being current.

---

## 5. `python` vs `python3` vs `py` Launcher

Three different commands can start "Python," and which one you get depends on your OS and how it
was installed:

- **`python`** — historically ambiguous (could be Python 2 or 3). On Windows it points at whatever
  `python.exe` is first on PATH.
- **`python3`** — the macOS/Linux convention; explicitly requests a Python 3 interpreter, since many
  distros used to ship Python 2 as `python`.
- **`py`** — the **Windows launcher** (installed alongside python.org's installer). It's smarter: it
  reads a shebang-like version specifier and picks the right installed version, independent of PATH
  ordering.

```powershell
py --list                 # shows every Python version the launcher knows about
py -3.11                  # run the 3.11 interpreter specifically
py -3.11 -m venv .venv     # use it to create a venv with a specific version
```

```
PATH resolution (python / python3):          py launcher resolution:
┌───────────────────────────┐                ┌───────────────────────────┐
│ Search PATH left to right │                │ Look up py.ini / registry  │
│ for first python.exe      │                │ of installed versions,      │
│ found → run it            │                │ pick highest (or the one    │
└───────────────────────────┘                │ requested with -3.x)         │
                                              └───────────────────────────┘
```

**Practical guidance:** on Windows, prefer `py` for launching arbitrary/version-specific Python; use
plain `python` once you're already inside an activated virtual environment (where it unambiguously
points at that venv's interpreter).

---

## 6. Interpreter Command-Line Flags

These are worth knowing early because they show up constantly in tooling, Docker images, and CI
scripts:

| Flag | Meaning | Example |
|---|---|---|
| `-m` | Run a **module** as a script (searches `sys.path`, not the filesystem) | `python -m venv .venv`, `python -m pip install requests`, `python -m http.server` |
| `-c` | Execute a command string inline | `python -c "print(2+2)"` |
| `-i` | Drop into interactive REPL after running a script (useful for post-mortem inspection) | `python -i script.py` |
| `-O` | Optimize: strips `assert` statements and `__debug__` blocks | `python -O script.py` |
| `-B` | **Don't** write `.pyc` files to `__pycache__` | `python -B script.py` |
| `-S` | Don't auto-import the `site` module (skips site-packages setup) — used for minimal/embedded environments | `python -S script.py` |
| `-I` | Isolated mode: ignores `PYTHONPATH`/user site-packages — for security-sensitive scripts | `python -I script.py` |

The `-m` flag deserves special emphasis: `python -m pip install X` is **safer** than bare `pip
install X` because it guarantees the `pip` tied to *that specific* interpreter is used — important
when multiple Python versions/venvs are on the machine.

---

## 7. Virtual Environments

### 7.1 The Problem They Solve

Without isolation, every project on your machine shares **one global site-packages** directory. Project
A needing `requests==2.0` and Project B needing `requests==2.31` cannot coexist.

```
WITHOUT virtual envs:                      WITH virtual envs:
┌─────────────────────────┐               ┌───────────────┐   ┌───────────────┐
│ Global site-packages      │               │ Project A      │   │ Project B      │
│  requests==2.31 (only     │               │ .venv/          │   │ .venv/          │
│  one version can exist!)  │               │  requests==2.0  │   │  requests==2.31 │
│                            │               └───────────────┘   └───────────────┘
│ Project A ──┐              │                       ▲                    ▲
│ Project B ──┴─── both      │               each venv has its OWN copy of
│   forced to share it       │               site-packages — fully isolated
└─────────────────────────┘
```

### 7.2 `venv` (standard library, the default choice)

```powershell
python -m venv .venv                 # create
.venv\Scripts\Activate.ps1           # activate (PowerShell)
# .venv\Scripts\activate.bat         # activate (cmd.exe)
python -m pip install requests       # installs INTO .venv only
deactivate                            # leave the venv
```

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
deactivate
```

**What `activate` actually does** (it's just a shell script — no magic):

```
Before activate:                          After activate:
PATH = C:\Python312\;C:\Windows\...       PATH = C:\project\.venv\Scripts;C:\Python312\;...
(no VIRTUAL_ENV variable)                 VIRTUAL_ENV = C:\project\.venv
                                           prompt prefixed with "(.venv)"
```

It **prepends** the venv's `Scripts` (Windows) / `bin` (Unix) folder to `PATH`, so typing `python` or
`pip` now resolves to the venv's copies first. `deactivate` is a function the script defines that
restores the original `PATH`. That's the entire mechanism — no process isolation, just PATH
reordering plus a `pyvenv.cfg` file telling the interpreter where its site-packages live.

### 7.3 `virtualenv` (third-party predecessor to `venv`)

Pre-dates `venv` (which was standardized in Python 3.3 based on `virtualenv`'s design). Still used
because it's faster to create envs and supports older Python versions:

```powershell
pip install virtualenv
virtualenv .venv
```

### 7.4 `conda env`

Conda's own environment manager — same isolation idea, but also isolates non-Python binaries:

```powershell
conda create -n myenv python=3.12
conda activate myenv
conda deactivate
conda env list
conda env remove -n myenv
```

### 7.5 Comparison

| Tool | Ships with Python? | Isolates non-Python libs | Speed | Typical use |
|---|---|---|---|---|
| `venv` | Yes (stdlib) | No | Fast | Default choice for pure-Python projects |
| `virtualenv` | No (`pip install`) | No | Faster, more features | Legacy Python support, advanced options |
| `conda env` | No (needs conda) | **Yes** | Slower to create | Data science/ML with native deps |

---

## 8. Package Managers

| Tool | Role | Notes |
|---|---|---|
| `pip` | The standard installer, pulls from PyPI | Ships with Python; works with `venv` |
| `pipx` | Installs **CLI applications** into isolated envs automatically | Use for tools like `black`, `poetry`, `httpie` — keeps them off your project's venv |
| `poetry` | Dependency + packaging + venv manager combined | Uses `pyproject.toml` + `poetry.lock`; opinionated, reproducible builds |
| `uv` | Extremely fast modern replacement for pip/venv/pip-tools, written in Rust | Drop-in `pip`-compatible commands, 10-100x faster resolution |
| `conda` | Package + environment manager for Python and native libraries | Own package format & channel (conda-forge), separate from PyPI |

```powershell
# pipx: install a CLI tool globally without polluting any project venv
pipx install black
pipx install poetry

# poetry: create + manage a project
poetry init
poetry add requests
poetry install
poetry run python main.py

# uv: blazing-fast pip/venv replacement
uv venv                       # create a venv (like python -m venv)
uv pip install requests       # like pip install, but much faster
uv sync                       # install exactly what's locked in uv.lock
uv run python main.py         # run inside the project's env automatically
```

**Decision guide:**
- Quick script, solo use → `pip` + `venv`
- Installing a CLI tool you'll use across many projects → `pipx`
- Building a distributable library/app with reproducible installs → `poetry` or `uv`
- Need non-Python dependencies (BLAS, CUDA, etc.) → `conda`

---

## 9. pip Fundamentals

`pip` is the tool you'll type most often. Core commands:

```powershell
python -m pip install requests            # install latest version
python -m pip install requests==2.31.0    # install a specific version
python -m pip install "requests>=2.20,<3" # version range constraint
python -m pip install -U requests         # upgrade to latest
python -m pip uninstall requests          # remove a package

python -m pip list                         # list installed packages in this env
python -m pip show requests                # metadata: version, location, dependencies
python -m pip freeze                       # output installed packages in requirements.txt format
python -m pip freeze > requirements.txt    # snapshot current env's dependencies

python -m pip install --user requests      # install to user site-packages (no venv, no admin)
python -m pip install -e .                 # EDITABLE install: local package, changes reflect live
python -m pip install git+https://github.com/psf/requests.git   # install from a git repo
python -m pip install ./my_local_package    # install from a local directory/wheel/sdist
```

**Editable installs (`-e`)** matter for development: instead of copying your package's files into
site-packages, pip creates a link back to your source directory. Edit the code, re-run your script,
see the change immediately — no reinstall needed. This is what you use while developing your *own*
package that other code in the same project imports.

**`--user` vs venv:** `--user` installs into a per-user directory *outside* any virtual environment
— useful for quick one-off tools, but it reintroduces the "shared dependencies across projects"
problem venvs exist to solve. Prefer venvs for real projects.

---

## 10. `requirements.txt` vs `pyproject.toml`

### `requirements.txt` — simple, flat, no metadata

```text
requests==2.31.0
flask>=2.0,<3.0
python-dotenv
```

Installed with `pip install -r requirements.txt`. It's just a list of pins — no project metadata,
no build instructions, no way to distinguish "my app's dependencies" from "dependencies needed only
for testing."

### `pyproject.toml` — the modern standard (PEP 518 + PEP 621)

- **PEP 518** introduced `pyproject.toml` to declare **build-system requirements** (what's needed
  just to *build* the package, e.g. `setuptools`, `poetry-core`).
- **PEP 621** standardized declaring **project metadata** (name, version, dependencies) in the same
  file, so tools don't need a separate `setup.py`.

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "my-app"
version = "0.1.0"
dependencies = [
    "requests>=2.31,<3",
    "flask>=2.0,<3.0",
]

[project.optional-dependencies]
dev = ["pytest", "black", "ruff"]
```

| | `requirements.txt` | `pyproject.toml` |
|---|---|---|
| Project metadata (name, version) | No | Yes |
| Build system declaration | No | Yes |
| Optional/dev dependency groups | No (needs separate files) | Yes, natively |
| Standardized by PEP | No | Yes (518, 621) |
| Used by | pip, legacy projects | poetry, uv, modern pip, hatch, PDM |

**Practical guidance:** for a distributable package or any project managed with `poetry`/`uv`, use
`pyproject.toml`. For a small script or quick internal tool, `requirements.txt` is still perfectly
fine.

---

## 11. pip Configuration Files & Private Indices

pip reads configuration from files so you don't have to repeat flags every time:

```ini
; Windows: %APPDATA%\pip\pip.ini    macOS/Linux: ~/.pip/pip.conf or ~/.config/pip/pip.conf
[global]
index-url = https://pypi.org/simple
extra-index-url = https://my-company-repo.example.com/simple
timeout = 60

[install]
trusted-host = my-company-repo.example.com
```

Common real-world reasons to touch this file:
- **Corporate/private package index** — your company mirrors or hosts internal packages.
- **Proxy settings** — behind a corporate firewall, pip needs `proxy = http://user:pass@host:port`.
- **`.pypirc`** — a *separate* file (`~/.pypirc`) used only when **publishing** packages with
  `twine upload`, storing PyPI/TestPyPI credentials and repository URLs.

---

## 12. Interactive Shells

| Shell | What it adds over the plain REPL |
|---|---|
| Default REPL (`python`) | Basic read-eval-print, minimal features |
| `IPython` | Tab completion, syntax highlighting, `%magic` commands (`%timeit`, `%run`), rich tracebacks, history search |
| `bpython` | Inline syntax highlighting, auto-suggestion, live docstring popup as you type |

```powershell
pip install ipython
ipython
```

```python
# Inside IPython — magics are IPython-only, not standard Python
%timeit sum(range(1000))
%run my_script.py
```

Jupyter Notebook/Lab (covered more under IDEs below) actually **uses IPython as its kernel** under
the hood — the same magics work there too.

---

## 13. IDEs & Editors

- **VS Code**: install the official "Python" extension; then explicitly **select the interpreter**
  (Ctrl+Shift+P → "Python: Select Interpreter") so it points at your project's `.venv`, not a global
  install. This is the #1 setup step people miss, leading to "but I installed the package!" confusion
  when VS Code's linter/runner is actually using a different Python.
- **PyCharm**: has first-class virtual environment creation built into project setup; auto-detects
  `requirements.txt`/`pyproject.toml` and offers to install missing packages.
- **Jupyter Notebook/Lab**: cell-based execution model, backed by an IPython kernel; useful for
  exploratory/data work, less suited to production application code (no natural place for tests,
  version control diffs are noisy on `.ipynb` JSON).

---

## 14. Running Scripts

```powershell
python file.py                 # the normal way
python file.py arg1 arg2       # extra args land in sys.argv
```

**Shebang lines** (`#!/usr/bin/env python3` as the first line of a file) let Unix-like systems run a
script directly, e.g. `./file.py`, by telling the OS which interpreter to hand the file to. On
Windows, the `py` launcher also reads shebang lines for compatibility, but Windows normally relies on
file-extension association instead.

```bash
# Unix: make it directly executable
chmod +x file.py
./file.py
```

**The `__main__` idiom** — critical to understand early:

```python
def main():
    print("running as a script")

if __name__ == "__main__":
    main()
```

`__name__` is `"__main__"` only when the file is *run directly*; when the same file is *imported* as
a module elsewhere, `__name__` is the module's name instead, and this block is skipped. This is how
a file can act as both a reusable library and a runnable script.

---

## 15. Environment Variables

| Variable | Effect |
|---|---|
| `PYTHONPATH` | Extra directories prepended to `sys.path` for module search |
| `PYTHONDONTWRITEBYTECODE` | If set, skips writing `.pyc` files to `__pycache__` |
| `PYTHONUNBUFFERED` | Forces stdout/stderr to be unbuffered — important in Docker/CI logs so output appears immediately |
| `PYTHONHASHSEED` | Controls hash randomization seed (set to a fixed value for reproducible hashing in tests) |
| `VIRTUAL_ENV` | Set automatically by `venv activate`; points at the active venv's root |
| `PATH` | Determines which `python`/`pip` binary resolves first |

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"   # PowerShell: set for current session
python script.py
```

```bash
PYTHONUNBUFFERED=1 python script.py   # Unix: set inline for a single run
```

---

## 16. `.env` Files & python-dotenv

Environment variables are the standard way to inject secrets/config (API keys, database URLs)
without hardcoding them in source. A `.env` file lets you define them per-project without exporting
them in your shell manually every time:

```text
# .env
DATABASE_URL=postgres://localhost:5432/mydb
API_KEY=supersecret123
```

```python
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env and injects into os.environ
db_url = os.environ["DATABASE_URL"]
```

```powershell
pip install python-dotenv
```

**Always add `.env` to `.gitignore`** — it typically holds secrets and must never be committed.

---

## 17. `.pyc` Files & `__pycache__`

Python compiles source to bytecode before execution (see the diagram in section 1). To avoid
recompiling unchanged files every run, CPython **caches** that bytecode:

```
my_project/
├── main.py
├── utils.py
└── __pycache__/
    ├── main.cpython-312.pyc
    └── utils.cpython-312.pyc
```

- The filename encodes the interpreter version (`cpython-312`) so different Python versions don't
  clash over the same cache.
- CPython checks the source file's modification time/hash against the cached `.pyc`; if the source
  changed, it recompiles automatically — you never manage this by hand.
- Only **imported modules** get cached this way; the script you invoke directly (`python main.py`)
  is compiled in-memory each run but not written to disk.
- Safe to delete `__pycache__` anytime — it will simply be regenerated. It should always be
  git-ignored (see section 19).

---

## 18. Python Implementations

"Python" is a language *specification* — CPython is just the most common implementation of it.

| Implementation | Written in | Key trait | Use case |
|---|---|---|---|
| **CPython** | C | The reference implementation; what "Python" means by default | General use — 99% of the time this is what you want |
| **PyPy** | RPython | JIT-compiled — often much faster for long-running, CPU-bound pure-Python code | Performance-sensitive pure-Python workloads |
| **Jython** | Java | Compiles to JVM bytecode, imports Java classes directly | Integrating Python into a Java ecosystem |
| **IronPython** | C# | Runs on .NET/CLR, interoperates with C# code | Integrating Python into a .NET ecosystem |
| **MicroPython** | C (stripped down) | Minimal footprint, runs on microcontrollers | Embedded systems / IoT |

Most third-party C-extension packages (like `numpy`) assume **CPython**; PyPy/Jython/IronPython
compatibility varies per package.

---

## 19. `.gitignore` Essentials

A Python project should never commit its virtual environment, bytecode cache, or secrets:

```gitignore
# Virtual environments
.venv/
venv/
env/

# Bytecode cache
__pycache__/
*.pyc

# Packaging artifacts
*.egg-info/
dist/
build/

# Secrets / local config
.env

# Tooling caches
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Jupyter checkpoints
.ipynb_checkpoints/
```

**Why `.venv/` specifically:** it's large (hundreds of MB), machine-specific (absolute paths baked
into activation scripts), and fully reproducible from `requirements.txt`/`pyproject.toml` — there is
never a good reason to commit it.

---

## 20. Troubleshooting Cheat Sheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `'python' is not recognized as an internal or external command` | Python not added to PATH during install | Reinstall with "Add to PATH" checked, or manually add the install dir + `Scripts` to PATH |
| `pip install X` succeeds but `import X` fails in your script | Script is running under a *different* interpreter than the `pip` you used | Check `where python` / VS Code's selected interpreter; use `python -m pip install X` to guarantee the match |
| Multiple Python versions conflict, wrong one keeps running | PATH order, or `py` vs `python` ambiguity | Use `py -0` / `py --list` to see what's registered; use `py -3.x` to be explicit |
| `SSLError` / certificate errors during `pip install` | Corporate proxy intercepting HTTPS, or outdated certs | Configure `trusted-host`/proxy in `pip.ini` (section 11); update `certifi` |
| Installed package works in terminal but not in VS Code (or vice versa) | Different interpreter selected in the editor vs terminal shell | Explicitly select the venv's interpreter in the editor |
| Old code still runs after editing a module | Stale `__pycache__` in a rare corruption case, or editing the wrong copy (e.g. edited source but an editable install points elsewhere) | Delete `__pycache__`; confirm `pip show <pkg>` points at expected path |
| `venv` activate script "cannot be loaded because running scripts is disabled" (PowerShell) | PowerShell execution policy blocks script activation | Run PowerShell as appropriate user and use `Set-ExecutionPolicy -Scope Process Bypass` for that session, or activate via `activate.bat` in cmd.exe instead |

---

## 21. Quick-Start Checklist

Use this every time you start a new Python project:

1. `py --list` (or `pyenv versions`) → confirm which Python version you're using.
2. `python -m venv .venv` → create an isolated environment for this project.
3. Activate it: `.venv\Scripts\Activate.ps1` (Windows) / `source .venv/bin/activate` (Unix).
4. `python -m pip install --upgrade pip` → make sure pip itself is current.
5. Install dependencies: `pip install -r requirements.txt` **or** `pip install -e .` if using
   `pyproject.toml` for your own package.
6. Create `.gitignore` (section 19) before your first commit.
7. In your editor, explicitly select the `.venv` interpreter.
8. `python -c "import sys; print(sys.executable)"` → sanity-check you're running the venv's Python,
   not a global one.
