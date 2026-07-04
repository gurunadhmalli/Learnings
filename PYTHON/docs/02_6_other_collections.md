# 2.6 Other Built-in Collections — Complete Deep-Dive Guide

This is the companion reference for **Section 2.6** of [`python_full_syllabus.md`](python_full_syllabus.md).
Same format as [`02_1_lists.md`](02_1_lists.md), [`02_2_tuples.md`](02_2_tuples.md),
[`02_3_dictionaries.md`](02_3_dictionaries.md), [`02_4_sets.md`](02_4_sets.md), and
[`02_5_strings.md`](02_5_strings.md): **what it is → why it exists → how it works, all the way down to
memory and the CPython runtime → a plain-English analogy**. Everything in this doc is a *specialist*
tool — each structure below exists because `list`/`tuple`/`dict`/`set` (2.1–2.4) each have exactly one
specific weakness, and someone in the standard library built the specialist that fixes it. This doc is
organized around that idea: for every structure, the first question answered is "what, specifically,
was wrong with the general-purpose collection that made this necessary?"

> **A note on gaps in the syllabus outline.** Before writing this, I compared the original 2.6 bullet
> list against what mastering these collections actually requires, and found real gaps — two structures
> were named but never actually explained:
> - **`memoryview` was listed but never explained at all.** `02_5_strings.md` Section 5 even explicitly
>   forward-references "→ syllabus 2.6" for it — this doc pays off that promise: the buffer protocol
>   (PEP 3118), zero-copy slicing, and mutating shared memory through a view (→ Section 4).
> - **`array.array`'s actual memory model was never explained**, just "vs lists." The real, measurable
>   reason to use it — raw densely-packed C values instead of a list's array of pointers to separately
>   heap-allocated boxed objects — was missing, along with the type-code table (→ Section 3).
> - **`deque`'s O(1)-both-ends claim was stated with no mechanism.** `02_1_lists.md` Section 7 already
>   derives *why* (a doubly-linked list of fixed-size blocks) and explicitly defers `maxlen`/`.rotate()`
>   and full API coverage to "syllabus section 2.6" — this doc is where that promise gets kept
>   (→ Section 5).
> - **`ChainMap`'s write semantics** — the fact that mutating a `ChainMap` only ever touches the
>   *first* underlying mapping — wasn't mentioned, and this is the single most common surprise
>   newcomers hit with it (→ Section 6).
> - **`heapq`'s array-index math, its min-heap-only limitation, and the tie-breaking gotcha** weren't
>   covered — only "priority queues/heaps" was named (→ Section 7).
> - **`bisect` requires pre-sorted input and does not sort for you** — a silent-wrong-answer trap if
>   violated — plus its O(log n)-search-vs-O(n)-insertion trade-off, neither of which was stated
>   (→ Section 8).
> - **No cross-collection decision guide existed** tying 2.1–2.6 together into one "which structure do
>   I actually reach for" reference (→ Section 9).
>
> Read it beginner-first (skim "What it is" and "Layman version") or internals-first (read the
> "bottom-up" blocks) — both paths are here.

---

## Table of Contents

1. [The Big Picture: Why These Collections Exist](#1-the-big-picture-why-these-collections-exist)
2. [`range` — The Lazy Integer Sequence (Recap)](#2-range--the-lazy-integer-sequence-recap)
3. [`array.array` — Densely-Packed, Typed Numeric Sequences](#3-arrayarray--densely-packed-typed-numeric-sequences)
4. [`bytearray` (Recap) & `memoryview` — Zero-Copy Views over Binary Buffers](#4-bytearray-recap--memoryview--zero-copy-views-over-binary-buffers)
5. [`collections.deque` — The Double-Ended Queue](#5-collectionsdeque--the-double-ended-queue)
6. [`collections.ChainMap` — Layered Mappings Without Copying](#6-collectionschainmap--layered-mappings-without-copying)
7. [`heapq` — Binary Heaps on Plain Lists](#7-heapq--binary-heaps-on-plain-lists)
8. [`bisect` — Binary Search & Maintaining Sorted Order](#8-bisect--binary-search--maintaining-sorted-order)
9. [Choosing the Right Collection](#9-choosing-the-right-collection)
10. [Cheat Sheet: Common Gotchas](#10-cheat-sheet-common-gotchas)
11. [Quick-Reference Checklist](#11-quick-reference-checklist)

---

## 1. The Big Picture: Why These Collections Exist

**What this section covers, as a category:** none of these are "general-purpose" containers the way
`list`/`dict`/`set` are — each one is a **narrow specialist** that trades away generality for one
specific, dramatic improvement over what you'd get from 2.1–2.4's default tools.

| Structure | The ONE thing it fixes | What it gives up in exchange |
|---|---|---|
| `range` | A `list` of consecutive integers wastes memory proportional to length | Can't hold arbitrary values, only an arithmetic integer progression |
| `array.array` | A `list` of numbers wastes memory boxing every number as a separate object | Every element must be the *same* fixed numeric type |
| `memoryview` | Slicing `bytes`/`bytearray` always copies, even for huge buffers | Only works over objects that support the buffer protocol |
| `deque` | A `list`'s front operations (`insert(0,...)`, `pop(0)`) are O(n) | Loses O(1) random indexing by position |
| `ChainMap` | Merging several `dict`s to search them together means copying all of them | Writes always land on just one (the first) underlying mapping |
| `heapq` | Finding/removing the smallest of many items repeatedly is O(n) per call on a plain list | Only the *smallest* element is cheap to reach — no O(1) arbitrary lookup |
| `bisect` | Checking "does this belong here" in a sorted list via linear scan is O(n) | Only works if the list is *already* sorted — doesn't sort for you |

**Layman version:** `list`/`dict`/`set`/`tuple` are the standard-issue tools every household owns — a
hammer, a screwdriver, a pair of scissors. Every structure in this section is a **specialist tool from
the back of the toolbox** — a torque wrench, a wire stripper, a compass — each one built to be
dramatically better at exactly one job, and noticeably worse (or simply incapable) at everything else.
Knowing this whole section is really about pattern-matching "which specific weakness am I hitting
right now" to "which specialist tool fixes exactly that weakness" (Section 9 makes this a lookup table).

---

## 2. `range` — The Lazy Integer Sequence (Recap)

`range` already got a full bottom-up treatment in
[`01_4_control_flow.md`](01_4_control_flow.md) **Section 6** — the short version, recapped here because
it belongs conceptually in this "specialist collections" lineup: `range(start, stop, step)` stores only
three integers and computes each value on demand, giving it **O(1) memory regardless of length** —
`sys.getsizeof(range(10_000_000))` is the same tiny, fixed size as `sys.getsizeof(range(10))`, unlike
`list(range(10_000_000))`, which actually allocates ten million separate integer objects plus a pointer
array to hold them (→ `02_1_lists.md` Section 1's pointer-array model).

```python
import sys
r = range(10_000_000)
print(sys.getsizeof(r))                    # tiny, fixed — same for range(10) or range(10**9)
print(sys.getsizeof(list(range(10_000_000))))     # dramatically larger — a real materialized list
```

`range` also supports `len()`, indexing, and `in` — all as **O(1) arithmetic**, not a scan, because
knowing just `start`/`stop`/`step` is enough to answer "how many elements," "what's element `i`," and
"is `x` in here" without ever generating a single value. Full details, diagrams, and the negative-step
walkthrough live in `01_4_control_flow.md` Section 6 — go there for the complete derivation.

---

## 3. `array.array` — Densely-Packed, Typed Numeric Sequences

**What it is:** `array.array(typecode, iterable)` is a mutable sequence that stores **raw, fixed-width
C values packed directly next to each other in memory** — not, like a `list`, an array of pointers to
separately-allocated boxed objects. Every element must be the same numeric type, declared up front via
a one-character type code.

**The type-code table (the width is genuinely fixed and platform-independent for these, except `'l'`/`'L'`):**
| Code | C type | Typical size |
|---|---|---|
| `'b'` / `'B'` | signed / unsigned char | 1 byte |
| `'h'` / `'H'` | signed / unsigned short | 2 bytes |
| `'i'` / `'I'` | signed / unsigned int | 2 or 4 bytes (platform-dependent — see note) |
| `'l'` / `'L'` | signed / unsigned long | 4 or 8 bytes (**platform-dependent** — e.g. 4 bytes on Windows, 8 on 64-bit Linux/macOS) |
| `'q'` / `'Q'` | signed / unsigned long long | 8 bytes (guaranteed on any platform with `long long` support) |
| `'f'` | float | 4 bytes |
| `'d'` | double | 8 bytes |

```python
import array
a = array.array('l', range(5))
print(a.typecode, a.itemsize)          # 'l' 4   (on this build/platform — always check, don't assume)
```
**Why the platform-dependence matters:** if you need a guaranteed, portable width (e.g. writing a binary
file format that another machine will read), prefer `'q'`/`'Q'` (8 bytes, effectively always) over
`'l'`/`'L'` — a very common real bug is a file written on 64-bit Linux (`'l'` = 8 bytes there) read back
incorrectly on Windows (`'l'` = 4 bytes there).

**The memory model, bottom-up — this is the entire reason `array` exists.** `02_1_lists.md` Section 1
showed that a `list` is a C array of *pointers*, with every element living as a **separately
heap-allocated boxed object** elsewhere in memory. `array.array` stores the *actual numeric values*
inline, back-to-back, with no boxing and no pointer indirection at all — exactly the "C array of
values" mental model that Section 1 said a `list` deliberately is **not**:
```
 list of ints (pointers to boxed objects, elsewhere on the heap):

  lst ──► [ptr0][ptr1][ptr2][ptr3] ...        <- 8 bytes per pointer (64-bit)
             │     │     │     │
             ▼     ▼     ▼     ▼
            [0]  [1]  [2]  [3]   <- each is a SEPARATE ~28-byte PyLong object, elsewhere in memory

 array.array('l', ...) (raw values, packed inline, nothing elsewhere):

  arr ──► [ 0 ][ 1 ][ 2 ][ 3 ] ...            <- 4 bytes per slot, values stored DIRECTLY, no boxing
```

**Measuring the real difference (not just the container's own `getsizeof`, which understates a list's
true footprint since it excludes every object the pointers point at):**
```python
import sys, array
n = 100_000
lst = list(range(n))
arr = array.array('l', range(n))

print(sys.getsizeof(lst))                              # ~800,000 bytes — just the pointer array
print(sys.getsizeof(arr))                                  # ~408,000 bytes — the array's ENTIRE storage

# the list's pointer array alone is already bigger than array's ENTIRE footprint — and the list
# ALSO has ~100,000 separate boxed int objects elsewhere on the heap (~28 bytes each for values
# outside the small-int cache, → 01_2 §3), adding several more MB that getsizeof(lst) doesn't show:
one_boxed_int = sys.getsizeof(10**8)                          # 28 — a single non-cached int object
print(one_boxed_int)
```
The list's *reported* size is already larger than the array's entire size, and the list still has
~100,000 more boxed integer objects sitting elsewhere on the heap that `sys.getsizeof(lst)` never
counts at all — the true gap is far bigger than the two `getsizeof` numbers alone suggest.

**Why `array` doesn't replace `list` for general use:** the price of that density is losing
heterogeneity entirely (`array.array('l', [1, "x"])` raises `TypeError` immediately — every element
must fit the declared C type) and losing the rich object-oriented behavior Python objects normally
have. `array` earns its keep specifically for **large, uniform numeric buffers** — signal data, raw
sensor readings, interfacing with C libraries/structs via `struct` (→ syllabus 7.1) — not as an
everyday list replacement. (For serious numeric work at scale, `NumPy`'s `ndarray`, → syllabus 15, is
built on this exact same "packed raw values" idea but adds vectorized math on top — `array.array` is
the pure-standard-library ancestor of that idea, no math operations included.)

**Layman version:** recall `02_1_lists.md`'s coat-check rack of numbered hooks holding claim *tickets*,
with the real coats hanging elsewhere in a giant communal cloakroom. `array.array` is a completely
different piece of furniture — a labeled parts drawer with **uniform little compartments of one exact
size**, where the actual small parts (all the same kind — all bolts, say) sit *directly in* the
compartments themselves, no claim-ticket indirection at all. You can't put a "coat" in a bolt drawer —
every compartment demands the one declared shape — but for a drawer that's genuinely full of nothing
but identical bolts, this is a far more compact way to store them than hanging ten thousand individual
claim tickets on a rack.

---

## 4. `bytearray` (Recap) & `memoryview` — Zero-Copy Views over Binary Buffers

**`bytearray` recap:** already covered in depth in [`02_5_strings.md`](02_5_strings.md) **Section 10**
— the mutable, binary counterpart to the immutable `bytes` (itself the binary counterpart to `str`).
The one fact this doc needs from there: a `bytearray` is a genuinely mutable, in-place-editable buffer
of raw bytes — which is exactly what makes it a useful *target* for the tool this section actually
introduces: `memoryview`.

**What `memoryview` is:** a `memoryview` is a **zero-copy window onto another object's underlying
memory buffer** — it lets you slice, read, and even *write* into part of a `bytes`/`bytearray`/`array`
object **without copying any data**, via a CPython-wide mechanism called the **buffer protocol** (PEP
3118). Any object that exposes its raw memory in a standard way (bytes, bytearray, array.array, and
many third-party types like NumPy arrays) can be wrapped in a `memoryview`.

**The problem it solves — ordinary slicing always copies, even when you don't want it to:**
```python
ba = bytearray(b"hello world")
sub = ba[0:5]          # this is a COPY — a brand-new bytearray object, independent of ba
sub[0] = ord("H")
print(ba)                 # bytearray(b'hello world')  <- UNCHANGED — sub was never connected to ba
```

**`memoryview` gives you the opposite: a slice that stays connected to the original buffer:**
```python
ba2 = bytearray(b"hello world")
mv = memoryview(ba2)
sub_view = mv[0:5]              # a VIEW, not a copy — no bytes were duplicated
sub_view[0] = ord("H")             # writes THROUGH the view, directly into ba2's own memory
print(ba2)                            # bytearray(b'Hello world')  <- ba2 itself changed!
print(mv.obj is ba2)                     # True — the memoryview is genuinely backed by ba2's own buffer
```

**Diagram — the structural difference between the two:**
```
 Slicing a bytearray directly (COPY):          Slicing through a memoryview (VIEW):

  ba2: [h][e][l][l][o]...                       ba2: [h][e][l][l][o]...
        │                                              ▲  ▲  ▲  ▲  ▲
        ▼ (data duplicated)                            │  │  │  │  │
  sub: [h][e][l][l][o]   <- independent          mv[0:5] just points at ba2's own bytes 0-4 —
       copy, editing this                        no new storage allocated; editing THIS
       never touches ba2                         writes directly back into ba2
```

**Why this matters — bottom-up:** for a small 11-byte example the copy is free; the entire point of
`memoryview` shows up at scale. Slicing a 500 MB `bytearray` the ordinary way allocates and copies
another 500 MB (or however large the slice is); wrapping it in a `memoryview` and slicing *that*
allocates a tiny fixed-size view object regardless of how large the underlying buffer is — the same
"don't pay for what you don't need" philosophy already seen in `range` (Section 2) and PEP 393's string
storage (→ `02_5_strings.md` Section 1), now applied to binary buffers. This matters enormously for
network protocols and file parsing, where repeatedly re-slicing a large incoming buffer to peel off
headers/fields would otherwise mean constant, wasteful copying.

**`.cast()` — reinterpreting the same raw bytes as a different type, still with zero copying:**
```python
buf = bytearray((1).to_bytes(4, "little") + (2).to_bytes(4, "little"))     # 8 raw bytes
mv_int = memoryview(buf).cast("i")           # reinterpret those SAME 8 bytes as two 4-byte ints
print(list(mv_int))                             # [1, 2] — no data was moved or copied, only reinterpreted
```

**`.release()`:** a `memoryview` holds a lock on its source buffer while it's alive — the source can't
be resized while a view exists (e.g. `bytearray.resize()` will refuse while a `memoryview` is open on
it). Call `.release()` (or use it as a context manager, `with memoryview(x) as mv:`) when you're done,
so the underlying object is free to resize/be garbage-collected promptly.

**Layman version:** an ordinary slice is a photocopier — ask it for pages 1 through 5, and it hands you
brand-new paper with those pages duplicated onto it; scribble on the copy, the original book is
untouched. A `memoryview` is a **transparent plastic overlay with a cut-out window**, laid directly on
top of the *original* book, showing (and letting you write on, through the cut-out) exactly pages 1
through 5 of the *actual* book underneath — nothing was ever copied, so anything you write through the
window changes the real page. `.cast()` is like relabeling that same window to read the same underlying
ink as a different unit (say, reading four adjacent letters as one four-letter word instead) without
moving a single drop of ink.

---

## 5. `collections.deque` — The Double-Ended Queue

`02_1_lists.md` **Section 7** already derived *why* `deque` can do what a plain `list` structurally
cannot: a `list` is one contiguous pointer array (→ `02_1_lists.md` Section 1), so inserting/removing at
the *front* means shifting every remaining pointer — O(n) — while `deque` gives up strict single-array
contiguity in exchange for a **doubly-linked list of fixed-size blocks**, so both ends support O(1)
insertion/removal (that section explicitly deferred `maxlen`/`.rotate()`/full API coverage to *here*).

**Quick recap of the core operations (full derivation + diagram: `02_1_lists.md` Section 7):**
```python
from collections import deque
dq = deque([1, 2, 3])
dq.append(4)          # O(1) — add at the right end
dq.appendleft(0)          # O(1) — add at the left end (a list has NO O(1) equivalent for this)
print(dq.pop(), dq.popleft())     # 4 0  — O(1) removal at either end
print(dq)                            # deque([1, 2, 3])
```
**The one thing a `deque` gives up in return:** random indexed access, `dq[500]`, is **O(n)** — the
structure may have to walk block-to-block to reach an arbitrary middle position, something a `list`'s
single contiguous array does in O(1). This is the deliberate trade Section 1 of this doc's table names:
"loses O(1) random indexing by position."

**`maxlen` — a bounded deque, i.e. a ring buffer / sliding window, built in:**
```python
dq = deque(maxlen=3)
for i in range(5):
    dq.append(i)
    print(i, list(dq))
# 0 [0]
# 1 [0, 1]
# 2 [0, 1, 2]
# 3 [1, 2, 3]      <- appending past maxlen SILENTLY evicts from the OPPOSITE end (here, the left)
# 4 [2, 3, 4]
```
**Why this is the single most common real-world use of `deque`:** "keep only the last N items seen"
(a sliding window over a stream, a fixed-size recent-history log, a simple LRU-adjacent cache) is
exactly what a bounded `deque` gives you for free — every `append()` beyond `maxlen` automatically
evicts the oldest element from the far end, with no manual bookkeeping (`if len(x) > n: x.pop(0)`)
needed, and no O(n) shifting cost either.

**`.rotate(n)` — cyclically shift all elements by `n` positions, O(k) where `k = abs(n)`, not O(len):**
```python
dq2 = deque([1, 2, 3, 4, 5])
dq2.rotate(2)          # positive n: rotate elements toward the RIGHT (wrap around)
print(list(dq2))          # [4, 5, 1, 2, 3]
dq2.rotate(-2)               # negative n: rotate toward the LEFT
print(list(dq2))                # [1, 2, 3, 4, 5]  — back to the original order
```
`rotate` is implemented as repeated `pop`/`appendleft` (or the mirror) internally — cheap precisely
*because* those are each O(1) on a `deque`, another direct payoff of the block-based structure.

**Layman version:** picture several *short* coat racks chained end to end (the `02_1_lists.md` Section
7 analogy) — pulling a coat off the very first hook of the very first mini-rack, or hanging one on the
very last hook of the very last mini-rack, never disturbs any other rack. A bounded `deque` (`maxlen`)
is the same chain of racks with a hard rule taped to it: "the instant a new coat comes in past our
capacity, the oldest coat at the far end gets automatically kicked off to make room" — a self-managing
coat check that never needs to be told to clear out old inventory. `.rotate()` is walking down the
entire chain and shifting every coat over by a fixed number of hooks, wrapping the ones that fall off
one end back onto the other.

---

## 6. `collections.ChainMap` — Layered Mappings Without Copying

**What it is:** `ChainMap(map1, map2, ...)` presents **several mappings as if they were one**, searched
in the order given, **without merging, copying, or modifying any of them**. It's the mapping
counterpart to `memoryview` (Section 4) in spirit — a lightweight *view* over existing storage, not a
new copy of it.

**The problem it solves — merging dicts to search them together wastes memory and goes stale:**
```python
defaults = {"color": "blue", "size": "M"}
user_prefs = {"size": "L"}

merged = {**defaults, **user_prefs}          # a real, independent COPY — now two sources of truth
                                                 # exist; if `defaults` changes later, `merged` won't see it
```

**`ChainMap` instead layers the *same* underlying dicts, live, in lookup-priority order:**
```python
from collections import ChainMap
cm = ChainMap(user_prefs, defaults)          # user_prefs is searched FIRST, defaults is the fallback
print(cm["size"])          # 'L'  — found in user_prefs (first map), so defaults is never even checked
print(cm["color"])            # 'blue' — NOT in user_prefs, falls through to defaults
```

**The critical gotcha this doc's audit flagged: writes ALWAYS go to the *first* mapping only, never
wherever the key currently "lives":**
```python
cm["color"] = "red"          # color currently resolves from defaults, but the WRITE still targets maps[0]
print(user_prefs)               # {'size': 'L', 'color': 'red'}  <- user_prefs was modified!
print(defaults)                    # {'color': 'blue', 'size': 'M'}  <- UNCHANGED — 'blue' is now shadowed,
                                       # not overwritten — cm['color'] reads 'red' from user_prefs
                                       # first, but the OLD 'blue' is still sitting in defaults underneath
```
**Why:** `ChainMap` doesn't "know" or care which underlying map a key's *current* value came from when
you write — `__setitem__` is unconditionally implemented as "write to `self.maps[0]`." This is
deliberate: the whole point is a stack of override layers, and a write is always meant as "record an
override at the top layer," never as "go find and mutate whatever layer happens to currently answer
this key."

**`.maps` — the live list of underlying mappings, and `.new_child()` — pushing a new override layer
without disturbing the chain beneath it:**
```python
print(cm.maps)          # [{'size': 'L', 'color': 'red'}, {'color': 'blue', 'size': 'M'}]

child = cm.new_child({"extra": 1})          # a NEW ChainMap with one more layer stacked on FRONT
print(child.maps)                              # [{'extra': 1}, {'size': 'L', 'color': 'red'}, {...}]
```

**The canonical practical use case — layered configuration, checked in priority order (command-line
overrides > environment variables > file-based defaults), without ever physically merging three
separate config sources into one throwaway dict** (→ `02_3_dictionaries.md`, which this directly
builds on — every read/iteration behavior a `ChainMap` exposes ultimately delegates down to ordinary
`dict` mechanics on each layer):
```python
cli_args = {"verbose": True}
env_vars = {"verbose": False, "timeout": 30}
file_defaults = {"verbose": False, "timeout": 10, "retries": 3}

config = ChainMap(cli_args, env_vars, file_defaults)
print(config["verbose"], config["timeout"], config["retries"])     # True 30 3
```

**Layman version:** think of three transparency sheets stacked on an overhead projector, each with some
values filled in and some left blank — you read the *combined* image, and wherever the top sheet has an
actual mark, it's what you see; wherever it's blank, your eye falls through to whatever the sheet
beneath has drawn. Nobody ever traces a fourth, merged sheet — you're just looking through the stack as
it sits. But if you pick up a pen to "correct" what you're seeing, you can only ever draw on the very
**top** sheet — writing "red" over a spot that used to show through as "blue" from a lower sheet doesn't
erase or repaint that lower sheet's blue mark; it just adds a new mark on top that now blocks it from
view.

---

## 7. `heapq` — Binary Heaps on Plain Lists

**What it is:** a **binary min-heap** — a structure that keeps "give me the smallest element" cheap
(`O(log n)`), even though it never fully sorts anything. `heapq` is unusual among the structures in this
doc: it is **not a class or container type at all** — it's a set of module-level *functions*
(`heappush`, `heappop`, `heapify`, ...) that operate on a **plain ordinary `list`**, which you supply
and which they rearrange in place.

**Why `heapq` deliberately isn't its own class — a genuine, documented design choice, not an oversight:**
letting you keep the underlying storage as a plain `list` means you get every ordinary list operation
(`len()`, iteration, indexing, pickling, `sorted()`ing a snapshot) for free, with the heap functions
layered on top only when you actually need heap-specific behavior — no wrapper class, no hidden extra
object, no API surface to learn beyond "call these five functions on your list."

**The heap invariant and the array-index math that makes it work — the actual bottom-level mechanism:**
a binary heap is conceptually a binary tree where every parent is `<=` both its children — but instead
of building actual tree nodes with left/right pointers, `heapq` stores that tree **flattened into a
plain list**, using pure arithmetic to find "the children of the node at index `i`":
```
 Heap invariant (parent <= children), stored as a flat list:

 index:        0    1    2    3    4    5
 value:      [ 1 ,  2 ,  3 ,  5 ,  4 ,  8 ]

 as a tree:              1  (index 0)
                       /    \
                     2        3           (indices 1, 2)
                    / \      /
                   5   4    8              (indices 3, 4, 5)

 the rule, purely arithmetic, no pointers at all:
   children of index i  are at indices  2*i + 1  and  2*i + 2
   parent of index i    is at index     (i - 1) // 2
```
This is exactly why `heapq` can operate on a bare `list` — "find this node's children" is just index
arithmetic on the same flat array, never a separate linked-node traversal.

**Complexity of the core operations:**
| Operation | Cost | What it does |
|---|---|---|
| `heapq.heappush(h, x)` | O(log n) | add `x`, then "bubble" it up until the heap invariant holds again |
| `heapq.heappop(h)` | O(log n) | remove and return the smallest element, then re-settle the heap |
| `heapq.heapify(lst)` | O(n) | rearrange an existing plain list into valid heap order **in place** — cheaper than `n` individual pushes |
| `h[0]` | O(1) | peek at the smallest element *without* removing it — the root is always at index 0 |

```python
import heapq
h = [5, 1, 3, 2, 4]
heapq.heapify(h)              # O(n) — now a valid heap, NOT a fully sorted list (don't expect [1,2,3,4,5])
print(h)                          # e.g. [1, 2, 3, 5, 4] — invariant holds, but this is NOT sorted order
heapq.heappush(h, 0)                 # O(log n)
print(heapq.heappop(h), h)              # 0  [1, 2, 3, 5, 4]  — smallest is always cheap to pull
```

**Python's min-heap-only limitation, and the standard negate trick for a max-heap:** `heapq` only ever
gives you the *smallest* element cheaply — there's no built-in max-heap variant. The standard
workaround: store the **negated** values, so the mathematically-smallest negated value corresponds to
the actual-largest original value:
```python
nums = [5, 1, 3, 2, 4]
maxheap = [-x for x in nums]
heapq.heapify(maxheap)
print(-heapq.heappop(maxheap))          # 5 — the actual MAXIMUM, recovered by negating back
```

**The tie-breaking gotcha — comparing heap entries that aren't themselves comparable:** heap entries are
commonly `(priority, item)` tuples so items can be prioritized; but if two entries share the same
priority, Python falls back to comparing the *second* tuple element to break the tie — which raises
`TypeError` the moment `item` is something with no natural ordering (like a plain `dict`). **The fix:
insert a unique, always-comparable tiebreaker (e.g. an incrementing counter) as the middle element:**
```python
import itertools
counter = itertools.count()          # an infinite, always-increasing, always-comparable sequence
pq = []
heapq.heappush(pq, (1, next(counter), {"a": 1}))
heapq.heappush(pq, (1, next(counter), {"b": 2}))     # SAME priority (1) as the entry above
print(heapq.heappop(pq))                                # (1, 0, {'a': 1}) — resolved by counter, no TypeError
print(heapq.heappop(pq))                                   # (1, 1, {'b': 2})
```
Without the counter in the middle, both pushes above would work fine individually, but the moment two
equal-priority entries needed to be compared against each other during a push/pop, Python would attempt
`{"a": 1} < {"b": 2}` and raise `TypeError: '<' not supported between instances of 'dict' and 'dict'`.
The counter guarantees the second tuple slot is always distinct and always orderable, so the comparison
*never actually reaches* the un-comparable third element.

**Layman version:** a heap is a triage nurse's clipboard — it never bothers fully sorting the entire
waiting room by severity, it only ever guarantees that whoever's called next is truly the most urgent
patient currently waiting, and re-checking that guarantee after each new arrival or departure is cheap
(a quick local reshuffle, not a full re-sort). The "no max-heap" trick is the nurse writing every
priority number as a negative, so "most urgent" and "smallest number" always mean the same thing to the
clipboard's simple rule. The tie-breaking counter is a ticket-number stapled to every patient's chart
specifically so that if two patients ever have the *exact* same severity score, the clipboard has an
unambiguous, always-comparable number to fall back on instead of trying (and failing) to compare the
patients' actual medical charts directly against each other.

---

## 8. `bisect` — Binary Search & Maintaining Sorted Order

**What it is:** the `bisect` module answers "where in this **already-sorted** list should `x` go, to
keep it sorted?" in **O(log n)**, via binary search — and optionally performs the insertion for you.

**The critical precondition this doc's audit flagged — `bisect` never checks or sorts for you; feeding
it an unsorted list produces a silently wrong (not an error!) answer:**
```python
import bisect
unsorted = [5, 3, 1, 4, 2]
print(bisect.bisect_left(unsorted, 3))          # 5 — A number is confidently returned, no exception —
                                                    # but it is MEANINGLESS, since the precondition
                                                    # (sorted input) was never met; binary search
                                                    # silently assumes sortedness and never verifies it
```
**Why no error is raised:** binary search's entire O(log n) speed comes from *trusting* the sorted
precondition to eliminate half the remaining search space at every step, without ever inspecting most
of the list — it structurally cannot detect "this input wasn't sorted" without doing an O(n) scan
first, which would defeat the entire point of using binary search at all.

**`bisect_left` vs `bisect_right` — where equal elements land:**
```python
sorted_list = [1, 3, 3, 5, 7]
print(bisect.bisect_left(sorted_list, 3))          # 1 — insertion point BEFORE existing equal elements
print(bisect.bisect_right(sorted_list, 3))            # 3 — insertion point AFTER existing equal elements
```
Both are valid "keeps it sorted" positions when duplicates of the search value are already present —
which one you want depends on whether a new equal element should sort before or after existing equal
ones (e.g. for a stable "insert new items after any existing ties" policy, use `bisect_right`).

**`bisect.insort` — convenience, but with a real, often-overlooked cost:**
```python
sorted_list = [1, 3, 3, 5, 7]
bisect.insort(sorted_list, 4)          # finds the position (O(log n)) AND inserts it for you
print(sorted_list)                        # [1, 3, 3, 4, 5, 7]
```
**Why `insort` is not simply "O(log n)" overall, despite the fast search:** finding *where* to insert is
O(log n), but a plain Python `list` is a contiguous array (→ `02_1_lists.md` Section 1) — actually
inserting into the middle still requires shifting every element after that position one slot over,
which is **O(n)**. `bisect.insort`'s total cost is therefore O(log n) search + O(n) shift = **O(n)
overall**, same asymptotic cost as `list.insert()` alone — the binary search only saves you from also
having to do an O(n) *linear scan* to find the spot; it does not make the insertion itself free.

**Contrast with `heapq` (Section 7) — genuinely different jobs, easy to conflate:** `bisect` answers
"where does this belong in sorted *position* order, and let me look at/iterate everything in that
order"; `heapq` answers "let me repeatedly and cheaply pull out just the *current smallest*, without
caring about the relative order of everything else." If you need the full sorted sequence available at
every step (e.g. for range queries, `sorted_list[lo:hi]`), reach for `bisect`; if you only ever need
"give me the next smallest, one at a time" (a scheduler, a priority queue), reach for `heapq` — using
`bisect.insort` in a loop just to repeatedly pull the minimum is strictly worse than `heapq` for that
job (O(n) per insert vs `heapq`'s O(log n) per push).

**Layman version:** `bisect` is a librarian who can find *exactly* which slot a new book belongs in on
an alphabetized shelf almost instantly, by repeatedly halving the search range (never checking every
book one by one) — but the shelf has to have been alphabetized already, or the "correct slot" the
librarian confidently points to is meaningless. And even once the slot is found instantly, physically
sliding every book after that point down to make room still takes real, proportional effort — finding
the spot fast doesn't make the shelving itself instant. `heapq`, by contrast, is a different librarian
who never bothers alphabetizing the shelf at all — they just always know, cheaply, which single book on
the whole shelf is currently the "most urgent" one to hand you next.

---

## 9. Choosing the Right Collection

A decision guide spanning all of Section 2 (2.1–2.6) — start from what you actually need, not from
which structure you already know best:

| If you need... | Reach for | Why (→ section) |
|---|---|---|
| An ordered, mutable, heterogeneous general-purpose sequence | `list` | The default — general-purpose, O(1) indexing (→ 2.1) |
| An ordered, immutable, hashable sequence (safe as a dict key) | `tuple` | Immutability + hashability (→ 2.2) |
| Fast key→value lookup | `dict` | O(1) average hash-table lookup (→ 2.3) |
| Fast membership testing / uniqueness, order doesn't matter | `set` | O(1) average membership, no ordering guarantee (→ 2.4) |
| Text data | `str` | Immutable Unicode code-point sequence (→ 2.5) |
| A long run of consecutive integers, without materializing them | `range` | O(1) memory regardless of length (→ Section 2) |
| A large buffer of same-typed numbers, memory-density matters | `array.array` | Raw packed C values, no per-element boxing (→ Section 3) |
| To slice/mutate part of a large binary buffer without copying it | `memoryview` | Zero-copy view via the buffer protocol (→ Section 4) |
| Fast append/pop at **both ends** (queue, sliding window, BFS frontier) | `collections.deque` | O(1) both ends via block-based linked storage (→ Section 5) |
| "Keep only the last N items seen," automatically | `collections.deque(maxlen=N)` | Built-in bounded ring-buffer eviction (→ Section 5) |
| Layered config/lookup across several dicts, without merging/copying | `collections.ChainMap` | Live layered view, first-match wins on read, writes hit layer 0 (→ Section 6) |
| Repeatedly pull the smallest/highest-priority item, cheaply | `heapq` | O(log n) push/pop of the current minimum (→ Section 7) |
| Maintain a sorted list and find insertion points fast | `bisect` | O(log n) search (though O(n) insertion) on pre-sorted data (→ Section 8) |

**Layman version:** this table is the master index for the whole specialist-toolbox analogy from
Section 1 — instead of memorizing every tool's shape, start every decision from "what am I actually
struggling to do right now," find that row, and let the row tell you which specialist tool was built
for exactly that struggle.

---

## 10. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `array.array('i', [1, "x"])` or a similar append raises `TypeError` | `array` enforces ONE fixed numeric type for every element — no heterogeneity like `list` allows (Section 3) | Use a `list` if you genuinely need mixed types; keep `array` elements uniform |
| `array.array('b', ...).append(200)` raises `OverflowError` | The chosen type code's range was exceeded (`'b'` is signed, -128..127) (Section 3) | Pick a wider/unsigned type code (`'B'`, `'h'`, `'i'`, ...) that can hold the actual value range |
| A binary file written on one machine reads back with wrong values on another | Used `'l'`/`'L'` (platform-dependent width) instead of a fixed-width code (Section 3) | Use `'q'`/`'Q'` (8 bytes, effectively guaranteed) for portable binary formats |
| Mutating a slice of a `bytes`/`bytearray` doesn't affect the original | A plain slice always COPIES (Section 4) — this is often exactly what you want, but not if you intended a live view | Use `memoryview(obj)[start:stop]` instead for a zero-copy, writable view onto the same buffer |
| `bytearray.resize()` (or similar) raises `BufferError` | An open, un-released `memoryview` is still holding a lock on that buffer (Section 4) | Call `.release()` on the memoryview (or use it as a `with` context manager) before resizing/discarding the source |
| `deque[500]` feels slower than expected compared to `list[500]` | Random indexed access on a `deque` is O(n) — it may have to walk block-to-block (Section 5) | Use a `list` when you need frequent random access by index; use `deque` for end-operations, not middle lookups |
| Old items you expected to still be in a `deque` have silently disappeared | `maxlen` was set, and appending past capacity SILENTLY evicts from the opposite end (Section 5) | This is the intended ring-buffer behavior — remove `maxlen` if unbounded history is actually required |
| Updating a `ChainMap` value doesn't seem to change the dict you expected | `ChainMap` writes ALWAYS target `maps[0]` (the first mapping), never wherever the key currently resolves from (Section 6) | Write directly to the specific underlying dict if you need to modify a deeper layer; `cm.maps[i][key] = ...` |
| `heapq.heapify()`'d list, printed, doesn't look "sorted" | A heap only guarantees the invariant (parent ≤ children) and O(1) access to the MINIMUM — it is NOT a fully sorted sequence (Section 7) | Use `sorted(h)` (or repeated `heappop`) if you need the fully sorted order, not just cheap min-access |
| `TypeError: '<' not supported between instances of 'dict' and 'dict'` from a `heapq` push/pop | Two heap entries had equal priority, and Python fell back to comparing the un-comparable payload (Section 7) | Add a unique, always-comparable tiebreaker as the middle tuple element: `(priority, next(counter), item)` |
| `bisect` returns a confident-looking index on data that isn't actually sorted | `bisect` NEVER verifies its precondition — it silently trusts the input is already sorted (Section 8) | Only ever call `bisect`/`insort` on genuinely sorted data; sort first if there's any doubt |
| `bisect.insort` in a hot loop is slower than expected | The search is O(log n), but the actual list insertion still shifts elements — O(n) overall (Section 8) | If you only need "give me the current minimum repeatedly," use `heapq` instead — it avoids the O(n) shift entirely |

---

## 11. Quick-Reference Checklist

Use this whenever you're reasoning about which "specialist" collection to reach for:

1. Am I about to materialize a huge `list` of consecutive integers I'll only ever iterate once? A
   `range` object gives the same iteration for O(1) memory. (→ Section 2)
2. Is every element in this collection going to be the same numeric type, and is memory density
   actually a concern (large buffers, C interop)? Consider `array.array` over `list`. (→ Section 3)
3. Am I about to slice/mutate part of a large `bytes`/`bytearray`/`array` buffer? Would a
   `memoryview` avoid an unnecessary full copy? (→ Section 4)
4. Do I need genuine O(1) operations at **both ends** of a sequence (a queue, a sliding window, a BFS
   frontier) — not just at the end a `list` is already good at? (→ Section 5, `02_1_lists.md` §7)
5. Do I only ever need to remember the last N items seen? `deque(maxlen=N)` gives automatic eviction
   for free, with no manual bookkeeping. (→ Section 5)
6. Am I merging several dicts together just to search them in priority order? A `ChainMap` avoids the
   copy — but remember: writes always land on the FIRST mapping only. (→ Section 6)
7. Do I need the true minimum/maximum of a changing collection repeatedly, without needing everything
   else in sorted order? `heapq` gives O(log n) push/pop of just that one element. (→ Section 7)
8. If using `heapq` with tuple entries, have I added a unique, always-comparable tiebreaker to avoid a
   `TypeError` the moment two priorities happen to be equal? (→ Section 7)
9. Am I about to call `bisect`/`insort` on data I haven't actually verified is sorted? There's no
   built-in check — a silently wrong answer, not an error, is what you'll get. (→ Section 8)
10. Am I choosing between `bisect.insort` (keeps full sorted order visible, but O(n) per insert) and
    `heapq` (cheap repeated min-extraction, no full ordering) based on which one I actually need — not
    just habit? (→ Sections 7 & 8)
11. When in doubt, can I trace my actual need back to Section 9's decision table, rather than reaching
    for whichever structure I already happen to know best?
