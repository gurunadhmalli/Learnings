# LangChain Output Parsers — Complete Notes

---

## 1. Why Output Parsers?

### The Problem

When you call an LLM, it returns a **plain string** by default. For example:

> "The person is named Alex and they are 25 years old and work as a developer..."

This is just raw text — you **cannot** access `name`, `age`, or `job` directly from it in your code. It's unstructured and hard to work with programmatically.

### The Solution

An **Output Parser** sits between the LLM response and your application logic. It transforms that raw string into a **structured object** you can actually use:

```
name: "Alex"
age:  25
job:  "developer"
```

Now you can access `result.name`, `result.age`, etc.

### Why Are Output Parsers Important?

| Benefit | Description |
|---|---|
| **Parse JSON, lists, objects** | Convert raw LLM text into Python dicts, lists, or objects |
| **Handle errors gracefully** | Retry or fix malformed output automatically |
| **Enable downstream processing** | Feed structured data into APIs, databases, UIs |
| **Type-safe with Pydantic** | Validate types automatically, get IDE support |

> 💡 **Key idea:** Parsers bridge LLM output → Application logic

---

## 2. StrOutputParser

### What It Is

`StrOutputParser` is the **simplest parser** in LangChain. It takes the raw model response (an `AIMessage` object) and extracts just the clean text string from it.

### How It Works

```
AIMessage(content: "AI is transforming...") → StrOutputParser → "AI is transforming..."  (type: str)
```

The model returns an `AIMessage` object — not a plain string. `StrOutputParser` strips away the wrapper and gives you the `.content` field as a pure Python `str`.

### Code Example

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
chain = model | parser

result = chain.invoke("Tell me about AI")
print(result)        # "AI is transforming..."
print(type(result))  # <class 'str'>
```

### When to Use It

- Simple **text responses** where structure doesn't matter
- **Chat interfaces** — you just want the reply text
- When you **don't need structured data** downstream
- Quick prototyping

---

## 3. JsonOutputParser

### What It Is

`JsonOutputParser` parses LLM output into a **Python dictionary**. The LLM returns a JSON-formatted string, and the parser converts it into a usable `dict`.

### How It Works

```
LLM returns string:          →   JsonOutputParser   →   Python dict:
{                                                        name: "Alex"
  "name": "Alex",                                        age:  25
  "age": 25                                              (type: dict)
}"
```

### Code Example

```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

parser = JsonOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ("system", "Return a JSON object with name and age."),
    ("user", "{input}")
])

chain = prompt | model | parser

result = chain.invoke({"input": "Tell me about Alex who is 25"})

# Now access data like a dict:
print(result["name"])  # → "Alex"
print(result["age"])   # → 25
```

### When to Use It

- When you want a **Python dictionary** from LLM output
- For **simple flat structures** (no strict type enforcement needed)
- When you don't need Pydantic validation

### Limitation

It has no schema — the LLM might return unexpected keys or wrong types, and `JsonOutputParser` won't catch that. For strict validation, use `PydanticOutputParser`.

---

## 4. PydanticOutputParser ⭐ Recommended

### What It Is

`PydanticOutputParser` is the **most powerful and recommended** parser. It uses Pydantic models to:
1. **Define a schema** for what the output should look like
2. **Auto-generate instructions** for the LLM to follow
3. **Return a validated Python object** (not just a dict)

### How It Works — 3 Steps

#### Step 1 — Define a Schema (Pydantic Model)

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    job: str
```

This defines exactly what fields you expect and their types.

#### Step 2 — Auto Instructions Generated for LLM

The parser automatically creates a prompt instruction like:

> "Return JSON with name (str), age (int), job (str)..."

You don't have to write this manually — LangChain handles it for you.

#### Step 3 — Validated Object Returned

```python
# Result is a Person object, not a dict:
result.name  # → 'John'
result.age   # → 30
result.job   # → 'engineer'
```

### Full Code Example

```python
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

# 1. Define schema
class Person(BaseModel):
    name: str
    age: int
    job: str

# 2. Create parser
parser = PydanticOutputParser(pydantic_object=Person)

# 3. Build prompt with format instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract person info.\n{format_instructions}"),
    ("user", "{input}")
]).partial(format_instructions=parser.get_format_instructions())

# 4. Chain it
chain = prompt | model | parser

result = chain.invoke({"input": "John is 30 and works as an engineer"})
print(result.name)  # 'John'
print(result.age)   # 30
print(result.job)   # 'engineer'
```

### Why It's Recommended

| Feature | Benefit |
|---|---|
| ✅ **Type Safety** | Validates types automatically — `age` will always be `int` |
| ✅ **IDE Support** | Autocomplete and hints because it's a real Python class |
| ✅ **Error Handling** | Clear validation errors when LLM returns wrong types |
| ✅ **Nested objects** | Best for complex schemas with nested Pydantic models |

> 💡 **Best for:** Complex schemas with nested objects that need strict validation.

---

## 5. Structured Output — The 2026 Way

### What It Is

`with_structured_output()` is the **newest and simplest** approach introduced in LangChain V1. Instead of manually creating a parser and wiring it up, you call one method on the model directly.

### Old Way vs New Way

#### ❌ Old Way (5 Steps)

```python
# 1. Define Pydantic model
class MovieReview(BaseModel):
    title: str
    rating: int
    summary: str

# 2. Create PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=MovieReview)

# 3. Get format instructions
instructions = parser.get_format_instructions()

# 4. Add to prompt template
prompt = ChatPromptTemplate.from_messages([...]).partial(
    format_instructions=instructions
)

# 5. Chain together manually
chain = prompt | model | parser
```

#### ✅ New Way (1 Line!)

```python
structured_model = model.with_structured_output(MovieReview)
result = structured_model.invoke("Inception is a masterpiece. 9/10")
```

That's it. Returns a typed `MovieReview` object directly.

### Example: Movie Review

```python
from pydantic import BaseModel

class MovieReview(BaseModel):
    title: str
    rating: int
    summary: str

# One line setup
structured_model = model.with_structured_output(MovieReview)

# Invoke
result = structured_model.invoke("Inception is a masterpiece. 9/10")

print(result.title)    # 'Inception'
print(result.rating)   # 9
print(result.summary)  # '...'
```

### When to Use Each Approach

| Approach | Use When |
|---|---|
| `StrOutputParser` | You just need clean text, no structure |
| `JsonOutputParser` | You want a dict, no strict validation |
| `PydanticOutputParser` | You need strict types, nested objects, IDE hints |
| `with_structured_output()` | You want the simplest code with full type safety (modern, recommended) |

---

## Summary

```
LLM Raw Output (string)
        ↓
    [Output Parser]
        ↓
Structured Data → Application Logic
```

- **StrOutputParser** → plain `str`
- **JsonOutputParser** → Python `dict`
- **PydanticOutputParser** → validated Pydantic object (⭐ recommended for complex use)
- **with_structured_output()** → same as Pydantic but in one line (⭐ recommended for simplicity)

Output parsers are essential in any real LangChain application where you need to do something useful with the LLM's response beyond just printing it.
