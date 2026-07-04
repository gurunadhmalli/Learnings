# 2.5 Strings — Complete Deep-Dive Guide

This is the companion reference for **Section 2.5** of [`python_full_syllabus.md`](python_full_syllabus.md).
Same format as [`02_1_lists.md`](02_1_lists.md), [`02_2_tuples.md`](02_2_tuples.md),
[`02_3_dictionaries.md`](02_3_dictionaries.md), and [`02_4_sets.md`](02_4_sets.md): **what it is → why
it exists → how it works, all the way down to memory and the CPython runtime → a plain-English
analogy**. Strings are the collection type you touch the most and understand the least — everyone
knows `"hello".upper()` on day one, almost nobody has seen *why* `s += x` in a loop is a performance
trap, why `"hello" is "hello"` can be `True` while `("hello " + "world") is ("hello " + "world")` is
`False`, or why Python stores `"café"` differently in memory than `"cafe"`. This doc builds all of that
up from the actual CPython object layout.

> **A note on gaps in the syllabus outline.** Before writing this, I compared the original 2.5 bullet
> list against what mastering strings actually requires, and found real gaps. I've folded all of them
> in here (and added bullets back into the syllabus so the outline stays honest):
> - **PEP 393, the flexible string representation** — *the* bottom-level fact everything else in this
>   doc hangs off (why some strings take more memory per character than others) — wasn't mentioned at
>   all (→ Section 1).
> - **Escape sequences and the different quoting forms** — `\n`, `\t`, `\uXXXX`, `\N{...}`, triple vs
>   single/double quotes — the outline jumped straight to methods without ever covering literal syntax
>   (→ Section 2).
> - **Slicing, indexing, and iterate-by-code-point** weren't listed under 2.5 at all, even though
>   strings support the exact same `[start:stop:step]` machinery as lists (→ Section 5).
> - **The format-spec mini-language** (`{:>10,.2f}`) — "f-strings" was listed as a bullet, but the
>   actual mini-language that powers `.format()`, f-strings, *and* the built-in `format()` was never
>   named (→ Section 7).
> - **Why `+=` concatenation is a performance trap** — implied by section 19 ("efficient string
>   building") elsewhere in the syllabus, but 2.5 itself never explained the immutability mechanism
>   behind it, and CPython's actual behavior here is subtler than the usual one-line warning
>   (→ Section 8).
> - **String interning and cached hashing as one connected, mechanistic story** — `01_2` mentions
>   "string interning" only in a cheat-sheet line about `is` vs `==`; nowhere is the actual mechanism
>   (which strings get interned, and why immutability lets a string cache its own hash) explained
>   (→ Section 4).
> - **Unicode normalization** — "Unicode, encoding/decoding" was listed, but the NFC/NFD gotcha (two
>   strings that *look* identical but compare unequal) was never mentioned (→ Section 9).
>
> This doc keeps the same top-down bug fix habit as its siblings: read it beginner-first (skim "What
> it is" and "Layman version") or internals-first (read the "bottom-up" blocks) — both paths are here.

---

## Table of Contents

1. [The Big Picture: What a String *Actually* Is — PEP 393](#1-the-big-picture-what-a-string-actually-is--pep-393)
2. [Literal Forms & Escape Sequences](#2-literal-forms--escape-sequences)
3. [Immutability — What It Actually Implies](#3-immutability--what-it-actually-implies)
4. [Interning & Hash Caching (Bottom-Up)](#4-interning--hash-caching-bottom-up)
5. [Indexing, Slicing & Iteration](#5-indexing-slicing--iteration)
6. [The Full Method Survey](#6-the-full-method-survey)
7. [String Formatting: Three Generations](#7-string-formatting-three-generations)
8. [Concatenation Performance & the "O(n²)" Question](#8-concatenation-performance--the-on²-question)
9. [Unicode, Encoding & Decoding](#9-unicode-encoding--decoding)
10. [`str` vs `bytes` vs `bytearray`](#10-str-vs-bytes-vs-bytearray)
11. [Text Alignment & Wrapping](#11-text-alignment--wrapping)
12. [Cheat Sheet: Common Gotchas](#12-cheat-sheet-common-gotchas)
13. [Quick-Reference Checklist](#13-quick-reference-checklist)

---

## 1. The Big Picture: What a String *Actually* Is — PEP 393

**What it is:** a `str` is an **immutable sequence of Unicode code points** — not bytes, not
characters-on-screen, but abstract Unicode code points (integers from `0` to `0x10FFFF`, the same
numbers `ord()` returns). Every string operation (`len()`, indexing, slicing, iteration) counts and
addresses code points.

**The naive mental model most people carry over from C/Java:** "a string is an array of bytes/chars,
all stored the same way." **This is wrong in CPython**, and the correction is worth understanding
because it explains a whole category of "why does this string take more memory than that one" and
"why is encoding sometimes lossless and sometimes not" surprises later in this doc.

**How it actually works — bottom-up (PEP 393, "Flexible String Representation," Python 3.3+):**
CPython does **not** store every string the same way in memory. When a string is created, CPython
looks at the *widest* code point that string actually contains and picks the **narrowest fixed-width
storage** that can hold it:

```
 Storage kind     Bytes/char   Used when the string's widest code point is...
 ─────────────    ──────────   ────────────────────────────────────────────────
 ASCII-compact     1 byte       every code point ≤ 0x7F (plain ASCII, the common case)
 Latin-1 (UCS-1)   1 byte       every code point ≤ 0xFF, but at least one > 0x7F
 UCS-2             2 bytes      every code point ≤ 0xFFFF, but at least one > 0xFF
 UCS-4             4 bytes      at least one code point > 0xFFFF (e.g. most emoji, rare CJK)
```

```python
import sys
print(sys.getsizeof("cafe"))     # e.g. 53  — pure ASCII, 1 byte/char, smallest struct overhead
print(sys.getsizeof("café"))     # e.g. 77  — has 'é' (U+00E9 ≤ 0xFF but > 0x7F) → Latin-1 kind,
                                    #            still 1 byte/char, but a LARGER base struct than
                                    #            pure-ASCII strings (see "why" below)
print(sys.getsizeof("日本語"))    # e.g. 80  — every char ≤ 0xFFFF but > 0xFF → UCS-2 kind, 2 bytes/char
print(sys.getsizeof("😀"))       # e.g. 80  — U+1F600 > 0xFFFF → UCS-4 kind, 4 bytes/char
# exact numbers vary by Python build/version — run sys.getsizeof yourself to see your build's numbers
```

**Why pure ASCII gets an even smaller footprint than Latin-1, not just "the same 1-byte encoding":**
CPython has a *fourth*, more specialized struct (`PyASCIIObject`) reserved for strings that are 100%
ASCII. Because ASCII bytes are already valid UTF-8 bytes, an ASCII string can skip the separate
"cached UTF-8 encoding" pointer/buffer that every other kind carries — that's the extra ~24 bytes you
see between `"cafe"` and `"café"` above, even though both are nominally "1 byte per character."

**Why CPython bothers with all this instead of just always using UCS-4 (4 bytes/char, simplest code):**
memory. The overwhelming majority of real-world strings (variable names, JSON keys, English text, log
lines) are pure ASCII. Before PEP 393 (Python ≤ 3.2), CPython builds were compiled *either* narrow
(UCS-2, breaking on code points beyond the Basic Multilingual Plane) *or* wide (UCS-4, correct but 4×
the memory for every string in the program, including the millions of tiny ASCII ones). PEP 393 lets
every **individual string object** pick its own narrowest-correct width, so a program that's 99% ASCII
text with the occasional emoji doesn't pay a 4-byte tax on every character everywhere.

**Layman version:** imagine a print shop that stocks type-blocks in three sizes — small, medium, and
large — and, for every single job, uses the *smallest* size that can print every character in that
particular job. A job that's plain English text gets the small blocks (cheapest). The instant a single
Chinese character or emoji shows up in a job, the *whole job* switches to whichever size block is big
enough for *that* character — not because every character in the job needs it, but because all the
blocks in one print run have to be a uniform size for the printing press to work efficiently. Two jobs
sitting side by side on the shop floor can genuinely be using different-sized blocks; that's exactly
what `sys.getsizeof` is showing you above.

---

## 2. Literal Forms & Escape Sequences

**Three ways to quote a string — functionally identical, chosen by convention/convenience:**
```python
s1 = 'single quotes'
s2 = "double quotes"        # use when the string itself contains a '
s3 = '''triple single'''
s4 = """triple double
spans multiple physical lines
without needing \n"""          # triple-quoted strings can embed literal newlines
```
There is no semantic difference between `'...'` and `"..."` in Python (unlike some languages where one
means "literal" and the other "interpolated") — pick whichever avoids escaping a quote character
inside the string. Triple-quoted strings are used both for genuinely multi-line text *and* — by
convention only, not a separate syntax — for docstrings (→ syllabus 1.1).

**Escape sequences — backslash + character means something other than the literal two characters:**
```python
print("Line1\nLine2")        # \n = newline
print("Col1\tCol2")          # \t = tab
print("Quote: \"hi\"")       # \" = literal double-quote inside a double-quoted string
print("Backslash: \\")       # \\ = a single literal backslash
print("é")              # \uXXXX = the character at Unicode code point U+00E9  → 'é'
print("\N{BULLET}")          # \N{NAME} = the character with this official Unicode name → '•'
```
**Why this matters bottom-up:** the tokenizer (→ syllabus 1.1) processes escape sequences *while
building the string literal's bytes*, before the object even exists — `"\n"` is a **one-character**
string (code point 10), never a two-character `\` followed by `n`. This is exactly why a Windows path
like `"C:\new\test.txt"` silently corrupts (`\n` and `\t` get swallowed as newline/tab) — which is the
whole reason raw strings exist:
```python
path = "C:\new\test.txt"
print(path)          # C:
                        # ew	est.txt   <- \n and \t were consumed as escapes, NOT what you wanted

path_ok = r"C:\new\test.txt"
print(path_ok)          # C:\new\test.txt   <- raw string: backslashes are literal, no escape processing
```
**Raw strings (`r"..."`)** tell the tokenizer "treat every backslash as a literal backslash" — used
constantly for Windows paths and regex patterns (→ syllabus 8.1), where backslashes are meaningful to
the *regex engine* and you don't want Python's own escape processing interfering first. A raw string
can be combined with an f-string (`rf"..."` / `fr"..."`, → Section 7) but **cannot** end in an odd
number of backslashes (`r"\"` is a syntax error — the parser can't tell if that trailing `\` is escaping
the closing quote).

**Byte strings (`b"..."`)** look like a string literal but produce a `bytes` object, not a `str` — a
sequence of raw 0–255 integers, not Unicode code points (full contrast in Section 10).

**Adjacent string literal concatenation** (already introduced in syllabus 1.1): `"a" "b"` is folded by
the compiler into the single literal `"ab"` at compile time — useful for breaking a long literal across
lines without a `+`.

**Layman version:** think of the backslash as a stage direction rather than dialogue — `\n` doesn't
mean "the characters backslash and n," it means "insert a line break here," the same way a hyphen at
the end of a printed line doesn't mean "print a hyphen," it means "this word continues on the next
line." A raw string is you telling the typesetter "no stage directions this time — print every
backslash exactly as I wrote it, literally."

---

## 3. Immutability — What It Actually Implies

**What it is:** once a `str` object is created, **nothing about it can ever change** — not a single
character, not its length. Every string method that "looks like" it modifies a string
(`.upper()`, `.replace()`, `.strip()`, ...) actually **builds and returns a brand-new string object**,
leaving the original completely untouched.

```python
s = "hello"
t = s.upper()
print(s, t)          # hello HELLO   <- s is UNCHANGED; upper() returned a NEW string
print(s is t)          # False — two genuinely different objects in memory

s[0] = "H"                # TypeError: 'str' object does not support item assignment — no such thing
                              # as "mutate character 0 in place"; the object has no write API at all
```

**How this contrasts with a list, concretely (→ `02_1_lists.md` Section 3):**
```
 list.append(x)      →  mutates the SAME list object in place, same id() before/after
 s.upper()            →  allocates a BRAND NEW string object, different id() from s

 lst = [1, 2, 3]           s = "abc"
 lst.append(4)             t = s.upper()
 id(lst) unchanged           id(s) != id(t)
```

**Why Python designed it this way — three concrete payoffs, not just "tradition":**
1. **Safe sharing without defensive copying.** Because a string can never change out from under you,
   passing the *same* string object to ten different functions is always safe — none of them can
   corrupt what the others see. A mutable type has no such guarantee (→ `02_1_lists.md` Section 3's
   aliasing pitfalls).
2. **Hashability** (→ Section 4 below, → `02_3_dictionaries.md` Section 1): a dict/set key's hash must
   never change while it's stored in the table, or the table's internal bucket assignment silently
   breaks. An object that's physically incapable of changing is automatically safe to hash — this is
   the exact same reason tuples are hashable and lists aren't (→ `02_2_tuples.md` Section 5).
3. **Interning is only safe because of immutability** (→ Section 4) — if `"hello"` could be mutated in
   place, every variable that happened to be pointing at the *same* interned `"hello"` object would see
   the change too, which would be catastrophic action-at-a-distance. Immutability is the precondition
   that makes sharing/caching a single object across the whole program safe at all.

**Layman version:** a Python string is like a sheet of paper that came out of a laminating machine —
once it's laminated, you cannot erase or alter a single letter on it, ever. If you want a version with
different text, you generate a brand-new laminated sheet from scratch and hand that one out instead;
the original sheet keeps existing, unchanged, for as long as anyone's still holding onto a copy of it.
Because everyone knows a laminated sheet can never be secretly altered, it's completely safe to hand
the *exact same physical sheet* to a hundred different people at once — nobody has to worry that
someone else's copy will change what's printed on theirs.

---

## 4. Interning & Hash Caching (Bottom-Up)

`01_2_variables_and_data_types.md` Section 3 already warned that relying on `is` for string equality is
a trap, because of "string interning" — this section explains the actual mechanism, not just the
warning.

**What interning is:** CPython maintains an internal table of "canonical" string objects, and for
certain strings, instead of allocating a new object it hands back a pointer to the *same* existing
object every time an equal string is needed. Two *interned* equal strings are therefore not just
`==`, but literally `is` the same object.

**Which strings actually get interned, demonstrated across two independently-compiled chunks of code
(so we're not fooled by the compiler merely deduplicating identical literals within one code object):**
```python
ns1, ns2 = {}, {}
exec('x = "hello"', ns1)
exec('x = "hello"', ns2)
print(ns1['x'] is ns2['x'])          # True  — identifier-shaped literal: genuinely interned

exec('y = "hello world"', ns1)
exec('y = "hello world"', ns2)
print(ns1['y'] is ns2['y'])          # False — contains a space: NOT automatically interned
```
**Why the distinction:** CPython automatically interns string literals that **look like identifiers**
(letters/digits/underscore, matching the same character set a variable name could use) — because these
are exactly the strings the interpreter itself is constantly comparing internally: attribute names,
dict keys for `__dict__`, keyword-argument names, module names. Interning these means the interpreter
can compare two such strings with a cheap pointer comparison (`is`) internally instead of a full
character-by-character comparison, which measurably speeds up attribute/name lookups across the whole
runtime. A string with a space, punctuation, or arbitrary content has no such internal-lookup use case,
so CPython doesn't bother interning it automatically.

**You can force interning yourself with `sys.intern()`** — useful if you're about to store millions of
repeated non-identifier strings (e.g. parsing a huge log file where the same field values repeat) and
want them to collapse to one shared object in memory:
```python
import sys
a = sys.intern("hello world")
b = sys.intern("hello world")
print(a is b)          # True — now genuinely the same object, forced manually
```

**Why the earlier warning matters in practice — what actually breaks:**
```python
a = "hello"
b = "hello"
print(a is b)              # True (interned, identifier-shaped) — but this is an IMPLEMENTATION DETAIL

c = "hello!" [:-1]           # built at runtime via slicing, not a literal
d = "hello"
print(c is d)                 # commonly False — NOT interned, even though c == d is True
print(c == d)                   # True — always use == for string comparison, never is
```
Never write `if x is "some_string"` — it happens to work in quick REPL experiments (because short
identifier-like literals get interned) and then mysteriously fails the moment the same-looking string
is built at runtime via concatenation/slicing/formatting instead of typed as a literal.

**Hash caching — the other payoff of immutability, and why it matters for dict/set performance
(→ `02_3_dictionaries.md` Section 1):** computing `hash("some long string")` requires reading every
character. Because a `str` can never change after creation, CPython computes its hash **once**, on
first use, and caches the result directly on the string object — every subsequent `hash()` call (and
every dict/set lookup using this exact string object as a key) is then just "read the cached integer,"
not "recompute from scratch."
```python
s = "a fairly long string used as a dictionary key over and over"
hash(s)          # first call: computes and CACHES the hash on the object itself
hash(s)            # every later call on the SAME object: instant, just reads the cached value
```
This caching would be **unsafe** for a mutable type — if the string's content could change after the
hash was cached, the cached hash would go stale and silently corrupt any dict/set that used it as a
key (the entry would sit in the wrong bucket forever). Immutability is precisely what makes "compute
once, trust forever" a safe optimization.

**Layman version:** interning is the library keeping exactly one master copy of extremely common,
name-shaped index cards (like "AUTHOR" or "TITLE") and handing out a reference to that *same* card
every time someone asks for one, instead of photocopying a fresh card each time — but it only bothers
doing this for name-shaped cards, not arbitrary sentences. Hash caching is the library writing a
lookup-code directly on each laminated card the very first time it's filed anywhere — because the card
is laminated (immutable), that code can never go stale, so the library never has to recompute it again
for that exact card.

---

## 5. Indexing, Slicing & Iteration

**Indexing and slicing work exactly like lists (→ `02_1_lists.md` Section 2) — same `[start:stop:step]`
syntax, same negative-index-from-the-end convention — but a string slice always returns a *new*
`str`, never a "view" into the original (there is no such thing as a mutable view onto part of a
string, unlike, say, a `memoryview` over bytes, → syllabus 2.6):**
```python
s = "Hello, World!"
print(s[0])           # 'H'   — single index
print(s[-1])            # '!'  — negative index counts from the end
print(s[7:12])             # 'World'  — slice: start inclusive, stop exclusive
print(s[::-1])                # '!dlroW ,olleH'  — step -1 reverses the whole string
print(s[::2])                    # 'Hlo ol!'  — every 2nd character
```

**Membership (`in`) is substring search, not "is this single character present":**
```python
print("World" in s)          # True — substring search
print("world" in s)             # False — case-sensitive
```
CPython uses an efficient substring-search algorithm (a variant of Crochemore–Perrin/"two-way" string
matching) under the hood — not a naive character-by-character rescan for every position — so `in` on
strings is fast in practice even for longer needle/haystack combinations.

**Comparison is lexicographic, exactly like list comparison (→ `02_1_lists.md` Section 8), comparing
code point by code point:**
```python
print("apple" < "banana")          # True — 'a' (97) < 'b' (98) at the first differing position
print("Apple" < "apple")             # True — 'A' (65) < 'a' (97): uppercase sorts BEFORE lowercase in
                                         # plain code-point order — a common source of "wrong" sort
                                         # results when mixing cases (fix: sort with key=str.lower)
```

**Iteration is by Unicode code point — NOT by "visual character"/grapheme cluster, and `len()` counts
code points, not what a human would call "one character on screen":**
```python
s = "a" + "́"          # 'a' followed by a COMBINING ACUTE ACCENT — renders on screen as "á"
print(len(s))                  # 2  — TWO code points, even though it visually looks like one character
for ch in s:
    print(repr(ch))               # 'a'  then  '́'  — iteration yields each code point separately

precomposed = "á"                    # a single, precomposed code point U+00E1
print(len(precomposed))                 # 1
print(s == precomposed)                    # False!  Same visual appearance, DIFFERENT code point sequence
                                              # (this is the normalization gotcha — full story in Section 9)
```
**Why:** a `str`'s iterator protocol (→ syllabus 3.5) walks the underlying PEP 393 buffer (Section 1)
one fixed-width unit at a time — it has no concept of "combining characters" or "grapheme clusters"
(what a human perceives as one printed glyph); that's a higher-level linguistic concept the `str` type
simply doesn't model. Emoji built from multiple code points (e.g. a flag emoji, or a skin-tone-modified
emoji using a ZWJ sequence) show the same surprise: `len()` reports more than "1," because Python is
counting code points, not rendered glyphs.

**Layman version:** slicing a string is like using scissors on a photocopy, not the original — you
always get a brand-new strip of paper back, the source sheet is untouched. Iterating a string is like
reading a sentence one Unicode "type-block" at a time off the print shop's press (Section 1) — the
press has no idea that two adjacent blocks ("a" then "combining accent") are meant to be *read* as one
visual glyph; it just knows it laid down two blocks, so it reports two blocks when asked "how many did
you lay down."

---

## 6. The Full Method Survey

Grouped by purpose rather than alphabetically — the grouping itself is the thing worth memorizing;
individual method names are easy to look up once you know which drawer to open.

**Search — find things inside a string:**
| Method | Behavior |
|---|---|
| `s.find(sub)` | index of first occurrence, or **`-1`** if not found (never raises) |
| `s.rfind(sub)` | index of *last* occurrence, or `-1` |
| `s.index(sub)` | like `find`, but **raises `ValueError`** if not found |
| `s.rindex(sub)` | like `rfind`, but raises `ValueError` if not found |
| `s.count(sub)` | number of non-overlapping occurrences |
| `sub in s` | boolean membership (Section 5) |
```python
s = "the cat sat on the mat"
print(s.find("cat"), s.find("dog"))          # 4 -1
print(s.count("at"))                            # 3   ("cat", "sat", "mat")
```
This `find`/`index` split is the exact same lenient-vs-strict naming pattern seen throughout the
standard library (`dict.get` vs `d[key]`, `set.discard` vs `set.remove` → `02_4_sets.md` Section 3).

**Transform — produce a new string derived from this one (Section 3: none of these mutate!):**
| Method | Behavior |
|---|---|
| `s.replace(old, new)` | all occurrences of `old` replaced with `new` |
| `s.strip()` / `.lstrip()` / `.rstrip()` | remove leading/trailing whitespace (or a given char set) |
| `s.upper()` / `.lower()` | case conversion |
| `s.casefold()` | *aggressive* case-folding for caseless comparison — stronger than `.lower()` |
| `s.title()` / `.capitalize()` | title-case each word / capitalize just the first character |
```python
print("straße".upper())            # 'STRASSE' — German ß uppercases to 'SS' (two characters!)
print("ß".lower(), "ß".casefold())     # 'ß' 'ss'  — lower() leaves ß as-is; casefold() normalizes it
                                          # to 'ss' specifically so caseless comparisons match correctly
print("Straße".casefold() == "STRASSE".casefold())     # True — this is casefold()'s actual job:
                                                           # robust caseless comparison across scripts
```
**Why `.casefold()` exists as a separate method from `.lower()`:** some Unicode characters (like German
`ß`) don't have a simple 1:1 lowercase mapping that round-trips correctly for *comparison* purposes.
`.lower()` is for "display this in lowercase"; `.casefold()` is specifically for "I want to compare two
strings ignoring case, robustly, across languages" — use `.casefold()`, not `.lower()`, when the goal
is a caseless *comparison* rather than a display transformation.

**Split / Join — convert between one string and many:**
```python
csv_row = "alice, bob ,carol"
parts = csv_row.split(",")               # ['alice', ' bob ', 'carol']  — split does NOT strip whitespace
cleaned = [p.strip() for p in parts]        # ['alice', 'bob', 'carol']
print(",".join(cleaned))                       # 'alice,bob,carol'

print("a b  c   d".split())                       # ['a', 'b', 'c', 'd']  — split() with NO args collapses
                                                      # ANY run of whitespace and drops leading/trailing —
                                                      # different from split(" ") which splits on EVERY
                                                      # single space and keeps empty strings from doubles
print("a b  c".split(" "))                              # ['a', 'b', '', 'c']  — note the empty string!

print("line1\nline2\r\nline3".splitlines())                 # ['line1', 'line2', 'line3'] — handles
                                                                # \n, \r\n, and \r uniformly
```
**Why `join` is a method on the *separator string*, not on the list** (a very common point of
confusion for people coming from other languages): `", ".join(parts)` reads oddly at first — "shouldn't
it be `parts.join(", ")`?" — but the design lets `join` accept *any* iterable of strings (a list, a
generator, a `dict.keys()` view, ...), not just a list specifically. The separator is the one fixed,
known piece; the thing being joined can be any iterable, so it's the argument, not the receiver.

**Test — ask a yes/no question about a string's shape, without modifying it:**
```python
print("hello.py".startswith("hello"), "hello.py".endswith(".py"))     # True True
print("123".isdigit(), "abc".isalpha(), "  ".isspace(), "abc123".isalnum())     # True True True True
print("Title Case".istitle(), "UPPER".isupper(), "lower".islower())               # True True True
```

**Alignment / padding — pad a string to a fixed width (full treatment in Section 11):**
```python
print("hi".ljust(6, "-"), "|", "hi".rjust(6, "-"), "|", "hi".center(6, "-"))     # hi---- | ----hi | --hi--
print("42".zfill(5))          # '00042' — zero-pad, understands a leading sign correctly: "-3".zfill(4) -> '-003'
```

**Layman version:** think of these as five labeled drawers in the same filing cabinet — a "does this
exist / where" drawer (search), a "make me a modified copy, never touch the original" drawer
(transform — same laminated-sheet rule as Section 3), a "cut this into pieces / glue pieces back
together" drawer (split/join), a "yes-or-no shape check" drawer (test), and a "pad this out to a fixed
width for a printed column" drawer (alignment). Once you know which drawer a job belongs in, the
specific method name is just a label you look up.

---

## 7. String Formatting: Three Generations

Python has accumulated three ways to build a string from variables, in this chronological order — all
three still work today, but only the last two are considered idiomatic in new code.

**Generation 1 — `%`-formatting (inherited from C's `printf`, legacy but still seen in older code and
in logging-library format strings):**
```python
name, age = "Ana", 30
print("Name: %s, Age: %d" % (name, age))          # 'Name: Ana, Age: 30'
```

**Generation 2 — `.format()` and the format-spec mini-language:** introduced a placeholder syntax,
`{}`, with an entire **mini-language** after a colon for controlling width, alignment, precision, sign,
and thousands separators — the same mini-language f-strings (Generation 3) also use:
```python
print("{}, {}!".format("Hello", "World"))          # positional
print("{name} is {age}".format(name="Ana", age=30))   # by keyword

# The format-spec mini-language, field by field: {value:fill-align-sign-width-,-.precision-type}
print("{:>10}".format("hi"))          # '        hi'   — > right-align, width 10
print("{:<10}|".format("hi"))            # 'hi        |' — < left-align
print("{:^10}|".format("hi"))               # '    hi    |' — ^ center
print("{:*^10}|".format("hi"))                 # '****hi****|' — '*' as the explicit fill character
print("{:+d}".format(42))                         # '+42'  — force a sign to always show
print("{:05d}".format(42))                           # '00042' — zero-padded width 5
print("{:,}".format(1234567))                           # '1,234,567' — thousands separator
print("{:.2f}".format(3.14159))                            # '3.14' — fixed-point, 2 decimal places
print("{:>10.2f}".format(3.14159))                            # '      3.14' — width AND precision combined
print("{:.1%}".format(0.1234))                                   # '12.3%' — percentage, 1 decimal place
```

**Generation 3 — f-strings (PEP 498, Python 3.6+):** the expression goes *inside* the string literal
itself, using the exact same format-spec mini-language after the colon:
```python
name, age = "Ana", 30
print(f"{name} is {age} years old")          # 'Ana is 30 years old'
print(f"{3.14159:>10.2f}")                      # same mini-language as .format(), applied inline
print(f"{age * 2}")                                # any valid expression is allowed inside {}

x = 42
print(f"{x=}")          # 'x=42' — the "debug specifier" (Python 3.8+): prints BOTH the source
                            # expression text and its value, purely for quick print-debugging
```
**Why f-strings aren't "just `.format()` with nicer syntax" — the bottom-up distinction:** an f-string
is parsed and **compiled** at the same time as the rest of the source code — the expressions inside
`{}` become real bytecode that evaluates in the enclosing scope at the point the f-string literal is
reached, exactly like any other expression in that function. `.format()`, by contrast, is a genuinely
runtime method call operating on a plain string template that happens to contain `{}` markers, parsed
and substituted only when `.format()` actually runs. Practically: an f-string can see local variables
directly (`f"{some_local_var}"`) because it's compiled inline as real code; `.format()` templates have
no automatic access to the calling scope and must be handed every value explicitly as an argument.

**Raw f-strings (`rf"..."` / `fr"..."`)** combine both behaviors — no backslash-escape processing
(Section 2) *and* `{}` expression interpolation — commonly used for regex patterns that also need a
variable spliced in.

**Layman version:** `%`-formatting is filling out an old carbon-copy form with blanks in a fixed order.
`.format()` is a form with *named*, reorderable blanks, and a small "style guide" (the mini-language)
for how each blank should be padded, aligned, or rounded when filled in. An f-string is that same form,
except you write the answer directly into the blank on the form itself, in front of the person printing
it, instead of handing the printer a separate list of answers to match up afterward — which is exactly
why it can casually reach for whatever's already sitting on your desk (a local variable) without you
having to hand it over explicitly first.

---

## 8. Concatenation Performance & the "O(n²)" Question

**The naive mental model, straight from immutability (Section 3):** every `s = s + x` (or `s += x`)
must — because strings can never be mutated in place — allocate a brand-new string, copy the *entire*
old content into it, then append the new piece. Do that `n` times in a loop, copying an
ever-growing string each time, and the total work is `1 + 2 + 3 + ... + n`, which is `O(n²)` — this is
the standard warning every Python style guide repeats, and it's the correct mental model to reach for
*first*.

**The subtler, bottom-up truth in real CPython:** the reference implementation special-cases the
extremely common `s = s + x` / `s += x` pattern. When CPython can prove the string being reassigned has
**exactly one reference** (nothing else in the program is pointing at the old value — the common case
for a simple accumulator loop like `s += x`), it can often **resize the existing buffer in place**
instead of allocating fresh and copying everything, via an internal optimization
(`PyUnicode_Append`/`PyUnicode_Resize` used by the bytecode compiler's `STORE_FAST`/augmented-assign
path). In practice, on CPython specifically, simple `+=` accumulation loops often run closer to linear
than the naive `O(n²)` model predicts:
```python
import timeit

def concat_loop(n):
    s = ""
    for i in range(n):
        s += "x"
    return s

def join_loop(n):
    return "".join("x" for i in range(n))

for n in (1000, 2000, 4000):
    t_concat = timeit.timeit(lambda: concat_loop(n), number=200)
    t_join = timeit.timeit(lambda: join_loop(n), number=200)
    print(n, round(t_concat, 4), round(t_join, 4))
# Illustrative output on one machine:
# 1000 0.0275 0.0151
# 2000 0.0764 0.0323
# 4000 0.2308 0.0832
# concat_loop scales worse than join_loop as n grows, but not as catastrophically as a strict O(n^2)
# model alone would suggest -- this IS the in-place-resize optimization at work
```

**Why `''.join(parts)` remains the correct, idiomatic tool regardless of this optimization:**
1. **It's a CPython implementation detail, not a language guarantee.** The Python *language
   specification* makes no such promise — PyPy and other implementations are not required to (and
   historically do not) special-case this the same way. Code relying on the "usually fast" behavior is
   relying on an accident of one specific interpreter.
2. **The optimization silently stops applying the moment there's a second reference** to the
   accumulating string (e.g. you stashed an earlier value in a list for logging, or the loop body
   captures `s` in a closure) — at that point you're back to full `O(n²)` copying with zero warning.
3. **`''.join(parts)` is unconditionally `O(n)` total** — it computes the final total length once,
   allocates exactly one buffer of the right size, and copies each piece in once. No implementation
   detail to depend on, no hidden reference-count trapdoor.

**Layman version:** naively, "add one more sentence onto this laminated sheet" (Section 3) should mean
"print a whole new, longer sheet from scratch and re-copy everything each time" — genuinely slow if
you're doing it thousands of times. CPython's print shop has a clever trick where, *if it can be sure
nobody else in the building is holding a copy of the sheet you're about to replace*, it'll sometimes
just reprint onto a bigger sheet in place rather than starting from zero — a nice speed-up, but it's a
private trick of this one particular print shop, not something guaranteed by the printing standard
itself, and it stops working the instant someone else is holding a copy of that sheet too. `''.join()`
instead measures the *whole* final document's length up front, prints exactly one sheet of the right
size, and pastes every piece onto it exactly once — reliably fast no matter which print shop (Python
implementation) you're standing in.

---

## 9. Unicode, Encoding & Decoding

**The core distinction — code points vs. bytes:** a `str` (Section 1) is a sequence of abstract
Unicode *code points* (numbers). Bytes are what actually exist on disk, over a network socket, or in a
`bytes`/`bytearray` object (Section 10). **Encoding** converts code points → bytes using a chosen rule
(an encoding scheme); **decoding** converts bytes → code points using that same rule. Mismatching the
rule used to encode vs. the rule used to decode is the single most common source of "mojibake"
(garbled text).

```python
s = "café"
print(s.encode("utf-8"))          # b'caf\xc3\xa9'   — 'é' (U+00E9) becomes TWO bytes in UTF-8
print(s.encode("utf-16-le"))         # b'c\x00a\x00f\x00\xe9\x00' — every char becomes exactly TWO bytes
print(len(s.encode("utf-8")))            # 5 bytes for 4 code points (the accented char costs 2 bytes)
print(len(s.encode("utf-16-le")))           # 8 bytes for 4 code points (fixed 2 bytes/char in this range)
```

**Diagram — the same 4-code-point string, three different byte layouts:**
```
 code points:    c        a        f        é (U+00E9)
                 U+0063   U+0061   U+0066   U+00E9

 UTF-8   :       63       61       66       C3 A9              <- variable width: 1 byte for ASCII,
                                                                    2 bytes here since 0xE9 > 0x7F
 UTF-16LE:       63 00    61 00    66 00    E9 00               <- fixed 2 bytes per unit in this range
 UTF-32LE:       63 00 00 00  61 00 00 00  66 00 00 00  E9 00 00 00   <- fixed 4 bytes, ALWAYS
```
**Why UTF-8 dominates on the wire/on disk despite being variable-width:** it's ASCII-compatible byte-
for-byte (any pure-ASCII file is already valid UTF-8), and it's dramatically more compact for the
overwhelmingly-ASCII text (source code, JSON, HTML, log files) that makes up most real-world data —
exactly the same "don't pay for width you don't need" philosophy as PEP 393 (Section 1), just applied
to the on-disk/wire format instead of the in-memory `str` object.

**`chr()` / `ord()` — the direct code-point ↔ integer bridge:**
```python
print(ord("é"))          # 233  (0xE9)
print(chr(233))            # 'é'
print(chr(0x1F600))           # '😀'
```

**Decode/encode errors — exactly what triggers them:**
```python
try:
    b"\xff".decode("utf-8")          # 0xFF is never a valid START byte in UTF-8's byte-layout rules
except UnicodeDecodeError as e:
    print(e)          # 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte

try:
    "café".encode("ascii")          # ASCII has no code point above 0x7F — 'é' (0xE9) doesn't fit
except UnicodeEncodeError as e:
    print(e)          # 'ascii' codec can't encode character '\xe9' in position 3: ordinal not in range(128)
```
**Why:** `DecodeError` means "these bytes don't form a valid sequence under this rule" (you're reading
with the wrong scheme, or the data is corrupt/truncated); `EncodeError` means "this code point has no
representation in the target scheme" (you're writing text into a scheme too narrow to hold it, like
Unicode text into ASCII or Latin-1). Always know which encoding a byte stream is actually in — "just
try UTF-8" is a reasonable default (it's Python 3's default for `open()`'s text mode on most modern
systems), never a universal guarantee.

**Unicode normalization — the gotcha promised back in Section 5:** the same visible glyph, "é," can be
represented as **one** precomposed code point (U+00E9) *or* **two** code points (U+0065 'e' + U+0301
combining acute accent) — visually identical, but genuinely different `str` objects that compare
unequal and hash differently:
```python
import unicodedata
precomposed = "é"                 # 'é' as ONE code point
decomposed = "é"                    # 'é' as base 'e' + a COMBINING accent — two code points
print(precomposed == decomposed)             # False! — looks identical when printed, but IS NOT equal
print(unicodedata.normalize("NFC", decomposed) == precomposed)     # True — NFC = "compose": collapse
                                                                       # combining sequences into their
                                                                       # single precomposed code point
print(unicodedata.normalize("NFD", precomposed) == decomposed)         # True — NFD = "decompose": the
                                                                           # reverse direction
```
This is a genuinely common real-world bug source: text copy-pasted from different sources (different
OSes, different input methods) can look pixel-identical yet fail an `==` check or a dict lookup, because
one came pre-composed and the other didn't. **Fix:** normalize both sides to the same form (NFC is the
usual choice) before comparing, hashing, or storing as a dict key.

**Layman version:** a code point is the *idea* of a letter — the abstract entry in the Unicode
dictionary. Encoding is choosing a specific alphabet-to-Morse-code table (UTF-8, UTF-16, UTF-32) to
transmit that idea as dots-and-dashes (bytes) over a wire; decoding is receiving dots-and-dashes and
looking them back up in that same table to recover the idea. If the sender and receiver are using
*different* Morse tables, you get garbage (`UnicodeDecodeError`) or the sender simply has no Morse
symbol at all for a letter the receiver's table doesn't include (`UnicodeEncodeError`). Normalization
is the separate, sneakier problem that the *same* letter idea, "é," can honestly be spelled two
different ways in the Unicode dictionary itself (one entry for the accented letter directly, or two
entries: plain "e" plus a separate "add an accent to the previous letter" instruction) — both spellings
render identically on the page, so the mismatch is invisible until a computer tries to compare them
letter-for-letter.

---

## 10. `str` vs `bytes` vs `bytearray`

**The three-way relationship — text vs. binary, mutable vs. immutable:**
```
              Immutable          Mutable
 Text:        str                (no mutable text type — strings are always immutable, Section 3)
 Binary:      bytes              bytearray
```
```python
s = "hello"            # str: Unicode code points, immutable
b = b"hello"               # bytes: raw 0-255 integers, immutable — looks like a string literal but ISN'T text
ba = bytearray(b"hello")      # bytearray: raw 0-255 integers, MUTABLE — the "list" to bytes' "tuple"

ba[0] = 72              # works — bytearray supports item assignment (72 == ord('H'))
print(ba)                  # bytearray(b'Hello')
print(bytes(ba))              # b'Hello' — convert back to an immutable bytes object when done mutating
```

**You cannot silently mix `str` and `bytes` in one operation — this is deliberate, not a missing
feature:**
```python
try:
    "hello" + b"world"          # TypeError: can only concatenate str (not "bytes") to str
except TypeError as e:
    print(e)
```
**Why:** Python 3's entire design philosophy around text (a lesson learned hard from Python 2, where
`str` was itself a byte string and text/binary confusion was a constant, silent source of bugs) is that
text and binary data are **fundamentally different kinds of information** that must be explicitly
converted between via `.encode()`/`.decode()` (Section 9) — never implicitly and silently coerced. A
`bytes` object has no inherent "text meaning" until you decide *which* encoding to interpret it under;
letting `+` silently guess would reintroduce exactly the bug class Python 3 was designed to eliminate.

**When to reach for each:**
- **`str`** — anything that's conceptually text: user-facing strings, JSON/config content, source code,
  anything you'd read out loud.
- **`bytes`** — read-only binary data: file contents read in `"rb"` mode, network payloads before
  you've decided how to interpret them, hash digests (→ syllabus `hashlib`).
- **`bytearray`** — binary data you need to build up or mutate incrementally (e.g. assembling a network
  packet piece by piece) without the cost of allocating a new object on every change — the same
  "mutable-when-you-need-in-place-edits" role `list` plays next to `tuple` (→ `02_2_tuples.md`
  Section 8).

**Layman version:** `str` is a laminated sheet of *readable text* (Section 3). `bytes` is a laminated
sheet of *raw punch-card holes* — technically also sealed shut, but there's no assumption at all about
what alphabet those holes are supposed to spell out until someone tells you which decoding template
(encoding) to hold over them. `bytearray` is the same punch-card, but *not yet* laminated — you can
still physically punch new holes or patch existing ones in place, which is exactly what you want while
you're still assembling the card, before sealing it into a permanent `bytes` object once you're done.

---

## 11. Text Alignment & Wrapping

**Fixed-width padding — the three alignment methods, already introduced in Section 6, used constantly
for lining up columns of output:**
```python
rows = [("Name", "Score"), ("Alice", "95"), ("Bob", "7")]
for name, score in rows:
    print(name.ljust(10) + score.rjust(5))
# Name      Score
# Alice        95
# Bob           7
```

**`textwrap` — wrapping/filling paragraphs of text to a fixed line width:**
```python
import textwrap

paragraph = "This is a fairly long sentence that we want to wrap to a narrow column width."
print(textwrap.fill(paragraph, width=30))
# This is a fairly long sentence
# that we want to wrap to a
# narrow column width.

print(textwrap.shorten(paragraph, width=30, placeholder="..."))
# This is a fairly long...
```
`textwrap.fill()` returns one wrapped multi-line string; `textwrap.wrap()` returns the same content as
a *list* of individual lines (useful when you need to process each line separately rather than print
the block as-is).

**Layman version:** `ljust`/`rjust`/`center` are for lining up a single short label inside a
fixed-width box — like right-aligning numbers in a spreadsheet column. `textwrap` is for the different
job of reflowing a long paragraph so it fits inside a narrow column at all, breaking at word boundaries
rather than mid-word, the way a newspaper column wraps body text.

---

## 12. Cheat Sheet: Common Gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `TypeError: 'str' object does not support item assignment` | Tried `s[0] = "x"` — strings are immutable (Section 3), no in-place character mutation exists | Build a new string instead: `s = "x" + s[1:]`, or use `"".join()` on a list of characters |
| A Windows path like `"C:\new\file.txt"` prints with a stray blank line / tab in it | `\n` and `\t` were interpreted as escape sequences (Section 2), not literal backslash-n / backslash-t | Use a raw string: `r"C:\new\file.txt"` |
| `"hello" is "hello"` is `True` in one script but the equivalent runtime-built string comparison is `False` elsewhere | Relying on CPython's interning of identifier-shaped literals (Section 4) — an implementation detail, not a language guarantee | Always use `==` for string value comparison; reserve `is` for `None`/singleton checks |
| A loop doing `s += chunk` thousands of times is slow, or slows down unpredictably after refactoring | Immutability means every `+=` can require a full reallocation+copy (Section 8); CPython's in-place-resize optimization only applies when there's exactly one reference to `s` | Build a list of chunks and `''.join(chunks)` once at the end — unconditionally `O(n)`, no hidden reference-count dependency |
| Two strings that print identically still compare unequal (`==` gives `False`), or a dict lookup with a "matching" key misses | Unicode normalization mismatch (Section 9) — one is precomposed (NFC), the other decomposed (NFD) into base+combining characters | Normalize both with `unicodedata.normalize("NFC", s)` (or `"NFD"`, pick one convention) before comparing/hashing |
| `UnicodeDecodeError: invalid start byte` when reading a file | Reading bytes with the wrong encoding assumption (e.g. treating Latin-1-encoded bytes as UTF-8) | Determine (don't guess) the actual source encoding; when unknown, `errors="replace"` or `"backslashreplace"` can degrade gracefully instead of crashing |
| `TypeError: can only concatenate str (not "bytes") to str` | Mixed a `str` and a `bytes` object directly (Section 10) — Python 3 never auto-converts between text and binary | Explicitly `.encode()` the str or `.decode()` the bytes first, choosing the right encoding deliberately |
| `len()` reports more "characters" than a string visually appears to have | Counting Unicode code points, not rendered glyphs (Section 5) — combining accents / multi-code-point emoji each count separately | Use `unicodedata.normalize("NFC", s)` first to collapse decomposed sequences, or a grapheme-cluster-aware library (e.g. `regex` module's `\X`) if true "visual character" counting is required |
| `"straße".upper() == "STRASSE"` surprises someone expecting a simple per-character case flip | Some Unicode case mappings aren't 1:1 — German `ß` uppercases to two characters, `"SS"` (Section 6) | Expected behavior, not a bug — be aware case conversion can change string length |
| `"a b  c".split(" ")` returns an unexpected empty string in the middle of the list | `split(" ")` (explicit separator) splits on every single space, keeping empties from doubled spaces; only the no-argument `split()` collapses runs of whitespace (Section 6) | Use `s.split()` with no arguments when you want "any whitespace run" splitting behavior |

---

## 13. Quick-Reference Checklist

Use this whenever you're reasoning about a string in Python:

1. Am I remembering that a `str` is a sequence of **Unicode code points**, not bytes and not
   necessarily "visual characters" — and that CPython may store it as ASCII/Latin-1/UCS-2/UCS-4
   internally depending on its widest code point? (→ Section 1)
2. Am I using a raw string (`r"..."`) for anything with literal backslashes — Windows paths, regex
   patterns — instead of fighting escape-sequence interpretation? (→ Section 2)
3. Am I treating every string method as producing a **new** string, never mutating the original in
   place? (→ Section 3)
4. Am I ever using `is` to compare string *values*? That's relying on CPython's interning
   implementation detail — use `==` instead. (→ Section 4)
5. Do I need this exact string object reused as a dict key or set element repeatedly? Its hash is
   cached once, forever, precisely because it's immutable. (→ Section 4)
6. Am I slicing/indexing and expecting a "view" into the original string? There's no such thing —
   every slice is a fresh copy. (→ Section 5)
7. Am I counting `len()` or iterating and implicitly assuming "one code point = one visual character"?
   Combining characters and some emoji break that assumption. (→ Section 5)
8. Do I know which "drawer" a string method belongs to — search, transform, split/join, test, or
   alignment — so I can guess/look up the right one quickly? (→ Section 6)
9. Am I choosing the format-spec mini-language deliberately (alignment/width/precision/thousands
   separator) rather than hand-rolling padding logic myself? (→ Section 7)
10. Am I building a string incrementally in a loop with `+=`? Would `''.join(list_of_parts)` be the
    safer, unconditionally-`O(n)` choice instead of relying on CPython's in-place-resize optimization?
    (→ Section 8)
11. Am I aware which encoding a byte stream is actually in before decoding it, rather than assuming
    UTF-8 by default? (→ Section 9)
12. Am I comparing or hashing strings that might have come from different input sources (different
    OSes/keyboards)? Could a Unicode normalization mismatch (NFC vs NFD) be causing a "look-identical
    but compare-unequal" bug? (→ Section 9)
13. Am I mixing `str` and `bytes` anywhere without an explicit `.encode()`/`.decode()` step in between?
    (→ Section 10)
14. Do I need mutable binary data I'll build up incrementally? That's `bytearray`, not `bytes`.
    (→ Section 10)
