# 2.2 Tuples — Complete Deep-Dive Guide

This is the companion reference for **Section 2.2** of [`python_full_syllabus.md`](python_full_syllabus.md).
Same format as [`01_2_variables_and_data_types.md`](01_2_variables_and_data_types.md) and
[`02_1_lists.md`](02_1_lists.md): **what it is → why it exists → how it works, all the way down to
memory and the CPython runtime → a plain-English analogy**. This doc leans heavily on `02_1_lists.md`
— a tuple is, at first glance, "a list that can't change," so instead of re-deriving everything from
scratch, this doc will repeatedly point at the exact place lists already explained a shared mechanism
(indexing, slicing, comparison) and spend its own effort on what's genuinely *different*: the memory
layout, the consequences of immutability, and hashability.

> **A note on gaps in the syllabus outline.** Before writing this, I compared the original 2.2 bullet
> list against what a working Python programmer actually needs to know about tuples, and found real
> gaps. I've folded all of them in here (and added short bullets back into the syllabus itself so the
> outline stays honest about what it covers):
> - **Indexing & slicing** weren't listed at all — implied by "creation," but tuples support the full
>   indexing/slicing machinery from `02_1_lists.md` Section 2, and it's worth stating explicitly that
>   slicing a tuple gives back a *tuple*, not a list (→ Section 3).
> - **The actual memory-layout reason tuples can't grow and take less memory than lists** — CPython
>   stores a tuple's items *inline*, in the same block as the object itself, unlike a list's separate
>   resizable buffer. This is the single most important "bottom-level" fact the original outline never
>   states (→ Section 1).
> - **The minimal method set** (`count()`/`index()` — nothing else) as a direct, structural consequence
>   of immutability, not an arbitrary omission (→ Section 4).
> - **Immutability is shallow, not deep** — a tuple containing a list still lets that list mutate
>   freely. This is the most common real-world misconception about tuples, and wasn't listed at all
>   (→ Section 4).
> - **Hashability** — arguably *the* reason tuples exist as a distinct type rather than "list but
>   read-only" — was completely absent from the original outline (→ Section 5).
> - **Concatenation/repetition always building a new tuple** (no `__iadd__`), directly reusing the
>   `01_2` Section 13 augmented-assignment material (→ Section 6).
> - **Multiple function return values are just tuple packing** — the single most common reason
>   ordinary Python code uses tuples every day, and unstated in the original outline (→ Section 9).

Read it beginner-first (skim "What it is" and "Layman version") or internals-first (read the
"bottom-up" blocks) — both paths are here.

---

## Table of Contents

1. [The Big Picture: What a Tuple *Actually* Is](#1-the-big-picture-what-a-tuple-actually-is)
2. [Creation, Packing & Unpacking, the Single-Element Gotcha](#2-creation-packing--unpacking-the-single-element-gotcha)
3. [Indexing & Slicing](#3-indexing--slicing)
4. [Immutability — What's Actually Frozen](#4-immutability--whats-actually-frozen)
5. [Hashability & Tuples as Dict Keys / Set Members](#5-hashability--tuples-as-dict-keys--set-members)
6. [Concatenation, Repetition & the Missing In-Place Operators](#6-concatenation-repetition--the-missing-in-place-operators)
7. [Named Tuples: `collections.namedtuple` & `typing.NamedTuple`](#7-named-tuples-collectionsnamedtuple--typingnamedtuple)
8. [Tuple vs List — When to Use Which](#8-tuple-vs-list--when-to-use-which)
9. [Gotchas](#9-gotchas)
10. [Cheat Sheet: Common Gotchas](#10-cheat-sheet-common-gotchas)
11. [Quick-Reference Checklist](#11-quick-reference-checklist)

---

## 1. The Big Picture: What a Tuple *Actually* Is

**What it is:** a `tuple` is Python's ordered, **immutable**, heterogeneous sequence — like a list,
you can mix any types and access by position, but once created its contents can never be reassigned,
grown, or shrunk.

**The mental model most people start with (and it's *almost* right this time):** "a tuple is just a
list that can't change." That's true at the *behavioral* level — but the reason it can't change isn't
an arbitrary rule bolted on top of the same structure as a list. It comes from a genuinely different
memory layout underneath.

**Recall from `02_1_lists.md` Section 1: a `list` is two separate memory blocks** — a small fixed-size
`PyListObject` header containing a *pointer* (`ob_item`) to a second, separately-allocated, resizable
C array of `PyObject*` pointers. That separation is exactly what lets a list grow: CPython can
`realloc` (or replace) the second block without touching the first.

**A `tuple` collapses this into ONE block.** CPython's `PyTupleObject` embeds the item pointers
*directly inside the same allocation as the object header* — there is no second, separate, resizable
buffer to grow at all:

```c
/* Simplified CPython layout */

typedef struct {
    PyObject_VAR_HEAD          /* ob_refcnt, ob_type, ob_size (fixed at creation, never changes) */
    PyObject *ob_item[1];       /* the item pointers themselves, INLINE, right here in this struct */
} PyTupleObject;                /* actual size of this allocation = header + N pointer slots, in ONE malloc */
```

```
 list  (TWO allocations, header separate from resizable item buffer):

  lst ──► ┌───────────────────┐        ┌─────┬─────┬─────┬─────┐
          │ header, ob_size=3 │        │ptr0 │ptr1 │ptr2 │spare│  <- separate block, CAN be resized
          │ ob_item ──────────┼───────►└─────┴─────┴─────┴─────┘     independently of the header
          └───────────────────┘

 tuple (ONE allocation — header and items are the SAME block):

  tup ──► ┌────────────────────────────────────┐
          │ header, ob_size=3                  │
          │ ptr0 │ ptr1 │ ptr2                 │   <- items live INSIDE this same block, fixed at
          └────────────────────────────────────┘      creation time — nowhere to "grow into"
```

**Why this explains everything else about tuples in one stroke:**
- **Tuples cannot grow or shrink** — not because of an artificial permission check, but because there
  is no separate resizable buffer to resize; the item slots *are* the object, sized once at creation.
- **Tuples have lower memory overhead per element than lists** — no second allocation, no pointer to
  it, and (unlike a list, → `02_1_lists.md` Section 3) no spare over-allocated capacity sitting unused.
  This is measurable directly:

```python
import sys
t = (1, 2, 3, 4, 5)
l = [1, 2, 3, 4, 5]
print(sys.getsizeof(t))     # 80  bytes
print(sys.getsizeof(l))       # 104 bytes — extra header field (allocated capacity) + any spare slots

print(sys.getsizeof(()))       # 40 bytes — smallest possible tuple
print(sys.getsizeof([]))         # 56 bytes — smallest possible list, already bigger with ZERO elements
```
Even an *empty* list is bigger than an empty tuple, because a list's header must always reserve room
for the `ob_item` pointer *and* the `allocated`-capacity field, whether or not anything has been
appended yet.

**Layman version:** in `02_1_lists.md` we compared a list to a coat-check rack with numbered hooks,
where the rack (header) is a separate physical thing from the row of hooks (the resizable buffer) — you
can unbolt the hook-row and replace it with a longer one without touching the rack's signage. A tuple
is more like a rack that's **cast as a single solid block, hooks and all, in one mold** — there's no
seam to unbolt. That's exactly why you can't add a hook later (no growing), and why it's a bit lighter
overall (one solid casting instead of a frame plus a separately-bolted-on hook-row).

---

## 2. Creation, Packing & Unpacking, the Single-Element Gotcha

**Creating a tuple — parentheses are optional; the comma is what actually matters:**
```python
a = (1, 2, 3)          # the common, explicit way
b = 1, 2, 3               # IDENTICAL — parentheses are just visual grouping, not required
c = tuple([1, 2, 3])        # tuple(iterable) — a real constructor call, like list() in 02_1 Section 2
d = tuple("abc")               # ('a', 'b', 'c') — consumes any iterable, one element per item produced
e = ()                           # empty tuple
```
This "parens optional" fact is exactly what makes `return 1, 2` and `x, y = 1, 2` read naturally —
under the hood, both sides are just tuples (→ Section 9).

**The single-element tuple gotcha — parentheses alone do NOT make a tuple; the trailing comma does:**
```python
not_a_tuple = (1)          # just an int, 1 — parentheses here are ordinary math-style grouping
really_a_tuple = (1,)        # a genuine 1-element tuple — the COMMA is what signals "this is a tuple"

print(type(not_a_tuple))       # <class 'int'>
print(type(really_a_tuple))      # <class 'tuple'>
```
**Why — bottom-up, at the grammar level:** Python's parser treats a bare `(expr)` as **just
parenthesized grouping** (the same parentheses that let you write `(2 + 3) * 4`) — there is nothing in
the grammar that turns a single parenthesized expression into a tuple. The **comma** is the actual
tuple-constructing token; `1,` is a complete (if minimal) tuple-packing expression all on its own, with
or without wrapping parens:
```python
x = 1,             # ALSO a valid 1-element tuple — the parentheses in (1,) were never load-bearing
print(x, type(x))    # (1,) <class 'tuple'>
```
This is *the* most common tuple bug in real code — writing `return (result)` expecting a 1-tuple and
getting back the bare value instead, or forgetting the comma in a function-call argument.

**Packing and unpacking — reuses exactly the mechanism from `01_2_variables_and_data_types.md` Section
12; not re-derived here, just applied to tuples specifically:**
```python
point = 3, 4                  # PACKING: the right-hand side builds a tuple (3, 4) implicitly
x, y = point                    # UNPACKING: positions matched left-to-right against the tuple
print(x, y)                       # 3 4

first, *rest = (1, 2, 3, 4)         # extended/star unpacking works identically on tuples as on lists
print(first, rest)                    # 1 [2, 3, 4]  — note: *rest is still a LIST, even though the
                                        # source was a tuple (→ 01_2 Section 12 — *name always yields a list)
```

**Layman version:** the parentheses around a tuple are like the ribbon around a gift box — they make
it *look* like a package, but what actually declares "this is a bundle, not just one item passed
through" is the comma, the little tag that says "there's more than one thing tied together here (or
exactly one thing deliberately bundled)." No tag, no bundle — `(1)` is just the number 1 wearing a
ribbon for decoration.

---

## 3. Indexing & Slicing

**What it is:** tuples support exactly the same read-access mechanics as lists — this section is
intentionally short because `02_1_lists.md` Section 2 already derived all of it in full; only what's
*different* for tuples is called out here.

```python
t = (10, 20, 30, 40, 50)

print(t[0])            # 10   — positive indexing, identical mechanism to list (→ 02_1_lists.md Sec 2)
print(t[-1])             # 50   — negative indexing, same normalization rule (index + len(t))
print(t[1:3])              # (20, 30)  — slicing works identically...
print(type(t[1:3]))           # <class 'tuple'> — ...but the RESULT is a tuple, not a list
print(t[::-1])                  # (50, 40, 30, 20, 10) — reverse-via-slice, same idiom as lists
```

**The one real difference: what slicing *returns*.** A list slice returns a new list (because slicing
copies pointers into a fresh resizable buffer, → `02_1_lists.md` Section 2); a tuple slice returns a
new tuple — CPython builds a new fixed-size, inline-item block (Section 1) sized exactly for the
slice's length. There's no capacity/over-allocation concept for either case here — only *list*
`append` benefits from spare capacity; slicing a list doesn't over-allocate the result either.

**What's genuinely *missing* compared to lists, and why:** there is no slice **assignment** on a tuple
(`t[1:3] = (...)` is not legal) — this follows directly from Section 4 (immutability): if the tuple's
item slots can never be reassigned or resized after creation, "assign to a slice" has no operation to
perform.
```python
t = (1, 2, 3)
t[0:2] = (9, 9)     # TypeError: 'tuple' object does not support item assignment
```

**Layman version:** reading from the tuple's welded-in-place hooks works exactly like reading from the
list's rack — "give me what's on hook 3" doesn't care whether the rack can be resized or not. But
asking to "replace hooks 1 through 3 with a different number of hooks" (slice assignment) simply has no
answer here, the same way you can't unbolt-and-replace part of a single-cast block — there's nothing
to unbolt.

---

## 4. Immutability — What's Actually Frozen

**What it is:** once a tuple is created, its own item slots can never be reassigned, and no items can
be added or removed — enforced directly at the C level, since (Section 1) there is no resizable buffer
to grow and no per-slot "set" operation implemented at all.

```python
t = (1, 2, 3)
t[0] = 99         # TypeError: 'tuple' object does not support item assignment
```

**Why the method set is so small — a direct structural consequence, not an arbitrary restriction:**
```python
print([m for m in dir(tuple) if not m.startswith('_')])
# ['count', 'index']
```
Compare this to `list`'s full method survey in `02_1_lists.md` Section 3 (`append`, `extend`, `insert`,
`remove`, `pop`, `clear`, `sort`, `reverse`, `copy`, `index`, `count`) — every single one of those *except*
`index`/`count` exists specifically to mutate a list in place. A tuple structurally cannot support any
of them, so they simply aren't defined. `count()` and `index()` are the only methods that make sense
for something you can only ever *read*, never change.

**The critical subtlety: immutability is SHALLOW, not deep.** A tuple guarantees its own slots won't be
repointed — it says **nothing** about whether the objects those slots point to can themselves be
mutated. If a tuple holds a reference to a mutable object (like a `list`), that object is exactly as
mutable as it would be anywhere else:
```python
t = ([1, 2], 3)        # slot 0 points at a real, ordinary, MUTABLE list object
t[0].append(99)           # this does NOT reassign slot 0 — it mutates the object slot 0 already points to
print(t)                    # ([1, 2, 99], 3)  — the tuple "changed," yet nothing about the tuple itself did

t[0] = [9, 9]              # THIS still fails — reassigning the SLOT itself is what's actually forbidden
                             # TypeError: 'tuple' object does not support item assignment
```
```
 t ──► ┌────────────┬────────────┐
       │ slot0: ptrA│ slot1: ptrB│    <- these TWO pointer slots are frozen forever, can't repoint
       └─────┬──────┴─────┬──────┘        (this IS what "immutable" actually means for a tuple)
             ▼             ▼
          [1, 2]           3            <- but this LIST is an ordinary, fully mutable object;
                                             the tuple has no say over what happens to it
          .append(99) mutates THIS
          object in place — the tuple's
          slot0 pointer never had to
          change to "see" that mutation
```
**Why this matters directly:** it's the exact same distinction from `01_2_variables_and_data_types.md`
Section 9 (mutable vs immutable is a property of the *object*, never of the *name/slot* pointing at
it) — just now applied at the container level instead of the variable level. "This tuple is immutable"
is a precise, narrow claim about the tuple's own slots; it is not a transitive claim about everything
reachable through it.

**Layman version:** the tuple's hooks are welded solid — you truly cannot add, remove, or re-point any
hook after the rack is cast. But if hook #1 happens to be holding a *string bag* (a mutable container)
rather than a solid coat, nothing stops you from reaching into that bag and rearranging what's inside
it — the hook itself never moved, so the weld was never violated; you just changed the contents of
something the weld never had authority over.

---

## 5. Hashability & Tuples as Dict Keys / Set Members

**What it is:** `hash(obj)` computes an integer "fingerprint" of an object, used internally by `dict`/
`set` (→ syllabus 2.3, 2.4) to place and locate entries in O(1) average time. **A tuple is hashable if
and only if every element it directly or indirectly contains is itself hashable.**

```python
print(hash((1, 2, 3)))       # some integer, deterministic within a run
print(hash((1, 2, 3)) == hash((1, 2, 3)))     # True — equal tuples always hash equal, every time

d = {}
d[(0, 0)] = "origin"           # tuples are commonly used as COMPOUND dict keys — e.g. grid coordinates
d[(1, 2)] = "point A"
print(d[(0, 0)])                  # "origin"
```

**Why `list` can never do this — the direct, structural reason:** `hash()` must return the *same*
value for the *same* logical content, for as long as the object exists (this is a hard requirement —
→ syllabus 4.4, `__hash__`'s relationship with `__eq__`). A `list` is mutable — its contents can change
after being hashed, which would silently break every `dict`/`set` that had already placed it based on
its *old* hash. Rather than allow that kind of silent corruption, CPython simply makes `list.__hash__`
`None` — lists are unconditionally unhashable, full stop. A tuple's contents can never change after
creation, so its hash is guaranteed stable for its entire lifetime — which is precisely what makes it
*eligible* to be hashable at all.

**But eligibility isn't automatic — a tuple containing an unhashable element is itself unhashable:**
```python
t = ([1, 2], 3)          # contains a LIST — itself unhashable
hash(t)                     # TypeError: unhashable type: 'list'

d = {}
d[t] = "won't work"           # same TypeError — a dict key computation calls hash() internally
```
```
 hash((1, 2, 3))  →  combines hash(1), hash(2), hash(3)  →  one stable integer   (works: all hashable)

 hash(([1,2], 3)) →  needs hash([1, 2])  →  list.__hash__ is None  →  TypeError  (fails immediately)
```
**Why this is the central reason tuples exist as their own type, not just "read-only list syntax":**
this is the one capability immutability *unlocks* that a list structurally can never have — using a
compound, multi-part value as a single dict key or set member. Nested/multi-dimensional lookups
(`grid[(row, col)]`, memoizing a function of several arguments as `cache[(arg1, arg2)]`) are the
single most common real-world reason to reach for a tuple over a list.

**Layman version:** a hash is like a claim-check number stamped onto an item the moment it's checked
in — it only works as a reliable lookup if the item can never secretly change shape afterward (imagine
trying to find "the red bag" in storage after someone repainted it blue — the stamped description would
now be wrong). A tuple, being welded solid at creation (Section 4), can safely be stamped with a
permanent number. A list, being reshape-able at any time, categorically can't be trusted with one — so
the cloakroom simply refuses to stamp one at all. And even a *welded* tuple can't be stamped if one of
the things sealed inside it is itself an unstamped, reshape-able bag.

---

## 6. Concatenation, Repetition & the Missing In-Place Operators

**`+` and `*` on tuples always build a brand-new tuple — never mutate in place, because there is
nothing to mutate (Section 1):**
```python
a = (1, 2)
b = (3, 4)
print(a + b)          # (1, 2, 3, 4) — a NEW tuple; a and b are both untouched
print(a * 3)             # (1, 2, 1, 2, 1, 2) — repetition, same idea as list * n (→ 02_1_lists.md Sec 5),
                            # but tuples holding only immutable elements sidestep that section's
                            # aliasing trap entirely for simple cases — though a tuple containing a
                            # MUTABLE element still shares that one inner object across repeats,
                            # exactly like the list case, e.g. (([],) * 3)[0] is ([],)*3)[1]
```

**No `__iadd__` exists on tuple — so `+=` always rebinds, never mutates, directly mirroring the
immutable-type branch of `01_2_variables_and_data_types.md` Section 13:**
```python
a = (1, 2)
id_before = id(a)
a += (3,)               # tuple has NO __iadd__ → falls back to a = a.__add__((3,)) → brand new object
print(id(a) == id_before)     # False — confirms a NEW tuple was built and a was rebound to it

b = a
a += (4,)                       # only rebinds the LOCAL name a; b still points at the tuple from before
print(b)                          # unaffected — exactly the "aliased += surprise" from 01_2 Section 13,
                                    # except tuples ALWAYS take the "rebinds" branch, never the
                                    # "mutates in place" branch that list took there
```

**Layman version:** because the tuple-rack is one solid casting, there's no way to "weld two more hooks
onto the end" — concatenation instead casts an entirely new, longer block from scratch and hands you
that. `+=` on a tuple is therefore never a shortcut for "grow this rack" (there's no such operation) —
it's always secretly "cast a whole new rack, then point my wristband at the new one instead."

---

## 7. Named Tuples: `collections.namedtuple` & `typing.NamedTuple`

**What it is:** a way to access tuple elements by **name** (`point.x`) as well as by position
(`point[0]`) — solving the readability problem of plain tuples, where `p[0]` and `p[1]` give no clue
what they mean, without giving up any of a tuple's immutability, hashability, or memory layout.

**`collections.namedtuple` — a factory FUNCTION that generates and returns a new class:**
```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])     # Point is now a genuine CLASS, built dynamically
p = Point(1, 2)

print(p.x, p.y)          # 1 2   — named attribute access
print(p[0], p[1])          # 1 2   — STILL works positionally — it really is a tuple underneath
print(isinstance(p, tuple))  # True  — confirms it, not just "tuple-like"
print(p)                       # Point(x=1, y=2) — a readable __repr__ generated for you
```

**`typing.NamedTuple` — the same underlying idea, via modern class syntax with type hints:**
```python
from typing import NamedTuple

class Point(NamedTuple):
    x: int
    y: int

p = Point(1, 2)
print(isinstance(p, tuple))     # True — same guarantee
print(p.x, p[0])                  # 1 1
```
The `typing.NamedTuple` form is generally preferred in modern code because the field list doubles as
real (if unenforced, → `01_2` Section 15) type annotations, and it reads like an ordinary class
definition rather than a slightly unusual function call.

**How it works — bottom-up:** both forms generate a real subclass of `tuple` at class-creation time.
The named fields are implemented as **class-level `property` descriptors** (→ syllabus 4.5, descriptors)
that each do nothing more than `return self[i]` for their assigned index — so `p.x` and `p[0]` are
genuinely, provably the same underlying data, accessed through two different syntactic doors. Because
the result is still exactly a `PyTupleObject` underneath (Section 1's inline-item layout, unchanged),
a named tuple carries **zero extra per-instance memory overhead** over a plain tuple of the same
length — the "names" live once on the *class*, not repeated in every instance.

```
 Point(1, 2) in memory:  IDENTICAL layout to the plain tuple (1, 2) from Section 1

 p.x   →  Point.x is a property  →  calls  return self[0]   →  reads slot 0, same as p[0]
 p.y   →  Point.y is a property  →  calls  return self[1]   →  reads slot 1, same as p[1]
```

**Forward-reference:** `dataclasses.dataclass(frozen=True)` (→ syllabus 4.5) is a *newer* alternative
that gives similar "immutable, named-field record" ergonomics but is a genuinely different underlying
type (a regular class instance with `__slots__`-like storage, not a `tuple` subclass) — it trades away
`isinstance(x, tuple)`/positional-unpacking compatibility for a more class-like feel; which to use is a
design choice covered fully in that section.

**Layman version:** a plain tuple's hooks are numbered but unlabeled — you have to remember "hook 0 is
always the x-coordinate" from memory. A named tuple sticks a small nameplate ("x", "y") next to each
welded hook, purely for readability — but underneath, it's still the exact same solid welded rack from
Section 1, and you can still address any hook by its original number if you prefer. The nameplates
themselves don't cost extra material per rack — the manufacturer (the class) prints one master
nameplate template once, and every individual rack that rolls off the line just reuses it.

---

## 8. Tuple vs List — When to Use Which

| Use a **tuple** when... | Use a **list** when... |
|---|---|
| The collection represents a fixed-shape *record* (a coordinate, an RGB triple, a database row) | The collection is a growable/shrinkable sequence of similar items |
| You need it as a dict key or set member (→ Section 5) | You need in-place mutation: `append`, `sort`, `insert`, etc. |
| You're returning multiple values from a function (→ Section 9) | The number of elements isn't known/fixed in advance |
| You want to signal "this won't change" to readers and tools | You want the smaller, richer method set irrelevant — mutation IS the point |
| Marginal memory/perf matters and the data is genuinely fixed-size (→ Section 1's `getsizeof` numbers) | — |

**Memory footprint, concretely (from Section 1, repeated here for the side-by-side decision table):**
```python
import sys
print(sys.getsizeof((1, 2, 3, 4, 5)))     # 80  bytes
print(sys.getsizeof([1, 2, 3, 4, 5]))       # 104 bytes
```
Both support O(1) indexing and the same lexicographic comparison rules (→ `02_1_lists.md` Section 8,
not re-derived here) — the decision is almost never about raw performance for small/medium data; it's
about **whether the shape is meant to change**, and (often decisively) **whether you need it as a
hashable key**.

**Layman version:** reach for a tuple when you're describing "one specific, fixed-shape *thing*" (one
coordinate, one RGB color, one row) — reach for a list when you're describing "a *collection* of
things that may grow, shrink, or get reordered." A recipe's single ingredient-line `("flour", "2 cups")`
is naturally a tuple; the whole shopping list of such lines is naturally a list.

---

## 9. Gotchas

**The shallow-immutability trap, concretely (full derivation in Section 4) — this is the single most
common "but I thought tuples were immutable!" bug report:**
```python
def add_tag(tags_tuple, tag):
    tags_tuple[0].append(tag)     # "tags_tuple is immutable, this is safe," goes the mistaken assumption
    return tags_tuple

data = (["draft"], "article-1")
add_tag(data, "reviewed")
print(data)     # (['draft', 'reviewed'], 'article-1') — the caller's data WAS changed, silently
```

**Lexicographic comparison — identical rule to lists, not re-derived here (→ `02_1_lists.md` Section
8):**
```python
print((1, 2, 3) < (1, 2, 4))     # True — same element-by-element comparison rule as lists
print((1, 2) < (1, 2, 0))            # True — shorter "prefix" tuple loses, same rule as lists
```

**Multiple return values are just tuple packing/unpacking — not special syntax:**
```python
def min_max(nums):
    return min(nums), max(nums)     # PACKS the two return values into a tuple, per Section 2

lo, hi = min_max([3, 1, 4, 1, 5])     # UNPACKS them back into two names
print(lo, hi)                            # 1 5

result = min_max([3, 1, 4])                # if you DON'T unpack, you just get the whole tuple back
print(result, type(result))                  # (1, 4) <class 'tuple'>
```
There is no dedicated "multiple return value" feature in Python — `return a, b` is ordinary tuple
packing (Section 2), and `x, y = f()` on the calling side is ordinary tuple unpacking. Understanding
this removes any mystery about *why* you can sometimes do `first, *rest = f()` on a function's return
value, or why forgetting to unpack just silently hands you back "one tuple" instead of an error.

---

## 10. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `(1)` is an `int`, not a 1-element tuple | Parentheses alone never make a tuple — only the trailing comma does | Write `(1,)` (or bare `1,`) whenever you deliberately want a 1-element tuple (→ Section 2) |
| Mutating something reached through a tuple "shouldn't be possible," but it happened | Tuple immutability is SHALLOW — it freezes the tuple's own slots, not any mutable object a slot points to | Don't assume "wrapped in a tuple" means "fully frozen"; if true deep immutability is required, every nested element must itself be immutable (→ Section 4) |
| `TypeError: unhashable type: 'list'` when using a tuple as a dict key or set member | The tuple contains a mutable (and therefore unhashable) element, like a nested list | Only tuples composed ENTIRELY of hashable elements can be hashed/used as dict keys — use nested tuples instead of nested lists if this is needed (→ Section 5) |
| `TypeError: 'tuple' object does not support item assignment` | Tried to reassign a slot (`t[0] = x`) or slice-assign (`t[1:3] = ...`) on a tuple | Build a NEW tuple instead (e.g. `t = (new_val,) + t[1:]`), or use a `list` if in-place mutation is actually needed (→ Sections 3, 4) |
| A function seems to "return two values," and that feels like special syntax | `return a, b` is ordinary tuple packing — there is no separate multi-return mechanism | Recognize `return a, b` as packing and `x, y = f()` as unpacking, the same mechanism as any other tuple (→ Section 9) |
| Expected `t1 += t2` to mutate `t1` in place, but something aliased to it didn't change | Tuples have no `__iadd__` — `+=` on a tuple always REBUILDS a new tuple and rebinds the name, never mutates | Know that `+=` mutates in place only for types with `__iadd__` (like `list`); for tuples it's always equivalent to `t1 = t1 + t2` (→ Section 6) |
| Confusing `namedtuple`/`typing.NamedTuple` instances with plain classes | They're still genuine `tuple` subclasses underneath — `isinstance(x, tuple)` is `True`, and positional access/unpacking still works | Use named access (`p.x`) for readability, but remember positional unpacking (`x, y = p`) and `tuple`-based equality/hashing still apply (→ Section 7) |

---

## 11. Quick-Reference Checklist

Use this whenever you're reasoning about a tuple in Python:

1. Am I aware a tuple's items live INLINE in the same memory block as the tuple object itself — no
   separate resizable buffer like a list has — which is *why* it can't grow or shrink? (→ Section 1)
2. If I meant to create a 1-element tuple, did I actually include the trailing comma (`(x,)`), not
   just parentheses (`(x)`)? (→ Section 2)
3. Am I trying to slice-assign or index-assign into a tuple? That's not legal — do I need a `list`
   instead, or should I build a brand-new tuple? (→ Sections 3, 4)
4. Does this tuple contain any mutable element (a list, dict, or set)? If so, am I aware the tuple's
   "immutability" does NOT prevent that inner element from being mutated? (→ Section 4)
5. Am I trying to use a tuple as a dict key or set member? If so, is EVERY element inside it (including
   nested ones) itself hashable — no nested lists/dicts/sets anywhere inside? (→ Section 5)
6. Am I relying on `+=` to mutate a tuple in place? It never does — it always rebuilds and rebinds,
   unlike a list's `+=`. Am I sure that's the behavior I actually want here? (→ Section 6)
7. Would this data read more clearly with named-field access (`p.x`)? If so, is `typing.NamedTuple`
   (or `collections.namedtuple`) a better fit than a plain positional tuple? (→ Section 7)
8. Is this collection's SHAPE meant to change over its lifetime (append/remove elements)? If yes, I
   want a `list`, not a tuple — tuples are for fixed-shape data (→ Section 8)
9. Am I returning multiple values from a function and treating it as "special syntax"? It's just tuple
   packing on the way out, and unpacking on the way in — nothing more (→ Section 9)
10. If comparing two tuples with `<`/`>`, do I know it's the same element-by-element lexicographic rule
    as lists, not some tuple-specific rule? (→ Section 9, → `02_1_lists.md` Section 8)
