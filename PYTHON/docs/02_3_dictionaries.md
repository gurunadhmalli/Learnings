# 2.3 Dictionaries — Complete Deep-Dive Guide

This is the companion reference for **Section 2.3** of [`python_full_syllabus.md`](python_full_syllabus.md).
Same format as [`02_1_lists.md`](02_1_lists.md) and [`02_2_tuples.md`](02_2_tuples.md): **what it is →
why it exists → how it works, all the way down to memory and the CPython runtime → a plain-English
analogy**. This is arguably the most important data structure in the entire language — Python's own
namespaces (`globals()`, an object's `__dict__`, keyword arguments) are all, literally, dictionaries
under the hood — so understanding *how* a dict achieves fast lookup pays off everywhere, not just when
you type `{}`.

> **A note on gaps in the syllabus outline.** Before writing this, I compared the original 2.3 bullet
> list against what mastering dictionaries actually requires, and found real gaps. I've folded all of
> them in here (and added short bullets back into the syllabus so the outline stays honest):
> - **How a dict actually achieves O(1) lookup** — hash table mechanics, open addressing, load factor,
>   resizing — was entirely absent. This is the single biggest "bottom-level" gap, and it's the whole
>   reason section 2.1 kept saying "use a dict/set instead of a list for O(1) membership" without ever
>   explaining *why* that's true (→ Section 1).
> - **Hash randomization (`PYTHONHASHSEED`)** — a security-relevant detail (defense against
>   hash-flooding denial-of-service attacks) with zero mention in the original outline (→ Section 1).
> - **`d[key]` vs `.get()` vs `del d[key]` vs `.pop()`** — the four different ways to read/remove a
>   key, each with different failure behavior, weren't distinguished at all (→ Section 3).
> - **Dictionary view objects are live, not snapshots** — a very common misconception, and their
>   set-like operations (`&`, `|`, `-` on `.keys()`) weren't mentioned (→ Section 4).
> - **Mutating a dict's size while iterating raises `RuntimeError`** — direct, useful contrast with
>   the *silent* list-mutation-during-iteration bug from `02_1_lists.md` Section 8, and wasn't listed
>   (→ Section 5).
> - **`dict.fromkeys()`** and **building a dict from `zip()`** — two extremely common construction
>   idioms, absent from the "creation" bullet (→ Section 2).
> - **`popitem()`'s LIFO order** — an under-appreciated, version-guaranteed behavior (→ Section 4).
> - **`setdefault` vs `defaultdict`** — both solve "insert-if-missing," but mechanically differently,
>   and the outline listed them as unrelated bullets rather than the same problem solved two ways
>   (→ Section 7).
> - **`types.MappingProxyType`** — the standard read-only dict wrapper, missing entirely, and directly
>   relevant to why a hashable key can't itself be a plain (mutable) dict (→ Section 8).

Read it beginner-first (skim "What it is" and "Layman version") or internals-first (read the
"bottom-up" blocks) — both paths are here.

---

## Table of Contents

1. [The Big Picture: What a Dict *Actually* Is — Hash Tables from the Ground Up](#1-the-big-picture-what-a-dict-actually-is--hash-tables-from-the-ground-up)
2. [Creation & Key-Value Semantics](#2-creation--key-value-semantics)
3. [Reading, Writing & Removing: `[]`, `.get()`, `del`, `.pop()`](#3-reading-writing--removing---get-del-pop)
4. [Dict Methods & View Objects](#4-dict-methods--view-objects)
5. [Iteration, Ordering & the Mutate-While-Iterating Trap](#5-iteration-ordering--the-mutate-while-iterating-trap)
6. [Dict Comprehensions](#6-dict-comprehensions)
7. [Merging Dicts, `setdefault` vs `defaultdict`](#7-merging-dicts-setdefault-vs-defaultdict)
8. [`collections.OrderedDict`, `defaultdict`, `Counter`, and `MappingProxyType`](#8-collectionsordereddict-defaultdict-counter-and-mappingproxytype)
9. [Nested Dictionaries](#9-nested-dictionaries)
10. [Cheat Sheet: Common Gotchas](#10-cheat-sheet-common-gotchas)
11. [Quick-Reference Checklist](#11-quick-reference-checklist)

---

## 1. The Big Picture: What a Dict *Actually* Is — Hash Tables from the Ground Up

**What it is:** a `dict` is an unordered-by-nature-but-ordered-by-guarantee (see Section 5) mapping
from unique, hashable **keys** to arbitrary **values**, supporting average **O(1)** lookup, insertion,
and deletion regardless of how many entries it holds.

**The mental model most people start with:** "a dict is like a list, but you look things up by name
instead of by number." That's true at the interface level, but it hides the actual reason dicts are
fast — and understanding that reason is what makes section 2.1's repeated claim ("`in` is O(n) on a
list, O(1) on a dict/set") something you actually *understand* rather than just memorize.

**Why a list-style linear scan can't be the mechanism:** if `d["alice"]` had to check every key one by
one until it found a match (the way `x in some_list` works, → `02_1_lists.md` Section 8), lookup cost
would grow with the number of entries — no different from a list. A dict needs a way to jump **almost
directly** to the right slot instead of checking each one.

**The mechanism: a hash table.** Every key is run through `hash(key)` (→ `02_2_tuples.md` Section 5 —
the same hashing machinery that makes a tuple usable as a dict key) to produce an integer. That
integer is used, via `hash(key) % table_size` (conceptually — the real code uses bitmasking, not `%`,
for speed), to pick a **slot index** directly — no scanning required. Two completely different keys
that happen to want the *same* slot ("a collision") are resolved by **open addressing**: CPython
computes a deterministic sequence of alternative slots to probe (a "probe sequence") until it finds
either the key itself or an empty slot.

```
 Conceptual hash table (heavily simplified):

  hash("alice") = 84109...   → slot index = hash % table_size → say, slot 3
  hash("bob")   = 19273...   → slot index = 6
  hash("carol") = 84200...   → slot index = 3  <- COLLISION with "alice"! probe to next candidate slot

  slots: [ _ ][ _ ][ _ ][alice:30][ _ ][ _ ][bob:25][ _ ][carol:22(probed)]
           0    1    2      3       4    5     6      7        8

  d["alice"]  → hash("alice") → jump STRAIGHT to slot 3 → found, O(1), no scanning of slots 0,1,2
```

**Why lookup is O(1) *average*, not O(1) *guaranteed*:** if hashes were perfectly spread out, one
computed jump would almost always land directly on (or very near) the right slot — that's the
"average case." But nothing stops many keys from *pathologically* colliding into the same slot (in the
worst theoretical case, an attacker who can predict your hash function could deliberately craft keys
that all collide, degrading every lookup toward O(n) — a real denial-of-service technique called
**hash flooding**). This is precisely why CPython salts `str`/`bytes` hashing with a random value
chosen fresh at process startup (`PYTHONHASHSEED`, default `random`) — it makes it computationally
infeasible for an external attacker (e.g., someone submitting JSON keys to a web server that gets
loaded into a dict) to predict collisions in advance. You can pin it for reproducible debugging:
```python
import os
print(os.environ.get("PYTHONHASHSEED"))    # None by default = fresh random seed each run
# PYTHONHASHSEED=0 python script.py         # (set before starting the interpreter) makes str/bytes
                                              # hashing DETERMINISTIC across runs — useful for
                                              # reproducing a bug, never for production security
```

**CPython's actual layout since 3.6 — a "compact dict": two structures, not one.** Modern CPython
doesn't store keys/values directly in the sparse hash-indexed table. Instead it keeps a **sparse index
array** (just integers, pointing into...) a **separate, dense, insertion-ordered array of actual
key/value/hash entries**. This split is *why* dicts guarantee insertion order (Section 5) despite being
"hash tables" underneath — the order-preserving data lives in the dense array, completely independent
of however scattered the hash-based slot assignments are.

```
 Sparse index table (hash-based, may have gaps): [ -1 | 2 | -1 | 0 | 1 | -1 | -1 | -1 ]
                                                    (each entry is just an INDEX into the array below,
                                                     or -1 for "empty" — this table can be much smaller
                                                     than before because it stores only small ints)

 Dense entries array (INSERTION ORDER, no gaps):   [0: (alice,30)] [1: (bob,25)] [2: (carol,22)]
```
This two-structure design (introduced by Raymond Hettinger's "compact dict" proposal) made dicts both
**more memory-efficient** (the sparse table stores small integers, not full key/value/hash triples) and
**ordered for free** — a genuine two-birds-one-stone optimization.

**Resizing — measurable, and load-factor driven, just like `02_1_lists.md` Section 3's list growth:**
```python
import sys
d = {}
prev = sys.getsizeof(d)
for i in range(30):
    d[i] = i
    cur = sys.getsizeof(d)
    if cur != prev:
        print(f"len={len(d):2d}  bytes={cur}  (grew from {prev})")
        prev = cur
```
```
len= 1  bytes=224   (grew from 64)
len= 6  bytes=352   (grew from 224)
len=11  bytes=632   (grew from 352)
len=22  bytes=1168  (grew from 632)
```
Just like a list's over-allocation (→ `02_1_lists.md` Section 3), CPython resizes the underlying table
**before** it gets too full — once the table crosses an internal load-factor threshold (roughly two-
thirds full), it allocates a larger table and re-inserts every existing entry into it. This is why a
dict's *average* per-insertion cost is still O(1) amortized, exactly like list `append` — occasional
expensive resizes are averaged out over many cheap insertions.

**Layman version:** a list is a single long shelf you must walk past item by item to find what you
want. A dict is more like a **library with a call-number system**: instead of walking every aisle, you
run the book's title through a formula (hashing) that tells you almost exactly which shelf to walk to
directly. Two different titles occasionally hash to the "same" shelf number by coincidence (a
collision) — the librarian's rule for that case is "if the shelf you were sent to is occupied by
something else, check the next shelf over, then the next, following a fixed pattern, until you find
either your book or an empty shelf." And crucially, this library *also* keeps a separate, ordinary
logbook recording every book in the exact order it was checked in — that logbook is what makes "walk
through my dict in insertion order" free, entirely independent of which shelf-numbers the hashing
formula happened to assign.

---

## 2. Creation & Key-Value Semantics

**Literal and constructor forms:**
```python
d1 = {"a": 1, "b": 2}                  # literal syntax
d2 = dict(a=1, b=2)                       # constructor with keyword arguments — keys become strings "a", "b"
d3 = dict([("a", 1), ("b", 2)])              # constructor from an iterable of (key, value) PAIRS
d4 = dict(zip(["a", "b"], [1, 2]))              # a very common idiom: pair up two parallel sequences
d5 = dict.fromkeys(["a", "b", "c"], 0)             # {'a': 0, 'b': 0, 'c': 0} — same default value for every key
d6 = {}                                               # empty dict (NOT a set — {} is always an empty dict)
```
`dict(zip(keys, values))` deserves calling out explicitly: it's the standard way to combine two
"parallel" lists into a mapping — e.g. CSV header row + a data row, or two arrays you already have —
and it comes up constantly once you're comfortable with the iterator-based tools in syllabus 3.5.

**Key-value semantics — every key must be unique; the LAST assignment to a repeated key wins:**
```python
d = {"a": 1, "a": 2}       # NOT an error — the second "a" simply overwrites the first
print(d)                      # {'a': 2}
```

**The hashability requirement for keys — directly reusing `02_2_tuples.md` Section 5's material,
just now on the "key" side instead of the "tuple element" side:**
```python
d = {}
d[(1, 2)] = "a tuple key works"      # fine — tuples are hashable (assuming their contents are too)
d["a string key"] = "also fine"        # strings are hashable

try:
    d[[1, 2]] = "a list key"              # lists are NOT hashable (→ 02_2_tuples.md Section 5)
except TypeError as e:
    print(e)                                # unhashable type: 'list'
```
**The deeper contract this rests on — hash/`__eq__` consistency (→ syllabus 4.4):** for dict lookup to
work at all, two keys that compare equal (`k1 == k2`) **must** produce the same hash (`hash(k1) ==
hash(k2)`) — otherwise a key could hash to one slot on insertion and hash to a *different* slot when
you later look it up with an equal-but-not-identical key, and the dict would never find it. This is why
custom classes that override `__eq__` must also override `__hash__` consistently (or explicitly opt out
by setting `__hash__ = None`) — full coverage in syllabus 4.4.

**Layman version:** think of a key as the exact label you hand the librarian to compute a shelf number
from. If two different-looking labels are supposed to mean "the same book" (`==`), they'd better
produce the *same* shelf-number formula result (`hash`) — otherwise the librarian would file "your"
book on one shelf today and go looking for it on a different shelf tomorrow, and never find it.

---

## 3. Reading, Writing & Removing: `[]`, `.get()`, `del`, `.pop()`

**Four different operations, four different failure behaviors — a very common source of confusion:**
```python
d = {"a": 1, "b": 2}

# READING
print(d["a"])              # 1
try:
    d["z"]                    # KeyError: 'z' — raises if missing, no default possible
except KeyError as e:
    print("KeyError:", e)
print(d.get("z"))              # None — returns a default (None unless specified) instead of raising
print(d.get("z", "fallback"))    # "fallback" — explicit default value

# WRITING (always succeeds — creates the key if absent, overwrites if present)
d["c"] = 3                        # adds a new key
d["a"] = 99                          # overwrites the existing key's value

# REMOVING
del d["c"]                            # removes the key; raises KeyError if missing, returns NOTHING
x = d.pop("b")                          # removes AND RETURNS the value; raises KeyError if missing...
print(x)                                   # 2
print(d.pop("missing", "fallback"))          # ...UNLESS a default is given, exactly like .get()
```
**The pattern to internalize:** `[]` and `del` are the "strict" pair (both raise `KeyError` on a
missing key, no way to opt out); `.get()` and `.pop()` are the "lenient" pair (both accept an optional
default and never raise for a missing key when one is given) — `.pop()` additionally *removes* the
key, `.get()` never touches the dict at all.

**Layman version:** asking the librarian "give me book X" (`d["a"]`) with no fallback plan means
you'll hear "we don't have that" (`KeyError`) if it's missing. Asking "give me book X, or tell me
'not found' if you don't have it" (`.get()`) never produces an angry response. `del` is "remove this
book, and yell at me if it wasn't there"; `.pop()` is "hand me the book AND remove it, but it's fine if
it wasn't there as long as I told you what to say instead."

---

## 4. Dict Methods & View Objects

**The full method survey:**
```python
d = {"a": 1, "b": 2, "c": 3}

d.update({"b": 20, "d": 4})     # {'a':1,'b':20,'c':3,'d':4} — merges in place; overlapping keys overwritten
print(d.keys())                    # dict_keys(['a', 'b', 'c', 'd'])
print(d.values())                    # dict_values([1, 20, 3, 4])
print(d.items())                       # dict_items([('a',1), ('b',20), ('c',3), ('d',4)])
print(d.get("a"))                        # 1
print(d.setdefault("e", 5))                # 5 — key was missing, so it's inserted with this default AND returned
print(d.setdefault("a", 999))                # 1 — key EXISTED already, so 999 is IGNORED, existing value returned
print(d.pop("d"))                              # 4 — removes and returns
print(d.popitem())                               # ('e', 5) — removes and returns the LAST inserted pair (LIFO!)
```

**`popitem()`'s LIFO order is a real, version-guaranteed behavior (Python 3.7+), not incidental:**
```python
d = {"a": 1, "b": 2, "c": 3}
print(d.popitem())     # ('c', 3) — the MOST recently inserted pair, removed first — a stack-like (LIFO) pop
print(d.popitem())     # ('b', 2)
```
This follows directly from Section 1's compact-dict layout: the dense entries array is append-ordered,
so "remove the last entry" is the cheap, natural operation — exactly analogous to why `list.pop()`
(from the end) is O(1) in `02_1_lists.md` Section 3.

**Dictionary view objects — `.keys()`, `.values()`, `.items()` are LIVE windows, not snapshots:**
```python
d = {"a": 1, "b": 2}
keys_view = d.keys()
print(keys_view)          # dict_keys(['a', 'b'])
d["c"] = 3                   # mutate the dict AFTER creating the view...
print(keys_view)                # dict_keys(['a', 'b', 'c']) — the EXISTING view object reflects the change!
```
**Why — bottom-up:** a view object doesn't copy anything at creation time; it holds a reference back to
the dict itself and re-reads it live on every access (conceptually similar to how `range` in
`01_4_control_flow.md` is a lazy, computed-on-demand sequence rather than a materialized list). This is
efficient (no copying) but means you should never assume a view "freezes" the dict's state at the
moment you grabbed it.

**`.keys()` and `.items()` support set-like operations directly (because dict keys are guaranteed
unique — → syllabus 2.4, sets) — `.values()` does NOT (values aren't guaranteed unique):**
```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 3, "c": 4}
print(d1.keys() & d2.keys())     # {'b'}          — intersection: keys present in BOTH
print(d1.keys() | d2.keys())     # {'a', 'b', 'c'} — union: all keys from either
print(d1.keys() - d2.keys())     # {'a'}          — keys in d1 but NOT in d2
```

**Layman version:** `.keys()`/`.values()`/`.items()` aren't photocopies of the card catalog — they're
live windows into the *same* catalog drawer. Add a card to the drawer later, and every window you
already opened shows the new card too, because they're all looking at the one real drawer, not a copy
of it. And because every card's title (key) in the drawer is guaranteed unique, you can meaningfully
ask "which titles are in both drawer A and drawer B" the same way you'd compare two sets of unique
labels.

---

## 5. Iteration, Ordering & the Mutate-While-Iterating Trap

**Iterating a dict — by default, over its keys:**
```python
d = {"a": 1, "b": 2, "c": 3}
for k in d:                  # equivalent to `for k in d.keys()`
    print(k)                    # a, b, c

for k, v in d.items():         # the idiomatic way to get BOTH key and value while iterating
    print(k, v)

for v in d.values():             # just the values
    print(v)
```

**Ordering — a real, version-guaranteed language feature since Python 3.7 (was a CPython
implementation detail in 3.6), directly following from Section 1's dense insertion-ordered array:**
```python
d = {}
d["z"] = 1
d["a"] = 2
d["m"] = 3
print(list(d))     # ['z', 'a', 'm'] — INSERTION order, not sorted/alphabetical order
print(list(reversed(d)))     # ['m', 'a', 'z'] — reversed(dict) works too, since 3.8, for the same reason
```
This is *not* the same as "sorted" — a dict never reorders keys based on their value; it simply
remembers the order keys were first inserted, and preserves that order even after updates to existing
keys (re-assigning an existing key's value does **not** move it to the end).

**Mutating a dict's SIZE while iterating over it raises `RuntimeError` — a loud failure, in deliberate
contrast to a list's silent skip bug (→ `02_1_lists.md` Section 8):**
```python
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    if k == "b":
        del d[k]     # RuntimeError: dictionary changed size during iteration
```
**Why — bottom-up:** CPython's dict iterator tracks the dict's internal version/size counter; every
mutation that changes the number of entries bumps that counter, and the iterator checks it on every
`next()` call, raising immediately if it's changed mid-iteration. This is a deliberate design choice —
unlike a list (where shifting elements during iteration silently skips items with no error at all,
→ `02_1_lists.md` Section 8), a dict's hash-table internals could be reshuffled entirely by a resize
triggered mid-iteration (Section 1), making "just keep going" unsafe in a much deeper way than a list's
simple index-shift — so CPython refuses outright rather than risk silently wrong behavior.
```python
# The fix — iterate over a snapshot copy of the keys, mutate the ORIGINAL dict safely:
d = {"a": 1, "b": 2, "c": 3}
for k in list(d):          # list(d) materializes a separate, static snapshot of the keys right now
    if k == "b":
        del d[k]
print(d)     # {'a': 1, 'c': 3}
```
Note: **re-assigning an existing key's value** during iteration is fine (it doesn't change the dict's
size); only insertion/deletion of keys triggers the error.

**Layman version:** the library's catalog logbook remembers the exact order books were checked in,
forever — walking through it in that order costs nothing extra, it's just how the log was written.
But if you try to tear a page out of the logbook (delete an entry) while someone else is actively
reading through it page by page, the librarian stops you immediately and loudly, rather than letting
the reader silently skip a page and not notice — a stricter, safer policy than the "shelf" (list)
case, where nobody's watching for that kind of mid-walk disruption at all.

---

## 6. Dict Comprehensions

**What it is:** the dict equivalent of a list comprehension (→ `02_1_lists.md` Section 4) — builds a
new dict from an iterable in one expression, using `{key_expr: value_expr for ... }` syntax.

```python
squares = {x: x * x for x in range(5)}
print(squares)     # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# Conditional (filtering) form:
evens_only = {x: x * x for x in range(10) if x % 2 == 0}
print(evens_only)     # {0: 0, 2: 4, 4: 16, 6: 36, 8: 64}

# From an existing dict — a very common "transform every value" idiom:
prices = {"apple": 1.0, "banana": 0.5}
doubled = {k: v * 2 for k, v in prices.items()}
print(doubled)     # {'apple': 2.0, 'banana': 1.0}

# Inverting a dict (swap keys and values) — only safe if original values are unique AND hashable:
inverted = {v: k for k, v in prices.items()}
print(inverted)     # {1.0: 'apple', 0.5: 'banana'}
```
**How it works — bottom-up:** exactly like a list comprehension (→ `02_1_lists.md` Section 4), a dict
comprehension compiles to its own code object with its own scope — the loop variable (`x`, or `k, v`)
does not leak into the enclosing namespace, unlike a plain `for` loop (→ `01_4_control_flow.md`).

**Layman version:** instead of building the card catalog one card at a time with a loop and repeated
`d[k] = v` lines, a dict comprehension is the "fill out the whole drawer from this list, following this
one rule for every card" shorthand — same private-booth scoping behavior as a list comprehension.

---

## 7. Merging Dicts, `setdefault` vs `defaultdict`

**Merging — several equivalent-ish tools, with one crucial difference (in-place vs new object):**
```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 20, "c": 3}

merged = d1 | d2              # Python 3.9+ merge operator — returns a NEW dict; d1, d2 UNCHANGED
print(merged)                    # {'a': 1, 'b': 20, 'c': 3}

d1 |= d2                           # in-place merge operator — mutates d1 directly
print(d1)                             # {'a': 1, 'b': 20, 'c': 3}

merged2 = {**d1, **d2}                  # ** unpacking inside a literal — also builds a NEW dict
d1.update(d2)                             # .update() — the original, pre-3.9 in-place merge method
```
**Precedence rule — whichever dict's key appears LAST/on-the-right wins, consistently across every
merge tool:** in `d1 | d2`, `{**d1, **d2}`, and `d1.update(d2)`, if both dicts share a key, **`d2`'s
value wins** in all three — a deliberately consistent rule, not something you need to memorize
per-tool.

**`setdefault` vs `collections.defaultdict` — both solve "insert a default value the first time a key
is used," mechanically differently:**
```python
# setdefault: an ordinary dict method, called explicitly, every time you touch a possibly-new key
groups = {}
groups.setdefault("fruits", []).append("apple")
groups.setdefault("fruits", []).append("banana")     # key already exists — the [] argument is built
                                                        # AND THROWN AWAY, since it's not used
print(groups)     # {'fruits': ['apple', 'banana']}

# defaultdict: a dict SUBCLASS that auto-creates a default value the moment a MISSING key is accessed
from collections import defaultdict
groups2 = defaultdict(list)          # 'list' here is a FACTORY — called with no args to build each default
groups2["fruits"].append("apple")       # no .setdefault needed — missing-key access itself triggers creation
groups2["fruits"].append("banana")
print(dict(groups2))                      # {'fruits': ['apple', 'banana']}
```
**Why they're not just cosmetic twins — the actual mechanical difference:** `setdefault` always
constructs its default-value argument (`[]` in the example) **every single call**, even on the calls
where the key already exists and the freshly-built empty list is immediately discarded — a small but
real, repeated bit of wasted work. `defaultdict` instead overrides `__missing__` (→ syllabus 4.4,
attribute/item access hooks) — a hook that's only invoked *once*, exactly when a key turns out to be
absent — so the factory (`list`, `int`, or any zero-argument callable) only ever runs on genuine
first-use, never wastefully.

**Layman version:** `setdefault` is like always pre-preparing a brand new empty folder "just in case,"
every time you approach the filing cabinet, and only actually filing it away if the cabinet turns out
not to already have one (otherwise you just toss the spare folder you made). `defaultdict` is smarter —
it only reaches for a brand-new folder-making machine at the exact moment it discovers the drawer is
genuinely empty, never a moment before.

---

## 8. `collections.OrderedDict`, `defaultdict`, `Counter`, and `MappingProxyType`

**`collections.OrderedDict` — largely a historical artifact after Python 3.7:** before 3.7, plain
dicts did not guarantee insertion order at all (Section 5) — `OrderedDict` was the only ordered
mapping available. Today, plain `dict` already preserves insertion order, so `OrderedDict`'s remaining
practical advantages are narrower: it supports `.move_to_end()` (reposition a key without removing/
re-inserting it) and its equality comparison is **order-sensitive** (two `OrderedDict`s with the same
pairs in different order compare unequal — unlike plain dicts, Section 2):
```python
from collections import OrderedDict
od = OrderedDict(a=1, b=2)
od.move_to_end("a")
print(od)     # OrderedDict({'b': 2, 'a': 1})

print(OrderedDict(a=1, b=2) == OrderedDict(b=2, a=1))     # False — order matters here
print({"a": 1, "b": 2} == {"b": 2, "a": 1})                  # True — plain dicts ignore order (Section 2)
```

**`collections.defaultdict`** — covered in full in Section 7; the key API surface: constructed with a
zero-argument **factory callable** (`list`, `int`, `set`, or any custom no-arg function), which
`__missing__` invokes automatically on first access to any absent key.

**`collections.Counter` — a `dict` subclass purpose-built for counting hashable items, with
convenience methods no plain dict has:**
```python
from collections import Counter

words = ["a", "b", "a", "c", "b", "a"]
counts = Counter(words)
print(counts)                # Counter({'a': 3, 'b': 2, 'c': 1})
print(counts["a"])              # 3
print(counts["nonexistent"])       # 0 — Counter overrides __missing__ to return 0, NEVER raises KeyError!
print(counts.most_common(2))          # [('a', 3), ('b', 2)] — the 2 most frequent items, descending
print(counts + Counter(["a", "d"]))     # Counter({'a': 4, 'b': 2, 'c': 1, 'd': 1}) — counters can be ADDED
```
`Counter["missing_key"]` returning `0` instead of raising is a deliberate, specialized override of
`.get()`-with-a-default behavior baked directly into the type, tailored for the "count of something
never seen" use case.

**`types.MappingProxyType` — a genuinely READ-ONLY *view* onto an existing dict (not a copy):**
```python
from types import MappingProxyType

original = {"a": 1}
readonly_view = MappingProxyType(original)

print(readonly_view["a"])     # 1 — reading works fine
try:
    readonly_view["a"] = 99      # TypeError: 'mappingproxy' object does not support item assignment
except TypeError as e:
    print(e)

original["a"] = 2                  # mutating the ORIGINAL dict still works...
print(readonly_view["a"])            # 2 — ...and the proxy reflects it immediately, because it's a
                                        # LIVE VIEW (Section 4's view-object behavior), not a snapshot
```
**Why this exists:** it's the standard way to hand out a dict to code you don't fully trust (or just
want to protect from accidental mutation) while still allowing the *owner* to keep updating it — e.g.
exposing `type.__dict__` safely (which is, itself, actually a `mappingproxy` in real CPython, precisely
to prevent arbitrary code from directly rewriting a class's internals through it). It's also the
concrete mechanism behind "why can't I use a plain mutable dict as another dict's key" from Section 2 —
a `MappingProxyType` wrapper is itself still unhashable (it doesn't freeze the *contents*, only blocks
*writes through this particular view*), so it doesn't solve that problem; true hashable "frozen
mapping" isn't a built-in type, unlike `frozenset` (→ syllabus 2.4).

**Layman version:** `OrderedDict` is the old specialized logbook from before the main catalog itself
started keeping order — still useful for its extra "move this card to the back of the log" trick and
its stricter "the exact same order counts as a real difference" comparison rule. `Counter` is a tally
clicker built into a drawer — ask about anything, even something you've genuinely never seen, and it
just says "zero," never "not found." `MappingProxyType` is handing someone a **display case** in front
of the real catalog drawer — they can look, but the glass won't let them reach in and rearrange
anything; meanwhile you, behind the counter with the actual drawer, can still restock it, and the
display case always shows the current contents live.

---

## 9. Nested Dictionaries

**What it is:** a dict whose values are themselves dicts (or lists, or any other structure) — the
natural way to represent hierarchical/tree-shaped data (JSON documents, configuration trees, grouped
records).

```python
users = {
    "alice": {"age": 30, "roles": ["admin", "editor"]},
    "bob": {"age": 25, "roles": ["viewer"]},
}
print(users["alice"]["age"])                # 30
print(users["alice"]["roles"][0])             # "admin"

users["alice"]["age"] = 31                      # updating a nested value — reaches through both levels
```

**The shallow-copy aliasing trap applies here exactly as it did for nested lists
(→ `02_1_lists.md` Section 5) — a shallow `.copy()` of an outer dict still shares its nested dict
objects with the original:**
```python
import copy

original = {"a": {"x": 1}}
shallow = original.copy()
shallow["a"]["x"] = 999           # mutates the SHARED nested dict
print(original)                      # {'a': {'x': 999}} — original sees it too!

deep = copy.deepcopy(original)          # recursively duplicates every nested dict/list — genuinely independent
deep["a"]["x"] = 1
print(original)                            # {'a': {'x': 999}} — unaffected this time
```

**A common idiom for safely building nested structures — `defaultdict` nested inside itself, avoiding
manual existence-checking (`if key not in d: d[key] = {}`) at every level:**
```python
from collections import defaultdict

tree = defaultdict(lambda: defaultdict(list))
tree["fruit"]["citrus"].append("orange")
tree["fruit"]["citrus"].append("lemon")
tree["fruit"]["berry"].append("strawberry")
print(dict(tree))     # {'fruit': defaultdict(<class 'list'>, {'citrus': ['orange', 'lemon'], 'berry': ['strawberry']})}
```

**Layman version:** a nested dict is a filing cabinet where each drawer's card itself points to a
*second, smaller* filing cabinet, rather than a single flat value — reaching `users["alice"]["age"]`
means "open the top cabinet, pull alice's card, follow it to her personal mini-cabinet, then pull her
age card from inside that." And exactly like the coat-check aliasing trap from `02_1_lists.md`, a
shallow copy of the outer cabinet photocopies only the top-level *pointers to* each person's mini-
cabinet — everyone's actual mini-cabinet is still the one-and-only original, shared by both the copy
and the source, unless you deep-copy all the way down.

---

## 10. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError` on a lookup that "should" be fine | Used `d[key]` (strict) on a key that might legitimately be absent | Use `d.get(key, default)` when absence is expected/acceptable (→ Section 3) |
| `TypeError: unhashable type: 'list'/'dict'` when creating a dict key | Tried to use a mutable object (list, dict, set) directly as a key | Use an immutable, hashable equivalent instead — e.g. a tuple instead of a list (→ Section 2, `02_2_tuples.md` Section 5) |
| A view object (`.keys()`, `.items()`) shows unexpected NEW entries later | Views are LIVE windows into the dict, not snapshots taken at creation time | If you need a frozen snapshot, explicitly convert: `list(d.keys())` (→ Section 4) |
| `RuntimeError: dictionary changed size during iteration` | Inserted/deleted a key while a `for` loop was actively iterating over the dict | Iterate over `list(d)` (a static snapshot of keys) if you need to mutate the dict during the loop (→ Section 5) |
| Two dicts with identical pairs compare unequal | Actually comparing `OrderedDict`s, whose `==` IS order-sensitive — unlike plain dicts | Use plain `dict` if order shouldn't affect equality, or be intentional about choosing `OrderedDict` for that exact property (→ Section 8) |
| `setdefault("key", expensive_default())` feels wasteful | The default-value expression is evaluated EVERY call, even when the key already exists and the value gets discarded | Use `collections.defaultdict` with a factory instead — its default is only ever built on genuine first-use, via `__missing__` (→ Section 7) |
| Merging two dicts gives an unexpected winning value for a shared key | Every merge tool (`|`, `{**a, **b}`, `.update()`) consistently lets the RIGHT-HAND / later dict's value win on conflicts | Order your merge operands deliberately — put the "should win on conflict" dict last/right (→ Section 7) |
| A shallow copy of a nested dict still lets mutations "leak" back to the original | `.copy()` only duplicates the OUTER dict's key/value pointers, not nested dict/list objects | Use `copy.deepcopy()` when nested structures need to be genuinely independent (→ Section 9, `02_1_lists.md` Section 5) |
| A custom object works fine as a dict key sometimes, then mysteriously "disappears" from lookups | Overrode `__eq__` without also overriding `__hash__` consistently (or vice versa) — breaks the hash/equality contract | Ensure equal objects always produce equal hashes; if `__eq__` is defined, deliberately decide `__hash__`'s behavior too (→ Section 2, syllabus 4.4) |

---

## 11. Quick-Reference Checklist

Use this whenever you're reasoning about a dictionary in Python:

1. Am I thinking of dict lookup as "hash the key, jump almost straight to a slot" (O(1) average) rather
   than "scan until found" (which is what a list's `in` actually does, → `02_1_lists.md` Section 8)?
   (→ Section 1)
2. Is every key I'm using actually hashable — and if it's a custom object, does its `__hash__` stay
   consistent with its `__eq__`? (→ Section 2)
3. Am I using `d[key]` where a missing key should be a hard error, or should I be using `.get()`/
   `.pop(key, default)` instead because absence is a normal, expected case here? (→ Section 3)
4. Did I grab a `.keys()`/`.items()` view and assume it was frozen at that moment? It isn't — it's live
   against the dict's current state. (→ Section 4)
5. Am I about to insert or delete a key while iterating over this exact dict? If so, am I iterating
   over `list(d)` instead of `d` directly to avoid a `RuntimeError`? (→ Section 5)
6. Do I actually need order-sensitive equality or `.move_to_end()`? If not, plain `dict` (not
   `OrderedDict`) is almost always the right default now. (→ Section 8)
7. Am I about to reach for `.setdefault(key, some_default())` inside a loop? Would `defaultdict` avoid
   repeatedly constructing (and discarding) that default value? (→ Section 7)
8. When merging dicts, am I clear on which side "wins" for overlapping keys — the RIGHT-hand/later one,
   consistently across `|`, `{**a, **b}`, and `.update()`? (→ Section 7)
9. If this dict has nested dicts/lists as values, do I need a shallow copy (shares nested objects) or
   a `copy.deepcopy()` (fully independent) for my next operation? (→ Section 9)
10. Am I counting occurrences of things by hand with `if k not in d: d[k] = 0`? `collections.Counter`
    almost certainly already does exactly this, with fewer lines and no `KeyError` risk. (→ Section 8)
