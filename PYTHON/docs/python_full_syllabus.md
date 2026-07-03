# Python Mastery Syllabus — Zero to Advanced

A complete, topic-by-topic curriculum for mastering Python: from absolute basics through advanced language internals, regex, and the standard/third-party library ecosystem.

---

## 0. Setup & Tooling

> 📄 Full deep-dive companion doc: [`00_setup_and_tooling.md`](00_setup_and_tooling.md) — every topic below explained in detail with diagrams and code.

- Installing Python (CPython, pyenv/pyenv-win, conda/miniconda)
- Verifying an install (`python --version`, `pip --version`, `where`/`which python`)
- Python versions (2 vs 3, version differences, EOL policy)
- `python` vs `python3` vs `py` launcher (and Windows PATH resolution order)
- Interpreter command-line flags (`-m`, `-c`, `-i`, `-O`, `-B`, `-S`, `-I`)
- Virtual environments: `venv`, `virtualenv`, `conda env`
  - How `activate`/`deactivate` scripts modify `PATH` and `VIRTUAL_ENV`
- Package managers: `pip`, `pipx`, `poetry`, `uv`, `conda`
- `pip` fundamentals: `install`, `uninstall`, `list`, `show`, `freeze`, `install -U`,
  `install --user`, editable installs (`pip install -e .`), installing from git/local path/wheel
- `requirements.txt` vs `pyproject.toml` (PEP 518, PEP 621)
- `pip` configuration files (`pip.conf`/`pip.ini`), private/internal package indices, proxies
- Interactive shells: default REPL, `IPython`, `bpython`
- IDEs/editors: VS Code (interpreter selection), PyCharm, Jupyter Notebook/Lab
- Running scripts: `python file.py`, shebang lines, executable scripts, the `__main__` idiom
- Environment variables (`PYTHONPATH`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, etc.)
- `.env` files and `python-dotenv`
- `.pyc` files and `__pycache__` (bytecode caching mechanics)
- Python implementations: CPython, PyPy, Jython, IronPython, MicroPython
- `.gitignore` essentials for Python projects
- Troubleshooting common setup issues (multiple Python versions, PATH conflicts, SSL/proxy errors)

---

## 1. Language Fundamentals

### 1.1 Syntax Basics
- Indentation and block structure
- Comments (`#`) and docstrings (`'''`, `"""`)
- Statements vs expressions
- Line continuation (`\`, implicit continuation in brackets)
- Multiple statements per line (`;`)
- The `print()` function (sep, end, file, flush)
- The `input()` function
- Naming conventions (PEP 8), identifiers, reserved keywords
- The `pass`, `...` (Ellipsis) placeholders

### 1.2 Variables & Data Types
- Dynamic typing, variable binding vs assignment
- `None`, `NoneType`
- Booleans (`True`, `False`), truthy/falsy values
- Numeric types: `int`, `float`, `complex`
  - Integer literals (binary, octal, hex, underscores in literals)
  - Float precision, `decimal.Decimal`, `fractions.Fraction`
  - Arbitrary precision integers
- Strings (`str`) — see section 3
- Type checking: `type()`, `isinstance()`, `issubclass()`
- Type conversion/casting (`int()`, `str()`, `float()`, `bool()`, etc.)
- Mutable vs immutable types
- Variable scope basics (local, global, nonlocal — deep dive in 4.5)
- Multiple assignment, chained assignment, tuple unpacking
- Augmented assignment operators (`+=`, `-=`, etc.)
- The walrus operator `:=` (assignment expressions, PEP 572)
- Constants (naming convention, `typing.Final`)

### 1.3 Operators
- Arithmetic operators (`+ - * / // % **`)
- Comparison operators (`== != > < >= <=`)
- Logical operators (`and`, `or`, `not`) and short-circuit evaluation
- Bitwise operators (`& | ^ ~ << >>`)
- Identity operators (`is`, `is not`) vs equality (`==`)
- Membership operators (`in`, `not in`)
- Operator precedence and associativity
- Operator overloading (link to dunder methods, section 6.4)

### 1.4 Control Flow
- `if` / `elif` / `else`
- Conditional expressions (ternary: `x if cond else y`)
- `while` loops, `else` clause on loops
- `for` loops, iterating over sequences
- `range()` deep dive
- `break`, `continue`, loop `else`
- Nested loops and labeled-loop alternatives (using flags/functions)
- Structural Pattern Matching: `match` / `case` (PEP 634, Python 3.10+)
  - Literal patterns, capture patterns, wildcard `_`
  - Sequence patterns, mapping patterns
  - Class patterns, guards (`if`), OR patterns (`|`)

---

## 2. Data Structures (Built-in)

### 2.1 Lists
- Creation, indexing, slicing (`[start:stop:step]`)
- Mutability, list methods (`append`, `extend`, `insert`, `remove`, `pop`, `clear`, `sort`, `reverse`, `copy`, `index`, `count`)
- List comprehensions (basic, nested, conditional)
- Shallow vs deep copy (`copy.copy`, `copy.deepcopy`)
- Sorting: `sorted()` vs `.sort()`, `key=`, `reverse=`
- List as stack/queue (and why `collections.deque` is better for queues)

### 2.2 Tuples
- Creation, immutability, packing/unpacking
- Single-element tuple gotcha
- Named tuples (`collections.namedtuple`, `typing.NamedTuple`)
- Tuple vs list use cases

### 2.3 Dictionaries
- Creation, key-value semantics, hashability requirement for keys
- Dict methods (`get`, `setdefault`, `update`, `pop`, `popitem`, `keys`, `values`, `items`)
- Dict comprehensions
- Merging dicts (`|`, `|=`, `**` unpacking, `update`)
- Ordered nature of dicts (insertion order, Python 3.7+ guarantee)
- `collections.OrderedDict`, `collections.defaultdict`, `collections.Counter`
- Nested dictionaries

### 2.4 Sets
- Creation, uniqueness, hashability
- Set operations (union, intersection, difference, symmetric difference)
- Set methods (`add`, `remove`, `discard`, `pop`, `update`)
- Frozensets
- Set comprehensions

### 2.5 Strings (Deep Dive)
- Immutability implications
- String methods (`split`, `join`, `strip`, `replace`, `find`, `format`, `startswith`, `endswith`, `casefold`, etc. — full method survey)
- String formatting: `%`-formatting, `.format()`, f-strings (PEP 498), f-string debugging (`f"{x=}"`)
- Raw strings (`r"..."`), byte strings (`b"..."`), f-strings combined with raw
- Unicode, encoding/decoding (`encode()`, `decode()`, UTF-8/16/32, `chr()`, `ord()`)
- String interning
- `str` vs `bytes` vs `bytearray`
- Text wrapping/alignment (`textwrap`, `str.ljust/rjust/center`)

### 2.6 Other Built-in Collections
- `range` objects (lazy sequences)
- `bytearray`, `memoryview`
- Arrays (`array` module) vs lists
- `collections.deque` (O(1) append/pop both ends)
- `collections.ChainMap`
- `heapq` (priority queues/heaps)
- `bisect` (binary search / sorted insertion)

---

## 3. Functions

### 3.1 Basics
- Defining functions (`def`), calling, return values
- Parameters vs arguments
- Default argument values (and the mutable-default-argument pitfall)
- Positional vs keyword arguments
- `*args` and `**kwargs`
- Positional-only (`/`) and keyword-only (`*`) parameters (PEP 570)
- Docstrings and function annotations
- `None` return implicit behavior

### 3.2 Scope & Closures
- LEGB rule (Local, Enclosing, Global, Built-in)
- `global` and `nonlocal` keywords
- Closures — capturing variables from enclosing scope
- Late binding closures gotcha (loop variable capture)

### 3.3 Functional Programming Tools
- First-class functions, functions as objects
- Lambda expressions
- `map()`, `filter()`, `reduce()` (`functools.reduce`)
- `functools`: `partial`, `wraps`, `lru_cache`, `cache`, `cached_property`, `reduce`, `singledispatch`, `total_ordering`
- `operator` module (`operator.add`, `itemgetter`, `attrgetter`, `methodcaller`)
- Recursion, recursion limits (`sys.setrecursionlimit`), tail-call absence in Python

### 3.4 Decorators
- Functions as decorators, `@decorator` syntax
- Decorators with arguments
- Class-based decorators
- Stacking multiple decorators
- Preserving metadata with `functools.wraps`
- Common built-ins: `@staticmethod`, `@classmethod`, `@property`
- Practical patterns: timing, caching, retry, logging, validation decorators

### 3.5 Generators & Iterators
- Iterables vs iterators, the iterator protocol (`__iter__`, `__next__`)
- `iter()`, `next()`, `StopIteration`
- Generator functions (`yield`)
- Generator expressions
- `yield from` (delegation)
- Sending values into generators (`.send()`, `.throw()`, `.close()`)
- Infinite generators, lazy evaluation
- `itertools` module deep dive:
  - Infinite iterators: `count`, `cycle`, `repeat`
  - Combinatoric: `product`, `permutations`, `combinations`, `combinations_with_replacement`
  - Terminating: `chain`, `zip_longest`, `islice`, `takewhile`, `dropwhile`, `groupby`, `accumulate`, `starmap`, `tee`, `compress`, `filterfalse`

---

## 4. Object-Oriented Programming

### 4.1 Classes & Instances
- `class` keyword, instance creation, `__init__`
- Instance attributes vs class attributes
- Methods vs functions, `self`
- `__new__` vs `__init__`
- Instance methods, class methods, static methods
- `@property`, getters/setters/deleters, computed attributes
- `__slots__` and memory optimization

### 4.2 Inheritance & Polymorphism
- Single inheritance, `super()`
- Multiple inheritance, Method Resolution Order (MRO), `C3` linearization
- Abstract base classes (`abc` module, `ABCMeta`, `@abstractmethod`)
- Mixins
- Duck typing vs formal interfaces
- Operator/method overriding, polymorphism in practice
- Composition vs inheritance

### 4.3 Encapsulation
- Public/protected/private naming conventions (`_x`, `__x`)
- Name mangling
- Properties for controlled attribute access

### 4.4 Dunder (Magic) Methods
- Object representation: `__repr__`, `__str__`, `__format__`
- Comparison: `__eq__`, `__lt__`, `__le__`, etc., `functools.total_ordering`
- Arithmetic: `__add__`, `__sub__`, `__mul__`, `__radd__`, `__iadd__`, etc.
- Container emulation: `__len__`, `__getitem__`, `__setitem__`, `__delitem__`, `__contains__`, `__iter__`
- Callable objects: `__call__`
- Context managers: `__enter__`, `__exit__`
- Attribute access hooks: `__getattr__`, `__getattribute__`, `__setattr__`, `__delattr__`
- Hashing: `__hash__` and its relationship with `__eq__`
- `__bool__`, `__len__` truthiness
- `__copy__`, `__deepcopy__`

### 4.5 Advanced OOP
- Metaclasses (`type`, custom metaclasses, `__init_subclass__`)
- Class decorators
- `dataclasses` module (`@dataclass`, `field`, frozen, ordering, `__post_init__`)
- `typing.NamedTuple` vs `dataclass` vs plain class
- Descriptors (`__get__`, `__set__`, `__delete__`), how `property` is built on descriptors
- Enum classes (`enum.Enum`, `IntEnum`, `Flag`, `auto()`)
- Protocols / structural typing (`typing.Protocol`, PEP 544)
- Abstract vs concrete class design patterns

---

## 5. Error Handling & Debugging

### 5.1 Exceptions
- `try` / `except` / `else` / `finally`
- Catching multiple exceptions, exception hierarchies
- Raising exceptions (`raise`, `raise ... from ...`)
- Custom exception classes
- Built-in exception hierarchy (`BaseException`, `Exception`, `ArithmeticError`, etc.)
- `assert` statements and `-O` optimization flag
- Exception groups and `except*` (PEP 654, Python 3.11+)
- Context of exceptions: `__cause__`, `__context__`, exception chaining

### 5.2 Context Managers
- `with` statement mechanics
- Writing context managers via classes (`__enter__`/`__exit__`)
- `contextlib`: `@contextmanager`, `closing`, `suppress`, `ExitStack`, `redirect_stdout`

### 5.3 Debugging & Diagnostics
- `pdb` (Python debugger): breakpoints, stepping, inspecting
- `breakpoint()` built-in
- Logging module (`logging`): loggers, handlers, formatters, levels, config
- `traceback` module
- `warnings` module
- Profiling: `cProfile`, `profile`, `timeit`, `tracemalloc`
- Static analysis tools: `pylint`, `flake8`, `mypy`, `pyright`, `ruff`

---

## 6. Modules & Packages

- `import` statement variants (`import x`, `from x import y`, `import x as y`)
- Module search path (`sys.path`), `PYTHONPATH`
- `__name__ == "__main__"` idiom
- Creating packages, `__init__.py`
- Relative vs absolute imports
- `__all__` and controlling exports
- Namespace packages (PEP 420)
- Reloading modules (`importlib.reload`)
- Building distributable packages: `setup.py`, `pyproject.toml`, `setuptools`, `build`, `twine`
- Publishing to PyPI
- Circular import problems and solutions

---

## 7. File I/O & Serialization

### 7.1 File Handling
- `open()` modes (`r`, `w`, `a`, `x`, `b`, `+`)
- Reading/writing text and binary files
- Context managers for files (`with open(...) as f`)
- File methods (`read`, `readline`, `readlines`, `write`, `writelines`, `seek`, `tell`)
- Working with paths: `os.path` vs `pathlib.Path`
- `pathlib` deep dive (globbing, resolving, joining paths)
- Temporary files (`tempfile`)
- Working with CSV (`csv` module), TSV
- Working with JSON (`json` module: `dumps`, `loads`, `dump`, `load`, custom encoders/decoders)
- Working with YAML (`PyYAML`), TOML (`tomllib`/`tomli`)
- Working with XML (`xml.etree.ElementTree`, `lxml`)
- Working with Excel (`openpyxl`, `xlrd`, `pandas.read_excel`)
- Working with binary formats: `pickle` (and security caveats), `shelve`, `struct`

### 7.2 OS & System Interaction
- `os` module (environment vars, process info, file system ops)
- `shutil` (copying, moving, archiving)
- `sys` module (argv, path, exit, stdin/stdout/stderr)
- `subprocess` module (`run`, `Popen`, pipes, shell commands)
- `platform` module
- `glob` module

---

## 8. Regular Expressions (Deep Dive)

### 8.1 Fundamentals
- What regex is, use cases, `re` module overview
- Raw strings and why they matter for regex
- `re.match` vs `re.search` vs `re.fullmatch`
- `re.findall` vs `re.finditer`
- `re.sub` and `re.subn`
- `re.split`
- Compiling patterns: `re.compile`, reuse and performance
- Flags: `re.IGNORECASE`, `re.MULTILINE`, `re.DOTALL`, `re.VERBOSE`, `re.ASCII`, `re.UNICODE`

### 8.2 Pattern Syntax
- Literal characters vs metacharacters
- Character classes (`[abc]`, `[^abc]`, `[a-z]`, `\d \D \w \W \s \S`)
- Anchors (`^`, `$`, `\b`, `\B`, `\A`, `\Z`)
- Quantifiers (`*`, `+`, `?`, `{m,n}`) — greedy vs lazy/non-greedy (`*?`, `+?`, `??`, `{m,n}?`)
- Grouping `()`, non-capturing groups `(?:...)`
- Alternation `|`
- Backreferences (`\1`, `(?P=name)`)
- Named groups (`(?P<name>...)`)
- Lookahead (`(?=...)`, `(?!...)`)
- Lookbehind (`(?<=...)`, `(?<!...)`)
- Conditional patterns
- Unicode property escapes
- Escaping special characters (`re.escape`)

### 8.3 Practical Regex
- Match objects: `.group()`, `.groups()`, `.groupdict()`, `.start()`, `.end()`, `.span()`
- Common recipes: email/URL/phone validation, whitespace normalization, log parsing, extracting numbers/dates
- Catastrophic backtracking and performance pitfalls
- Regex debugging tools (regex101-style thinking, verbose mode with comments)
- Alternative regex engines: `regex` third-party module (features beyond `re`)

---

## 9. Concurrency & Parallelism

### 9.1 Threading
- `threading` module: `Thread`, `Lock`, `RLock`, `Event`, `Condition`, `Semaphore`
- Global Interpreter Lock (GIL) — what it is and its implications
- Thread pools (`concurrent.futures.ThreadPoolExecutor`)
- Race conditions, deadlocks, thread safety

### 9.2 Multiprocessing
- `multiprocessing` module: `Process`, `Pool`, `Queue`, `Pipe`, shared memory
- `concurrent.futures.ProcessPoolExecutor`
- Pickling requirements for multiprocessing
- Comparing multiprocessing vs threading vs asyncio use cases

### 9.3 Asynchronous Programming
- `async`/`await` syntax
- Event loop concepts (`asyncio.run`, `get_event_loop`)
- Coroutines vs generators
- `asyncio.gather`, `asyncio.create_task`, `asyncio.wait`
- Async context managers (`async with`) and async iterators (`async for`)
- `asyncio` synchronization primitives (`Lock`, `Event`, `Queue`, `Semaphore`)
- Async libraries: `aiohttp`, `httpx` (async mode), `asyncpg`, `aiofiles`
- Structured concurrency, `asyncio.TaskGroup` (Python 3.11+)
- Timeouts and cancellation

---

## 10. Type System & Static Typing

- Gradual typing philosophy
- `typing` module: `List`, `Dict`, `Tuple`, `Optional`, `Union`, `Any`, `Callable`, `Iterable`, `Iterator`, `Sequence`, `Mapping`
- Modern generics syntax (`list[int]`, `dict[str, int]`, PEP 585)
- `Optional[X]` vs `X | None` (PEP 604 union syntax)
- Generics with `TypeVar`, `Generic`
- `TypedDict`, `NewType`, `Literal`, `Final`
- `Protocol` for structural typing
- `overload` decorator
- Type checking tools: `mypy`, `pyright`, strictness levels
- Runtime type checking libraries: `pydantic`, `typeguard`

---

## 11. Testing

- `unittest` framework (`TestCase`, assertions, setup/teardown, test suites)
- `pytest`: fixtures, parametrize, marks, plugins, conftest.py
- Mocking: `unittest.mock` (`Mock`, `MagicMock`, `patch`)
- Test coverage (`coverage.py`, `pytest-cov`)
- Property-based testing (`hypothesis`)
- Doctest (`doctest` module)
- Test-driven development (TDD) workflow
- Continuous integration basics (GitHub Actions running pytest)

---

## 12. Standard Library Survey (Beyond the Above)

- `datetime`, `time`, `calendar`, `zoneinfo` — dates, times, timezones
- `math`, `statistics`, `random`, `secrets`
- `string` module (constants, `Template`)
- `re` (covered in section 8)
- `collections` (covered in section 2)
- `itertools`, `functools` (covered in section 3)
- `copy` — shallow/deep copy
- `argparse` — CLI argument parsing (also `click`, `typer` as alternatives)
- `configparser` — INI config files
- `hashlib`, `hmac`, `secrets` — hashing and crypto basics
- `uuid`
- `socket`, `http.client`, `urllib` — low-level networking
- `email`, `smtplib` — email handling
- `sqlite3` — embedded database
- `venv`, `sysconfig`
- `dataclasses`, `enum` (covered in OOP)
- `weakref`
- `gc` module (garbage collection internals)
- `inspect` module (introspection)
- `dis` module (bytecode disassembly)
- `abc`, `typing` (covered above)
- `zipfile`, `tarfile`, `gzip`, `bz2`, `lzma`
- `base64`, `binascii`

---

## 13. Networking & Web

- HTTP fundamentals recap
- `requests` library (GET/POST, sessions, headers, auth, timeouts, retries)
- `httpx` (sync + async HTTP client)
- Web scraping: `BeautifulSoup`, `lxml`, `Scrapy`
- Web frameworks:
  - `Flask` (routing, templates with Jinja2, blueprints, extensions)
  - `FastAPI` (path/query params, Pydantic models, dependency injection, async endpoints, OpenAPI docs)
  - `Django` (MVT architecture, ORM, admin, migrations, DRF for REST APIs)
- WSGI vs ASGI
- Building REST APIs, authentication (JWT, OAuth basics)
- WebSockets (`websockets` library, FastAPI/Starlette websocket support)
- Templating engines (`Jinja2`)

---

## 14. Databases

- Relational basics recap (tables, joins, normalization)
- `sqlite3` standard library usage
- SQL toolkits/ORMs: `SQLAlchemy` (Core + ORM), `Django ORM`, `peewee`
- Database drivers: `psycopg2`/`psycopg` (Postgres), `PyMySQL`/`mysqlclient` (MySQL)
- NoSQL: `pymongo` (MongoDB), `redis-py` (Redis)
- Connection pooling, migrations (`alembic`, Django migrations)

---

## 15. Data Science & Numerical Libraries

- `NumPy`: ndarray, broadcasting, vectorization, indexing/slicing, linear algebra ops, random module
- `pandas`: Series, DataFrame, indexing (`loc`/`iloc`), groupby, merge/join, pivot tables, missing data handling, time series
- `matplotlib`: figures, axes, plotting APIs (pyplot vs OO interface)
- `seaborn`: statistical plotting built on matplotlib
- `plotly`: interactive visualizations
- `scipy`: stats, optimization, linear algebra, signal processing
- `scikit-learn`: estimators API, preprocessing, model selection, pipelines, common algorithms
- Jupyter notebooks workflow, magics (`%timeit`, `%matplotlib inline`)
- `polars` (modern high-performance DataFrame alternative)

---

## 16. Machine Learning / AI Libraries (Overview Level)

- `scikit-learn` deep dive (classification, regression, clustering, cross-validation, metrics)
- `TensorFlow` and `Keras` basics
- `PyTorch` basics (tensors, autograd, `nn.Module`, training loop)
- `Hugging Face transformers` basics
- `LangChain` / `LangGraph` basics (given current project context)
- Model serialization (`joblib`, `pickle`, ONNX overview)

---

## 17. GUI & Desktop Applications

- `tkinter` (widgets, layout managers, event loop)
- `PyQt`/`PySide`
- `Kivy` (cross-platform, mobile)

---

## 18. Packaging, Distribution & Deployment

- Building wheels and sdists
- Entry points, console scripts
- Dockerizing Python applications
- Environment reproducibility (`pip freeze`, lock files, `poetry.lock`, `uv.lock`)
- Semantic versioning
- CI/CD basics for Python projects (GitHub Actions, pre-commit hooks)
- `pre-commit` framework (linting/formatting automation)
- Code formatters: `black`, `isort`, `ruff format`

---

## 19. Performance & Optimization

- Profiling and benchmarking (`timeit`, `cProfile`, `line_profiler`, `memory_profiler`)
- Big-O awareness for built-in operations (list vs dict vs set lookup costs)
- Efficient string building (`''.join()` vs concatenation)
- Generators for memory efficiency
- `__slots__` for memory savings
- Caching strategies (`lru_cache`, memoization patterns)
- C extensions overview: `Cython`, `ctypes`, `cffi`
- `numba` (JIT compilation for numerical code)
- Understanding the GIL's effect on CPU-bound vs I/O-bound workloads
- When to use multiprocessing vs threading vs asyncio

---

## 20. Python Internals (Advanced/Expert Level)

- CPython object model (`PyObject`, reference counting)
- Memory management, garbage collection (generational GC, reference cycles)
- The GIL in depth, GIL removal efforts (PEP 703 / free-threaded builds)
- Bytecode and the `dis` module
- The data model (`__dict__`, `__class__`, MRO internals)
- Import system internals (`importlib`, finders, loaders, meta path)
- `sys` internals (`sys.modules`, `sys.settrace`, frame objects)
- Writing C extensions for Python
- Understanding the compilation pipeline (source → AST → bytecode → execution)
- `ast` module — parsing and manipulating Python syntax trees
- Python Enhancement Proposals (PEPs) — how the language evolves

---

## 21. Best Practices & Software Design

- PEP 8 style guide in depth
- PEP 20 (The Zen of Python)
- Writing idiomatic ("Pythonic") code
- Docstring conventions (Google, NumPy, reStructuredText styles)
- Project structure conventions (`src` layout vs flat layout)
- SOLID principles applied in Python
- Common design patterns in Python (Singleton, Factory, Strategy, Observer, Decorator pattern vs `@decorator`, Adapter)
- Dependency injection patterns
- Code review practices, type hints as documentation
- Writing effective READMEs and documentation (`Sphinx`, `mkdocs`)
- Security basics: avoiding `eval`/`exec` misuse, safe deserialization, secrets management, dependency vulnerability scanning (`pip-audit`)

---

## 22. Capstone Practice Tracks

- Building a CLI tool end-to-end (`argparse`/`click`/`typer` + packaging)
- Building a REST API (FastAPI + SQLAlchemy + Pytest)
- Building a data pipeline (pandas + scheduling)
- Building a scraper (requests/httpx + BeautifulSoup + storage)
- Building an automation script (os/shutil/subprocess)
- Contributing to an open-source Python project
- Solving algorithmic problems (LeetCode-style) to reinforce data structures section

---

### How to Use This Syllabus

1. Work top to bottom for structured mastery — each section builds on the previous.
2. For every topic, practice with small scripts before moving on.
3. Revisit sections 8 (Regex), 9 (Concurrency), and 20 (Internals) after building real projects — they land better with context.
4. Use section 22 (Capstones) to force integration of everything learned.
