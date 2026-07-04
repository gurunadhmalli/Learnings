# 1.1 Syntax Basics — Complete Deep-Dive Guide

This is the companion reference for **Section 1.1** of [`python_full_syllabus.md`](python_full_syllabus.md).
Every bullet from that section is explained here the same way Section 0's guide works: what it is,
why it exists, how it works **all the way down to memory and the operating system**, and runnable
code you can try. Where a concept has a "surface" behavior (what you type) and a "hidden" mechanism
(what the interpreter actually does), both are covered — surface first, mechanism second — so you
can read this either as a beginner's tour or an internals reference.

---

## Table of Contents

1. [The Big Picture: One Pipeline, Referenced Everywhere](#1-the-big-picture-one-pipeline-referenced-everywhere)
2. [Indentation & Block Structure](#2-indentation--block-structure)
3. [Comments vs Docstrings](#3-comments-vs-docstrings)
4. [Statements vs Expressions](#4-statements-vs-expressions)
5. [Simple vs Compound Statements](#5-simple-vs-compound-statements)
6. [Line Continuation](#6-line-continuation)
7. [Multiple Statements per Line (`;`)](#7-multiple-statements-per-line-)
8. [The `print()` Function — Deep Dive](#8-the-print-function--deep-dive)
9. [The `input()` Function — Deep Dive](#9-the-input-function--deep-dive)
10. [Naming Conventions & Identifiers](#10-naming-conventions--identifiers)
11. [Reserved Keywords vs Soft Keywords](#11-reserved-keywords-vs-soft-keywords)
12. [`pass` and `...` (Ellipsis)](#12-pass-and--ellipsis)
13. [Source Encoding Declarations](#13-source-encoding-declarations)
14. [Adjacent String Literal Concatenation](#14-adjacent-string-literal-concatenation)
15. [`__future__` Imports](#15-__future__-imports)
16. [Cheat Sheet: Common Syntax Gotchas](#16-cheat-sheet-common-syntax-gotchas)
17. [Quick-Reference Checklist](#17-quick-reference-checklist)

---

## 1. The Big Picture: One Pipeline, Referenced Everywhere

Before touching individual syntax rules, it helps to see the whole road a `.py` file travels before
it does anything. Almost every topic below is really just "what happens at one specific stage of
this road." Instead of re-explaining the pipeline in every section, we draw it once here and point
back to it (`→ Stage N`) throughout the doc.

```
 Stage 0            Stage 1            Stage 2          Stage 3            Stage 4
 Source bytes  ───►  Tokenizer   ───►  Parser     ───►  Compiler    ───►  CPython VM
 on disk             (lexer)           (PEG, 3.9+)       (bytecode)        (ceval.c loop)
 "syntax_basics.py"  produces a        builds the        emits a          executes bytecode
 — just bytes,       flat stream       AST (Abstract     "code object"    instructions one
 decoded using        of tokens:       Syntax Tree)       — the .pyc       at a time, on a
 an encoding           NAME, OP,       — a nested         payload —        stack, manipulating
 (→ Stage 13)          NEWLINE,        tree of Python     bytecode is      real objects
                       INDENT,         grammar rules      cached here      (PyObject*) that
                       DEDENT,         (If, Assign,       (→ 00_setup      live in heap
                       STRING,         Call, ...)         doc, §17)        memory, refcounted
                       NUMBER, ...
                       (→ Stage 6,     (→ Stage 4,        (→ Stage 4,      (→ Stage 8, 9 for
                        line joining)   stmt vs expr)      constant         I/O → syscalls)
                                                           folding)
```

**Layman version:** think of writing a letter. Stage 0 is the ink on paper. Stage 1 is breaking the
sentence into individual words ("tokenizing" — you don't process letter-by-letter, you process
word-by-word). Stage 2 is diagramming the sentence into subject/verb/object (grammar structure).
Stage 3 is translating it into a to-do list of atomic actions. Stage 4 is actually *doing* those
actions one at a time. Every "syntax rule" in Python is really a rule about how Stage 1 or Stage 2
is allowed to behave.

**Why this matters for learning:** almost every "why does Python require/forbid this?" question
has the same shape of answer: "because of how the tokenizer/parser/compiler works at some specific
stage." Keep this diagram in mind — each section below names which stage(s) it lives at.

---

## 2. Indentation & Block Structure

**What it is:** Python uses leading whitespace to mark which statements belong to a block (the
body of an `if`, `for`, `def`, etc.), instead of braces `{}` or `begin`/`end` keywords.

```python
if x > 0:
    print("positive")   # this line belongs to the if-block
    print("still inside")
print("outside the if")  # back to the outer indentation level
```

**Why it exists:** in brace-languages, indentation is a *style convention* — the compiler doesn't
care, only humans do, and code can visually lie (indentation says one thing, braces say another).
Python's designer (Guido van Rossum) made indentation *load-bearing*: what the code visually looks
like *is* what it structurally means. There is no way for visual nesting and actual nesting to
disagree, because they're the same information.

**How it works — bottom-up (→ Stage 1, the tokenizer):**

Python's tokenizer doesn't just emit tokens for words and symbols — it also emits two special
tokens that never appear as literal text: `INDENT` and `DEDENT`. It maintains a stack of the
indentation widths seen so far (starting with `[0]`):

```
Source:                         Tokenizer sees:               Indent stack:
if x > 0:                       NAME(if) NAME(x) OP(>) ...     [0]
    print("positive")           INDENT, NAME(print), ...       [0, 4]   <- pushed: 4 > 0
    print("still inside")       NAME(print), ...               [0, 4]   <- same level, no token
print("outside the if")         DEDENT, NAME(print), ...       [0]      <- popped: back to 0
```

- A line indented **more** than the current top-of-stack value emits an `INDENT` token and pushes
  the new width.
- A line indented to a **previously-seen** width emits one `DEDENT` token per level popped, until
  the stack top matches again. If it never matches exactly, that's an `IndentationError`.
- A line at the **same** width emits nothing extra — it's just the next statement in the same block.

The parser (Stage 2) then treats `INDENT ... DEDENT` as delimiters for a block, exactly the way a
brace-language's parser treats `{ ... }`. **Indentation isn't "converted to braces" as a metaphor —
it *is* mechanically identical to braces from the parser's point of view, just spelled differently
by the tokenizer.**

**Tabs vs spaces:** mixing tabs and spaces in a way that's ambiguous about the resulting width
raises `TabError: inconsistent use of tabs and spaces in indentation` — Python refuses to guess.
PEP 8 mandates **4 spaces per level, never tabs**, precisely because tab width is a rendering choice
(4? 8?) and Python's own correctness must not depend on someone's editor settings.

```python
def f():
	x = 1        # this line indented with a TAB
        y = 2    # this line indented with SPACES that render to the same width
```
This raises `TabError` even though it *looks* aligned in some editors — the tokenizer compares the
actual bytes, not the rendered appearance.

**Try it yourself:**
```python
import tokenize, io

code = "if True:\n    x = 1\n    y = 2\nprint(x)\n"
for tok in tokenize.generate_tokens(io.StringIO(code).readline):
    print(tok.type, tokenize.tok_name[tok.type], repr(tok.string))
```
Run this and you'll see `INDENT` and `DEDENT` appear in the token stream exactly where the diagram
above predicts.

---

## 3. Comments vs Docstrings

**What they are:** `#` starts a comment that runs to end of line. A string literal that is the
*first statement* inside a module, class, or function becomes that object's **docstring**
(conventionally written with triple quotes `'''...'''` or `"""..."""` so it can span lines).

```python
# This is a comment — a note for humans only.
def greet(name):
    """Return a friendly greeting for `name`."""   # this is a docstring
    return f"Hello, {name}!"
```

**Why the distinction matters — and it's a bigger difference than it looks:**

| | Comment (`#`) | Docstring (string literal) |
|---|---|---|
| Tokenizer stage | Recognized and **discarded** at Stage 1 — never becomes a token at all | Tokenized as a normal `STRING` token, like any other string literal |
| Reaches the AST? | **No** | **Yes** — it's an ordinary expression-statement node |
| Exists at runtime? | **No** — zero memory footprint, zero runtime cost | **Yes** — the compiler special-cases "first string literal in this block" and stores it on the object's `__doc__` attribute |
| Inspectable while the program runs? | No — it's gone before compilation even starts | Yes — `help(greet)`, `greet.__doc__`, `inspect.getdoc(greet)` |

**How it works — bottom-up:**

```
 Comments (# ...):                       Docstrings ("""..."""):
 Stage 1 (tokenizer)                     Stage 1 (tokenizer)
   sees "# ...", discards it               sees a STRING token, keeps it
        │  (never emitted as a token)           │
        ▼                                       ▼
 Stage 2 (parser)                        Stage 2 (parser)
   never sees it — doesn't exist            builds an Expr(Constant(str)) AST node,
                                             first in the block
        │                                        │
        ▼                                        ▼
 Stage 3 (compiler)                       Stage 3 (compiler)
   nothing to compile                        recognizes "first statement is a bare
                                             string" and stores it as __doc__ on the
                                             function/class/module object
        │                                        │
        ▼                                        ▼
 Runtime: no trace left                   Runtime: a real str object sitting in
                                             memory, reachable via greet.__doc__
```

**Layman version:** a comment is like a sticky note you leave on your own desk while writing a
letter — useful while writing, thrown away before the letter is sealed. A docstring is like a
label printed *inside* the envelope — it travels with the letter and anyone who opens it later can
read it.

```python
>>> greet.__doc__
'Return a friendly greeting for `name`.'
>>> help(greet)
Help on function greet in module __main__:

greet(name)
    Return a friendly greeting for `name`.
```

---

## 4. Statements vs Expressions

**What they are:**
- An **expression** is anything that *produces a value*: `2 + 2`, `f(x)`, `x > 0`, `[1, 2, 3]`.
- A **statement** is an *instruction to do something*; it may contain expressions but isn't
  required to hand back a value: `x = 2 + 2`, `if x > 0: ...`, `return f(x)`, `import os`.

Rule of thumb: **if you can wrap it in `print(...)` without a syntax error, it's an expression.**
`print(2 + 2)` works. `print(x = 2)` (an assignment) does not — assignment is a statement, not a
value-producing expression. (This is also *why* the walrus operator `:=` exists in section 1.2 —
it's an assignment that *is* an expression, for exactly the cases where you need both.)

**How it works — bottom-up (→ Stage 2 AST, Stage 3 bytecode):**

The parser's grammar has two separate node families: `stmt` (statement) nodes and `expr`
(expression) nodes. This isn't cosmetic — it changes what the compiler emits. Every expression,
once evaluated, leaves exactly one value sitting on the VM's **evaluation stack** (→ Stage 4).
A statement doesn't guarantee that — it's free to just have side effects and leave the stack as it
found it.

```python
import dis

def f():
    x = 1 + 2      # statement (Assign), containing an expression (BinOp) — but 1+2
    return x       # is constant-folded by the compiler before this ever runs

dis.dis(f)
```
Output (Python 3.12):
```
  2           0 LOAD_CONST               1 (3)
              2 STORE_FAST               0 (x)

  3           4 LOAD_FAST                0 (x)
              6 RETURN_VALUE
```
Notice `1 + 2` doesn't even appear as an addition — the compiler (Stage 3) evaluates constant
expressions at *compile time* ("constant folding") and just embeds `3`. This is only possible
because `1 + 2` is a pure expression with no side effects; statements are never folded away like
this because "doing" isn't optional the way "computing a value" is.

**Contrast: a plain expression statement** (an expression used *as* a statement, its value simply
discarded):
```python
def g():
    1 + 2   # a legal statement: evaluate, then throw the result away
```
```
  2           0 LOAD_CONST               1 (3)
              2 POP_TOP        # <-- computed, then immediately discarded
              4 LOAD_CONST               0 (None)
              6 RETURN_VALUE
```
That `POP_TOP` is the tell: the VM computed a value (because it's an expression) and then had to
explicitly throw it away (because, as a *statement*, nothing wanted to keep it). This is precisely
why linters warn about "expression result unused" — you paid for a computation whose value nobody
uses.

---

## 5. Simple vs Compound Statements

**What it is:** Python's grammar splits every statement into one of two families:
- **Simple statements** — fit on one logical line, no colon/block required: `x = 1`, `return x`,
  `import os`, `pass`, `break`, `raise`, `del x`.
- **Compound statements** — introduce a colon `:` and an indented block: `if`, `for`, `while`,
  `def`, `class`, `try`, `with`, `match`.

```python
x = 1; y = 2; print(x, y)     # three SIMPLE statements chained with ;

if x > 0:                      # a COMPOUND statement
    y = 2                      # its body: a block of (here) one simple statement
```

**Why this distinction exists (→ Stage 2, grammar):** it's the reason semicolons (`;`, next
section) can chain `x = 1` and `y = 2` but can *never* chain `if x: y = 1`. The grammar rule for
`;`-separated statements only accepts a list of `simple_stmt`s. A compound statement structurally
*requires* its own `:` + indented-block machinery (→ Section 2's INDENT/DEDENT tokens) — there's no
single-line slot for it to occupy next to a semicolon, because Python has no way to spell "the end
of this block" on the same physical line other than the dedent itself.

```
Grammar sketch (simplified from the real PEG grammar):

  statement       := compound_stmt | simple_stmts
  simple_stmts    := simple_stmt (';' simple_stmt)* [';'] NEWLINE
  compound_stmt    := if_stmt | for_stmt | while_stmt | def | class | try | with | match
```
`simple_stmts` is the only rule that knows about `;` — and `compound_stmt` is never one of the
things it's a list of.

---

## 6. Line Continuation

**What it is:** two ways to spread one *logical* line of code across multiple *physical* lines:

```python
# 1. Implicit continuation: inside (), [], {} — the tokenizer just keeps going
total = (1 + 2
         + 3 + 4)

# 2. Explicit continuation: a backslash at the very end of the physical line
total = 1 + 2 \
        + 3 + 4
```

**How it works — bottom-up (→ Stage 1, the tokenizer):** the tokenizer tracks a running "bracket
depth" counter as it scans characters — incrementing on `(`, `[`, `{` and decrementing on `)`, `]`,
`}`. A `NEWLINE` token (the one that actually ends a *logical* line, as opposed to just a line-feed
byte) is only emitted when bracket depth is **zero**. Inside brackets, physical newlines are
swallowed as insignificant whitespace — that's the entire mechanism; there's no special-casing
per bracket type.

```
Physical bytes:              Tokenizer's bracket-depth counter:      Emits NEWLINE?
total = (1 + 2                depth: 0 → 1 (open paren)                no (depth != 0)
         + 3 + 4)              depth: 1 → 0 (close paren)               yes (depth == 0)
```

The backslash (`\`) mechanism is unrelated and cruder: it's a literal escape recognized by the
tokenizer meaning "the following physical newline byte is not a line break, splice these two
physical lines into one before further tokenizing." No bracket tracking involved — just string
splicing before Stage 1 proper runs.

**Practical guidance:** prefer implicit continuation (parenthesize) — it's why PEP 8 discourages
backslash continuation except where brackets genuinely can't be used (e.g., a long `with` chain
before Python 3.10 added parenthesized `with`). A stray space after a trailing `\` is a syntax
error that's notoriously hard to spot visually, since trailing whitespace is invisible.

---

## 7. Multiple Statements per Line (`;`)

```python
x = 1; y = 2; z = 3
print(x); print(y)
```

**How it works:** as shown in Section 5's grammar sketch, `;` is just the separator inside a
`simple_stmts` production — the parser (Stage 2) builds the exact same list of statement AST nodes
it would from three separate lines. The compiler (Stage 3) then emits the exact same bytecode
sequence either way:

```python
import dis
dis.dis(compile("x = 1; y = 2", "<string>", "exec"))
dis.dis(compile("x = 1\ny = 2", "<string>", "exec"))
```
Both produce identical bytecode — `;` is purely a *textual/lexical* convenience with **zero**
runtime or performance difference from separate lines.

**Why PEP 8 discourages it:** since it changes nothing at the bytecode level, the only effect of
`;` is on human readability — it hides statement boundaries that a line break would make visually
obvious, and hurts diff-friendliness in version control (one line changing now touches what used to
be "two separate lines" worth of logic).

---

## 8. The `print()` Function — Deep Dive

**Surface API:**
```python
print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False)

print("a", "b", "c")                 # a b c
print("a", "b", "c", sep="-")        # a-b-c
print("no newline", end="")          # cursor stays on this line
print("to stderr", file=sys.stderr)  # goes to the error stream, not stdout
print("urgent", flush=True)          # bypass buffering, write immediately
```

**How it works — bottom-up, all the way to the OS (→ Stage 4 and beyond):**

`print()` is a thin convenience wrapper. Tracing one call all the way down:

```
 print("hi", flush=True)
      │
      ▼
 Builds one string: "hi" + end ("\n")           (sep only matters with multiple args)
      │
      ▼
 Calls file.write(that_string)                   file defaults to sys.stdout
      │
      ▼
 sys.stdout is a io.TextIOWrapper                 encodes str -> bytes (using the
      │                                            console's/locale's encoding, e.g. UTF-8)
      ▼
 wraps a io.BufferedWriter                        an in-process memory buffer that
      │                                            batches small writes into fewer,
      │                                            larger OS calls (this is "buffering")
      ▼
 flush=True (or buffer full, or newline           forces the buffer's contents out via
 in line-buffered mode) triggers a flush           a real write() system call
      │
      ▼
 OS kernel                                         kernel copies bytes from your
      │                                            process's memory into its own,
      │                                            queues them for the destination device
      ▼
 Terminal driver / redirected file / pipe          bytes finally become visible
```

**Buffering modes — why `flush` matters in practice:**

| Destination | Default buffering | Practical effect |
|---|---|---|
| A terminal (interactive, `isatty()` true) | **Line-buffered** — flushes automatically on every `\n` | `print()` output appears immediately, one line at a time |
| Redirected to a file or pipe (`python x.py > log.txt`) | **Block-buffered** — only flushes when the buffer fills (several KB) or the process exits | Output can appear to "hang" and show up in bursts, or all at once at exit |

This is exactly why `00_setup_and_tooling.md` (§15) calls out `PYTHONUNBUFFERED=1` for Docker/CI
logs: containers and CI runners capture stdout as a redirected pipe (not a terminal), so Python
silently switches to block-buffering, and log lines can appear minutes late or not until the
process ends. `flush=True` (or the environment variable, which forces unbuffered mode globally)
sidesteps the problem by forcing every write down to the OS immediately.

**Layman version:** buffering is like a mail carrier who doesn't run to your mailbox after every
single letter — they wait until their bag is reasonably full (or their shift ends) to make the
trip. `flush=True` is telling them "no, run this one over right now," at the cost of more trips.

---

## 9. The `input()` Function — Deep Dive

**Surface API:**
```python
name = input("Enter your name: ")   # prints the prompt, then waits
print(f"Hello, {name}")
```

**How it works — bottom-up:**

```
 input("Enter your name: ")
      │
      ▼
 Writes the prompt string to sys.stdout (same path as print(), minus the newline)
      │
      ▼
 Calls sys.stdin.readline()                io.TextIOWrapper around stdin
      │
      ▼
 Blocking read() system call                the OS suspends this process — it does
      │                                     no CPU work at all — until input arrives
      ▼
 Terminal driver, "canonical mode"          the kernel itself buffers your keystrokes
      │                                     line-by-line, handling Backspace/editing,
      │                                     and only hands the completed line to your
      │                                     process's read() once Enter is pressed
      ▼
 Bytes returned to Python, decoded to str, trailing "\n" stripped
      │
      ▼
 Returned as the input() call's value
```

**Two important edge behaviors:**
- **Blocking, not polling:** the process is genuinely suspended by the OS scheduler while waiting —
  it consumes no CPU. This is different from a loop that repeatedly *checks* for input.
- **`EOFError`:** if the input stream is closed with no more data (stdin redirected from a file
  that runs out, or Ctrl+D on Unix / Ctrl+Z+Enter on Windows), `input()` raises `EOFError` instead
  of returning — there's no line to return, and no sentinel string can safely represent "no more
  input" (a real line could equal any string), so Python raises an exception.

```python
try:
    line = input()
except EOFError:
    print("no more input")
```

---

## 10. Naming Conventions & Identifiers

**Identifier grammar (→ Stage 1 tokenizer):** an identifier is a `NAME` token matching (informally)
`[A-Za-z_][A-Za-z0-9_]*`, but Python 3 actually allows **Unicode letters**, not just ASCII (PEP
3131) — `café`, `变量`, and `Δx` are all legal identifiers, though ASCII remains overwhelmingly the
convention for shared/library code.

**PEP 8 casing conventions (a style convention — nothing enforces these at the language level):**

| Convention | Style | Used for |
|---|---|---|
| `snake_case` | lowercase, underscores | variables, functions, methods, modules |
| `PascalCase` | capitalized words, no separators | classes |
| `UPPER_SNAKE_CASE` | uppercase, underscores | constants (`MAX_RETRIES = 5`) |
| `_leading_underscore` | single leading underscore | "internal use" convention (not enforced — see §4.3 of the syllabus for name mangling with `__double`) |
| `dunder__` | double leading + trailing underscore | reserved for the language itself (`__init__`, `__name__`) — **never invent your own** |

**Why identifiers can't be keywords:** the parser (Stage 2) resolves grammar rules by looking at
tokens; if `if` could also be a variable name, the grammar would be ambiguous — every occurrence of
`if` would need extra context to decide "is this the start of a conditional, or someone's variable
called `if`?" Reserving keywords removes that ambiguity entirely at the grammar level, at the cost
of a short, fixed list of words you simply can't use as names.

```python
>>> import keyword
>>> keyword.iskeyword("if")
True
>>> keyword.iskeyword("match")
False        # 'match' is NOT a hard keyword — see the next section
```

---

## 11. Reserved Keywords vs Soft Keywords

**Hard (reserved) keywords** can *never* be used as identifiers, in any context:

```python
>>> import keyword
>>> keyword.kwlist
['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield']
```

**Soft keywords** are ordinary `NAME` tokens most of the time and are only special in the exact
grammar position where the parser expects them — introduced so new syntax (PEP 634 structural
pattern matching, PEP 695 type aliases) didn't have to break every existing program that happened
to use these words as variable names.

```python
>>> keyword.softkwlist
['_', 'case', 'match', 'type']
```

```python
match = 5          # perfectly legal — `match` is just a variable name here
print(match)       # 5

match command:     # here, in statement position followed by ':', it's the match-statement
    case "go":
        print("going")
    case _:
        print("unknown")
```

**How the parser tells them apart (→ Stage 2):** Python's PEG parser (the parsing engine since
3.9, replacing the old LL(1) parser specifically *to allow* soft keywords) can look ahead and try
alternative grammar rules — something the old parser's stricter one-token-lookahead design could
not do cheaply. It attempts to parse `match <expr>:` as a match-statement only in statement
position; if that fails, it falls back to treating `match` as a plain name. This lookahead
flexibility is *why* soft keywords became possible only after the 3.9 parser rewrite — it's not
just a style choice, it required a real internals change to the compiler pipeline.

---

## 12. `pass` and `...` (Ellipsis)

**`pass` — a true no-op statement:**
```python
def not_implemented_yet():
    pass    # do nothing; exists so the block isn't empty (empty blocks are a SyntaxError)

if x > 0:
    pass    # placeholder while you decide what this branch should do
else:
    handle_negative()
```
Every compound statement's body must contain at least one statement — Python's grammar simply has
no rule for "a block with zero statements." `pass` exists purely to satisfy that requirement when
you have nothing else to say. At the bytecode level it compiles to essentially nothing (in most
positions, no instruction is emitted at all — it's an instruction to the *parser*, not the *VM*).

**`...` (Ellipsis) — a real singleton object, not a comment:**
```python
>>> ... 
Ellipsis
>>> type(...)
<class 'ellipsis'>
>>> x = ...
>>> x is ...
True
```
Unlike `pass`, `Ellipsis` is a genuine value — a singleton object, analogous to `None` (which is
also a singleton of its own type `NoneType`). Because it's a real value, it can appear anywhere an
expression can, which `pass` (a statement) cannot:

```python
def stub_function():
    ...     # common in .pyi type-stub files: a placeholder body that IS a value, not a
            # statement — stylistically signals "deliberately unimplemented" (like pass,
            # but by convention reserved for stubs/interfaces rather than "not done yet")

import numpy as np
arr = np.zeros((3, 4, 5))
arr[..., 0]    # Ellipsis used as a real slicing value: "all preceding dimensions, unsliced"
```

**Layman version:** `pass` is a shrug — "nothing to do here, move on," addressed to the *parser*
just so the block isn't empty. `...` is an actual placeholder *token you can hold* — you can assign
it, compare identity against it, pass it as an argument — because underneath it's a real object
sitting in memory with its own type, not merely a syntactic filler.

---

## 13. Source Encoding Declarations

**What it is:** the very first (or second, after a shebang) line of a `.py` file can declare the
byte-encoding of the source file itself:

```python
# -*- coding: utf-8 -*-
café = "espresso"
```

**Why it exists (→ Stage 0, before tokenizing can even begin):** before the tokenizer can turn
bytes into tokens, it has to know how to turn *bytes* into *characters* — is byte `0xC3 0xA9` the
two-byte UTF-8 sequence for `é`, or something else in a different encoding (Latin-1, Shift-JIS)?
PEP 263 introduced the `# -*- coding: xxx -*-` declaration (or the shorter `# coding: xxx`) so a
file's own encoding travels with it instead of depending on the terminal/OS default, which varies
across machines and was a real source of `SyntaxError: invalid character` / mojibake bugs in
mixed-language teams.

**Since Python 3 (PEP 3120): you almost never need this anymore** — **UTF-8 is the default source
encoding** for every `.py` file unless a declaration says otherwise. The declaration still matters
for: (a) legacy files written under Python 2 defaults, (b) the rare case of deliberately using a
non-UTF-8 encoding, (c) making the encoding explicit and self-documenting in files with unusual
characters.

```
Stage 0 (before tokenizing):
  file bytes  ──►  look for coding declaration in first two lines
                        │
                found?  ├── yes → decode using that encoding
                        └── no  → decode using UTF-8 (Python 3 default)
                        │
                        ▼
                   now we have text (str), tokenizer (Stage 1) can begin
```

---

## 14. Adjacent String Literal Concatenation

**What it is:** two or more string literals written next to each other with nothing but whitespace
between them are joined into a single string — **at compile time**, not runtime:

```python
greeting = "Hello, " "World!"     # a single string: "Hello, World!"
long_text = (
    "This is a long message "
    "split across lines "
    "for readability."
)
```

**Why it exists:** it's purely a source-readability feature for breaking up long string literals
(especially combined with implicit line continuation inside parentheses, → Section 6) without
paying the runtime cost of an explicit `+` concatenation, and without needing a line-continuation
backslash inside the string itself.

**How it works — bottom-up (→ Stage 2/3):** the parser recognizes a sequence of adjacent `STRING`
tokens as one literal-concatenation grammar rule and the compiler folds them into a single constant
**before any bytecode runs** — there is no `+` operator call, no runtime string-building at all:

```python
import dis
dis.dis(compile('x = "a" "b" "c"', "<string>", "exec"))
```
```
  0 LOAD_CONST               0 ('abc')     # already joined — one constant, no concatenation op
  2 STORE_NAME               0 (x)
  ...
```
Contrast with actual runtime concatenation `"a" + "b" + "c"`, which (depending on optimization)
can involve real `BINARY_OP`/add instructions executed while the program runs. Adjacent literals
cost *nothing* at runtime because the compiler did the work once, permanently, while producing the
bytecode.

**Gotcha:** this only works for *literals*, never for variables or expressions:
```python
"a" "b"        # OK — concatenated into "ab"
"a" + "b"      # OK — but this is a real (fast, still) runtime addition
x = "a"
x "b"          # SyntaxError — x is not a literal, adjacency only applies to literal STRING tokens
```

---

## 15. `__future__` Imports

**What it is:** a special import form that pulls in a not-yet-default (or formerly different)
language behavior, one release ahead of when it becomes the automatic default:

```python
from __future__ import annotations   # postpone evaluation of type annotations
```

**Why it exists — Python's mechanism for evolving syntax/semantics without breaking every existing
program overnight:** language changes that affect *runtime behavior* (not just new syntax, which
can usually be added freely) are risky to flip on for everyone in one release. `__future__` lets
you opt a single file in early, giving the ecosystem a multi-release transition window before a
behavior becomes mandatory. Historically significant examples:

| Future import | What it changed | Became default in |
|---|---|---|
| `from __future__ import division` | `/` becomes *true* division (`1/2 == 0.5`) instead of floor division | Python 3.0 |
| `from __future__ import print_function` | `print` becomes a function, not a statement | Python 3.0 |
| `from __future__ import unicode_literals` | bare string literals default to Unicode | Python 3.0 |
| `from __future__ import annotations` | annotations (`x: int`) are stored as unevaluated strings, not live objects | still opt-in as of 3.12 (planned default under PEP 563, timeline deferred) |

**How it works (→ Stage 3, compiler flags):** unlike a normal `import`, `__future__` imports don't
just bind names — the compiler recognizes the specific module/name pair and sets an internal
compiler flag for **that source file only**, changing how the compiler itself translates subsequent
code in the file into bytecode. It must be the first statement in the file (other than the module
docstring) precisely because it has to take effect before *anything else* in that file gets
compiled.

**Layman version:** it's an opt-in preview toggle — "compile *this file* as if a future Python
version's rule were already active," so you (and the whole ecosystem) can migrate gradually instead
of everyone's code breaking the instant a new Python version ships.

---

## 16. Cheat Sheet: Common Syntax Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `TabError: inconsistent use of tabs and spaces` | Mixed tabs/spaces that render the same but differ in raw bytes | Configure your editor to insert spaces for Tab; never hand-mix (→ Section 2) |
| `IndentationError: unexpected indent` / `unindent does not match any outer indentation level` | A line's indentation doesn't match any width on the tokenizer's indent stack | Fix the whitespace to align exactly with an enclosing block's level |
| Output "hangs" then appears all at once when run in Docker/CI, but is instant in a terminal | stdout is block-buffered when redirected to a pipe/file, not line-buffered | Use `print(..., flush=True)` or set `PYTHONUNBUFFERED=1` (→ Section 8) |
| `EOFError` from `input()` in a script run with input redirected from a file | The redirected file ran out of lines | Wrap in `try/except EOFError`, or check you're not accidentally piping an empty/short file |
| `SyntaxError` on a line that "looks fine", right after a line ending in `\` | Trailing whitespace *after* the backslash (invisible in most editors) | Enable "show whitespace" in your editor; prefer parenthesized continuation instead (→ Section 6) |
| A variable named `match`, `type`, `case`, or `_` behaves oddly in one specific spot | You've hit the exact grammar position where a soft keyword is being parsed as the keyword, not your variable | Rename the variable, or move the code so it's unambiguous (→ Section 11) |
| Docstring seems to "disappear" | It wasn't the *first* statement in the block (e.g., a `pass` or import came before it) | Only the first statement in a module/class/function body becomes `__doc__` (→ Section 3) |
| `SyntaxError: invalid character` on non-ASCII text from an old/legacy file | Missing or wrong source-encoding declaration on a non-UTF-8 file | Add `# -*- coding: utf-8 -*-` (or re-save the file as UTF-8) (→ Section 13) |

---

## 17. Quick-Reference Checklist

Use this whenever you're unsure whether a piece of code is "idiomatic Python" at the syntax level:

1. Is this block's indentation **exactly 4 spaces**, consistently, with no tabs? (→ Section 2)
2. Are comments used for things a reader needs explained, and docstrings used for anything another
   piece of code might introspect (`help()`, IDE tooltips)? (→ Section 3)
3. Am I confusing a statement for an expression anywhere (e.g., trying to use an assignment where a
   value is expected)? Would the walrus `:=` be more appropriate? (→ Section 4)
4. Are semicolons (`;`) used sparingly, if at all — only for the rare case of two truly trivial
   simple statements together? (→ Section 7)
5. If this script's output is meant to be watched live (logs, CI), does it need `flush=True` or
   `PYTHONUNBUFFERED=1`? (→ Section 8)
6. Do all names follow PEP 8 casing (`snake_case` functions/variables, `PascalCase` classes,
   `UPPER_SNAKE_CASE` constants)? (→ Section 10)
7. Am I accidentally shadowing a soft keyword (`type`, `match`, `case`, `_`) in a way that will
   confuse a future reader, even if the parser handles it fine? (→ Section 11)
8. Is `...` used deliberately (stub files, slicing) rather than as a lazy substitute for writing
   real code? (→ Section 12)
9. Does this file need an explicit encoding declaration, or is plain UTF-8 (the default) enough?
   (→ Section 13)
10. For any long string, would adjacent-literal concatenation read better than one long unwrapped
    line or an explicit `+`? (→ Section 14)
