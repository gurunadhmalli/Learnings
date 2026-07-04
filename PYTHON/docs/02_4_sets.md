# 2.4 Sets — Complete Deep-Dive Guide

This is the companion reference for **Section 2.4** of [`python_full_syllabus.md`](python_full_syllabus.md).
Same format as [`02_1_lists.md`](02_1_lists.md), [`02_2_tuples.md`](02_2_tuples.md), and
[`02_3_dictionaries.md`](02_3_dictionaries.md): **what it is → why it exists → how it works, all the
way down to memory and the CPython runtime → a plain-English analogy**. A `set` is the simplest of the
four built-in "hash-based" structures to explain, precisely *because* you've already done the hard
work in `02_3_dictionaries.md` — a set is, almost exactly, **"a dict with no values, just keys."**
This doc leans on that relationship constantly rather than re-deriving hash-table mechanics from
scratch.

> **A note on gaps in the syllabus outline.** Before writing this, I compared the original 2.4 bullet
> list against what mastering sets actually requires, and found real gaps. I've folded all of them in
> here (and added short bullets back into the syllabus so the outline stays honest):
> - **The empty-set gotcha** — `{}` is a `dict`, not a set, and this trips up almost everyone once —
>   wasn't mentioned at all (→ Section 2).
> - **How a set actually achieves O(1) membership testing** — the hash-table mechanics — was implied
>   by "hashability" but never actually explained; this is exactly the "bottom-level" gap section 2.1
>   and 2.3 kept promising an explanation for (→ Section 1).
> - **Sets are UNORDERED** — a direct, important contrast with `dict`'s Python 3.7+ ordering
>   guarantee (→ `02_3_dictionaries.md` Section 5) — was never stated (→ Section 1).
> - **Operators (`|`, `&`, `-`, `^`) vs methods (`.union()`, etc.) behave differently with non-set
>   iterables** — operators require both sides to already be sets; methods accept any iterable. This
>   real, commonly-hit distinction wasn't in the outline (→ Section 4).
> - **In-place set operators/methods** (`|=`, `.intersection_update()`, etc.) weren't listed separately
>   from their new-set-returning counterparts (→ Section 4).
> - **`remove()` vs `discard()` vs `pop()`'s failure/return behaviors** weren't distinguished — this is
>   the same category of gap `02_3_dictionaries.md` Section 3 covered for dict access (→ Section 5).
> - **Frozensets are hashable and can themselves be set elements or dict keys** — the direct set-world
>   parallel to `02_2_tuples.md`'s "tuple vs list" hashability story — wasn't connected explicitly
>   (→ Section 6).
> - **`set(lst)` for dedup loses order; `dict.fromkeys(lst)` preserves it** — a genuinely useful,
>   commonly-needed idiom that ties this doc directly back to `02_3_dictionaries.md` (→ Section 8).

Read it beginner-first (skim "What it is" and "Layman version") or internals-first (read the
"bottom-up" blocks) — both paths are here.

---

## Table of Contents

1. [The Big Picture: What a Set *Actually* Is — "A Dict With No Values"](#1-the-big-picture-what-a-set-actually-is--a-dict-with-no-values)
2. [Creation, Uniqueness & the Empty-Set Gotcha](#2-creation-uniqueness--the-empty-set-gotcha)
3. [Adding & Removing Elements: `add`, `update`, `remove`, `discard`, `pop`](#3-adding--removing-elements-add-update-remove-discard-pop)
4. [Set Operations: Operators vs Methods, In-Place Variants](#4-set-operations-operators-vs-methods-in-place-variants)
5. [Subset/Superset Comparisons & `isdisjoint()`](#5-subsetsuperset-comparisons--isdisjoint)
6. [Frozensets — the Hashable, Immutable Set](#6-frozensets--the-hashable-immutable-set)
7. [Set Comprehensions](#7-set-comprehensions)
8. [Practical Idioms: Membership Testing & Deduplication](#8-practical-idioms-membership-testing--deduplication)
9. [Cheat Sheet: Common Gotchas](#9-cheat-sheet-common-gotchas)
10. [Quick-Reference Checklist](#10-quick-reference-checklist)

---

## 1. The Big Picture: What a Set *Actually* Is — "A Dict With No Values"

**What it is:** a `set` is an unordered collection of **unique, hashable** elements, supporting
average **O(1)** membership testing, insertion, and removal — plus the classic mathematical set
operations (union, intersection, difference).

**The relationship to `dict` — not just an analogy, a genuine structural fact:** recall from
`02_3_dictionaries.md` Section 1 that a `dict` achieves O(1) average lookup by hashing each key to
compute a slot index directly, resolving collisions via open addressing, and (since Python 3.6) storing
entries in a separate insertion-ordered dense array alongside a sparse hash-indexed table. **A `set` is
built from almost exactly the same underlying hash-table machinery — just with the "value" half of
each entry thrown away.** Historically in CPython's source, `set` and `dict` genuinely share
conceptual DNA (set's implementation was derived from dict's, and optimizations discovered for one have
historically influenced the other):

```
 dict entry:  [ hash | key | value ]      <- stores THREE things per slot
 set entry:   [ hash | key         ]      <- stores only TWO — no value slot at all

 dict:  d["alice"] = 30   →  hash("alice") locates a slot  →  slot holds ("alice", 30)
 set:   s.add("alice")     →  hash("alice") locates a slot  →  slot holds just "alice" (presence = membership)
```

**Why this one structural fact explains everything in this section:**
- **O(1) average membership testing (`x in s`)** works for exactly the same reason `d[key]` is O(1)
  average in `02_3_dictionaries.md` Section 1 — hash the element, jump nearly straight to its slot,
  no linear scan (contrast directly with `x in list`, O(n), → `02_1_lists.md` Section 8).
- **Elements must be hashable**, for exactly the same reason dict *keys* must be hashable
  (→ `02_3_dictionaries.md` Section 2, → `02_2_tuples.md` Section 5) — there's no meaningful way to
  compute a slot index for something that can't produce a stable hash.
- **A set (unlike a `dict`) makes NO insertion-order guarantee.** This is a real, important
  divergence from `dict`'s Python 3.7+ ordering promise (→ `02_3_dictionaries.md` Section 5) — CPython
  never adopted the "separate dense insertion-ordered array" design for `set` the way it did for
  `dict`, so a set's iteration order depends purely on each element's hash value and the table's
  current size, and can appear to reorder after resizing:
```python
s = {3, 1, 2}
print(s)                    # {1, 2, 3}  — NOT insertion order; happens to look sorted here by coincidence
                                # of small-int hashing, but this is NOT a guarantee — never rely on it

s2 = {5, 4, 3, 2, 1, 0}
print(s2)                     # {0, 1, 2, 3, 4, 5} — again looks "sorted," purely incidental to how
                                 # small ints hash (hash(n) == n for small ints) — try it with strings
                                 # or larger/negative numbers and the illusion breaks immediately
```

**Layman version:** if `02_3_dictionaries.md`'s dict was a library card-catalog with a title *and* a
shelf location on every card, a set is the exact same catalog drawer with the shelf-location half of
every card torn off — all that's left is "yes, this title is definitely in here" or "no, it isn't."
You still get the fast hash-based lookup speed from the same underlying filing system, you just never
asked the catalog to remember any extra information beyond bare presence. And — critically — this
catalog was never built with the "keep a separate ordered logbook" upgrade that the value-carrying
dict catalog got; ask this drawer to list everything and you'll get it back in whatever shelf-hash
order it happens to be sitting in right now, not the order you filed things.

---

## 2. Creation, Uniqueness & the Empty-Set Gotcha

**Creating a set:**
```python
s1 = {1, 2, 3}                    # set literal — curly braces, no colons (that's what distinguishes it from a dict)
s2 = set([1, 2, 2, 3, 3, 3])         # set() constructor from any iterable — DUPLICATES ARE SILENTLY DROPPED
print(s2)                               # {1, 2, 3}
s3 = set("hello")                          # {'h', 'e', 'l', 'o'} — iterates a string char-by-char, dedups
```

**The empty-set gotcha — `{}` is ALWAYS a dict, never an empty set:**
```python
empty_dict = {}
empty_set = set()

print(type(empty_dict))     # <class 'dict'>
print(type(empty_set))        # <class 'set'>
```
**Why — a grammar-level ambiguity resolved in dict's favor:** Python's `{}` literal syntax is shared
between dict and set literals — `{1, 2, 3}` (no colons) is a set, `{"a": 1}` (with colons) is a dict —
but an *empty* pair of braces gives the parser no colons to disambiguate with. Rather than guess, the
language simply defines `{}` to always mean "empty dict," for historical reasons (dict literals
predate set literals in the language) — you must call `set()` explicitly any time you want an empty
set. This is a very common real bug: writing `cache = {}` intending a set and getting a dict instead
(usually only discovered when `.add()` fails with `AttributeError: 'dict' object has no attribute
'add'`).

**Uniqueness is enforced automatically and silently, not by raising an error on a duplicate:**
```python
s = {1, 2, 2, 3}
print(s)     # {1, 2, 3} — no error, no warning; the second "2" is simply never added (it's already present)
```
**How it works — bottom-up:** exactly like a dict's key insertion (→ `02_3_dictionaries.md` Section
1), adding an element hashes it and probes to its slot; if that slot (or one reached via the probe
sequence) already holds an equal element, the "insert" is a no-op — nothing is duplicated, nothing is
overwritten, nothing raises.

**Layman version:** the empty curly braces `{}` are a bit like an unlabeled empty box in a warehouse
that historically always defaults to "assume it's a card-catalog drawer" unless you can see colon-
separated title:location pairs already inside it to prove otherwise — an empty box gives no such
proof, so the warehouse always assumes "dict" by default; ask for an empty "presence-only" drawer
explicitly (`set()`) if that's what you actually want. And when you try to file a duplicate title into
a presence-only drawer, the librarian just quietly notices "we already have this one" and does
nothing — no complaint, no second copy.

---

## 3. Adding & Removing Elements: `add`, `update`, `remove`, `discard`, `pop`

**Adding — `add()` for ONE element, `update()` for MERGING IN elements from other iterables:**
```python
s = {1, 2}
s.add(3)                        # adds exactly one element
s.update([4, 5], {6, 7})           # merges in elements from any number of iterables (lists, sets, etc.)
print(s)                              # {1, 2, 3, 4, 5, 6, 7}
```
This mirrors `list.append` (one element) vs `list.extend` (many elements, → `02_1_lists.md` Section
3) exactly — same "singular vs plural" naming convention, applied to a different container.

**Removing — three different tools, three different failure/return behaviors (the same category of
distinction `02_3_dictionaries.md` Section 3 drew for dict access):**
```python
s = {1, 2, 3}

s.discard(99)         # SILENT no-op if the element isn't present — never raises
print(s)                 # {1, 2, 3} — unchanged, no error

try:
    s.remove(99)            # RAISES KeyError if the element isn't present
except KeyError as e:
    print("KeyError:", e)

x = s.pop()                  # removes and returns an ARBITRARY element — no ordering guarantee (Section 1!),
print(x, s)                     # unlike dict.popitem()'s guaranteed LIFO order (→ 02_3_dictionaries.md Section 4)
```
**Why `pop()` on a set can't promise "the last one" the way `dict.popitem()` can:** `dict.popitem()`'s
LIFO guarantee comes directly from the dense, insertion-ordered array `02_3_dictionaries.md` Section 1
described — "remove the last entry in that array" is a well-defined operation. A `set` has no such
ordered array (Section 1) — `pop()` simply removes whatever element its internal hash table happens to
encounter first during a scan of its slots, which depends on hash values and table layout, not
insertion history. Never rely on *which* element `set.pop()` removes.

**The naming-convention pattern to internalize (same one used across the whole `collections` family):**
`discard` = "remove if present, otherwise silently do nothing" (the lenient one); `remove` = "remove,
and complain loudly if it wasn't there" (the strict one) — same strict/lenient pairing philosophy as
`del d[key]` (strict) vs `.pop(key, default)` (lenient) from `02_3_dictionaries.md` Section 3.

**Layman version:** `.add()` files one new card; `.update()` dumps in a whole stack of cards from one
or more other boxes at once, silently skipping any that are already filed. `.discard()` is "throw this
card out if it's in there, and don't bother me either way"; `.remove()` is "throw this card out, and
tell me if it was never there in the first place." `.pop()` on this drawer is "just hand me *some*
card from the box" — since this drawer was never given the ordered logbook the dict-drawer had, there's
no meaningful "give me the most recent one" request to make of it.

---

## 4. Set Operations: Operators vs Methods, In-Place Variants

**The four classic mathematical set operations — available BOTH as operators and as methods:**
```python
a = {1, 2, 3}
b = {2, 3, 4}

print(a | b)          # {1, 2, 3, 4}    — UNION: everything in either
print(a.union(b))        # identical result, method form

print(a & b)              # {2, 3}          — INTERSECTION: only what's in BOTH
print(a.intersection(b))     # identical, method form

print(a - b)                  # {1}             — DIFFERENCE: in a, but NOT in b (order matters!)
print(a.difference(b))           # identical, method form

print(a ^ b)                      # {1, 4}          — SYMMETRIC DIFFERENCE: in exactly one of the two, not both
print(a.symmetric_difference(b))     # identical, method form
```

**The crucial difference between operators and methods: what they accept on the right-hand side.**
Operators (`|`, `&`, `-`, `^`) **require both operands to already be sets** — they raise `TypeError`
for a plain list/tuple. Methods accept **any iterable**, converting it internally:
```python
a = {1, 2}

try:
    print(a | [2, 3])        # TypeError: unsupported operand type(s) for |: 'set' and 'list'
except TypeError as e:
    print(e)

print(a.union([2, 3]))         # {1, 2, 3} — works fine; .union() happily accepts a plain list
```
**Why — bottom-up:** operators like `|` dispatch to dunder methods (`__or__`/`__ror__`, → syllabus
4.4) that CPython's `set` type implements to only recognize another *actual* `set`/`frozenset` as a
valid partner, returning `NotImplemented` (and thus a `TypeError`) for anything else — a deliberate,
strict design choice for operator syntax. The named methods (`.union()`, etc.) were written with a
looser contract on purpose: "accept anything iterable, and build a real set out of it internally
before combining." Neither is a bug — they're two intentionally different levels of strictness for
the same underlying operation.

**In-place variants — mutate the LEFT operand directly, instead of building a new set:**
```python
a = {1, 2, 3}
a |= {2, 3, 4}                  # in-place union — a is MUTATED directly
print(a)                           # {1, 2, 3, 4}

b = {1, 2, 3}
b.intersection_update({2, 3, 4})     # in-place intersection — same idea, method form
print(b)                                # {2, 3}

# The full in-place family: |=/.update(), &=/.intersection_update(),
#                            -=/.difference_update(), ^=/.symmetric_difference_update()
```
This is exactly the same "operator/method pair, in-place vs new-object" pattern already seen for dicts
(→ `02_3_dictionaries.md` Section 7: `|` builds new, `|=`/`.update()` mutates in place) — just now with
four operations instead of one, because sets have four natural binary operations where a plain merge
(dict) only has one.

**Layman version:** `|`/`&`/`-`/`^` are strict clerks who only know how to combine two *already-
organized* card-catalog drawers with each other — hand one a loose stack of unsorted index cards
instead of a drawer, and they refuse outright. The `.union()`/`.intersection()`/etc. methods are more
accommodating clerks who'll happily take a loose stack of cards, quietly organize them into a
temporary drawer themselves, and then do the combination — same job, more tolerant of what you hand
them. The `|=` family of clerks do their combination job **directly into your existing drawer**
instead of handing you back a brand-new one to carry away.

---

## 5. Subset/Superset Comparisons & `isdisjoint()`

**Comparison operators ask relationship questions between two sets, not "which is bigger":**
```python
a = {1, 2}
b = {1, 2, 3}

print(a < b)      # True  — a is a PROPER subset of b (all of a's elements are in b, and b has more)
print(a <= b)       # True  — a is a subset of b (proper OR equal)
print(a <= a)         # True  — a set is always a subset of itself (non-proper)
print(a < a)            # False — NOT a PROPER subset of itself (proper requires strictly fewer elements)

print(b > a)              # True  — b is a proper SUPERSET of a
print(b >= a)               # True  — b is a superset of a (proper or equal)

print(a == {2, 1})            # True  — set equality ignores order entirely (there IS no order, Section 1)
```
**Why these read naturally as `<`/`<=` rather than feeling arbitrary:** subset is genuinely a partial
ordering relationship (analogous to "is this a smaller-or-equal collection, containment-wise"), which
is precisely what `<`/`<=` are used to express elsewhere — Python's designers deliberately overloaded
these operators (→ syllabus 4.4, operator overloading) for sets because the mathematical analogy holds
up cleanly, unlike, say, trying to force `+` to mean something for sets beyond union (which Python
correctly does NOT do — sets have no `+` operator at all, only `|`).

**`isdisjoint()` — "do these two sets share absolutely nothing in common?":**
```python
print({1, 2}.isdisjoint({3, 4}))     # True  — no overlap at all
print({1, 2}.isdisjoint({2, 3}))       # False — they share the element 2
```
This is a genuinely useful shortcut over `len(a & b) == 0` — it's also more efficient, since CPython
can short-circuit and return `False` the instant it finds a single shared element, without needing to
actually build the full intersection set first.

**Layman version:** `a <= b` is asking "is every card in drawer A also somewhere in drawer B?" — if
yes, A is (at most) a smaller sub-collection nested inside B's contents. `isdisjoint` is a quick yes/no
question — "do these two drawers share literally any card at all?" — answerable the instant a single
shared card turns up, no need to lay out the full overlap first.

---

## 6. Frozensets — the Hashable, Immutable Set

**What it is:** `frozenset` is to `set` exactly what `tuple` is to `list` (→ `02_2_tuples.md` Sections
1 and 5) — an immutable variant with the identical read-side behavior, but none of the mutating
methods, and — crucially — **hashable**, which a plain `set` is not.

```python
s = {1, 2, 3}
try:
    hash(s)                  # TypeError: unhashable type: 'set' — plain sets can change, so can't be hashed
except TypeError as e:
    print(e)

fs = frozenset([1, 2, 3])
print(hash(fs))                 # works fine — frozensets are guaranteed never to change after creation
```

**Why this matters — the direct parallel to `02_2_tuples.md` Section 5's tuple-as-dict-key story: a
frozenset can be a set ELEMENT or a dict KEY, exactly because it's hashable:**
```python
d = {}
d[frozenset([1, 2])] = "a compound, order-independent key"
print(d[frozenset([2, 1])])     # "a compound, order-independent key" — SAME frozenset, order doesn't matter!

nested = {frozenset([1, 2]), frozenset([3, 4])}     # a set... of frozensets
print(nested)
```
Notice `frozenset([1, 2])` and `frozenset([2, 1])` are treated as the exact same dict key — unlike a
tuple (where `(1, 2)` and `(2, 1)` are different keys, since a tuple's order is part of its identity),
a frozenset's equality/hash genuinely ignore element order, exactly like a plain set's `==` does
(Section 5) — this makes `frozenset` specifically the right tool when you need an **order-independent
compound key** (e.g., "this exact combination of tags, regardless of what order they were added in").

**Frozensets support every read-only set operation, just no mutation:**
```python
fs1 = frozenset([1, 2, 3])
fs2 = frozenset([2, 3, 4])
print(fs1 | fs2)          # frozenset({1, 2, 3, 4}) — union works, returns ANOTHER frozenset
print(fs1 & fs2)             # frozenset({2, 3})
try:
    fs1.add(5)                    # AttributeError: 'frozenset' object has no attribute 'add'
except AttributeError as e:
    print(e)
```

**Layman version:** a `frozenset` is a card-catalog presence-drawer that's been sealed shut and welded,
exactly like the tuple-vs-list relationship from `02_2_tuples.md` — you can still ask it every read-
only question a normal drawer answers (what's in here, does it overlap with that other drawer), but
you can never add or remove a card again. And because it's permanently sealed, it's now trustworthy
enough to get its own claim-check stamp (a hash) — meaning you can now use a *whole sealed drawer* as
a single card filed inside some *other* drawer or catalog, the same trick tuples pulled off for lists.

---

## 7. Set Comprehensions

**What it is:** the set equivalent of a list/dict comprehension (→ `02_1_lists.md` Section 4,
`02_3_dictionaries.md` Section 6) — builds a new set from an iterable in one expression, using
`{expr for ... }` syntax (no colon — that's what keeps it a set comprehension instead of a dict one).

```python
squares = {x * x for x in range(-3, 4)}
print(squares)     # {0, 1, 4, 9} — note: -3 and 3 both square to 9, so the DUPLICATE is naturally
                      # collapsed away by set uniqueness (→ Section 2) — this wouldn't happen in a list comprehension

# Conditional (filtering) form:
evens = {x for x in range(10) if x % 2 == 0}
print(evens)     # {0, 2, 4, 6, 8}
```
**How it works — bottom-up:** exactly like list/dict comprehensions, a set comprehension compiles to
its own code object with its own scope (→ `02_1_lists.md` Section 4) — the loop variable does not leak
into the enclosing namespace.

**Layman version:** same private-booth mechanism as a list/dict comprehension — feed it a rule and a
source of raw material, get back a finished presence-only drawer — except this booth automatically
throws away any duplicate result the rule happens to produce along the way, since a drawer can't hold
two copies of the same card anyway.

---

## 8. Practical Idioms: Membership Testing & Deduplication

**The single most common reason to reach for a set: O(1) average membership testing, directly
following from Section 1, in a hot loop where a list would degrade to O(n) per check
(→ `02_1_lists.md` Section 8):**
```python
allowed_ids = {101, 205, 309, 412}     # a set of IDs to check against repeatedly

def is_allowed(user_id):
    return user_id in allowed_ids        # O(1) average — same speed whether allowed_ids has 4 or 4 million entries

# Contrast: if allowed_ids were a LIST instead, `in` would be O(n) EVERY call (→ 02_1_lists.md Section 8)
```

**Deduplicating a list — `set(lst)` is fast and idiomatic, but LOSES the original order:**
```python
names = ["bob", "alice", "bob", "carol", "alice"]
unique = set(names)
print(unique)     # {'bob', 'carol', 'alice'} — order is NOT the original insertion order (Section 1)
```

**If original order must be preserved, use `dict.fromkeys()` instead — the direct payoff of
`02_3_dictionaries.md`'s ordering guarantee applied here:**
```python
names = ["bob", "alice", "bob", "carol", "alice"]
unique_ordered = list(dict.fromkeys(names))
print(unique_ordered)     # ['bob', 'alice', 'carol'] — FIRST-SEEN order preserved, duplicates dropped
```
**Why this works — bottom-up:** `dict.fromkeys(names)` builds a dict using each name as a key (with a
throwaway `None` value); dict keys are unique (→ `02_3_dictionaries.md` Section 2) so duplicates
collapse exactly like a set's would, but because a `dict`'s dense array *is* insertion-ordered
(→ `02_3_dictionaries.md` Section 1, Section 5), the first-seen order of each unique name survives —
something a plain `set` structurally cannot promise (Section 1 of this doc). Wrapping the result in
`list(...)` just extracts the (already order-preserving) keys back out as a list.

**Layman version:** if you just need to know "what are all the unique titles here, I don't care what
order," dumping everything into a presence-only drawer (`set(lst)`) is the fast, natural move — but
remember that drawer never promised to remember arrival order. If arrival order genuinely matters,
route the same "no duplicates allowed" filing job through the ordered-logbook catalog (`dict`) instead,
using each title as a card and throwing away the (irrelevant) shelf-location value — you get the exact
same deduplication guarantee, but the ordered logbook remembers the sequence the presence-only drawer
never bothered to.

---

## 9. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `AttributeError: 'dict' object has no attribute 'add'` | Wrote `{}` intending an empty SET, but `{}` is always an empty `dict` | Use `set()` explicitly for an empty set (→ Section 2) |
| A set's printed order doesn't match insertion order, and shifts after adding more elements | Sets make NO ordering guarantee at all (unlike `dict` since 3.7) — order depends purely on hash values and table layout | Never rely on set iteration order; if order matters, use a `list`/`dict` instead (→ Section 1) |
| `TypeError: unsupported operand type(s) for \|` when combining a set with a list | Operators (`\|`, `&`, `-`, `^`) require BOTH sides to already be sets | Use the method form instead (`.union(iterable)`, etc.), which accepts any iterable (→ Section 4) |
| `s.pop()` doesn't remove "the last added" element the way `dict.popitem()` does | Sets have no insertion-ordered backing array, so `pop()` removes whatever element the hash table encounters first — no LIFO guarantee | Don't rely on which element `set.pop()` removes; if you need order-based removal, use a `list`/`deque`/`dict` instead (→ Section 3) |
| `TypeError: unhashable type: 'set'` when using a set as a dict key or set element | Plain `set` is mutable and therefore unhashable, exactly like `list` | Use `frozenset` instead — the immutable, hashable set variant (→ Section 6) |
| `s.remove(x)` raised `KeyError` unexpectedly | `.remove()` is the STRICT removal method — raises if `x` isn't present | Use `.discard(x)` instead if "remove if present, otherwise ignore" is the actual intent (→ Section 3) |
| Deduplicating a list with `set(lst)` scrambled the original order | Sets are unordered (Section 1) — this is expected, not a bug | Use `list(dict.fromkeys(lst))` instead when original order must be preserved (→ Section 8) |
| Two sets with the same elements compare unequal | Almost certainly comparing element VALUES that aren't actually equal (e.g. `1` vs `"1"`), since set `==` genuinely ignores order and correctly reports equal elements as equal regardless of insertion sequence | Double check the actual element values, not the order they were added in (→ Section 5) |

---

## 10. Quick-Reference Checklist

Use this whenever you're reasoning about a set in Python:

1. Am I thinking of a set as "a dict with the values stripped out" — same hash-table mechanics, same
   O(1) average membership testing, same hashability requirement on elements? (→ Section 1)
2. Did I write `{}` intending an empty set? Remember: that's always a `dict` — use `set()` explicitly.
   (→ Section 2)
3. Am I relying on this set's iteration order in any way? Sets make NO ordering guarantee, unlike
   `dict` — if order matters, this is the wrong structure. (→ Section 1)
4. Am I combining a set with a plain list/tuple using an OPERATOR (`|`, `&`, `-`, `^`)? That will raise
   `TypeError` — use the equivalent METHOD (`.union()`, etc.) instead, which accepts any iterable.
   (→ Section 4)
5. Do I need to mutate a set in place (union/intersect it INTO an existing set) rather than build a new
   one? Am I using the in-place operator/method (`|=`, `.intersection_update()`, etc.)? (→ Section 4)
6. Am I choosing between `.remove()` (raises if missing) and `.discard()` (silent no-op) deliberately,
   based on whether a missing element should actually be an error here? (→ Section 3)
7. Do I need this collection to be hashable — usable as a dict key, or as an element of another set? If
   so, am I using `frozenset` instead of a plain `set`? (→ Section 6)
8. Am I deduplicating a list and actually need to preserve the ORIGINAL order? `set(lst)` won't do
   that — `list(dict.fromkeys(lst))` will. (→ Section 8)
9. Am I checking membership (`in`) repeatedly in a loop against a collection that's currently a list?
   Would converting it to a `set` once, up front, turn an O(n)-per-check cost into O(1)? (→ Section 8,
   `02_1_lists.md` Section 8)
10. Am I using `<`/`<=`/`>`/`>=` on sets and reading them correctly as subset/superset questions, not
    as "which set has bigger elements"? (→ Section 5)
