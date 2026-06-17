
# LangChain Prompt Templates & Message Types - Detailed Notes

## 1. ChatPromptTemplate Basics

### What is ChatPromptTemplate?
ChatPromptTemplate is a LangChain component used to create dynamic prompts.

Instead of hardcoding prompts, you define a template once and provide values later.

### Example

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(
    "Tell me a {adjective} joke about {topic}"
)
```

### Variables

```python
adjective = "funny"
topic = "cats"
```

### Output

```text
Tell me a funny joke about cats
```

### Benefits
- Reusable
- Dynamic
- Easy maintenance
- Cleaner code

---

## 2. Message Types

### SystemMessage
Defines AI behavior, role, and personality.

```python
SystemMessage(
    content="You are a helpful tutor."
)
```

### HumanMessage
Represents user input.

```python
HumanMessage(
    content="Explain recursion."
)
```

### AIMessage
Stores model responses.

```python
AIMessage(
    content="Recursion is a function calling itself."
)
```

### ToolMessage
Contains results from tools/APIs.

```python
ToolMessage(
    content="Weather: 28°C"
)
```

### Conversation Flow

```text
System
 ↓
Human
 ↓
AI
 ↓
Human
 ↓
AI
```

---

## 3. Multi-Message Templates

### Purpose
Combine multiple message types into a single prompt.

### Example

```python
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a {role}. Always be {tone}."),
        ("human", "{question}")
    ]
)
```

### Input

```python
role = "tutor"
tone = "encouraging"
question = "Explain recursion"
```

### Generated Messages

```python
SystemMessage(
    content="You are a tutor. Always be encouraging."
)

HumanMessage(
    content="Explain recursion"
)
```

### Advantages
- Clear separation of instructions and user input
- Better maintainability
- Easier debugging

---

## 4. Few-Shot Prompting

### What is Few-Shot Prompting?

Teaching the model using examples.

### Examples

```text
happy → sad
tall → short
hot → cold
```

### New Input

```text
fast → ?
```

### Output

```text
slow
```

The model learns the pattern:
"Give the opposite word"

### Benefits
- Better accuracy
- Consistent outputs
- Less hallucination
- Easy implementation

### Common Use Cases
- Classification
- Translation
- Data extraction
- Structured output generation

---

## 5. Prompt Composition

### What is Prompt Composition?

Building large prompts using smaller reusable prompt blocks.

### Components

System Prompt:

```python
"You are a {role}."
```

User Prompt:

```python
"{question}"
```

### Combined Prompt

```text
You are a tutor.

Explain recursion.
```

### Benefits

#### Reusable
Use the same prompt blocks in multiple projects.

#### Modular
Replace one component without affecting others.

#### Maintainable
Update one place and changes apply everywhere.

---

## Real LangChain Example

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful {role}."),
        ("human", "{question}")
    ]
)

formatted_prompt = prompt.invoke(
    {
        "role": "Python Tutor",
        "question": "Explain recursion"
    }
)

print(formatted_prompt)
```

---

# Interview Questions

## ChatPromptTemplate
1. What is ChatPromptTemplate?
2. Why use templates?
3. What are template variables?
4. Difference between from_template() and from_messages()?

## Message Types
1. What is SystemMessage?
2. What is HumanMessage?
3. What is AIMessage?
4. What is ToolMessage?

## Few-Shot Prompting
1. What is Few-Shot Prompting?
2. Difference between Zero-Shot and Few-Shot?
3. Advantages of Few-Shot Prompting?

## Prompt Composition
1. What is Prompt Composition?
2. Benefits of reusable prompts?
3. Why modular prompts are important?

---

# Quick Revision

- ChatPromptTemplate = Dynamic Prompt Builder
- SystemMessage = AI Behavior
- HumanMessage = User Input
- AIMessage = Model Response
- ToolMessage = Tool Output
- Multi-Message Templates = Multiple messages in one prompt
- Few-Shot Prompting = Learning from examples
- Prompt Composition = Building prompts from reusable blocks
