# 1.4 Control Flow — Complete Deep-Dive Guide

This is the companion reference for **Section 1.4** of [`python_full_syllabus.md`](python_full_syllabus.md).
Same format as [`01_1_syntax_basics.md`](01_1_syntax_basics.md),
[`01_2_variables_and_data_types.md`](01_2_variables_and_data_types.md), and
[`01_3_operators.md`](01_3_operators.md): every bullet explained surface-first, then pushed down to
what the CPython VM is actually doing — this time, that means **jumps**. Control flow is, at bottom,
entirely about the VM's instruction pointer moving somewhere other than "the next instruction" —
every construct in this document is a different flavor of that one mechanism.

---

## Table of Contents

1. [The Big Picture: Control Flow Is Just Conditional Jumps](#1-the-big-picture-control-flow-is-just-conditional-jumps)
2. [`if` / `elif` / `else`](#2-if--elif--else)
3. [Conditional Expressions (Ternary)](#3-conditional-expressions-ternary)
4. [`while` Loops & the Loop `else` Clause](#4-while-loops--the-loop-else-clause)
5. [`for` Loops & the Hidden Iterator Protocol](#5-for-loops--the-hidden-iterator-protocol)
6. [`range()` Deep Dive](#6-range-deep-dive)
7. [Common Iteration Idioms: `enumerate()`, `zip()`, `reversed()`](#7-common-iteration-idioms-enumerate-zip-reversed)
8. [`break`, `continue`, and Loop `else` — How They Interact](#8-break-continue-and-loop-else--how-they-interact)
9. [Nested Loops & the Absence of Labeled Break](#9-nested-loops--the-absence-of-labeled-break)
10. [Loop Variable Scope Leakage](#10-loop-variable-scope-leakage)
11. [Structural Pattern Matching: `match` / `case`](#11-structural-pattern-matching-match--case)
12. [Cheat Sheet: Common Gotchas](#12-cheat-sheet-common-gotchas)
13. [Quick-Reference Checklist](#13-quick-reference-checklist)

---

## 1. The Big Picture: Control Flow Is Just Conditional Jumps

**The unifying idea:** CPython bytecode (→ 1.1 Stage 3/4) is a flat array of instructions executed
one after another, top to bottom, by default — the "program counter" (instruction pointer) simply
increments. Every control-flow construct in Python — `if`, `while`, `for`, `break`, `continue`,
`match` — compiles down to exactly one primitive idea: **an instruction that can move the program
counter somewhere other than "the very next instruction," sometimes unconditionally, sometimes only
if a condition holds.**

```
 Normal execution (no control flow):        With a conditional jump (e.g. an `if`):

  instr 0                                    instr 0
  instr 1                                    instr 1: POP_JUMP_IF_FALSE -> instr 4   (test failed? skip ahead)
  instr 2   <- PC just increments,           instr 2: (body of the if)
  instr 3      one instruction at a time      instr 3: JUMP_FORWARD -> instr 5        (skip the else)
                                              instr 4: (body of the else)
                                              instr 5: (continues normally)
```

Every construct below is characterized here by **which jump instruction(s) it compiles to** and
**which direction they point** — forward jumps implement "skip this branch" (`if`/`else`), backward
jumps implement "go back and do this again" (`while`/`for` loops). Keep this one picture in mind —
it's the same anchoring device 1.1's tokenizer pipeline and 1.3's dunder-dispatch diagram serve for
their sections.

**Layman version:** think of bytecode as a to-do list read top to bottom. Most control-flow keywords
are really just sticky notes that say "if such-and-such, skip down to item #12 instead" (a forward
jump) or "once you reach the bottom, go back up to item #3 and read again" (a backward jump — a
loop). Nothing more mysterious is happening underneath any of `if`, `while`, or `for`.

---

## 2. `if` / `elif` / `else`

**What it is:** run one block among several alternatives, based on which condition (if any) is
truthy first — evaluated top to bottom, stopping at the **first** truthy condition.

```python
x = 5
if x < 0:
    print("negative")
elif x == 0:
    print("zero")
else:
    print("positive")
```

**How it works — bottom-up:** `elif` is not a separate bytecode concept — it's pure syntactic sugar
for a **nested** `if` inside the `else` block. The parser desugars `if / elif / elif / else` into
`if / else: if / else: if / else: ...`, arbitrarily deep, before it ever reaches the compiler:

```
 if a:            if a:
     A                A
 elif b:    ==>   else:
     B                if b:
 else:                    B
     C                else:
                            C
```

```python
import dis
dis.dis(compile("if a:\n x=1\nelif b:\n x=2\nelse:\n x=3", "<string>", "exec"))
```
```
  0 LOAD_NAME     0 (a)
  2 POP_JUMP_IF_FALSE  4      # a falsy? -> jump ahead to check b
  4 LOAD_CONST    0 (1)
  6 STORE_NAME    1 (x)
  8 JUMP_FORWARD  16          # skip past every remaining branch once a taken branch finishes
 10 LOAD_NAME     2 (b)
 12 POP_JUMP_IF_FALSE  16     # b falsy? -> jump ahead to the else body
 14 LOAD_CONST    1 (2)
 ...
```
(Exact opcode names/offsets vary across Python versions, but the shape — a chain of
"test, conditionally skip" jumps, with each taken branch finishing by jumping past all the rest — is
stable.) This directly explains why **only one branch ever runs**: each branch's own code ends with
an unconditional jump straight past every other branch, so there's no way to "fall through" into the
next one the way some other languages' `switch` can.

**Truthiness recap:** the condition in `if`/`elif` doesn't have to be a literal `bool` — it's passed
through the same `bool()` coercion covered in `01_2_variables_and_data_types.md` §5 (calls
`__bool__`, then `__len__`, then defaults to `True`). `if my_list:` and `if len(my_list) > 0:` are
equivalent for exactly this reason.

---

## 3. Conditional Expressions (Ternary)

**What it is:** `x if cond else y` — a single **expression** (→ 1.1 §4, statements vs expressions)
that evaluates to one of two values, usable anywhere a value is expected (inside a function call, a
list, an f-string) — unlike a full `if` statement, which cannot appear there.

```python
age = 20
status = "adult" if age >= 18 else "minor"     # a value, assignable in one line

# Only ONE side is ever evaluated — this is short-circuiting, same spirit as `and`/`or` (→ 1.3 §4)
print("yes" if True else 1 / 0)     # "yes" — the 1/0 branch never runs, so no ZeroDivisionError
```

**How it works — bottom-up:** compiles to the *same* jump-based shape as an `if`/`else` statement —
a conditional jump choosing which of two `LOAD_CONST`/expression-evaluating instruction sequences to
execute — with one difference: both branches funnel into leaving **exactly one value** on the
evaluation stack afterward, because (unlike a statement) an expression is required to produce a
value (→ 1.1 §4).

```python
import dis
dis.dis(compile("x = 'a' if cond else 'b'", "<string>", "exec"))
```
```
  0 LOAD_NAME      0 (cond)
  2 POP_JUMP_IF_FALSE   4
  4 LOAD_CONST     0 ('a')
  6 JUMP_FORWARD   2
  8 LOAD_CONST     1 ('b')
 10 STORE_NAME     1 (x)
```
Structurally identical to the `if`/`else` statement's bytecode from Section 2 — the only real
difference is that a full `if` statement is free to have side effects and produce no value at all,
while the ternary is required to always leave one value behind for `STORE_NAME` to consume.

**Layman version:** a ternary is an `if`/`else` squeezed onto one line specifically because you need
its *result*, not just its *side effects* — exactly the same "expressions produce values, statements
don't have to" distinction from Section 1.1.

---

## 4. `while` Loops & the Loop `else` Clause

**What it is:** repeat a block for as long as a condition stays truthy, re-checking the condition
**before** every iteration (including the very first).

```python
n = 3
while n > 0:
    print(n)
    n -= 1
print("done")
```

**How it works — bottom-up (the backward jump):**
```
 instr 0: LOAD n; LOAD 0; COMPARE (>)
 instr 1: POP_JUMP_IF_FALSE -> instr 5      (condition false? -> exit the loop)
 instr 2: (loop body: print(n))
 instr 3: (n -= 1)
 instr 4: JUMP_BACKWARD -> instr 0           (unconditional: go re-check the condition)
 instr 5: (code after the loop)
```
The defining feature of `while` versus `if` is exactly this **backward** jump at the bottom of the
body — it's the one new ingredient that turns "maybe skip this once" into "repeat this."

**The loop `else` clause — a genuinely Python-specific, frequently-misunderstood feature:** the
`else` block after a `while` (or `for`) runs **if and only if the loop finished normally — i.e., the
condition became falsy on its own, without ever hitting a `break`.**

```python
n = 10
while n != 0:
    if n == 5:
        break
    n -= 1
else:
    print("loop completed without break")     # will NOT print — we broke out at n == 5

print("after loop")
```

**Why this exists — the "search" idiom it was designed for:** before this feature, checking "did the
loop find what it was looking for, or did it just run out?" required a separate flag variable set
right before the `break`. The loop `else` clause makes that flag implicit:
```python
target = 7
numbers = [1, 3, 5, 9]

for n in numbers:
    if n == target:
        print("found it")
        break
else:
    print("not found — loop ran to completion without breaking")   # this DOES print here
```

```
 Mental model:  "else" here does NOT mean "if the loop condition was false" (that's every normal
 exit) — read it as "no-break": the block that runs only when NO break statement fired.
```

**Layman version:** think of the loop's `else` as a **"did I have to bail out early?" report card** —
it only gets filled in if you made it through the entire loop on your own terms, never if you jumped
out the emergency exit (`break`) partway through.

---

## 5. `for` Loops & the Hidden Iterator Protocol

**What it is, on the surface:** `for item in iterable: ...` runs the body once per element of
`iterable`, in order.

**What it actually is, underneath — a `for` loop is 100% syntactic sugar over `while` + the iterator
protocol.** Every `for` loop is mechanically equivalent to this hand-written expansion:

```python
# for item in iterable:
#     body

_it = iter(iterable)            # step 1: get an ITERATOR from the iterable (calls __iter__)
while True:
    try:
        item = next(_it)         # step 2: pull ONE value at a time (calls __next__)
    except StopIteration:         # step 3: the iterator signals "no more values" by raising this
        break                      #         (NOT a normal return value — an exception is the signal)
    body
```

(The full protocol — `__iter__`/`__next__`, writing your own iterators/generators, `StopIteration`
semantics — gets its complete treatment in **syllabus section 3.5**; this section's job is just to
show that a `for` loop is *nothing more* than this expansion, wired directly into the bytecode.)

**How it works — bottom-up, the real bytecode (not just a hand-simplified version):** CPython has
two dedicated opcodes purpose-built for exactly this pattern, `GET_ITER` and `FOR_ITER`, so the
interpreter doesn't have to re-derive "call iter, then loop calling next, catch StopIteration" from
generic pieces every single time — it's a fast, direct VM-level primitive:

```python
import dis
dis.dis(compile("for x in y:\n print(x)", "<string>", "exec"))
```
```
  0 LOAD_NAME      0 (y)
  2 GET_ITER                          # calls iter(y) once, up front
  4 FOR_ITER       8 (to instr 14)    # calls next() each pass; on StopIteration, jumps PAST the loop
  6 STORE_NAME     1 (x)
  8 LOAD_NAME      2 (print)
 10 LOAD_NAME      1 (x)
 12 CALL_FUNCTION  1
 14 JUMP_BACKWARD  4                  # go back to FOR_ITER for the next element
 16 ...                               # code after the loop (FOR_ITER jumped straight here at StopIteration)
```
`FOR_ITER` bundles "call `next()`, and if it raises `StopIteration`, jump past the loop entirely"
into a single instruction — this is *why* a `for` loop never needs to write an explicit
`try/except StopIteration` yourself; the VM is doing that catch for you, once, as part of the
primitive.

**Why this matters practically:** because `for` only ever asks an object for "give me one iterator,
then give me values one at a time," it works identically on a `list` (which builds its iterator on
the spot), a `dict` (iterates keys), a file object (iterates lines), a `range` (→ Section 6, computes
values on the fly), or a hand-written generator (→ 3.5) — the `for` statement itself never needs to
know or care which kind of object it's looping over. This uniform interface is precisely what "duck
typing" (→ 4.2) looks like at the control-flow level.

**Layman version:** a `for` loop doesn't actually know how to walk through a list, a file, or a
range — it only knows one trick: "hand me your iterator, then keep handing me items one at a time
until you tell me you're out." Every iterable object just has to know how to play that one game;
the `for` loop's job is identical no matter who it's playing with.

---

## 6. `range()` Deep Dive

**What it is:** `range(start, stop, step)` produces a sequence of integers — but critically, **not**
by building a list of them in memory. `range` is its own type: a compact object that stores only
three numbers (`start`, `stop`, `step`) and computes each value **on demand** as it's asked for one.

```python
r = range(0, 10_000_000, 1)
print(r)                 # range(0, 10000000) — nothing has been "generated" yet
import sys
print(sys.getsizeof(r))   # a small, FIXED number of bytes — same size whether the range has 3 or 3 billion elements
print(sys.getsizeof(list(range(10_000_000))))   # dramatically larger — an actual list of 10 million int objects
```

```
 range(0, 5) in memory:            list(range(0, 5)) in memory:

 ┌───────────────────┐             ┌────┬────┬────┬────┬────┐
 │ start=0            │             │ 0  │ 1  │ 2  │ 3  │ 4  │   <- 5 separate int objects
 │ stop=5             │             └────┴────┴────┴────┴────┘      (or pointers to the small-int
 │ step=1             │                                              cache, → 01_2 §3), all in memory
 └───────────────────┘             AT ONCE
 (fixed-size, O(1) memory,
  regardless of the range's length)
```

**Why this matters (→ 1.2 §6.2, arbitrary precision; → 3.5, lazy evaluation preview):** iterating
`for i in range(10_000_000):` never materializes ten million `int` objects up front — each value is
computed (`start + i * step`) exactly when `FOR_ITER`/`next()` asks for it (→ Section 5), then
discarded once the loop body moves on. This is the same "compute lazily, one at a time" philosophy
that generators (3.5) generalize into a full language feature — `range` is really the simplest
possible example of it, built into the language from the start.

**Full call signature and negative steps:**
```python
range(5)              # 0, 1, 2, 3, 4          — stop only; start defaults to 0, step to 1
range(2, 8)            # 2, 3, 4, 5, 6, 7        — start and stop; stop is EXCLUSIVE
range(0, 10, 2)         # 0, 2, 4, 6, 8           — every 2nd value
range(10, 0, -1)         # 10, 9, 8, ..., 1        — counting down; step must be negative to go backward
range(5, 5)               # empty — start == stop produces zero elements, not an error
```
`range` also supports `len()`, indexing (`range(10)[3]`), and `in` membership — all computed via
simple arithmetic (no scanning required), because with just `start`/`stop`/`step` known, "is x in
this range?" and "what's the 3rd element?" are both O(1) math problems, not searches.

---

## 7. Common Iteration Idioms: `enumerate()`, `zip()`, `reversed()`

These aren't new control-flow syntax — they're ordinary functions that return iterables/iterators,
which then plug into the exact `for` mechanism from Section 5. They exist to eliminate common
manual-indexing patterns that are easy to get subtly wrong.

**`enumerate()` — get the index and the value together, without a manual counter:**
```python
fruits = ["apple", "banana", "cherry"]

# Manual, error-prone way:
i = 0
for fruit in fruits:
    print(i, fruit)
    i += 1

# Idiomatic way — enumerate() yields (index, value) tuples, unpacked directly in the for-target:
for i, fruit in enumerate(fruits):
    print(i, fruit)

for i, fruit in enumerate(fruits, start=1):    # start counting from 1 instead of 0
    print(i, fruit)
```

**`zip()` — walk multiple iterables in lockstep, stopping at the shortest:**
```python
names = ["Alice", "Bob"]
ages = [30, 25, 99]      # note: longer than names

for name, age in zip(names, ages):
    print(name, age)
# Alice 30
# Bob 25
# (99 is silently never reached — zip() stops as soon as ANY input runs out)
```
`zip()` is itself just an iterator implementing the same protocol from Section 5 — internally it
calls `next()` on *every* input iterator each pass and stops the instant any single one raises
`StopIteration`. (`itertools.zip_longest`, syllabus 3.5, is the variant that pads shorter inputs
instead of truncating.)

**`reversed()` — iterate backward without manually reconstructing indices:**
```python
for fruit in reversed(fruits):
    print(fruit)         # cherry, banana, apple
```
`reversed()` requires the object to support either `__reversed__` or both `__len__`/`__getitem__` —
it doesn't work on arbitrary one-way iterators (like a generator) the way `for` itself does, because
walking backward needs to know "how many elements are there," which lazy, forward-only iterators
don't inherently provide.

**Unpacking while iterating — combining `for` with tuple unpacking (→ 1.2 §12):**
```python
prices = {"apple": 1.5, "banana": 0.5}

for name, price in prices.items():     # each iteration step hands back a (name, price) tuple,
    print(f"{name}: ${price}")           # immediately unpacked into two loop variables
```
This works because `dict.items()` yields 2-tuples, and the `for` target list `name, price` is just
an ordinary unpacking assignment target (→ 1.2 §12) applied fresh on every single iteration.

---

## 8. `break`, `continue`, and Loop `else` — How They Interact

**`break` — exit the loop immediately, skipping the rest of the body AND any remaining iterations:**
```python
for n in range(10):
    if n == 3:
        break
    print(n)          # prints 0, 1, 2, then stops entirely
```
Bytecode-wise, `break` is simply an unconditional jump straight to the first instruction **after**
the entire loop — bypassing both the rest of the current body and the loop's own backward jump.

**`continue` — skip straight to the next iteration, without exiting the loop:**
```python
for n in range(5):
    if n % 2 == 0:
        continue
    print(n)          # prints 1, 3 — even numbers are skipped, but the loop keeps going
```
`continue` jumps to the loop's *re-check* step (the condition test for `while`, or `FOR_ITER`'s next
`next()` call for `for`) — it does **not** skip the loop's own advancement logic (a `while` loop's
counter still needs updating before `continue`, or you'll spin forever, since `continue` jumps to
the *condition check*, not to a magical "increment and check" combo).

```
 while n < 5:              while n < 5:
     if n == 2:                 n += 1          # placed BEFORE the check-and-continue
         n += 1                 if n == 3:
         continue                   continue
     print(n)                   print(n)
     n += 1                 # <- correct pattern: advance the loop variable BEFORE any `continue`,
                             #    or the condition never changes and you get an infinite loop
```

**Loop `else` and `break` — the interaction spelled out precisely (recap of Section 4):** the `else`
block is skipped **entirely** if a `break` fires anywhere in the loop, no matter how many iterations
ran first. It runs only on the path where the loop's own condition (or the iterator's exhaustion)
ended things naturally.

---

## 9. Nested Loops & the Absence of Labeled Break

**What it is:** loops inside loops, iterating in lockstep with the outer structure:
```python
for i in range(3):
    for j in range(3):
        print(i, j)
```

**The gap many languages don't have: Python has no `goto`, and no labeled `break`/`continue`.** In
Java/C/JavaScript you can write `break outerLoop;` to escape two levels at once directly. Python's
`break` **always** exits only the single innermost loop it's textually inside — there is no syntax
to name an outer loop and jump to it directly. This is a deliberate design choice (Python's designers
consider `goto`-like jumps a source of hard-to-follow control flow, per PEP 20's "flat is better than
nested, explicit is better than implicit" spirit) — but it means breaking out of nested loops needs
one of a few standard workarounds:

**Workaround 1 — a flag variable:**
```python
found = False
for i in range(3):
    for j in range(3):
        if i == j == 1:
            found = True
            break
    if found:
        break
```

**Workaround 2 — extract the nested loops into a function and use `return` (often the cleanest):**
```python
def find_pair():
    for i in range(3):
        for j in range(3):
            if i == j == 1:
                return i, j     # return unwinds out of BOTH loops at once, cleanly
    return None

result = find_pair()
```

**Workaround 3 — raise and catch a sentinel exception** (rare, but shows exceptions are also just
another form of "jump," this time one that unwinds an arbitrary number of stack frames at once, →
syllabus 5.1):
```python
class _Found(Exception):
    pass

try:
    for i in range(3):
        for j in range(3):
            if i == j == 1:
                raise _Found()
except _Found:
    pass
```

**Workaround 4 — flatten the nested loop with `itertools.product` (→ syllabus 3.5), turning two
loops into one:**
```python
import itertools
for i, j in itertools.product(range(3), range(3)):
    if i == j == 1:
        break     # now there's only ONE loop, so a plain break already does the whole job
```

**Layman version:** most languages give you a fire escape door on every floor labeled with the floor
number, so you can jump straight to floor 2 from floor 5. Python only gives you the door on the floor
you're currently standing on — to get out further, you either climb down normally checking a flag
each floor (workaround 1), leave the whole building through `return` (workaround 2), pull the fire
alarm and let everyone evacuate via the exception path (workaround 3), or redesign the building so
it's a single floor to begin with (workaround 4).

---

## 10. Loop Variable Scope Leakage

**What it is — a fact that surprises people coming from block-scoped languages (C, Java, JavaScript's
`let`):** the variable(s) a `for` loop assigns on each iteration are **not** confined to the loop's
body. They live in whatever scope the `for` statement itself is in (the enclosing function or module
namespace, → `01_2_variables_and_data_types.md` §1), and they **keep their final value** after the
loop finishes:

```python
for i in range(5):
    pass

print(i)     # 4 — i is still alive and holds its LAST value, completely accessible after the loop
```

**Why — bottom-up (→ 1.2 §1, §2, and 3.2's LEGB preview):** Python has exactly four kinds of scope —
Local, Enclosing, Global, Built-in — and **none of them is "the body of a loop" or "the body of an
`if`."** Only `def` (functions), `class` bodies, and modules create a new namespace; a `for`/`while`
loop is just more statements inside whatever namespace already contains it. The loop-target
assignment (`i = next(_it)`, from Section 5's expansion) is an ordinary name-binding, in the ordinary
enclosing namespace — there's no special "loop-local" namespace for it to be confined to.

```
 What DOES create a new scope:      What does NOT create a new scope:
   def f(): ...                       for x in ...: ...
   class C: ...                       while cond: ...
   (module level itself)              if cond: ...
                                       with ... as x: ...   (x also leaks, same reason)
```

**Why this matters practically — an empty-iterable trap:**
```python
for item in []:
    last = item
print(last)     # NameError! the loop body never ran even once, so `last` was never bound at all
```
Because the loop variable is just a regular name in the surrounding scope, if the loop body never
executes (empty iterable), the name is never created — it isn't pre-declared with some default value
the way a block-scoped language might do.

**This same fact is what causes the closures "late-binding" gotcha** (full treatment in syllabus
3.2) — a function defined inside a loop that references the loop variable captures the *name*, not a
per-iteration snapshot, and since the name isn't loop-scoped, every such function ends up seeing
whatever value the shared name held when they're finally *called*, typically the last one.

**Layman version:** in many languages, a loop hands you a brand-new, disposable nametag each lap,
thrown away at the finish line. Python hands you one nametag for the entire race and just keeps
re-writing the number on it each lap — after the race ends, whoever's holding that nametag still
sees whatever number was written on it last.

---

## 11. Structural Pattern Matching: `match` / `case`

**What it is (PEP 634, Python 3.10+):** a statement that compares one **subject** value against a
series of **patterns**, top to bottom, running the body of the first pattern that matches — while
also, unlike a plain `if`/`elif` chain, being able to **destructure** the subject (pull it apart into
named pieces) as part of matching.

```python
def handle(command):
    match command:
        case "quit":
            return "exiting"
        case ["move", direction]:
            return f"moving {direction}"
        case {"action": "attack", "target": target}:
            return f"attacking {target}"
        case _:
            return "unknown command"
```

**Critically important mental model: `match` is NOT a C-style `switch` (no jump table, no hashing,
no O(1) dispatch).** It is evaluated as a genuinely **sequential top-to-bottom** series of pattern
checks, exactly like an `if`/`elif` chain — the first matching `case` wins, and later ones are never
even examined:

```
 match subject:
     case P1: A       ≈ (conceptually)      if <subject matches P1>: A
     case P2: B                              elif <subject matches P2>: B
     case _: C                               else: C
```
This is *why* there's no `break` needed (unlike C's `switch`, where forgetting `break` causes
fall-through) — exactly one `case` body ever executes, by construction, same as `if`/`elif`/`else`.
It also means, performance-wise, matching against many `case`s is O(n) in the number of cases in the
worst case, not the O(1) a hash-based dispatch table could offer — pattern matching optimizes for
*expressiveness and destructuring*, not dispatch speed.

**Pattern kinds, each explained:**

```python
# Literal pattern — matches an exact value (like a plain ==)
match status_code:
    case 200:
        print("OK")
    case 404:
        print("Not Found")

# Capture pattern — a bare name ALWAYS matches, and binds the subject to that name
match value:
    case n:              # matches ANYTHING, binds it to `n` — very different from a literal!
        print(f"got {n}")

# Wildcard `_` — matches anything, like a capture pattern, but binds NOTHING (a true "don't care")
match value:
    case _:
        print("catch-all, no binding created")

# Sequence pattern — destructures list/tuple-like subjects by position, with * for "the rest"
match point:
    case (0, 0):
        print("origin")
    case (x, 0):
        print(f"on the x-axis at {x}")
    case (x, y):
        print(f"at ({x}, {y})")
    case [first, *rest]:            # star-unpacking (→ 1.2 §12) works inside patterns too
        print(first, rest)

# Mapping pattern — destructures dict-like subjects by key; EXTRA keys are ignored unless you capture them
match config:
    case {"mode": "debug", **extras}:
        print("debug mode, plus:", extras)
    case {"mode": mode}:
        print(f"mode is {mode}")

# Class pattern — matches an instance's TYPE, and destructures its attributes
class Point:
    __match_args__ = ("x", "y")     # <-- controls what POSITIONAL patterns map to (see below)
    def __init__(self, x, y):
        self.x, self.y = x, y

match p:
    case Point(x=0, y=0):            # keyword-style class pattern — always works, no __match_args__ needed
        print("origin")
    case Point(0, 0):                 # POSITIONAL-style — requires __match_args__ to know x is 1st, y is 2nd
        print("origin (positional)")
    case Point(x, y):
        print(f"point at {x}, {y}")

# Guard — an extra `if` condition, only checked once the pattern itself already matched
match point:
    case Point(x, y) if x == y:
        print("on the diagonal")

# OR pattern — try several patterns, use whichever matches first
match command:
    case "quit" | "exit" | "q":
        print("goodbye")
```

**`__match_args__` explained — why `Point(0, 0)` (positional) needs it but `Point(x=0, y=0)`
(keyword) doesn't:** a class pattern with **positional** sub-patterns has no way to know, just from
looking at the class, which attribute corresponds to "position 0" versus "position 1" — attributes on
an instance are stored in an unordered `__dict__` (→ 1.2 §1), not in any fixed order. `__match_args__`
is a class-level tuple of attribute names that explicitly declares that order (`dataclasses`, →
syllabus 4.5, generate this automatically from field order — this is exactly why `dataclass`
instances support positional `case` patterns "for free," while plain classes need to opt in
explicitly).

**How it works — bottom-up:** the compiler doesn't have one universal "pattern matching bytecode
instruction" — each pattern kind lowers to the combination of primitives that already exist
elsewhere in this document: a literal pattern compiles to an equality comparison (→ 1.3 §3); a
sequence pattern compiles to a `len()` check plus indexing/unpacking (→ 1.2 §12); a class pattern
compiles to an `isinstance()` check (→ 1.2 §7) followed by attribute lookups guided by
`__match_args__`; a guard compiles to an ordinary conditional jump (→ Section 2) evaluated only after
the pattern's own checks pass. **Structural pattern matching's real contribution is syntax that
composes and sequences all of these existing mechanisms conveniently — it is not a new execution
primitive at the VM level**, in the same way `elif` (Section 2) wasn't a new primitive either, just a
convenient way to compose existing ones.

**One more syntax note (→ 1.1 §11):** `match` and `case` are **soft keywords** — this is precisely
why the very first line of every example above still works fine if you have an unrelated variable
literally named `match` elsewhere in your code; the parser only treats `match ...:` specially in
statement position followed by a colon and `case` blocks, exactly as `01_1_syntax_basics.md` §11
describes for soft keywords generally.

---

## 12. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| A variable used after a `for`/`while` loop has an unexpected leftover value, or a `NameError` | Loop variables aren't block-scoped — they live in the enclosing scope and persist after the loop (or never get created if the loop body never ran) | Don't rely on a loop variable's post-loop value unless that's deliberate; initialize a fallback before the loop if the iterable might be empty (→ Section 10) |
| A closure defined inside a loop always "sees" the same (usually last) value of the loop variable | The classic late-binding closure gotcha — every closure shares the same enclosing-scope name, not a per-iteration snapshot (→ Section 10, full treatment in syllabus 3.2) | Capture the current value via a default argument (`def f(x=x): ...`) or `functools.partial` |
| `continue` inside a hand-rolled `while` loop causes an infinite loop | The loop's own increment/advance step was placed *after* the `continue`, so it's skipped every time `continue` fires | Advance the loop's condition variable *before* any `continue` check (→ Section 8) |
| Trying to `break` out of two nested loops only exits the inner one | Python has no labeled `break`/`goto` — `break` always targets only the innermost enclosing loop | Use a flag variable, extract to a function and `return`, or flatten with `itertools.product` (→ Section 9) |
| A loop's `else` block runs (or doesn't) unexpectedly | Loop `else` means "the loop finished without hitting `break`" — it is NOT tied to the loop condition being false in the usual sense, and is skipped entirely if `break` ever fires | Read `else` here as "no-break", not "otherwise" (→ Sections 4, 8) |
| `range(10_000_000)` seems to use almost no memory, but `list(range(10_000_000))` does | `range` is a lazy O(1)-memory object computing values on demand; `list(...)` forces every value to be materialized as a real object up front | Prefer iterating a bare `range()` directly unless you truly need list operations (indexing all at once, repeated random access, mutation) (→ Section 6) |
| `Point(0, 0)` fails to match positionally in a `match` statement even though `Point(x=0, y=0)` works | The class has no `__match_args__`, so positional class patterns have no declared attribute order to use | Define `__match_args__ = (...)` explicitly, or use a `@dataclass` (auto-generates it), or just match by keyword (→ Section 11) |
| Expecting `match` to dispatch like a fast C `switch`/jump table | `match` is sequential top-to-bottom pattern testing under the hood, not hash-based dispatch | Fine for readability/destructuring; don't assume O(1) behavior for very large numbers of `case`s on a hot path (→ Section 11) |

---

## 13. Quick-Reference Checklist

Use this whenever you're reasoning about a control-flow construct in Python:

1. Am I thinking of `if`/`while`/`for` as literally "jumps in a flat instruction list," which
   explains why `elif` chains stop at the first match and why loops need a backward jump to repeat?
   (→ Section 1)
2. If I need a *value*, not just a branching side effect, would a ternary expression be more
   appropriate than a full `if`/`else` statement? (→ Section 3)
3. Do I understand that a `for` loop is just `iter()` + repeated `next()` + catching `StopIteration`,
   which is why it works uniformly across lists, dicts, files, and generators? (→ Section 5)
4. Am I materializing a `range()` into a `list` unnecessarily, when the lazy `range` object itself
   would do? (→ Section 6)
5. Could a manual index-counting loop be replaced with `enumerate()`, and could parallel manual
   indexing across two lists be replaced with `zip()`? (→ Section 7)
6. If using `continue` in a `while` loop, is the loop's advancement step guaranteed to run before it?
   (→ Section 8)
7. Am I trying to break out of nested loops — and if so, have I picked one of the standard
   workarounds (flag, function+return, exception, flattening) rather than assuming a labeled break
   exists? (→ Section 9)
8. Do I rely on a loop variable's value after the loop ends — and if the iterable could be empty,
   have I guarded against a `NameError`? (→ Section 10)
9. If using `match`/`case`, do I know whether each `case` is a capture pattern (matches anything,
   binds a name) versus a literal pattern (matches only an exact value) — these look superficially
   similar but behave very differently? (→ Section 11)
10. For class patterns, have I defined `__match_args__` (or used `@dataclass`) if I want positional
    matching to work, rather than assuming Python can infer attribute order? (→ Section 11)
