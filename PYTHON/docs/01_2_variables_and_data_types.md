# 1.2 Variables & Data Types — Complete Deep-Dive Guide

This is the companion reference for **Section 1.2** of [`python_full_syllabus.md`](python_full_syllabus.md).
Just like [`01_1_syntax_basics.md`](01_1_syntax_basics.md), every bullet from that section is explained
here the same way: what it is, why it exists, and how it works **all the way down to memory and the
CPython runtime**. Where 1.1 was about "how does typed-in source become running code," 1.2 is about
"once code is running, what actually *is* a variable, and what actually *is* a value" — the two
questions every other topic in this syllabus quietly depends on. Read it beginner-first (skim the
"What it is" and "Layman version" lines) or internals-first (read the "bottom-up" blocks) — both
paths are here.

---

## Table of Contents

1. [The Big Picture: What a Variable *Actually* Is](#1-the-big-picture-what-a-variable-actually-is)
2. [Dynamic Typing & Variable Binding vs Assignment](#2-dynamic-typing--variable-binding-vs-assignment)
3. [Object Identity: `id()`, `is`, and CPython's Caching Tricks](#3-object-identity-id-is-and-cpythons-caching-tricks)
4. [`None` and `NoneType`](#4-none-and-nonetype)
5. [Booleans, Truthy/Falsy, and `bool` as an `int` Subclass](#5-booleans-truthyfalsy-and-bool-as-an-int-subclass)
6. [Numeric Types Deep Dive: `int`, `float`, `complex`](#6-numeric-types-deep-dive-int-float-complex)
7. [Type Checking: `type()` vs `isinstance()` vs `issubclass()`](#7-type-checking-type-vs-isinstance-vs-issubclass)
8. [Type Conversion / Casting](#8-type-conversion--casting)
9. [Mutable vs Immutable Types](#9-mutable-vs-immutable-types)
10. [The `del` Statement & Reference Counting Basics](#10-the-del-statement--reference-counting-basics)
11. [Variable Scope Basics (Preview)](#11-variable-scope-basics-preview)
12. [Multiple Assignment, Chained Assignment, Tuple & Extended Unpacking](#12-multiple-assignment-chained-assignment-tuple--extended-unpacking)
13. [Augmented Assignment Operators (`+=` etc.)](#13-augmented-assignment-operators--etc)
14. [The Walrus Operator `:=`](#14-the-walrus-operator-)
15. [Variable Annotations (PEP 526) & Constants](#15-variable-annotations-pep-526--constants)
16. [Cheat Sheet: Common Gotchas](#16-cheat-sheet-common-gotchas)
17. [Quick-Reference Checklist](#17-quick-reference-checklist)

---

## 1. The Big Picture: What a Variable *Actually* Is

**The mental model almost everyone starts with (and needs to unlearn):** in many languages, a
variable is a labeled *box* — `x = 5` means "put the value 5 inside the box named x." Boxes have a
fixed size, live at a fixed address, and *are* the value.

**Python's actual model is different: a variable is a *label on a string* tied to an object floating
in memory.** The object exists independently, on the heap; the name is just a sticky note pointing
at it. `x = 5` does not mean "put 5 into x" — it means "create (or find) the object `5` somewhere in
memory, then tie the label `x` to it."

```
 The box model (NOT Python):        Python's actual model:

  ┌─────┐                            "x" ──────► ┌──────────────┐
  │  x  │  5                                     │ type: int    │
  └─────┘                                        │ refcount: 1  │  ◄── a real object,
  (fixed address, value lives here)              │ value: 5     │      living on the heap
                                                  └──────────────┘
                                        "y" ──────────────┘  (if you did y = x,
                                                               y points at the SAME object)
```

**Why this distinction matters immediately:** it explains, in one stroke, several things that
otherwise look like separate "rules" to memorize:
- Why `y = x` doesn't copy anything — it just adds a second label to the same object (→ Section 3).
- Why reassigning `x = 10` doesn't change the `5` object at all — it just moves the `x` label to
  point at a *different* object; the `5` object is untouched (and possibly still pointed to by other
  names) (→ Section 2).
- Why "mutable vs immutable" is a property of the *object*, never of the *name* (→ Section 9).

**How it works — bottom-up (CPython internals):**

Every single value in Python — `5`, `"hi"`, `[1,2,3]`, a function, a class — is represented in
CPython's C implementation as a `PyObject`, which always starts with the same fixed header:

```
 struct PyObject (simplified — every Python object starts with this header):
 ┌────────────────────────────┐
 │ ob_refcnt   (reference count)│  ← how many names/containers currently point at this object
 │ ob_type     (pointer to type)│  ← e.g. points at the `int` type object → this is what type() reads
 ├────────────────────────────┤
 │  ... type-specific payload ...│  ← for an int: the actual digits; for a list: a pointer to an
 │                              │     array of PyObject* pointers to its elements; etc.
 └────────────────────────────┘
```

A **namespace** (where names live) is, itself, essentially just a dictionary mapping name-strings to
object-pointers. At module level this is literally `globals()` (a real `dict`). Inside a function,
CPython usually optimizes local variables into a fast array (`f_locals` / the frame's "fast locals"
slots, accessed by `LOAD_FAST`/`STORE_FAST` bytecode) rather than a real dict, purely for speed — but
conceptually it is the same idea: **name → pointer to an object elsewhere in memory.**

```python
x = 5
print(globals()['x'] is x)   # True — "x" the string key maps to the very object x refers to
```

**Layman version:** think of every value in Python as a helium balloon floating in a warehouse
(the heap). A variable name is a piece of string tied around your wrist connecting you to one
balloon. Tying a *second* string (`y = x`) to the *same* balloon doesn't create a second balloon —
now two wrists are tied to one balloon. Untying your string (reassigning or `del`-ing) doesn't pop
the balloon if someone else is still holding it — it only pops when *nobody's* string is attached
anymore (→ Section 10, reference counting).

---

## 2. Dynamic Typing & Variable Binding vs Assignment

**What it is:** a name in Python has no declared type — it's just a label, and labels don't carry
type information. The *object* it currently points to has a type; the *name* never does. This is why
the same name can point at an `int`, then later a `str`, with no error:

```python
x = 5          # x is bound to an int object
x = "hello"    # x is now bound to a completely different (str) object — no conversion happened
```

**Why "binding," not "storing":** the word "assignment" quietly implies "storing a value in a slot,"
which is the box model from Section 1. Python's own documentation and community deliberately use
**"binding"** instead: `x = 5` binds the name `x`, in the current namespace, to the object `5`. Old
and new objects are otherwise unrelated — the `5` object doesn't know or care that `x` used to point
to it, and it isn't mutated, converted, or reused when `x` is rebound.

**How it works — bottom-up (→ `dis`, the bytecode compiler):**

```python
import dis

def f():
    x = 5
    x = "hello"

dis.dis(f)
```
```
  2           0 LOAD_CONST               1 (5)
              2 STORE_FAST               0 (x)

  3           4 LOAD_CONST               2 ('hello')
              6 STORE_FAST               0 (x)
              8 LOAD_CONST               0 (None)
             10 RETURN_VALUE
```

`STORE_FAST` (module level: `STORE_NAME`; class/global level: similar) always means the exact same
thing regardless of the object's type: "make slot/dict-entry `x` point at whatever object is
currently on top of the evaluation stack." There is no type tag on the *slot* — nothing in the
bytecode says "x must hold an int." All the type information lives on the *object* referenced by
`ob_type` in its `PyObject` header (→ Section 1), never on the name.

**Layman version:** dynamic typing means the wristband (the name) has no label saying "balloons
only" or "only red balloons" — you can retie it to any balloon, of any color, at any time. What
*does* have a fixed nature is each individual balloon itself, once it exists.

---

## 3. Object Identity: `id()`, `is`, and CPython's Caching Tricks

**What it is:** `id(obj)` returns a number that uniquely identifies an object for its lifetime — in
CPython this number literally *is* the object's memory address. `x is y` asks "do these two names
point at the exact same object?" — it compares `id(x) == id(y)`, nothing more.

```python
a = [1, 2, 3]
b = a                 # b now points at the SAME list object as a
c = [1, 2, 3]          # c points at a DIFFERENT list object, that happens to hold equal values

print(a is b)          # True  — same object
print(a is c)          # False — equal contents, different objects
print(a == c)          # True  — == compares VALUE, is compares IDENTITY
print(id(a), id(b), id(c))
```

```
 Heap:
   a ──┐
       ├──► [1, 2, 3]   (object #1, id = 0x7f...10)
   b ──┘
   c ──────► [1, 2, 3]   (object #2, id = 0x7f...40)   <- looks identical, is a different balloon
```

**Why `is` and `==` are not interchangeable:** `==` calls the object's `__eq__` method and can be
customized to mean anything ("do these represent the same value?"); `is` can never be overridden —
it is a raw pointer comparison, always meaning "is this the literal same object in memory?" Use `is`
only for identity questions that are conceptually about *sameness*, not equality — most importantly
`is None` / `is True` / `is False` (→ Section 4), never for comparing ordinary values.

**How it works — bottom-up, and CPython's identity-caching optimizations:**

CPython pre-creates and *reuses* certain very common immutable objects instead of building a fresh
one every time, purely as a memory/speed optimization. This is an **implementation detail**, not a
language guarantee — but it's important to know it exists so you never accidentally rely on it:

```python
a = 100
b = 100
print(a is b)     # True on CPython — small ints from -5 to 256 are pre-allocated and shared

a = 1000
b = 1000
print(a is b)     # Usually False — outside the cached range, each literal builds a new int object

s1 = "hello"
s2 = "hello"
print(s1 is s2)   # True — CPython interns most compile-time string literals that look like identifiers
```

```
 CPython's small-int cache (built once, at interpreter startup):
 ┌────┬────┬────┬─────┬─────┐
 │ -5 │ -4 │ ...│ 255 │ 256 │   <- every int literal in this range reuses ONE shared object
 └────┴────┴────┴─────┴─────┘    (256 total objects, permanently alive, refcount never hits 0)

 Any int outside [-5, 256]: a fresh object is (usually) allocated per literal.
```

**Why this exists:** small integers and short identifier-like strings are used *constantly*
(loop counters, dict keys, attribute names) — reusing one shared object instead of allocating a new
one every time is a meaningful performance win with zero downside, *because these objects are
immutable* — sharing an immutable object is always safe (→ Section 9). It would be unsafe to do this
for mutable objects like lists.

**The trap:** because this caching is an implementation detail (not guaranteed by the language spec,
and different between CPython versions or other implementations like PyPy), code that relies on
`is` for value comparison on ints/strings can appear to work by accident and then break the moment
the values fall outside the cached range, or on a different Python implementation.

**Layman version:** the warehouse keeps a small shelf of pre-inflated "common" balloons (numbers
-5 to 256, common short words) that it hands everyone the *same* balloon for, to save effort. Ask
for balloon #1000, though, and it inflates you a brand new one each time — even if someone else
already has an identical one.

---

## 4. `None` and `NoneType`

**What it is:** `None` is Python's way of representing "no value" / "nothing here." Its type is
`NoneType`, and — critically — **there is only ever one `None` object in an entire running program**
(a true singleton).

```python
x = None
print(type(x))       # <class 'NoneType'>
print(x is None)      # True — the idiomatic, correct check
print(x == None)      # Also True here, but NOT idiomatic — see why below
```

**Why `is None`, never `== None`:** because `None` is a guaranteed singleton, identity comparison
(`is`) is both *sufficient* and *faster* than equality comparison, and — more importantly —
`==` can be overridden by a custom class's `__eq__`, which could make `some_obj == None` return
something surprising (even `True` for a non-None object, if someone wrote a buggy `__eq__`). `is`
can never be fooled this way; it's a raw identity check the object cannot intercept. PEP 8 mandates
`is None` / `is not None` for exactly this reason.

**How it works — bottom-up:** `None` is created once, at interpreter startup, as a single
statically-allocated `PyObject` (CPython literally never frees it — its refcount is intentionally
never allowed to reach zero). Every place in your program that writes the literal `None` compiles to
a bytecode instruction (`LOAD_CONST` referencing that one shared object, or in newer CPython versions
a dedicated `LOAD_NONE`-style fast path) — there is no way to construct a "new" `None`.

```python
a = None
b = None
print(a is b)          # Always True, unconditionally, everywhere in the program
```

**Layman version:** `None` isn't "an empty balloon" — it's the *one specific* "nothing to see here"
sign that the entire warehouse shares. Every name that's tied to "nothing" is tied to that exact same
sign, so asking "is this THE nothing-sign?" (`is None`) is both correct and cheap.

---

## 5. Booleans, Truthy/Falsy, and `bool` as an `int` Subclass

**What it is:** `True` and `False` are the two values of type `bool`. Every object in Python,
regardless of type, can be asked "are you truthy or falsy?" via `bool(obj)`, which is what `if`,
`while`, and `and`/`or` implicitly do.

**The truthy/falsy table (what's falsy — everything else is truthy):**

| Falsy values |
|---|
| `False`, `None` |
| `0`, `0.0`, `0j` (any numeric zero) |
| `""`, `[]`, `()`, `{}`, `set()` (any empty sequence/collection) |
| Custom objects that define `__bool__` returning `False`, or `__len__` returning `0` |

**A frequently surprising fact: `bool` is a subclass of `int`.** This is a real inheritance
relationship, not just similar-looking behavior:

```python
print(isinstance(True, int))   # True  — bool literally IS-A int
print(True == 1)                # True
print(False == 0)               # True
print(True + True)              # 2  — booleans participate in arithmetic as 0/1
print(issubclass(bool, int))    # True
```

**Why this exists:** historically Python had no separate boolean type at all (`0`/`1` played that
role, as in C) — when `bool` was added (Python 2.3), making it a *subclass* of `int` rather than a
wholly separate type preserved every piece of existing code that used `0`/`1` as booleans, at the
cost of the mild surprise above.

**How it works — bottom-up:** `True` and `False`, like `None`, are singletons — there is exactly one
`True` object and one `False` object for the entire program's lifetime. `bool(obj)` calls, in order:
`obj.__bool__()` if defined; otherwise `obj.__len__()` (zero → `False`, nonzero → `True`) if defined;
otherwise every object is truthy by default.

```python
class Bucket:
    def __init__(self, items):
        self.items = items
    def __len__(self):
        return len(self.items)

b = Bucket([])
print(bool(b))     # False — __len__ returns 0, so bool() falls back to that
```

**Layman version:** `True`/`False` aren't a wholly separate kind of balloon — they're numbered
balloons `1` and `0` wearing a costume. Underneath the costume, arithmetic still treats them as
plain numbers, which is why `True + True == 2` isn't a bug, it's the mechanism working as designed.

---

## 6. Numeric Types Deep Dive: `int`, `float`, `complex`

### 6.1 Integer literals

```python
dec = 42
bina = 0b101010     # binary   -> 42
octa = 0o52         # octal    -> 42
hexa = 0x2A         # hex      -> 42
readable = 1_000_000  # underscores are purely cosmetic, ignored by the parser, aid readability
```
The leading `0b`/`0o`/`0x` prefixes are tokenizer-level (→ 1.1 Stage 1) — they only change how the
*literal's text* is parsed into a numeric value; the resulting `int` object is identical regardless
of which base you wrote it in (there's no "this int remembers it was written in hex").

### 6.2 Arbitrary-precision integers — how CPython avoids overflow

**What it is:** unlike C/Java's fixed-width integers (which silently wrap around or overflow at a
hardware-determined limit like 2³²−1), Python's `int` grows automatically to hold numbers of any
size, limited only by available memory:

```python
big = 2 ** 1000     # a genuinely enormous number, computed exactly, no overflow, no error
print(big)
```

**How it works — bottom-up:** CPython's `int` is not a single machine word. Internally it's stored
as an array of "digits" in a large base (30 bits per digit on most 64-bit builds), plus a sign — the
same conceptual technique as doing long multiplication on paper digit-by-digit, just in a much bigger
base than 10. Arithmetic on big ints is genuinely more expensive than a single CPU `ADD` instruction
(the CPU only natively adds machine-word-sized numbers) — CPython's C code performs the multi-digit
carrying/borrowing logic itself, in software, for any int that doesn't fit in one machine word.

```
 Small int (fits in hardware word): one digit,  fast native-ish arithmetic
 Huge int 2**1000:  [digit0][digit1][digit2]...[digitN]   <- array, arithmetic loops over all of them
```

**Layman version:** most languages give you a fixed-size cup for numbers — pour in too much and it
overflows and spills (wraps around to garbage). Python hands you a cup that *grows a new ring* every
time you're about to overflow it — slower to pour from as it gets bigger, but it never spills.

### 6.3 Floating-point representation pitfalls (IEEE-754)

**What it is:** `float` is a 64-bit IEEE-754 "double precision" number — the same representation
used by nearly every mainstream language (C, Java, JavaScript). It is a *binary* fraction
representation, and that single fact explains a whole category of "Python bugs" that are actually
universal binary-float behavior:

```python
print(0.1 + 0.2)          # 0.30000000000000004  — NOT a Python bug
print(0.1 + 0.2 == 0.3)   # False
```

**Why — bottom-up, at the bit level:** just as `1/3` has no finite representation in base 10
(`0.3333...` forever), many numbers that look "clean" in base 10 — like `0.1` — have **no exact
finite representation in base 2**. `0.1` in binary is a repeating fraction, just like `1/3` is
repeating in decimal. IEEE-754 double precision allocates exactly 64 bits (1 sign bit, 11 exponent
bits, 52 mantissa/fraction bits) — so any non-terminating binary fraction gets *rounded* to the
nearest representable value at those 52 bits of precision.

```
 "0.1" the human writes it:  a nice short decimal
 "0.1" in binary:            0.0001100110011001100110011... (repeats forever, like 1/3 in decimal)
 Stored in 52 mantissa bits: 0.000110011001100110011001100110011001100110011001101 (rounded, cut off)
                             ▲
                             this tiny rounding error is why 0.1 + 0.2 isn't EXACTLY 0.3
```

Every float operation carries this same small rounding error; they don't always cancel out, which is
why `0.1 + 0.2` lands on `0.30000000000000004` instead of exactly `0.3`.

**Special float values:**
```python
inf = float('inf')
ninf = float('-inf')
nan = float('nan')

print(inf > 10**1000)     # True — infinity beats even enormous finite numbers
print(nan == nan)          # False — NaN ("Not a Number") is defined to never equal anything, even itself
print(nan is nan)          # True — same object, but identity != equality (→ Section 3)
import math
print(math.isnan(nan))     # the correct way to test for NaN
```

**The fix, when exactness matters (money, precise decimals):**
```python
from decimal import Decimal
from fractions import Fraction

print(Decimal("0.1") + Decimal("0.2"))     # Decimal('0.3') — exact, base-10 arithmetic
print(Fraction(1, 3) + Fraction(1, 6))     # Fraction(1, 2) — exact rational arithmetic
```
`Decimal` stores numbers in base 10 (so "clean" decimal values really are exact) at the cost of being
slower than native `float`; `Fraction` stores an exact numerator/denominator pair — both trade speed
for exactness, and both exist specifically because binary `float` cannot represent every decimal
value exactly.

**Layman version:** asking a computer to store `0.1` in binary is like asking someone who only
measures in thirds to write down exactly "one tenth" — they can get *close* with enough thirds
stacked together, but never land on it exactly. The tiny leftover gap is what you see when you add
two "close-but-not-exact" numbers together.

### 6.4 `complex` numbers

```python
z = 3 + 4j          # a native literal — 'j' suffix marks the imaginary part
print(z.real, z.imag)   # 3.0 4.0
print(abs(z))            # 5.0 — magnitude, via Pythagorean theorem
```
`complex` is a built-in type storing two `float`s (real and imaginary parts) — used mainly in
scientific/engineering computation (signal processing, electrical engineering); everyday code rarely
touches it.

---

## 7. Type Checking: `type()` vs `isinstance()` vs `issubclass()`

**What each actually inspects:**

```python
class Animal: pass
class Dog(Animal): pass

d = Dog()

print(type(d) is Dog)          # True  — type() returns the EXACT class, no inheritance considered
print(type(d) is Animal)       # False — d's exact type is Dog, not Animal, even though Dog IS-A Animal

print(isinstance(d, Dog))      # True
print(isinstance(d, Animal))   # True  — isinstance() walks the whole inheritance chain (MRO)
print(issubclass(Dog, Animal)) # True  — asks the same IS-A question about two CLASSES, not instances
```

**How it works — bottom-up:** `type(obj)` simply reads the `ob_type` pointer straight out of the
object's `PyObject` header (→ Section 1) — an O(1) pointer dereference, no searching involved.
`isinstance(obj, Cls)` instead walks `type(obj)`'s **Method Resolution Order** (its full chain of
base classes, → syllabus 4.2) checking whether `Cls` appears anywhere in that chain. This is *why*
`isinstance` correctly says "yes" for a subclass while `type() is` says "no" — they're answering two
different questions ("what is your exact type?" vs "are you a kind of this?").

**Why `isinstance()` is almost always preferred:** it respects polymorphism/inheritance — code that
checks `type(x) is list` breaks the moment someone passes a legitimate `list` subclass, whereas
`isinstance(x, list)` correctly accepts it. It also naturally handles the `bool`/`int` relationship
from Section 5:

```python
print(isinstance(True, int))    # True — bool IS-A int, exactly like Dog IS-A Animal above
print(type(True) is int)         # False — True's exact type is bool, not int
```

`isinstance()` also accepts a tuple of types for a one-line "any of these" check:
`isinstance(x, (int, float))`.

---

## 8. Type Conversion / Casting

**What it is:** `int()`, `float()`, `str()`, `bool()`, `list()`, etc. are not special syntax — they
are **ordinary constructor calls** on built-in classes. Writing `int("42")` is calling the `int`
type's constructor, exactly the same mechanism as calling `Dog()` to build a `Dog`.

```python
int("42")          # 42        — parses a base-10 string
int("2A", 16)       # 42        — explicit base argument
int(3.9)            # 3         — TRUNCATES toward zero, does NOT round
int(-3.9)           # -3        — also truncates toward zero, not "floor"
float("3.14")        # 3.14
str(42)              # "42"
bool(0), bool("0")   # False, True  — "0" is a NON-empty string, therefore truthy! (→ Section 5)
```

**Common failure mode:**
```python
int("abc")     # ValueError: invalid literal for int() with base 10: 'abc'
```
Because these are real constructor calls with real parsing logic, they can fail exactly like any
function call — there is no silent "best effort" conversion; malformed input raises `ValueError`
rather than returning some default like `0`.

**The `int("0")`-is-truthy gotcha ties directly back to Section 5:** `bool("0")` is `True`, because
a non-empty string is truthy regardless of what characters it contains — this trips up beginners
converting user input (`input()` always returns a `str`, so `if input():` and `if int(input()):`
behave very differently for the input `"0"`).

---

## 9. Mutable vs Immutable Types

**What it is:** whether an object's *own memory contents* can change after creation, or whether
"changing" always actually means building a new object and rebinding a name to it.

| Immutable (contents can never change after creation) | Mutable (contents can change in place) |
|---|---|
| `int`, `float`, `complex`, `bool`, `str`, `tuple`, `frozenset`, `bytes` | `list`, `dict`, `set`, `bytearray`, most custom classes by default |

```python
s = "cat"
id_before = id(s)
s += "s"                 # looks like it "modified" s...
print(id(s) == id_before)  # False — a brand-new "cats" string object was created; the old "cat" is unaffected

lst = [1, 2, 3]
id_before = id(lst)
lst.append(4)             # this really does mutate in place
print(id(lst) == id_before)  # True — SAME object, its internal contents grew
```

```
 Immutable "mutation" (str += ):          Mutable mutation (list.append):

  s ──► "cat"   (unchanged, still exists   lst ──► [1,2,3]  ──.append(4)──►  lst ──► [1,2,3,4]
         if something else still           (SAME object, its internal array
         points at it)                      grows/reallocates as needed —
  s ──► "cats"  (a NEW object; s is         no new object, no rebinding)
         rebound to point here)
```

**Why this distinction is load-bearing, not academic:** it explains the single most common beginner
bug in the entire language — the **mutable default argument trap** (full coverage in syllabus 3.1),
and the **shared-reference bug**:

```python
def append_bad(item, bucket=[]):   # DANGER: default list is created ONCE, at def-time, and REUSED
    bucket.append(item)
    return bucket

print(append_bad(1))   # [1]
print(append_bad(2))   # [1, 2]  <- surprise! same list object reused across calls
```

**Why it matters for function arguments (call-by-object-reference, not "by value" or "by
reference"):** Python passes the *object reference itself* into a function — not a copy of the
value, and not a C-style pointer-to-a-variable either. Whether the caller sees a change depends
entirely on whether the callee **mutates** the object (visible to caller) or **rebinds** the local
name (invisible to caller, since rebinding a *name* inside the function has zero effect on the
caller's name — it's a completely separate label):

```python
def mutate(lst):
    lst.append(99)          # mutates the SAME object the caller's name points to — visible outside

def rebind(lst):
    lst = [1, 2, 3]          # rebinds the LOCAL name lst to a new object — invisible outside

original = [1, 2]
mutate(original)
print(original)              # [1, 2, 99] — the caller's list really changed

original = [1, 2]
rebind(original)
print(original)              # [1, 2] — unaffected; rebind() only ever touched its own local label
```

**Layman version:** an immutable object is a balloon that, once inflated, can never be repainted or
resized — any "change" secretly means inflating a brand-new balloon and moving your wristband to it.
A mutable object is a balloon you can actually repaint or blow more air into while everyone's
wristband stays tied to the very same balloon — so *everyone* holding a string to it sees the
repaint.

---

## 10. The `del` Statement & Reference Counting Basics

**What it is:** `del x` does **not** "delete the object" — it removes the name `x`'s binding from
its namespace. The object itself is only actually freed once *nothing at all* still points to it.

```python
a = [1, 2, 3]
b = a
del a          # only removes the NAME 'a'; the list object is still alive because b still points to it
print(b)        # [1, 2, 3] — completely unaffected
```

**How it works — bottom-up (CPython's reference-counting garbage collector):**

Recall the `PyObject` header from Section 1 — every object carries an `ob_refcnt` field, a running
count of how many names/containers currently point at it. `del x`, reassigning `x = something_else`,
a local variable going out of scope when a function returns, or a list/dict entry being overwritten
or removed — **every one of these decrements the refcount of the object that used to be referenced.**
The moment a refcount hits **zero**, CPython immediately and deterministically frees that object's
memory — no waiting, no separate garbage-collection pass required for the common case (this is
different from generational-GC-only languages like Java, where you generally cannot predict *when*
an object gets collected).

```
 a ──┐                         del a                          (b still holds a reference)
     ├──► [1,2,3] (refcnt=2)  ───────►   [1,2,3] (refcnt=1)  ───del b───►  refcnt=0 → FREED immediately
 b ──┘
```

**Inspecting this directly:**
```python
import sys

x = [1, 2, 3]
print(sys.getrefcount(x))    # typically 2 (x itself, plus the temporary reference getrefcount's own argument holds)
print(sys.getsizeof(x))       # size in BYTES of the list object's own overhead (not counting contained objects)
```

**Reference cycles — the one case pure refcounting can't handle, and the forward pointer:** two
objects that reference each other (`a.other = b; b.other = a`) will never naturally reach refcount
zero on their own, even if nothing external points to either anymore. CPython therefore *also* runs
a separate, periodic **generational cycle-detecting garbage collector** (the `gc` module) purely to
catch these cycles. Full internals of that mechanism — generations, thresholds, `gc.collect()` — are
covered in **syllabus section 20 (Python Internals)**; the takeaway here is just: refcounting handles
the vast majority of cleanup instantly and deterministically, and a backup collector exists only for
the cyclic-reference edge case.

**Layman version:** `del` doesn't pop the balloon — it just cuts *your* wristband. The warehouse
keeps a running tally on each balloon of how many wristbands are still attached; the instant that
count hits zero, the balloon is popped and its rubber recycled right then, no delay. The one thing
this tally-based system can't catch on its own is two balloons tied to *each other* with no outside
wristbands at all — a periodic warehouse sweep (the cycle collector) exists just to find and pop
those.

---

## 11. Variable Scope Basics (Preview)

**What it is, briefly:** every name lookup in Python is resolved by searching, in order: **L**ocal
(the current function) → **E**nclosing (any outer function, for nested functions/closures) →
**G**lobal (module level) → **B**uilt-in (`print`, `len`, etc.) — the **LEGB rule**.

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)        # "local" — found immediately at the Local level, search stops there
    inner()

outer()
```

The `global` keyword lets a function *write* to a module-level name instead of creating a new local
one; `nonlocal` does the equivalent for an enclosing function's name (needed for closures that
modify a captured variable). This preview is intentionally shallow — **the full deep dive, including
closures, the late-binding closure gotcha, and worked LEGB diagrams, lives in syllabus section 3.2
(Scope & Closures)**, once functions themselves have been properly introduced.

---

## 12. Multiple Assignment, Chained Assignment, Tuple & Extended Unpacking

**Chained assignment (`a = b = 5`) — one object, multiple names, all at once:**
```python
a = b = 5
print(a is b)     # True — both names are bound to the SAME single object 5 in one statement
```
This is different from `a = 5; b = 5` only in that it's guaranteed to be the *same* object (relevant
for mutable objects especially):
```python
a = b = []          # a and b point at the SAME empty list
a.append(1)
print(b)              # [1] — mutating through 'a' is visible through 'b' too, same object (→ Section 9)
```

**Tuple packing/unpacking (`a, b = 5, 6`) — two separate objects, matched by position:**
```python
a, b = 5, 6          # RHS first packs into a tuple (5, 6), then unpacks positionally into a, b
a, b = b, a           # the classic swap — RHS tuple (b, a) is fully built BEFORE any rebinding happens
```

```
 Chained:  a = b = 5        Tuple unpacking:  a, b = 5, 6

  a ──┐                      a ──► 5
      ├──► 5 (ONE object)    b ──► 6   (TWO distinct objects, matched left-to-right by position)
  b ──┘
```

**Extended (star) unpacking — capturing "the rest" into a list:**
```python
first, *rest, last = [1, 2, 3, 4, 5]
print(first, rest, last)     # 1 [2, 3, 4] 5    — *rest always becomes a real list, never a tuple

head, *tail = "hello"          # works on any iterable, not just lists
print(head, tail)               # h ['e', 'l', 'l', 'o']
```
**How it works — bottom-up:** the compiler recognizes exactly one `*name` in an assignment target
and emits a dedicated `UNPACK_EX` bytecode instruction (as opposed to plain `UNPACK_SEQUENCE` for
star-free unpacking) that knows how many fixed items come before and after the starred name, and
scoops everything in between into a new list — this only requires knowing the *counts* on each side,
which is why exactly one `*name` per assignment is allowed (two would make "how many go on each
side" ambiguous).

---

## 13. Augmented Assignment Operators (`+=` etc.)

**What it is:** shorthand — `x += 1` generally means "compute `x + 1`, then rebind `x` to the
result" — **except this "generally" hides a mutability-dependent trap that's one of the most
important things to internalize from this entire document.**

```python
# Immutable target (int): += always REBINDS — a new object, old one untouched
x = 5
id_before = id(x)
x += 1
print(id(x) == id_before)     # False — 5 is immutable, so a NEW int 6 was created and x rebound to it

# Mutable target (list): += MUTATES in place — same object, grown
lst = [1, 2]
id_before = id(lst)
lst += [3]
print(id(lst) == id_before)    # True — SAME list object, extended in place
```

**How it works — bottom-up:** `x += y` compiles to a dedicated bytecode instruction that first tries
to call `x.__iadd__(y)` ("in-place add") — a method a *mutable* type like `list` implements to grow
itself and return `self`. If the type has **no** `__iadd__` (true of every immutable type — `int`,
`str`, `tuple`, ...), Python transparently falls back to the ordinary `x = x.__add__(y)` (or
`x.__radd__`), which necessarily builds a brand-new object, because an immutable object structurally
cannot be changed in place.

```python
import dis
dis.dis(compile("x += 1", "<string>", "exec"))
```
```
  0 LOAD_NAME                0 (x)
  2 LOAD_CONST               0 (1)
  4 BINARY_OP               13 (+=)     # tries __iadd__ first, falls back to __add__ if absent
  8 STORE_NAME                0 (x)
```
The `STORE_NAME`/`STORE_FAST` at the end runs **unconditionally either way** — even the "mutates in
place" case still rebinds the name to (what happens to be) the same object it already pointed to;
what differs is purely whether a *new object* was created underneath.

**Why this matters in practice — the shared-reference surprise:**
```python
a = [1, 2]
b = a
a += [3]          # mutates the list in place (list has __iadd__)
print(b)            # [1, 2, 3] — b sees the change too, because a and b were the SAME object all along

a = (1, 2)
b = a
a += (3,)           # tuple has NO __iadd__ — this rebuilds a NEW tuple and rebinds a to it
print(b)              # (1, 2) — b is completely unaffected; a now points somewhere else entirely
```

---

## 14. The Walrus Operator `:=`

**What it is:** an **assignment expression** (PEP 572, Python 3.8+) — it assigns a value to a name
*and* evaluates to that value, in a single expression, which plain `=` (a statement — → 1.1 Section
4) can never do.

```python
# Before: compute once, store, then check — or compute twice (wasteful/buggy)
data = get_data()
if data:
    process(data)

# With walrus: assign AND test in one expression
if (data := get_data()):
    process(data)
```

**Why it needed new syntax at all:** as established in `01_1_syntax_basics.md` Section 4, plain
assignment (`=`) is a **statement**, and Python's grammar forbids statements from appearing inside
expression positions (inside an `if`'s condition, a comprehension, a `while` test). The walrus is a
*new, distinct* operator specifically because it's an assignment that behaves as an *expression* —
it produces a value that can sit inside a condition, exactly where plain `=` structurally cannot go.

**Where it earns its keep — avoiding redundant computation in loops and comprehensions:**
```python
# Classic redundant-call pattern:
while True:
    chunk = file.read(1024)
    if not chunk:
        break
    process(chunk)

# Walrus version — same logic, condition and assignment fused into one expression
while (chunk := file.read(1024)):
    process(chunk)

# Comprehension: filter AND reuse an expensive computed value, without computing it twice
results = [y for x in data if (y := expensive(x)) is not None]
```

---

## 15. Variable Annotations (PEP 526) & Constants

**What it is:** Python lets you attach a type *hint* to a variable using a colon — purely
informational syntax that documents intent for humans and static-analysis tools:

```python
age: int = 25
name: str
scores: list[int] = []

print(__annotations__)     # {'age': <class 'int'>, 'name': <class 'str'>, 'scores': list[int]}
```

**The single most important fact about annotations: Python itself never checks them.**
```python
age: int = "not an int at all"    # NO error, NO warning — this runs perfectly fine
print(age)                          # "not an int at all"
```
The annotation is stored (in the enclosing module's/class's `__annotations__` dict) purely as
metadata — nothing in the interpreter's execution path ever consults it to validate anything. Actual
enforcement is an entirely separate, optional layer: static type checkers like `mypy`/`pyright`
(analyze your code *without running it* and flag mismatches) or runtime validation libraries like
`pydantic` — both covered in full in **syllabus section 10 (Type System & Static Typing)**. Writing
`age: int` is a promise to tools and readers, not a lock enforced by the language.

**Constants — a naming convention backed by (at most) a linter, never the runtime:**
```python
MAX_RETRIES = 5          # UPPER_SNAKE_CASE signals "please treat this as constant" — a convention only
MAX_RETRIES = 10          # the language has NO problem with this; nothing prevents reassignment
```
`typing.Final` makes the "don't reassign this" *intent* explicit and machine-checkable by a type
checker — but, exactly like annotations generally, **it changes nothing about runtime behavior**:
```python
from typing import Final

MAX_RETRIES: Final = 5
MAX_RETRIES = 10          # mypy/pyright will flag this as an error; the Python interpreter will not
```

**Layman version:** an annotation is a sticky note on a balloon saying "this one should always be a
red balloon" — the warehouse itself will happily let you tie any color balloon to that wristband; the
note is only useful because *inspectors* (type checkers) walk around reading the notes and writing
you up if they spot a mismatch. Nobody's stopping you at the door.

---

## 16. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `x is y` gives inconsistent `True`/`False` for equal-looking ints/strings | Relying on CPython's small-int cache (-5..256) or string interning, which is an implementation detail, not a guarantee | Use `==` for value comparison; reserve `is` for `None`/`True`/`False`/genuine identity checks (→ Section 3) |
| `0.1 + 0.2 == 0.3` is `False` | Binary floating-point can't represent `0.1` exactly (IEEE-754 rounding) | Compare with a tolerance (`math.isclose`), or use `Decimal`/`Fraction` for exact arithmetic (→ Section 6.3) |
| A function's default list/dict "remembers" values across unrelated calls | Mutable default argument evaluated once at `def` time and reused every call | Default to `None`, create the mutable object fresh inside the function body (→ Section 9) |
| Mutating a list inside a function changes the caller's list, but reassigning it inside the function doesn't | Confusing "mutate the object" (visible outside) with "rebind the local name" (invisible outside) — both look like "changing x" but are not the same operation | Decide explicitly: mutate in place if the caller should see it, or return a new value and let the caller rebind (→ Section 9) |
| `a += [3]` vs `a = a + [3]` behave subtly differently when `a` is aliased elsewhere | `+=` uses `__iadd__` (mutates in place) when available; `+` always builds a new object | Know your target type's mutability before relying on `+=` semantics, especially with shared references (→ Section 13) |
| `isinstance(x, int)` unexpectedly returns `True` for a boolean value | `bool` is a genuine subclass of `int` in Python — not a bug | Check `type(x) is bool` explicitly if you truly need to exclude booleans (→ Section 5) |
| Annotated variable holds a value of the "wrong" type with zero error at runtime | Annotations (`x: int`) are purely metadata — Python never enforces them | Run a static checker (`mypy`/`pyright`) or use `pydantic` for real runtime validation (→ Section 15) |
| An object "disappears" (freed) sooner than expected, or lingers longer than expected | Refcounting frees objects the instant their reference count hits zero — no name pointing at it anymore, from any source, means it's gone right then | Trace every name/container that could be holding a reference; use `sys.getrefcount()` to check (→ Section 10) |

---

## 17. Quick-Reference Checklist

Use this whenever you're reasoning about a variable or value in Python:

1. Am I thinking of this name as a "box holding a value," or correctly as a "label tied to an object
   elsewhere in memory"? (→ Section 1)
2. When I write `x = ...`, am I clear on whether this **rebinds** `x` to a new object, or **mutates**
   the object `x` already pointed to? (→ Sections 2, 9, 13)
3. Am I using `is`/`is not` only for `None`, `True`, `False`, or genuine identity checks — never as a
   substitute for `==` on ordinary values? (→ Sections 3, 4)
4. If I'm comparing floats, am I aware `==` can fail for "obviously equal" values, and using
   `math.isclose` or `Decimal` where exactness matters? (→ Section 6.3)
5. Does this function use a mutable default argument (`def f(x=[])`)? If so, is that deliberate and
   safe, or a latent bug? (→ Section 9)
6. When I pass an object into a function, do I know whether the function will mutate it (visible to
   me afterward) or just rebind its own local name (invisible to me)? (→ Section 9)
7. Am I relying on `type(x) is SomeClass` where `isinstance(x, SomeClass)` would more correctly
   respect subclassing/polymorphism? (→ Section 7)
8. If I wrote a type annotation, do I understand it's documentation for humans/tools only, and does
   this project actually run a checker (`mypy`/`pyright`) that would catch a mismatch? (→ Section 15)
9. Am I using `del` expecting it to "free memory immediately," when really it only removes *one*
   reference — is anything else still holding this object alive? (→ Section 10)
10. For any assignment target with a `*`, do I understand it always collects into a `list`, and that
    only one `*name` per unpacking is allowed? (→ Section 12)
