# LangChain Output Parsers — Quick Reference

> Quick-reference version — see [09_output_parser.md](09_output_parser.md) for the complete deep dive.

---

## 1. Why Output Parsers?

LLMs return an `AIMessage` object, not a plain string — you can't directly pull `name`, `age`, etc. out of it. An **Output Parser** sits between the LLM response and your app logic and converts that raw output into a structured object (dict, list, Pydantic model...) you can actually use.

| Benefit | Description |
|---|---|
| **Parse JSON, lists, objects** | Convert raw LLM text into Python dicts, lists, or objects |
| **Handle errors gracefully** | Retry or fix malformed output automatically |
| **Enable downstream processing** | Feed structured data into APIs, databases, UIs |
| **Type-safe with Pydantic** | Validate types automatically, get IDE support |

> 💡 Parsers bridge LLM output → Application logic. (See 09 for the full `AIMessage` walkthrough and pipeline diagrams.)

---

## 2. StrOutputParser

Simplest parser — takes the `AIMessage` and returns just `.content` as a plain `str`.

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
chain = model | parser
result = chain.invoke("Tell me about AI")   # → str
```

**Use when:** plain text responses, chat interfaces, quick prototyping — no structure needed.

---

## 3. JsonOutputParser

Parses LLM output (a JSON-formatted string) into a Python **dict**.

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
chain = prompt | model | parser
result = chain.invoke({"input": "..."})
result["name"]   # dict-style access
```

**Use when:** you want a dict and don't need strict schema validation.

**Limitation:** no schema — the LLM can return unexpected keys or wrong types and `JsonOutputParser` won't catch it. Use `PydanticOutputParser` for that.

---

## 4. PydanticOutputParser ⭐ Recommended

Uses a Pydantic model to (1) define a schema, (2) auto-generate format instructions for the LLM, (3) return a **validated object** instead of a dict.

```python
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

class Person(BaseModel):
    name: str
    age: int
    job: str

parser = PydanticOutputParser(pydantic_object=Person)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract person info.\n{format_instructions}"),
    ("user", "{input}")
]).partial(format_instructions=parser.get_format_instructions())

chain = prompt | model | parser
result = chain.invoke({"input": "John is 30 and works as an engineer"})

result.name  # 'John'  — real attribute access, not dict lookup
```

| Feature | Benefit |
|---|---|
| ✅ **Type Safety** | Validates types automatically — `age` will always be `int` |
| ✅ **IDE Support** | Autocomplete and hints because it's a real Python class |
| ✅ **Error Handling** | Clear validation errors when LLM returns wrong types |
| ✅ **Nested objects** | Best for complex schemas with nested Pydantic models |

---

## 5. Structured Output — The 2026 Way

`with_structured_output()` is the newest, simplest approach (LangChain V1) — it skips manually building a parser and wiring it into the chain.

### Old Way (5 steps) vs New Way (1 line)

```python
# Old: define schema → PydanticOutputParser → get_format_instructions()
#      → add instructions to prompt → chain = prompt | model | parser

# New:
structured_model = model.with_structured_output(MovieReview)
result = structured_model.invoke("Inception is a masterpiece. 9/10")
```

Returns a typed object directly — no manual parser plumbing.

```python
from pydantic import BaseModel

class MovieReview(BaseModel):
    title: str
    rating: int
    summary: str

structured_model = model.with_structured_output(MovieReview)
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
| `with_structured_output()` | Simplest code with full type safety (modern, recommended) |

---

## Summary

- **StrOutputParser** → plain `str`
- **JsonOutputParser** → Python `dict`
- **PydanticOutputParser** → validated Pydantic object (⭐ recommended for complex use)
- **with_structured_output()** → same result as Pydantic but in one line (⭐ recommended for simplicity — not covered in 09)
