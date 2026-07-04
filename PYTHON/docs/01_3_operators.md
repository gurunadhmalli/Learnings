# 1.3 Operators — Complete Deep-Dive Guide

This is the companion reference for **Section 1.3** of [`python_full_syllabus.md`](python_full_syllabus.md).
Following the same format as [`01_1_syntax_basics.md`](01_1_syntax_basics.md) and
[`01_2_variables_and_data_types.md`](01_2_variables_and_data_types.md): every bullet is explained
surface-first (what you type, what it means) and mechanism-second (what CPython actually does, all
the way down to bytecode and bits). Read it top-to-bottom for a full walkthrough, or jump to any
section for a targeted answer — both work.

---

## Table of Contents

1. [The Big Picture: Every Operator Is a Method Call in Disguise](#1-the-big-picture-every-operator-is-a-method-call-in-disguise)
2. [Arithmetic Operators (`+ - * / // % ** @`) Deep Dive](#2-arithmetic-operators-------deep-dive)
3. [Comparison Operators & Chained Comparisons](#3-comparison-operators--chained-comparisons)
4. [Logical Operators (`and`, `or`, `not`) & Short-Circuit Evaluation](#4-logical-operators-and-or-not--short-circuit-evaluation)
5. [Bitwise Operators (`& | ^ ~ << >>`)](#5-bitwise-operators---)
6. [Identity vs Equality (`is`/`is not` vs `==`)](#6-identity-vs-equality-isis-not-vs-)
7. [Membership Operators (`in`, `not in`)](#7-membership-operators-in-not-in)
8. [Operator Precedence & Associativity](#8-operator-precedence--associativity)
9. [Operator Overloading — the Dunder Dispatch Mechanism](#9-operator-overloading--the-dunder-dispatch-mechanism)
10. [Cheat Sheet: Common Gotchas](#10-cheat-sheet-common-gotchas)
11. [Quick-Reference Checklist](#11-quick-reference-checklist)

---

## 1. The Big Picture: Every Operator Is a Method Call in Disguise

**The one idea that explains almost everything in this document:** when you write `a + b`, Python
does not have built-in "addition circuitry" that's separate from how objects work. Instead, `+` is
**syntax that gets translated into a method call** — `a.__add__(b)` — exactly the same kind of call
as `a.some_method(b)`. Every operator in this section (`+`, `<`, `and`'s truthiness check, `in`,
`&`, even `is`) is a thin layer of convenient syntax sitting on top of ordinary method dispatch.

```
 Source:            a + b
                        │
                        ▼ (compiler, → 1.1 Stage 3)
 Bytecode:          BINARY_OP (NAME a) (NAME b)     <- a single instruction, operator-agnostic
                        │
                        ▼ (CPython VM, ceval.c, → 1.1 Stage 4)
 C-level dispatch:  PyNumber_Add(a, b)
                        │
                        ▼
 Type-slot lookup:  looks up type(a)'s nb_add slot (a C function pointer table every type carries)
                        │
                        ▼
 Ends up calling:   type(a).__add__(a, b)      -- if that returns NotImplemented, tries
                                                    type(b).__radd__(b, a) before giving up (→ Section 9)
```

**Why Python is built this way:** it means operators are not a fixed, closed set of behaviors that
only work on `int`/`str`/`list`. Any class you define can opt into `+`, `<`, `in`, `[]`, etc. simply
by implementing the matching dunder ("double underscore") method — because the *operator* was never
anything more than a friendly spelling for "call this method." This single mechanism is what lets
`"a" + "b"` (string concatenation), `[1] + [2]` (list concatenation), and `3 + 4` (numeric addition)
all use the identical `+` symbol — each type simply provides its own `__add__`.

**Layman version:** think of an operator symbol like `+` as a universal doorbell button. Every house
(type) wires that same doorbell button to whatever it wants to happen when pressed — one house rings
a chime (numeric addition), another opens the door (string concatenation), another does nothing at
all and the button just doesn't work (`TypeError: unsupported operand type(s)`, meaning that "house"
never wired up a handler for this particular button).

Keep this diagram in mind — every section below names exactly which dunder method(s) it's really
calling.

---

## 2. Arithmetic Operators (`+ - * / // % ** @`) Deep Dive

**Surface table — every arithmetic operator and its dunder hook (→ Section 1):**

| Operator | Meaning | Dunder method |
|---|---|---|
| `+` | addition | `__add__` / `__radd__` |
| `-` | subtraction | `__sub__` / `__rsub__` |
| `*` | multiplication | `__mul__` / `__rmul__` |
| `/` | true division (always returns `float`) | `__truediv__` |
| `//` | floor division | `__floordiv__` |
| `%` | modulo (remainder) | `__mod__` |
| `**` | exponentiation | `__pow__` |
| `@` | matrix multiplication | `__matmul__` |
| unary `-x` | negation | `__neg__` |
| unary `+x` | identity (rarely overridden meaningfully) | `__pos__` |

```python
print(7 / 2)     # 3.5   — true division ALWAYS produces a float, even if evenly divisible: 4/2 == 2.0
print(7 // 2)     # 3     — floor division: rounds DOWN toward negative infinity
print(7 % 2)      # 1     — remainder
print(2 ** 10)     # 1024  — exponentiation
```

**Unary operators are a separate, one-argument dispatch — not "binary minus with a hidden zero":**
```python
x = 5
print(-x)     # calls x.__neg__() — a genuinely different dunder than __sub__
print(+x)     # calls x.__pos__() — usually a no-op for numbers, but a class CAN define custom behavior
```

**The floor-division / modulo sign gotcha — where Python differs from C/Java:**

Python defines `//` to always round **toward negative infinity** (not toward zero, which is what C's
integer division does), and `%` is defined so that `a == (a // b) * b + (a % b)` always holds exactly
— which forces `%`'s result to take the **sign of the divisor**, not the sign of the dividend.

```python
print(-7 // 2)     # -4   (NOT -3 — floors toward -infinity: -3.5 rounds DOWN to -4)
print(-7 % 2)       #  1   (result takes the sign of the divisor, which is positive here)

print(7 // -2)      # -4   (3.5 floored toward -infinity is -4)
print(7 % -2)        # -1   (sign of the divisor, which is negative here)
```

```
 Number line for -7 / 2 = -3.5:

  -4        -3.5        -3
  ─┼───────────┼──────────┼─►
   ▲           ▲
   floor(-3.5) actual quotient    <- // always picks the number line position to the LEFT
   = -4                              of the true quotient, never "toward zero"
```
This is a deliberate design choice (documented in PEP 238's discussion of division), not an
accident — it guarantees the identity above holds universally, which makes `%` reliable for things
like wrapping array indices or clock arithmetic even with negative inputs, unlike C where
`-7 % 2 == -1` (sign follows the *dividend*, and the identity above still holds, but the “remainder”
answer disagrees with Python's).

**`**` is right-associative, and it binds *tighter* than unary minus — two facts that combine into a
classic gotcha:**
```python
print(2 ** 3 ** 2)     # 512, not 64 — evaluated as 2 ** (3 ** 2), i.e. right-to-left, NOT left-to-right
print(-2 ** 2)          # -4, not 4  — evaluated as -(2 ** 2), because ** binds TIGHTER than unary minus
print((-2) ** 2)         # 4 — parentheses force the unary minus to apply first
```
(→ Section 8 has the full precedence table explaining exactly why these two rules combine this way.)

**Matrix multiplication `@` (PEP 465, Python 3.5+):** added specifically because scientific/numeric
code (NumPy, PyTorch) needed a symbol for matrix multiplication distinct from element-wise `*`
(which, for a NumPy array, multiplies element-by-element, not as matrices):
```python
import numpy as np
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
print(A @ B)        # real matrix multiplication, calls A.__matmul__(B)
print(A * B)         # element-wise multiplication — a COMPLETELY different operation, same-shaped inputs
```
Plain Python's built-in numeric types don't implement `__matmul__` at all — `@` only becomes usable
once a type (like NumPy's `ndarray`) opts in, exactly per the Section 1 dispatch mechanism.

---

## 3. Comparison Operators & Chained Comparisons

**Surface table:**

| Operator | Dunder method |
|---|---|
| `==` | `__eq__` |
| `!=` | `__ne__` (auto-derived from `__eq__` if not defined) |
| `<` | `__lt__` |
| `<=` | `__le__` |
| `>` | `__gt__` |
| `>=` | `__ge__` |

(Full coverage of implementing these on your own classes — including `functools.total_ordering` to
avoid writing all six by hand — lives in syllabus **4.4, Dunder Methods**; this section covers how
the *operators themselves* behave, using built-in types.)

**Chained comparisons — Python's genuinely distinct behavior:**

```python
x = 5
print(1 < x < 10)     # True — reads naturally as "is x between 1 and 10?"
```

In C, Java, and JavaScript, `1 < x < 10` would evaluate `1 < x` first (getting `True`/`1`), then
compare *that boolean* against `10` (`True < 10` → typically `True` since `True` coerces to `1`) —
producing a result that has nothing to do with whether `x` is actually between 1 and 10. **Python's
grammar treats `a < b < c` as its own special chained form**, rewritten as `a < b and b < c` — with
the crucial refinement that `b` is only evaluated **once**, even though it conceptually appears in
both halves:

```python
def loud(n):
    print(f"evaluating {n}")
    return n

print(1 < loud(5) < 10)
```
```
evaluating 5
True
```
`"evaluating 5"` prints only **once** — proof that the middle expression isn't literally duplicated
and re-run; the compiler generates code that evaluates it a single time and reuses the value for
both comparisons.

```
 a < b < c  compiles roughly to:

 tmp = b                  (evaluated exactly once)
 if not (a < tmp):
     result = False        (b's comparison to c is never even attempted — short-circuits, → Section 4)
 else:
     result = (tmp < c)
```

Chains of any length work the same way: `a < b <= c != d` becomes `a < b and b <= c and c != d`, with
each middle value evaluated once and short-circuiting the moment any link fails.

---

## 4. Logical Operators (`and`, `or`, `not`) & Short-Circuit Evaluation

**What "short-circuit" means:** `and`/`or` don't necessarily evaluate their right-hand side at all —
they stop as soon as the overall result is already determined:

```python
def loud(label, value):
    print(f"evaluating {label}")
    return value

loud("A", False) and loud("B", True)     # prints only "evaluating A" — B never runs, result is already False
loud("A", True) or loud("B", True)        # prints only "evaluating A" — result already True, B never runs
```

**The single most important, most-overlooked fact: `and`/`or` return one of their actual *operands*,
not a re-computed `True`/`False`.**

```python
print(5 and 10)      # 10   — both truthy, so `and` returns the SECOND operand
print(0 and 10)        # 0    — first operand is falsy, `and` returns it immediately, never looks at 10
print(5 or 10)          # 5    — first operand already truthy, `or` returns IT, never looks at 10
print(0 or 10)           # 10   — first operand falsy, so `or` moves on and returns the second
```

**Precise rule:**
- `a and b` → if `a` is falsy, return `a` (as-is, unevaluated `b`); otherwise return `b`.
- `a or b` → if `a` is truthy, return `a` (as-is, unevaluated `b`); otherwise return `b`.

**Why this matters — the extremely common default-value idiom relies on exactly this:**
```python
name = user_input or "Anonymous"     # if user_input is "" (falsy), name becomes "Anonymous"
```
This only works *because* `or` returns the actual operand value, not a boolean — if `or` returned a
plain `True`/`False`, this idiom couldn't exist. (The gotcha version: this idiom silently does the
"wrong" thing if a legitimately meaningful falsy value like `0` or `""` should have been kept —
→ Section 10.)

**How it works — bottom-up (bytecode):** short-circuiting is implemented with a conditional jump
that skips evaluating the right operand entirely — it's not that the interpreter evaluates both
sides and then discards one:
```python
import dis
dis.dis(compile("x = a or b", "<string>", "exec"))
```
```
  0 LOAD_NAME                0 (a)
  2 COPY                     1          # keep a's value in case we short-circuit
  4 POP_JUMP_IF_TRUE         5 (to a later offset)   # if a is truthy, JUMP PAST loading b entirely
  6 POP_TOP
  8 LOAD_NAME                1 (b)
 10 STORE_NAME               2 (x)
```
(Exact opcode names/offsets vary slightly by Python version, but the shape — load left operand, test
it, conditionally *skip* loading the right operand — is stable across versions.) The right operand's
bytecode is never even reached if the jump is taken, which is what makes it a genuine "circuit
that's broken partway," not merely "evaluate everything, then decide."

**`not` is different from `and`/`or`: it always produces a real `bool`, via `__bool__` (→ 1.2 §5):**
```python
print(not 5)      # False — always exactly True or False, never "5" or some other operand
print(not "")       # True
```

---

## 5. Bitwise Operators (`& | ^ ~ << >>`)

**What they are:** operators that act on the individual **bits** of an integer's binary
representation, rather than on its value as a whole number.

| Operator | Name | Effect |
|---|---|---|
| `&` | AND | 1 only where **both** bits are 1 |
| `\|` | OR | 1 where **either** bit is 1 |
| `^` | XOR | 1 where the bits **differ** |
| `~` | NOT (invert) | flips every bit |
| `<<` | left shift | shifts bits left, filling with 0s (≈ multiply by 2ⁿ) |
| `>>` | right shift | shifts bits right (≈ floor-divide by 2ⁿ) |

**Bit-grid diagram for `&`, `\|`, `^` on 4-bit values (using `12 = 0b1100` and `10 = 0b1010`):**
```
        1 1 0 0    (12)
        1 0 1 0    (10)
        ─ ─ ─ ─
  AND:  1 0 0 0    (8)   <- 1 only where BOTH columns have 1
  OR:   1 1 1 0    (14)  <- 1 where EITHER column has 1
  XOR:  0 1 1 0    (6)   <- 1 where columns DIFFER
```
```python
print(12 & 10)    # 8
print(12 | 10)     # 14
print(12 ^ 10)      # 6
```

**Why `~x == -x - 1` — two's complement representation:** CPython (like nearly all modern hardware)
represents negative integers using **two's complement**: inverting every bit of `x` and adding 1
gives `-x`. Rearranging that relationship gives the identity behind `~`:
```python
print(~5)       # -6   because ~x is defined as -(x + 1)
print(~0)        # -1
print(~-1)        # 0
```
```
 Two's complement intuition (conceptually — Python ints aren't a fixed width, but the bit-pattern
 idea still explains the -x-1 relationship):

  5  = ...00000101
  ~5 = ...11111010   <- every bit flipped
     = -6 in two's complement interpretation
```

**Shifts as fast multiply/divide by powers of two:**
```python
print(1 << 4)      # 16   — same as 1 * (2 ** 4)
print(16 >> 2)       # 4    — same as 16 // (2 ** 2), floor division
```
Because Python's `int` is arbitrary-precision (→ `01_2_variables_and_data_types.md` §6.2), shifting
left never "falls off the end" the way it can in fixed-width languages (C's 32-bit `int` overflowing
on a large left shift) — the integer's internal digit array simply grows to hold the larger value.

**Practical use case — bit flags/masks:**
```python
READ, WRITE, EXECUTE = 1, 2, 4        # 0b001, 0b010, 0b100 — each flag owns one distinct bit

permissions = READ | WRITE             # 0b011 — combine flags with OR
print(bool(permissions & WRITE))         # True  — test a flag with AND
permissions &= ~WRITE                     # turn OFF the WRITE bit: AND with the inverse mask
print(bool(permissions & WRITE))           # False
```
This pattern (each flag = one power of 2, combine with `|`, test with `&`, clear with `& ~flag`) is
exactly what `enum.Flag` (syllabus 4.5) wraps in a safer, named-constant interface — but the
underlying mechanism is precisely this bitwise arithmetic.

**Layman version:** think of an integer as a row of light switches. `&` only leaves a light on if
*both* rows had it on; `|` leaves it on if *either* did; `^` leaves it on only where the two rows
*disagreed*; `~` flips every switch; `<<`/`>>` physically slides the whole row of switches left or
right.

---

## 6. Identity vs Equality (`is`/`is not` vs `==`)

This exact topic already received full treatment in
[`01_2_variables_and_data_types.md`, Section 3](01_2_variables_and_data_types.md#3-object-identity-id-is-and-cpythons-caching-tricks) —
covering `id()`, why `is` is a raw pointer comparison that can never be overridden, and CPython's
small-integer/string identity-caching gotchas. It's listed here in 1.3 purely because `is`/`is not`
are, syntactically, operators alongside `==`/`!=` — the short version, for this doc's context:

```python
a = [1, 2, 3]
b = a
c = [1, 2, 3]

print(a is b)      # True  — SAME object (is compares identity — id(a) == id(b))
print(a is c)        # False — equal VALUES, different objects
print(a == c)          # True  — == compares value, via __eq__
```

**Rule of thumb:** use `is`/`is not` only for identity questions that are conceptually about
*sameness* — `x is None`, `x is True`, checking a sentinel object — never as a shortcut for comparing
ordinary values, where `==` is both correct and what you actually mean.

---

## 7. Membership Operators (`in`, `not in`)

**What it is:** `x in container` asks "does this container hold `x`?" — the exact dispatch mechanism
depends on what the container's type provides, tried in this order:

```
 x in container:
      │
      ▼
 1. Does type(container) define __contains__?         -> call container.__contains__(x) directly
      │  no
      ▼
 2. Does type(container) define __iter__?              -> iterate the whole container, compare each
      │  no                                                item to x with ==, stop at first match
      ▼
 3. Fall back to __getitem__(0), __getitem__(1), ...   -> old-style sequence protocol, index until
                                                            IndexError or a match is found
```

```python
print(3 in [1, 2, 3])         # True  — list has no __contains__ shortcut structure; falls to __iter__, scans
print("a" in "abc")             # True  — str defines __contains__ directly
print(3 in {1, 2, 3})            # True  — set/dict use __contains__ backed by HASHING (see below)
```

**Why this is a genuine Big-O difference, not just a style choice:**

| Container | `in` mechanism | Average time complexity |
|---|---|---|
| `list` / `tuple` | linear scan via `__iter__`, comparing each element | **O(n)** — checks every element until found |
| `set` / `dict` (keys) | hash the item, jump straight to its bucket | **O(1)** average — no scanning at all |

```
 list: "is 42 in here?"                    set:  "is 42 in here?"
 [7, 19, 3, 42, 8, ...]                     hash(42) -> bucket #6 directly
  ↑  check  ↑  check  ↑  check  ↑ FOUND      look in bucket #6 -> FOUND (no scanning the rest)
 (must check items in order until a match, worst case checks ALL n items)
```

**Practical consequence:** repeatedly testing membership against a `list` inside a loop
(`if x in my_list:` executed thousands of times) can be a real performance bug — converting `my_list`
to a `set` once, up front, turns an O(n²) pattern into O(n) overall. This is exactly why
`collections` (syllabus 2) and the hashing requirement on dict keys/set members exist the way they
do — hashability is what makes O(1) membership testing possible at all.

---

## 8. Operator Precedence & Associativity

**What it is:** when an expression mixes multiple operators with no parentheses, precedence decides
*which operator groups first*; associativity decides *which direction* operators of the *same*
precedence group when there are several in a row.

**Precedence table (highest to lowest binds first) — abbreviated to what's covered in this doc:**

| Precedence (high → low) | Operators | Associativity |
|---|---|---|
| 1 (highest) | `()` (call), `[]` (subscript), `.` (attribute) | left-to-right |
| 2 | `**` (exponentiation) | **right-to-left** |
| 3 | unary `+x`, `-x`, `~x` | n/a (single operand) |
| 4 | `* / // % @` | left-to-right |
| 5 | `+ -` (binary) | left-to-right |
| 6 | `<< >>` | left-to-right |
| 7 | `&` | left-to-right |
| 8 | `^` | left-to-right |
| 9 | `\|` | left-to-right |
| 10 | comparisons (`== != < > <= >= is is not in not in`), chained (→ Section 3) | left-to-right (chained) |
| 11 | `not` | n/a (single operand) |
| 12 | `and` | left-to-right, short-circuit (→ Section 4) |
| 13 (lowest) | `or` | left-to-right, short-circuit (→ Section 4) |

**The two counterintuitive rows, unpacked (already previewed in Section 2):**
- Row 2 (`**`) sits **above** row 3 (unary minus) — meaning `**` grabs its operands *before* a unary
  minus next to it does. That's why `-2 ** 2` parses as `-(2 ** 2)` = `-4`, not `(-2) ** 2` = `4`.
- Row 2 (`**`) is itself **right-associative** (every other row here is left-to-right) — so a chain
  of `**` groups from the right: `2 ** 3 ** 2` is `2 ** (3 ** 2)`, not `(2 ** 3) ** 2`.

**Expression tree for a mixed expression — `2 + 3 * 4 ** 2`:**
```
 Precedence order of operations: ** first, then *, then + (lowest of the three here)

           +                     Evaluation order:
          / \                    1. 4 ** 2  = 16    (highest precedence: **)
         2   *                   2. 3 * 16  = 48    (next: *)
            / \                  3. 2 + 48  = 50    (lowest: +)
           3   **
              /  \
             4    2

 print(2 + 3 * 4 ** 2)   # 50
```

**Layman version:** precedence is like PEMDAS/BODMAS from school math, extended to cover every
Python operator — the table above is just that idea made complete and precise, including the two
rows (`**`'s tight binding and right-associativity) that don't have an obvious school-math analogue
and therefore catch people off guard.

---

## 9. Operator Overloading — the Dunder Dispatch Mechanism

This section closes the loop back to **Section 1's big picture**: every operator behavior shown
throughout this document for built-in types (`int.__add__`, `list.__contains__`, `str.__lt__`, ...)
is available to **your own classes** too, by defining the matching dunder method. This is exactly
what "operator overloading" means in Python — there's no separate overloading syntax; you simply
implement the method the operator already calls.

```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)     # Vector(4, 6) — `+` on two Vectors now works, because __add__ exists
```

**The `NotImplemented` protocol — how Python handles "I don't know how to combine these two
types":**

```python
class Meters:
    def __init__(self, value):
        self.value = value
    def __add__(self, other):
        if not isinstance(other, Meters):
            return NotImplemented    # "I don't know how to add this — let Python try something else"
        return Meters(self.value + other.value)
```

```
 a + b, where a is a Meters and b is something Meters doesn't understand:

 1. Try a.__add__(b)                 -> returns NotImplemented (a explicitly punts)
 2. Try b.__radd__(a)  ("reflected") -> if b's type defines it and it succeeds, USE that result
 3. Neither worked                    -> Python raises TypeError: unsupported operand type(s)
```

Returning the special singleton `NotImplemented` (not the same as raising an exception, and not the
same as `None`) is what signals "ask the other side" — this is precisely how mixed-type arithmetic
between built-ins works too (e.g., `int.__add__` doesn't know how to add a `Fraction`, so it returns
`NotImplemented` and lets `Fraction.__radd__` handle it instead).

**Full survey of every dunder method** (`__eq__`, `__lt__`, `__len__`, `__getitem__`, `__call__`,
context managers, and more) is covered in depth in **syllabus section 4.4 (Dunder/Magic Methods)** —
this section's job was only to show *how operators reach those methods in the first place*, tying
every operator in this document back to the single dispatch mechanism from Section 1.

---

## 10. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `1 < x < 10` gives a surprising result coming from another language | Forgetting Python's chained comparisons aren't "compare-then-compare-the-bool" like C/Java | Trust it — `a < b < c` really does mean `a < b and b < c` in Python, evaluated left to right (→ Section 3) |
| `value = user_input or "default"` silently drops a legitimate `0`, `""`, or `[]` input | `or` returns the first *truthy* operand — any falsy "real" value is treated the same as missing | Use an explicit `if value is None: value = "default"` when falsy-but-meaningful values must be preserved (→ Section 4) |
| `-2 ** 2` evaluates to `-4`, not `4` | `**` binds tighter than unary minus | Parenthesize explicitly: `(-2) ** 2` if you want `4` (→ Sections 2, 8) |
| `2 ** 3 ** 2` evaluates to `512`, not `64` | `**` is right-associative, unlike every other binary operator in the table | Parenthesize explicitly if left-to-right grouping was intended: `(2 ** 3) ** 2` (→ Sections 2, 8) |
| `-7 % 2` or `-7 // 2` gives a different sign/value than expected from a C/Java background | Python's `//` floors toward negative infinity and `%` takes the divisor's sign — both differ from C's truncating division | Know the rule (→ Section 2), or use `math.fmod`/explicit logic if C-style truncation is genuinely required |
| Membership checks (`x in my_list`) get slower as a list grows, in a hot loop | `list`/`tuple` membership is O(n) linear scan; only `set`/`dict` get O(1) average via hashing | Convert to a `set` once, up front, if you'll test membership repeatedly (→ Section 7) |
| `a is b` gives inconsistent results for equal-looking values | Using identity (`is`) where value equality (`==`) was actually meant | Use `==` for value comparisons; reserve `is` for `None`/singleton/identity checks (→ Section 6, and `01_2` §3) |
| Custom class's `+`/`==`/etc. raises `TypeError: unsupported operand type(s)` | The relevant dunder method (or its reflected `__r...__` counterpart) isn't implemented, or returns something other than `NotImplemented` for unknown types | Implement the dunder method, returning `NotImplemented` (not raising) for types it doesn't handle (→ Section 9) |

---

## 11. Quick-Reference Checklist

Use this whenever you're reasoning about an operator expression in Python:

1. Do I know which dunder method this operator actually calls, in case I need to support it on my
   own class or debug why it isn't working? (→ Section 1, 9)
2. If dividing or taking a modulo with possibly-negative operands, have I accounted for Python's
   floor-toward-negative-infinity and sign-of-divisor rules, especially if porting logic from C/Java?
   (→ Section 2)
3. Am I chaining comparisons (`a < b < c`) intentionally and correctly, aware that the middle term is
   evaluated exactly once? (→ Section 3)
4. Does my code rely on `and`/`or` returning a *value* rather than a `bool` — and if so, is that
   deliberate, and safe against falsy-but-meaningful inputs? (→ Section 4)
5. Am I using bitwise operators (`& | ^ ~ << >>`) for genuine bit-level work — flags/masks, low-level
   protocols — rather than confusing them with the logical operators `and`/`or`? (→ Section 5)
6. Am I using `is`/`is not` only for true identity questions (`None`, singletons), and `==` for
   everything else? (→ Section 6)
7. If testing membership repeatedly in a loop, is the container a `set`/`dict` (O(1)) rather than a
   `list`/`tuple` (O(n))? (→ Section 7)
8. When an expression mixes several operators, have I checked precedence/associativity rather than
   assuming left-to-right — especially around `**` and unary minus? (→ Section 8)
9. If overloading an operator on a custom class, does my dunder method return `NotImplemented`
   (not raise) for types it doesn't know how to handle, so Python can try the reflected method?
   (→ Section 9)
