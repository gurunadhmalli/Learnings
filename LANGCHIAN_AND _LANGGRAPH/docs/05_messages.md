# LangChain Messages - Complete Notes

## What are Messages?

Messages are the fundamental building blocks of communication between a user and an LLM in LangChain.

Think of Messages as:

```text
Human  ---> Message ---> LLM
LLM    ---> Message ---> Human
```

Every conversation in LangChain is represented as a list of Messages.

Example:

```python
messages = [
    SystemMessage("You are a helpful assistant"),
    HumanMessage("What is AI?")
]
```

The model receives these messages and generates an AIMessage.

---

# Why Messages Exist?

Before Chat Models, people used simple prompts:

```python
model.invoke("What is AI?")
```

This works for one question.

But conversations require:

* Instructions
* User questions
* Previous answers
* Tool outputs
* Images
* PDFs

A simple string cannot store all of that.

Therefore LangChain uses Messages.

---

# Message Structure

Every Message contains three major parts:

```text
Message
│
├── Role
├── Content
└── Metadata
```

---

## 1. Role

Role tells the model who sent the message.

Examples:

```python
SystemMessage(...)
HumanMessage(...)
AIMessage(...)
ToolMessage(...)
```

Think of Role as:

```text
Who is speaking?
```

---

## 2. Content

Content contains the actual data.

Example:

```python
HumanMessage(
    content="What is Machine Learning?"
)
```

Content may contain:

* Text
* Images
* Audio
* Video
* PDF files
* Tool results

---

## 3. Metadata

Metadata contains extra information.

Example:

```python
HumanMessage(
    content="Hello",
    id="123",
    name="gurunadh"
)
```

Metadata is not the conversation itself.

It stores:

* Message ID
* User name
* Token usage
* Response details

---

# Message Flow

Example:

```python
messages = [
    SystemMessage("You are a teacher"),
    HumanMessage("What is AI?")
]

response = model.invoke(messages)
```

Flow:

```text
SystemMessage
      ↓
HumanMessage
      ↓
     LLM
      ↓
AIMessage
```

---

# Message Types

LangChain has four main message types.

```text
BaseMessage
│
├── SystemMessage
├── HumanMessage
├── AIMessage
└── ToolMessage
```

---

# 1. SystemMessage

Most important message.

Used to control model behavior.

Example:

```python
SystemMessage(
    content="You are an AI teacher."
)
```

Meaning:

```text
The model should behave like an AI teacher.
```

---

## Real Example

```python
messages = [
    SystemMessage(
        content="Answer only AI questions."
    ),
    HumanMessage(
        content="What is a transistor?"
    )
]
```

The model may refuse because the SystemMessage has higher priority.

---

## Purpose of SystemMessage

Used for:

* Role definition
* Rules
* Personality
* Tone
* Formatting

Example:

```python
SystemMessage(
"""
You are a senior Python developer.
Always explain code.
Give examples.
"""
)
```

---

# 2. HumanMessage

Represents user input.

Example:

```python
HumanMessage(
    content="What is AI?"
)
```

Meaning:

```text
This message came from the user.
```

---

## Shortcut

These are equivalent:

```python
model.invoke(
    HumanMessage("What is AI?")
)
```

and

```python
model.invoke(
    "What is AI?"
)
```

A string is automatically converted into a HumanMessage.

---

# 3. AIMessage

Represents model output.

Example:

```python
response = model.invoke("What is AI?")
```

Returned object:

```python
AIMessage(...)
```

---

## AIMessage Content

```python
print(response.content)
```

Output:

```text
Artificial Intelligence is...
```

---

## AIMessage Metadata

AIMessage also stores:

```python
response.id
response.usage_metadata
response.response_metadata
```

---

### Token Usage

```python
response.usage_metadata
```

Example:

```python
{
    "input_tokens": 50,
    "output_tokens": 100,
    "total_tokens": 150
}
```

Useful for:

* Cost tracking
* Token monitoring

---

# Multi-Turn Conversations

Example:

```python
messages = [
    HumanMessage("What is AI?")
]

response = model.invoke(messages)

messages.append(response)

messages.append(
    HumanMessage("Explain with example")
)
```

Now history becomes:

```text
Human: What is AI?
AI: Artificial Intelligence...
Human: Explain with example
```

The model remembers previous context.

---

# Why We Append AIMessage

Without:

```python
messages.append(response)
```

history becomes:

```text
Human: What is AI?
Human: Explain with example
```

Model forgets its previous answer.

With append:

```text
Human
AI
Human
AI
```

Full conversation remains.

---

# 4. ToolMessage

Used when tools are involved.

Example:

```python
search()
weather()
database_query()
```

Flow:

```text
HumanMessage
      ↓
AIMessage (tool call)
      ↓
ToolMessage
      ↓
AIMessage (final answer)
```

---

# Tool Calling Flow

User:

```text
What is the weather in Hyderabad?
```

Model:

```python
AIMessage(
    tool_calls=[...]
)
```

Tool Executes:

```python
ToolMessage(
    content="34°C"
)
```

Model Generates:

```python
AIMessage(
    content="Current temperature is 34°C."
)
```

---

# Content Types

Content is not limited to text.

LangChain supports:

```text
Text
Images
Audio
Video
PDF
Tool Calls
Reasoning
```

---

## Text Example

```python
HumanMessage(
    content="Explain AI"
)
```

---

## Image Example

```python
HumanMessage(
    content=[
        {
            "type":"image",
            "url":"image.jpg"
        }
    ]
)
```

---

## PDF Example

```python
HumanMessage(
    content=[
        {
            "type":"file",
            "url":"resume.pdf"
        }
    ]
)
```

---

# Message History

Think of Messages as a ChatGPT conversation.

```text
System : You are a teacher

Human  : What is AI?

AI      : AI is...

Human  : Give example

AI      : Self-driving cars...
```

Stored as:

```python
messages = [
    SystemMessage(...),
    HumanMessage(...),
    AIMessage(...),
    HumanMessage(...),
    AIMessage(...)
]
```

This entire list becomes the model's memory.

---

# Interview Question

## Difference Between Prompt and Messages

Prompt:

```python
model.invoke("What is AI?")
```

Single request.

No history.

---

Messages:

```python
messages = [
    SystemMessage(...),
    HumanMessage(...)
]
```

Supports:

* History
* Roles
* Images
* PDFs
* Tool Calls
* Multi-turn conversations

---

# One-Line Summary

```text
Messages are structured conversation objects used by LangChain to represent system instructions, user input, AI responses, and tool outputs while maintaining conversation history and metadata.
```
