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

> 📄 Full deep-dive companion doc: [`01_1_syntax_basics.md`](01_1_syntax_basics.md) — every topic below explained in depth, with diagrams, bottom-up (memory/OS-level) walkthroughs, and code.

- Indentation and block structure
- Comments (`#`) and docstrings (`'''`, `"""`)
- Statements vs expressions
- Simple vs compound statements (grammar-level distinction)
- Line continuation (`\`, implicit continuation in brackets)
- Multiple statements per line (`;`)
- The `print()` function (sep, end, file, flush)
- The `input()` function
- Naming conventions (PEP 8), identifiers, reserved keywords
- Soft keywords (`match`, `case`, `_`, `type`) vs reserved keywords
- The `pass`, `...` (Ellipsis) placeholders
- Source encoding declarations (`# -*- coding: utf-8 -*-`, PEP 263/3120)
- Adjacent string literal concatenation (`"a" "b"` → `"ab"`)
- `__future__` imports (syntax/behavior evolution mechanism)
- Tokenizer basics: physical vs logical lines, how source becomes tokens (`INDENT`/`DEDENT`, etc.)

### 1.2 Variables & Data Types

> 📄 Full deep-dive companion doc: [`01_2_variables_and_data_types.md`](01_2_variables_and_data_types.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- Names vs. objects: variables as labels bound to objects (not boxes holding values); `id()` and object identity
- Dynamic typing, variable binding vs assignment
- CPython identity caching: small-integer cache (`-5..256`), string interning, and why relying on `is` for equality is a trap
- `None`, `NoneType`
- Booleans (`True`, `False`), truthy/falsy values, `bool` as a subclass of `int` (`True == 1`)
- Numeric types: `int`, `float`, `complex`
  - Integer literals (binary, octal, hex, underscores in literals)
  - Arbitrary precision integers
  - Floating-point representation pitfalls (IEEE-754, `0.1 + 0.2 != 0.3`, `float('inf')`, `float('nan')`)
  - Float precision fixes: `decimal.Decimal`, `fractions.Fraction`
- Strings (`str`) — see section 3
- Type checking: `type()`, `isinstance()`, `issubclass()`
- Type conversion/casting (`int()`, `str()`, `float()`, `bool()`, etc.)
- Mutable vs immutable types
- The `del` statement (unbinding a name vs deleting an object) and reference counting basics (`sys.getrefcount`, `sys.getsizeof` — full GC internals in section 20)
- Variable scope basics (local, global, nonlocal — deep dive in 3.2)
- Multiple assignment, chained assignment, tuple unpacking, extended/star unpacking (`a, *rest = ...`)
- Augmented assignment operators (`+=`, `-=`, etc.)
- The walrus operator `:=` (assignment expressions, PEP 572)
- Variable annotations (PEP 526: `x: int = 5`, `__annotations__`) — not enforced at runtime
- Constants (naming convention, `typing.Final`)

### 1.3 Operators

> 📄 Full deep-dive companion doc: [`01_3_operators.md`](01_3_operators.md) — every topic below explained in depth, with diagrams, bottom-up (bytecode/CPython-dispatch) walkthroughs, and code.

- Arithmetic operators (`+ - * / // % ** @`), including the matrix multiplication operator `@` (PEP 465)
- Unary operators (`-x`, `+x`, `~x`)
- Floor division & modulo sign semantics with negative operands (`-7 // 2 == -4`, `-7 % 2 == 1` — differs from C)
- Comparison operators (`== != > < >= <=`)
- Chained comparisons (`a < b < c` means `a < b and b < c`, with `b` evaluated only once)
- Logical operators (`and`, `or`, `not`) and short-circuit evaluation
- Bitwise operators (`& | ^ ~ << >>`)
- Identity operators (`is`, `is not`) vs equality (`==`)
- Membership operators (`in`, `not in`)
- Operator precedence and associativity
- Operator overloading (link to dunder methods, section 4.4)

### 1.4 Control Flow

> 📄 Full deep-dive companion doc: [`01_4_control_flow.md`](01_4_control_flow.md) — every topic below explained in depth, with diagrams, bottom-up (bytecode-jump-level) walkthroughs, and code.

- `if` / `elif` / `else`
- Conditional expressions (ternary: `x if cond else y`)
- `while` loops, `else` clause on loops
- `for` loops, iterating over sequences
- How `for` actually works under the hood: the hidden `iter()`/`next()`/`StopIteration` protocol call (full iterator-protocol deep dive in 3.5)
- `range()` deep dive (a lazy, O(1)-memory sequence, not a pre-built list)
- Common iteration idioms: `enumerate()`, `zip()`, `reversed()`, unpacking while iterating (`for k, v in d.items()`)
- `break`, `continue`, loop `else`
- Nested loops and labeled-loop alternatives (using flags/functions) — Python has no `goto`/labeled `break` at all
- Loop variable scope leakage — loop variables are **not** block-scoped; they remain readable (and keep their last value) in the enclosing scope after the loop ends
- Structural Pattern Matching: `match` / `case` (PEP 634, Python 3.10+)
  - Literal patterns, capture patterns, wildcard `_`
  - Sequence patterns, mapping patterns
  - Class patterns, `__match_args__` (how positional class patterns are resolved), guards (`if`), OR patterns (`|`)

---

## 2. Data Structures (Built-in)

### 2.1 Lists

> 📄 Full deep-dive companion doc: [`02_1_lists.md`](02_1_lists.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- Creation, indexing, slicing (`[start:stop:step]`), negative indexing
- Mutability, list methods (`append`, `extend`, `insert`, `remove`, `pop`, `clear`, `sort`, `reverse`, `copy`, `index`, `count`)
- Slice assignment (`lst[1:3] = [...]`) — can grow/shrink the list, not just overwrite
- List comprehensions (basic, nested, conditional) — and their own implicit scope/frame
- Shallow vs deep copy (`copy.copy`, `copy.deepcopy`)
- List multiplication (`[x] * n`) and the shared-inner-list aliasing pitfall (`[[0]*3]*3`)
- Sorting: `sorted()` vs `.sort()`, `key=`, `reverse=`, stability (Timsort)
- List as stack/queue (and why `collections.deque` is better for queues)
- Big-O awareness: amortized O(1) `append` vs O(n) `insert(0, ...)`/`pop(0)`, O(n) membership (`in`) and search
- Gotchas: mutating a list while iterating over it, lexicographic comparison (`[1,2] < [1,3]`), `clear()` vs rebinding to `[]`

### 2.2 Tuples

> 📄 Full deep-dive companion doc: [`02_2_tuples.md`](02_2_tuples.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- Creation, immutability, packing/unpacking
- Single-element tuple gotcha
- Indexing and slicing (mechanically like lists, but slicing returns a tuple)
- Shallow immutability — the tuple's own slots are frozen, but a mutable element it contains (e.g. a nested list) can still be mutated
- Minimal method set (`count`, `index` only) and no in-place operators (`+=`/`*=` always build a new tuple)
- Hashability requirement — a tuple is hashable (usable as a dict key/set member) only if every element it contains is hashable
- Named tuples (`collections.namedtuple`, `typing.NamedTuple`)
- Tuple vs list use cases
- Multiple return values from functions are just tuple packing/unpacking

### 2.3 Dictionaries

> 📄 Full deep-dive companion doc: [`02_3_dictionaries.md`](02_3_dictionaries.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- Creation, key-value semantics, hashability requirement for keys (and the hash/`__eq__` contract)
- CPython dict internals: hash table + separate insertion-ordered compact array, open addressing, load factor & resizing, average O(1) vs worst-case O(n), hash randomization (`PYTHONHASHSEED`) against hash-flooding
- Dict methods (`get`, `setdefault`, `update`, `pop`, `popitem`, `keys`, `values`, `items`)
- `d[key]` (raises `KeyError`) vs `.get()` (returns a default) vs `del d[key]` vs `.pop()`
- Dictionary view objects (`.keys()`/`.values()`/`.items()`) are live/dynamic, not copies, and `keys()`/`items()` support set-like operations (`&`, `|`, `-`)
- Mutating a dict's size while iterating over it raises `RuntimeError` (contrast with a list's silent skip bug)
- `dict.fromkeys()`, building a dict from `zip(keys, values)`
- `popitem()`'s LIFO order (Python 3.7+ ordering guarantee)
- Dict comprehensions
- Merging dicts (`|`, `|=`, `**` unpacking, `update`) and right-hand/later-key precedence
- Ordered nature of dicts (insertion order, Python 3.7+ guarantee)
- `setdefault` vs `collections.defaultdict` — same end result, different mechanism
- `collections.OrderedDict`, `collections.defaultdict`, `collections.Counter`
- `types.MappingProxyType` — a read-only view onto a dict
- Nested dictionaries

### 2.4 Sets

> 📄 Full deep-dive companion doc: [`02_4_sets.md`](02_4_sets.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- Creation, uniqueness, hashability requirement for elements — the empty-set gotcha (`{}` is a dict, use `set()`)
- CPython set internals: a hash table like `dict` but keys-only (no values) — average O(1) `add`/`remove`/membership testing
- Sets are unordered — no insertion-order guarantee, unlike `dict` (Python 3.7+)
- Set operations (union, intersection, difference, symmetric difference) — operators (`|`, `&`, `-`, `^`) vs methods (`.union()`, etc.) and why only the methods accept arbitrary iterables
- In-place set operators/methods (`|=`, `&=`, `-=`, `^=`, `.update()`, `.intersection_update()`, etc.)
- Set methods (`add`, `remove`, `discard`, `pop`, `update`) — `remove` (raises `KeyError`) vs `discard` (silent no-op) vs `pop` (removes an arbitrary element, no LIFO guarantee)
- Subset/superset comparisons (`<`, `<=`, `>`, `>=`), `isdisjoint()`
- Frozensets — the hashable, immutable set variant (can itself be a set element or dict key)
- Set comprehensions
- Practical idioms: fast membership testing, `set(lst)` for dedup (order not preserved) vs `dict.fromkeys(lst)` for order-preserving dedup

### 2.5 Strings (Deep Dive)

> 📄 Full deep-dive companion doc: [`02_5_strings.md`](02_5_strings.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- CPython's flexible string representation (PEP 393) — strings are stored as the narrowest fixed-width form (Latin-1/UCS-2/UCS-4) that fits their widest character, not one-size-fits-all
- Immutability implications — every "mutating-looking" method returns a *new* string object; nothing is changed in place
- Literal forms & escape sequences (`\n`, `\t`, `\\`, `\uXXXX`, `\N{...}`), single/double/triple-quoted strings, quote-escaping
- Indexing and slicing (`[start:stop:step]`, negative indices) — mechanically like lists, but always returns a new string
- Membership (`in`) as substring search, and lexicographic string comparison
- String iteration is by Unicode code point, not by "visual character"/grapheme cluster (`len()` counts code points)
- String methods (`split`, `join`, `strip`, `replace`, `find`, `format`, `startswith`, `endswith`, `casefold`, etc. — full method survey)
- String formatting: `%`-formatting, `.format()` and the format-spec mini-language (`{:>10,.2f}`), f-strings (PEP 498), f-string debugging (`f"{x=}"`)
- Raw strings (`r"..."`), byte strings (`b"..."`), f-strings combined with raw
- Concatenation performance: why `s += x` in a loop is O(n²) (immutability forces a full reallocation each time) vs `''.join()` being O(n)
- Unicode, encoding/decoding (`encode()`, `decode()`, UTF-8/16/32, `chr()`, `ord()`), `UnicodeDecodeError`/`UnicodeEncodeError`
- Unicode normalization gotcha (`unicodedata.normalize`, NFC/NFD, combining characters — why two "equal-looking" strings can compare unequal)
- String interning and cached hashing — automatic interning of identifier-like literals, `sys.intern()`, and why immutability lets a string safely cache its own hash
- `str` vs `bytes` vs `bytearray`
- Text wrapping/alignment (`textwrap`, `str.ljust/rjust/center`)

### 2.6 Other Built-in Collections

> 📄 Full deep-dive companion doc: [`02_6_other_collections.md`](02_6_other_collections.md) — every topic below explained in depth, with diagrams, bottom-up (memory/CPython-level) walkthroughs, and code.

- `range` objects (lazy sequences, O(1) memory regardless of length — full derivation in 1.4)
- `bytearray`, `memoryview` — the buffer protocol (PEP 3118) and zero-copy slicing/mutation over binary data, vs. a `bytes`/`bytearray` slice which always copies
- Arrays (`array` module) vs lists — type codes (`'b'`, `'i'`, `'f'`, `'d'`, etc.) and why `array` stores raw, densely-packed C values inline instead of a list's array of pointers to separately-allocated boxed objects
- `collections.deque` (O(1) append/pop both ends) — the block-based doubly-linked-list internals that make this possible (vs. a list's O(n) `insert(0, ...)`), `maxlen` for a bounded ring buffer/sliding window, `.rotate()`
- `collections.ChainMap` — layered mapping lookups without copying/merging; writes always target the *first* mapping only; `.new_child()`
- `heapq` (priority queues/heaps) — why it's a set of functions over a plain list rather than its own class, the array-index parent/child math, Python's min-heap-only limitation and the negate-value trick for a max-heap, the `(priority, tiebreaker, item)` trick for stable tie-breaking
- `bisect` (binary search / sorted insertion) — requires an already-sorted list (doesn't sort for you), `bisect_left` vs `bisect_right` equal-element placement, O(log n) search vs O(n) insertion cost

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
