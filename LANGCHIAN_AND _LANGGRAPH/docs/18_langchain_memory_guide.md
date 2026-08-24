# LangChain Memory — Complete Deep-Dive Guide

> **Course:** LangChain for Developers (Udemy)  
> **Topic:** Conversational Memory — Theory, Architecture & Code

---

## Table of Contents

1. [Why Memory Matters](#1-why-memory-matters)
2. [Memory Evolution in LangChain](#2-memory-evolution-in-langchain)
3. [Modern Message History Approach](#3-modern-message-history-approach)
4. [Memory Strategies — Theory & Comparison](#4-memory-strategies--theory--comparison)
5. [Trimming Messages](#5-trimming-messages)
6. [Persistent Memory with SQLite](#6-persistent-memory-with-sqlite)
7. [Message Types in LangChain](#7-message-types-in-langchain)
8. [Vector Store Memory (Semantic Memory)](#8-vector-store-memory-semantic-memory)
9. [LangGraph Memory for Agents](#9-langgraph-memory-for-agents)
10. [Multi-User Memory Patterns](#10-multi-user-memory-patterns)
11. [Memory + RAG (Retrieval-Augmented Generation)](#11-memory--rag-retrieval-augmented-generation)
12. [Code Examples](#12-code-examples)
13. [Key Takeaways & Mental Model](#13-key-takeaways--mental-model)

---

## 1. Why Memory Matters

### The Core Problem

LLMs (Large Language Models) are **stateless by nature**. Every API call is completely independent — the model has zero awareness of anything said before.

```
Without Memory:
  User: "My name is Paulo"
  AI:   "Nice to meet you, Paulo!"
  User: "What's my name?"
  AI:   "I don't know your name."  ❌

With Memory:
  User: "My name is Paulo"
  AI:   "Nice to meet you, Paulo!"
  User: "What's my name?"
  AI:   "Your name is Paulo."      ✅
```

### Why This Is a Problem

- Each LLM call sends a raw HTTP request with no session awareness
- The model processes ONLY what is in the current prompt
- Context from previous turns is **lost** unless explicitly re-injected

### The Solution: Inject History

Memory in LangChain is simply the mechanism of **storing past messages and re-injecting them into every new prompt**. The model doesn't truly "remember" — we feed it the conversation history each time.

```
[System Prompt] + [Past Messages] + [New User Message] → LLM → [Response]
```

This is the fundamental architecture of all memory implementations.

---

## 2. Memory Evolution in LangChain

### Legacy Approach (Deprecated in v0.3.1)

| Class | What It Does |
|---|---|
| `ConversationBufferMemory` | Stores all messages in RAM |
| `ConversationSummaryMemory` | Summarizes history with an LLM |
| `ConversationBufferWindowMemory` | Keeps only the last k messages |

**Why deprecated?** These classes mixed concerns — they handled both storage AND injection into prompts, making them hard to customize and maintain.

### Modern Approach (Recommended)

| Approach | Use Case |
|---|---|
| `RunnableWithMessageHistory` | Primary approach — wraps any chain with history |
| Manual message management | When you need full control over what gets injected |
| `LangGraph` state | For agents that need complex stateful workflows |

### Key Mindset Shift

**Old way:** "Memory is a component I attach to a chain."  
**New way:** "Message history is explicit state I manage and pass into my chain."

This makes the flow transparent and composable.

---

## 3. Modern Message History Approach

### Architecture Diagram

```
┌──────────────────────────┐
│       Session Store       │
│  ┌────────────────────┐  │        ┌─────────────────────────┐        ┌──────────────┐
│  │ session_abc        │  │        │                         │        │              │
│  │ Hi! → Hello! → ... │  │        │  RunnableWithMessage     │        │    Your      │
│  ├────────────────────┤  │──────► │       History           │──────► │    Chain     │
│  │ session_xyz        │  │        │                         │        │              │
│  │ Q1 → A1 → Q2 → ...│  │        │  input_messages_key      │        └──────────────┘
│  ├────────────────────┤  │        │  history_messages_key   │
│  │ session_123        │  │        │                         │
│  │ New chat           │  │        └─────────────────────────┘
│  └────────────────────┘  │
└──────────────────────────┘

        Each session_id gets its own conversation history
```

### How `RunnableWithMessageHistory` Works

1. You define a **chain** (prompt + LLM)
2. You define a **get_session_history** function that returns a message store for a given `session_id`
3. `RunnableWithMessageHistory` wraps the chain and automatically:
   - Fetches history for the current session
   - Injects history into the chain input
   - Saves the new response back to the store

### Session ID Concept

The `session_id` is a unique string that identifies a conversation. Think of it like a room key — it opens a specific conversation's history.

```python
config = {"configurable": {"session_id": "user_123_chat_1"}}
chain_with_history.invoke({"input": "Hello!"}, config=config)
```

Different users, different `session_id` → completely isolated histories.

---

## 4. Memory Strategies — Theory & Comparison

### Overview

As conversations grow longer, you face the **context window problem**: LLMs have a fixed token limit (e.g., 128k tokens). You can't keep injecting the full history forever.

Different strategies solve this trade-off differently:

| Strategy | Tokens Used | Best For |
|---|---|---|
| **Full Buffer** | Grows linearly | Short conversations |
| **Window (k=5)** | Fixed | Long conversations |
| **Summary** | Grows slowly | Very long conversations |
| **Summary + Buffer** | Moderate | Balance of detail & context |

---

### Strategy 1: Full Buffer

**Theory:** Store and inject every message, forever.

```
Turn 1: [Msg1]
Turn 2: [Msg1, Msg2]
Turn 3: [Msg1, Msg2, Msg3]
...
Turn N: [Msg1, Msg2, ..., MsgN]
```

**Pros:** Perfect recall — nothing is lost.  
**Cons:** Token cost grows linearly. Eventually exceeds context window.  
**Use when:** Conversations are short or you have a large context window.

---

### Strategy 2: Window Memory (k=N)

**Theory:** Only keep the last `k` message pairs (human + AI = 1 pair).

```
k=3 window:
Turn 1: [Msg1]
Turn 2: [Msg1, Msg2]
Turn 3: [Msg1, Msg2, Msg3]
Turn 4: [Msg2, Msg3, Msg4]  ← Msg1 dropped
Turn 5: [Msg3, Msg4, Msg5]  ← Msg2 dropped
```

**Pros:** Fixed, predictable token cost. Simple to implement.  
**Cons:** Older context is completely forgotten — the model loses early instructions or facts.  
**Use when:** Conversations are long but only recent context matters.

---

### Strategy 3: Summary Memory

**Theory:** Use an LLM to summarize the conversation so far, and inject the summary instead of raw messages.

```
Raw history:   "Hi Paulo... you work at Google... you like Python..."
               → LLM summarization →
Summary:       "User is Paulo, works at Google, prefers Python."

Turn N prompt: [System] + [Summary] + [New Message]
```

**Pros:** Tokens grow slowly. Preserves semantic meaning of long conversations.  
**Cons:** Summarization costs extra LLM calls. Some details may be lost. Adds latency.  
**Use when:** Conversations are very long (support chats, multi-session agents).

---

### Strategy 4: Summary + Buffer (Hybrid)

**Theory:** Keep a running summary of old messages AND a full buffer of the most recent k messages.

```
Prompt =  [Summary of turns 1-50]
        + [Full messages of turns 51-60]  ← recent turns in detail
        + [New turn 61]
```

**Pros:** Best of both worlds — semantic long-term memory + precise recent memory.  
**Cons:** Slightly more complex to implement.  
**Use when:** You need both long-term context and precise recall of recent exchanges.

---

## 5. Trimming Messages

### The Problem

Even with a modern approach (explicit message management), your list of messages will eventually grow too large for the context window.

```
Full History (2000 tokens):
  [System]  You are helpful...
  [User]    Old message 1
  [AI]      Old response 1
  [User]    Old message 2
  [AI]      Old response 2
  [User]    Recent question
  [AI]      Recent answer
```

Sending 2000 tokens every call is expensive and often unnecessary.

### The Solution: `trim_messages`

LangChain provides `trim_messages()` to slice the message list to fit within a token budget.

```
trim_messages(
  max_tokens=1000,
  strategy="last",        ← Keep the MOST RECENT messages
  include_system=True     ← Always keep the system prompt
)

Result — Trimmed (1000 tokens):
  [System]  You are helpful...
  [User]    Recent question
  [AI]      Recent answer
```

### Key Parameters

| Parameter | Description |
|---|---|
| `max_tokens` | Maximum total tokens to allow |
| `strategy` | `"last"` keeps newest messages; `"first"` keeps oldest |
| `include_system` | Whether to always preserve the system message |
| `token_counter` | Function to count tokens (can use model's tokenizer) |

### Why `include_system=True` Matters

The system message defines the AI's persona, rules, and context. If you trim it away, the model loses its instructions. Always preserve it.

### Trim Strategy Visualization

```
strategy="last" (most common):
  Before: [System, OldMsg1, OldAI1, OldMsg2, OldAI2, RecentMsg, RecentAI]
  After:  [System, RecentMsg, RecentAI]   ← trims from the front

strategy="first":
  Before: [System, OldMsg1, OldAI1, OldMsg2, OldAI2, RecentMsg, RecentAI]
  After:  [System, OldMsg1, OldAI1]       ← trims from the back (rare)
```

---

## 6. Persistent Memory with SQLite

### In-Memory vs. Persistent Storage

| | In-Memory Storage | SQLite Storage |
|---|---|---|
| Where data lives | RAM | Disk (`chat_history.db`) |
| Survives restart | ❌ Lost | ✅ Preserved |
| Setup complexity | Trivial | Simple |
| Use case | Dev/testing | Production |

### The Problem with In-Memory

```python
store = {}  # Lives in RAM
# App restarts → store = {} → all history gone
```

This is fine during development, but unacceptable in production — users would lose their entire conversation history on every server restart.

### SQLite Solution

```
session_id  →  SQLChatMessageHistory  →  sqlite:///chat.db
```

The `SQLChatMessageHistory` class from LangChain Community handles:
- Creating the database table automatically
- Writing new messages on each turn
- Reading existing messages when a session is resumed
- Thread-safe operations

### Usage Pattern

```python
from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_session_history(session_id: str):
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string="sqlite:///chat_history.db"
    )
```

The database file persists between runs, so history is fully preserved across restarts.

### Other Storage Backends

SQLite is just one option. LangChain supports:
- **Redis** — for distributed/multi-server deployments
- **PostgreSQL / MySQL** — production databases
- **MongoDB** — document-based storage
- **DynamoDB** — AWS serverless option
- **Firestore** — Google Cloud option

All follow the same `BaseChatMessageHistory` interface, so you can swap backends without changing your chain logic.

---

## 7. Message Types in LangChain

Understanding message types is foundational — memory is just a list of these message objects stored and retrieved.

### The Four Core Message Types

| Type | Class | Role | When Created |
|---|---|---|---|
| System | `SystemMessage` | Sets AI persona/rules | You (developer) |
| Human | `HumanMessage` | User's input | User |
| AI | `AIMessage` | Model's response | LLM |
| Tool | `ToolMessage` | Result of a tool call | Tool execution |

### How Messages Flow Through Memory

```
Every conversation is just a list of message objects:

[
  SystemMessage(content="You are a helpful assistant."),
  HumanMessage(content="My name is Paulo"),
  AIMessage(content="Nice to meet you, Paulo!"),
  HumanMessage(content="What's my name?"),
  AIMessage(content="Your name is Paulo."),
]

This list IS the memory. Everything else is just how you store,
retrieve, and trim this list.
```

### Message Object Structure

```python
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

# Creating messages manually
system = SystemMessage(content="You are a pirate assistant.")
human  = HumanMessage(content="Hello!")
ai     = AIMessage(content="Ahoy there, matey!")

# AIMessage can also carry tool calls
ai_with_tool = AIMessage(
    content="",
    tool_calls=[{"name": "search", "args": {"query": "weather"}, "id": "call_001"}]
)

# ToolMessage carries the result back
tool_result = ToolMessage(
    content="Sunny, 25°C",
    tool_call_id="call_001"
)
```

### Why This Matters for Memory

When you store memory, you store these objects. When you retrieve memory, you get these objects back. The `BaseChatMessageHistory` interface is just:

```python
class BaseChatMessageHistory:
    def add_message(self, message: BaseMessage) -> None: ...
    def get_messages(self) -> list[BaseMessage]: ...
    def clear(self) -> None: ...
```

Simple as that — add, get, clear.

---

## 8. Vector Store Memory (Semantic Memory)

### The Problem with Sequential Memory

Buffer and window strategies retrieve messages **by recency**. But what if a critical fact from 200 turns ago is relevant RIGHT NOW?

```
Turn 3:   User says "I'm allergic to peanuts"
Turn 205: User asks "Can I eat pad thai?"

Window memory (k=10) → Turn 3 is gone → AI doesn't know about allergy ❌
Vector memory        → Semantic search finds turn 3 → AI knows ✅
```

### How Vector Store Memory Works

Instead of injecting all past messages, you:
1. **Store** each message as a vector embedding in a vector database
2. **At query time**, embed the current user message
3. **Retrieve** the top-k most semantically similar past messages
4. **Inject** only those relevant memories into the prompt

```
New message: "Can I eat pad thai?"
     ↓
Embed → [0.23, -0.87, 0.41, ...]
     ↓
Vector DB similarity search
     ↓
Top matches: ["I'm allergic to peanuts" (turn 3), ...]
     ↓
Inject into prompt as relevant context
```

### Architecture

```
User message
     │
     ▼
┌─────────────┐     embed      ┌─────────────────┐
│  Embeddings │ ──────────────►│   Vector Store  │
│   Model     │                │  (Chroma/FAISS/ │
└─────────────┘                │   Pinecone...)  │
                               └────────┬────────┘
                                        │ similarity search
                                        ▼
                               Top-k relevant memories
                                        │
                                        ▼
                            [System] + [Relevant Memories] + [New Message]
                                        │
                                        ▼
                                       LLM
```

### When to Use Vector Memory

- Long-running conversations (hundreds of turns)
- Personal assistant apps that accumulate user preferences
- Customer support with deep product knowledge per user
- Any scenario where **relevance** matters more than **recency**

### Code: Vector Store Memory with Chroma

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document

embeddings = OpenAIEmbeddings()
vectorstore = Chroma(embedding_function=embeddings)

def save_to_memory(user_msg: str, ai_msg: str, session_id: str):
    """Store a conversation turn as a document."""
    doc = Document(
        page_content=f"User: {user_msg}\nAI: {ai_msg}",
        metadata={"session_id": session_id}
    )
    vectorstore.add_documents([doc])

def retrieve_relevant_memory(query: str, session_id: str, k: int = 3):
    """Fetch top-k semantically relevant past exchanges."""
    results = vectorstore.similarity_search(
        query,
        k=k,
        filter={"session_id": session_id}  # isolate by user
    )
    return "\n".join([doc.page_content for doc in results])

# Usage in a chain
def chat_with_memory(user_input: str, session_id: str):
    relevant_past = retrieve_relevant_memory(user_input, session_id)
    
    prompt = f"""Relevant past context:
{relevant_past}

Current message: {user_input}"""
    
    response = ChatOpenAI(model="gpt-4o").invoke(prompt)
    save_to_memory(user_input, response.content, session_id)
    return response.content
```

---

## 9. LangGraph Memory for Agents

### Why Agents Need Different Memory

Simple chains have a fixed flow: input → process → output. Agents are dynamic — they decide which tools to call, loop back on results, and can run for many steps. Standard `RunnableWithMessageHistory` doesn't handle this complexity well.

**LangGraph** treats the entire agent state (including memory) as an explicit, typed graph state that flows through nodes.

### The State-as-Memory Concept

```python
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# The state IS the memory
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # add_messages is a reducer: it appends new messages
    # instead of overwriting the list
```

Every node in the graph reads from and writes to this state. The message list grows automatically as the agent runs.

### LangGraph Agent with Persistent Memory

```
┌─────────────┐
│    START    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Agent     │  ← Reads state.messages, decides action
│   Node      │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
Tools   END
Node
   │
   └──► Agent Node  (loops back)
```

### Short-Term vs Long-Term in LangGraph

| Memory Type | Scope | Implementation |
|---|---|---|
| **Short-term** | Within one run | `state["messages"]` list |
| **Long-term** | Across runs/restarts | `MemorySaver` checkpointer |

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# MemorySaver persists state between invocations
checkpointer = MemorySaver()

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o"),
    tools=[search_tool, calculator_tool],
    checkpointer=checkpointer,   # ← this enables memory
)

# thread_id acts like session_id
config = {"configurable": {"thread_id": "user_001_session_1"}}

# Turn 1
agent.invoke({"messages": [("user", "My budget is $500")]}, config=config)

# Turn 2 — agent remembers the $500 budget
agent.invoke({"messages": [("user", "Recommend a laptop")]}, config=config)
```

### `add_messages` Reducer — Deep Explanation

The `add_messages` annotation is key. Without it, each node would overwrite the messages list. With it, messages are **appended**, building up the history automatically:

```python
# Without add_messages (bad):
state = {"messages": [msg1]}
node_output = {"messages": [msg2]}
new_state = {"messages": [msg2]}  # msg1 is GONE ❌

# With add_messages (correct):
state = {"messages": [msg1]}
node_output = {"messages": [msg2]}
new_state = {"messages": [msg1, msg2]}  # both preserved ✅
```

---

## 10. Multi-User Memory Patterns

### The Problem

In production, you have many users. Each needs isolated memory. A naive implementation leaks one user's history to another.

### Pattern 1: Session ID Namespacing

The simplest approach — encode the user ID in the session ID:

```python
def get_session_id(user_id: str, conversation_id: str) -> str:
    return f"{user_id}:{conversation_id}"

# User A
config_a = {"configurable": {"session_id": "user_alice:chat_1"}}

# User B — completely separate history
config_b = {"configurable": {"session_id": "user_bob:chat_1"}}
```

### Pattern 2: Per-User Database Rows (SQLite)

`SQLChatMessageHistory` automatically isolates by `session_id` in the database:

```
Table: message_store
┌─────────────────┬──────────┬─────────────────────┐
│  session_id     │  type    │  content             │
├─────────────────┼──────────┼─────────────────────┤
│ alice:chat_1    │ human    │ "My name is Alice"   │
│ alice:chat_1    │ ai       │ "Hi Alice!"          │
│ bob:chat_1      │ human    │ "My name is Bob"     │
│ bob:chat_1      │ ai       │ "Hi Bob!"            │
└─────────────────┴──────────┴─────────────────────┘
```

Each `session_id` is a completely isolated partition.

### Pattern 3: Cross-Session User Profile Memory

For a persistent user profile across all conversations:

```python
# Short-term: conversation-specific (session_id = user+chat)
short_term = SQLChatMessageHistory(
    session_id=f"{user_id}:{chat_id}",
    connection_string="sqlite:///chats.db"
)

# Long-term: user-level profile (session_id = just the user)
long_term = SQLChatMessageHistory(
    session_id=f"profile:{user_id}",
    connection_string="sqlite:///profiles.db"
)

# Inject both into prompt
prompt = f"""
User Profile (long-term): {get_profile_summary(user_id)}
Recent conversation: {short_term.messages}
Current message: {user_input}
"""
```

### Clearing Memory

Always provide a way to clear a user's history:

```python
def clear_user_memory(session_id: str):
    history = get_session_history(session_id)
    history.clear()
    print(f"Cleared memory for session: {session_id}")
```

---

## 11. Memory + RAG (Retrieval-Augmented Generation)

### Two Different Retrieval Problems

| | Conversational Memory | RAG |
|---|---|---|
| What it retrieves | Past conversation turns | External documents/knowledge |
| Source | Your own chat history store | Knowledge base, PDFs, databases |
| Purpose | Remember what the user said | Answer from external knowledge |
| Retrieval trigger | Every turn (inject history) | When user asks about documents |

### Combining Both — The Power Pattern

```
User: "Based on the contract I uploaded, what did we agree about payment terms?
       And remember I mentioned I'm on a tight deadline."

          ┌──────────────────────────────┐
          │         Final Prompt          │
          │                              │
          │ [System]                     │
          │ [Memory: "tight deadline"]   │ ← from conversation history
          │ [RAG: contract payment terms]│ ← from uploaded document
          │ [User's current question]    │
          └──────────────────────────────┘
```

### Architecture

```python
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

def build_memory_rag_chain(retriever, model, get_history_fn):
    
    def get_context(inputs):
        # RAG: retrieve from knowledge base
        docs = retriever.invoke(inputs["input"])
        return "\n".join([d.page_content for d in docs])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are helpful. Use the context and history below."),
        ("system", "Retrieved context:\n{context}"),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])
    
    chain = (
        RunnablePassthrough.assign(context=RunnableLambda(get_context))
        | prompt
        | model
    )
    
    return RunnableWithMessageHistory(
        chain,
        get_history_fn,
        input_messages_key="input",
        history_messages_key="history",
    )
```

### Key Insight

RAG and memory solve **different** retrieval problems. Always use both in a production assistant:
- **Memory** = What did WE talk about?
- **RAG** = What does the knowledge base say?

---

## 12. Code Examples

### Example 1: Basic RunnableWithMessageHistory

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 1. Define your chain
model = ChatOpenAI(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="history"),  # ← history injected here
    ("human", "{input}"),
])

chain = prompt | model

# 2. Define session store
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 3. Wrap chain with history
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 4. Invoke with session config
config = {"configurable": {"session_id": "user_001"}}
response = chain_with_history.invoke({"input": "My name is Paulo"}, config=config)
response2 = chain_with_history.invoke({"input": "What's my name?"}, config=config)
print(response2.content)  # "Your name is Paulo."
```

---

### Example 2: Trimming Messages

```python
from langchain_core.messages import trim_messages
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

trimmer = trim_messages(
    max_tokens=1000,
    strategy="last",
    token_counter=model,       # use the model's tokenizer
    include_system=True,       # always keep system message
    allow_partial=False,       # don't cut mid-message
    start_on="human",          # ensure we start on a human turn
)

# Use trimmer in your chain
from langchain_core.runnables import RunnablePassthrough

chain = (
    RunnablePassthrough.assign(messages=lambda x: trimmer.invoke(x["messages"]))
    | prompt
    | model
)
```

---

### Example 3: Persistent SQLite Memory

```python
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

def get_session_history(session_id: str):
    return SQLChatMessageHistory(
        session_id=session_id,
        connection_string="sqlite:///chat_history.db"
        # Change this to postgresql://user:pass@host/db for PostgreSQL
    )

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Now conversations persist across restarts ✅
config = {"configurable": {"session_id": "user_001"}}
chain_with_history.invoke({"input": "Remember I like Python"}, config=config)

# Restart server... 
# Resume conversation — history is still there ✅
chain_with_history.invoke({"input": "What language do I like?"}, config=config)
```

---

### Example 4: Window Strategy (Manual)

```python
from langchain_core.messages import HumanMessage, AIMessage

def get_windowed_history(messages: list, k: int = 5):
    """Keep only the last k human+AI pairs."""
    # Always preserve system message (index 0)
    system = messages[:1]
    rest = messages[1:]
    
    # Each pair = 2 messages (human + AI)
    windowed = rest[-(k * 2):]
    
    return system + windowed
```

---

## 13. Key Takeaways & Mental Model

### The Golden Rule

> **LLMs don't remember. YOU remember, and you remind them.**

Every "memory" technique is just a different strategy for deciding:
1. What past context to include
2. How much of it to include
3. In what format to include it

### Decision Tree for Choosing a Strategy

```
How long are your conversations?
│
├── Short (< 20 turns)
│   └── Use: Full Buffer  →  SimpleChatMessageHistory
│
├── Medium (20-100 turns)  
│   └── Use: Window (k=10-20)  →  Manual slicing or trim_messages
│
├── Long (100+ turns)
│   └── Use: Summary or Summary+Buffer
│
└── Unknown / Varies
    └── Use: Summary+Buffer (safest default)

Does history need to survive restarts?
├── No (dev/testing)  →  InMemoryChatMessageHistory
└── Yes (production)  →  SQLChatMessageHistory or Redis
```

### The Three Layers of Memory

```
Layer 1: WHAT to store
  → All messages? Recent only? A summary?

Layer 2: WHERE to store it
  → RAM (in-memory) or disk (SQLite, Redis, Postgres)?

Layer 3: HOW to inject it
  → RunnableWithMessageHistory handles this automatically
```

### Common Pitfalls to Avoid

| Pitfall | Fix |
|---|---|
| Sending full history every time | Use `trim_messages` with a token budget |
| Using deprecated `ConversationBufferMemory` | Use `RunnableWithMessageHistory` |
| Storing history in RAM for production | Use SQLite or another persistent backend |
| Not including system message after trimming | Set `include_system=True` |
| Using same `session_id` for different users | Generate unique IDs per user+conversation |

### Token Cost Mental Model

```
Full Buffer:      ████████████████████ (grows forever)
Window (k=5):     ████████████         (fixed ceiling)
Summary:          ██                   (very compact but lossy)
Summary+Buffer:   █████████            (balanced)
```

---

## Quick Reference Card

```python
# ── Core Message Types ──────────────────────────────────────────
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, ToolMessage,
    trim_messages,
)

# ── Prompt with history placeholder ─────────────────────────────
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ── In-memory history (dev/testing) ─────────────────────────────
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# ── Persistent history (production) ─────────────────────────────
from langchain_community.chat_message_histories import SQLChatMessageHistory

# ── Vector memory ────────────────────────────────────────────────
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# ── LangGraph agent memory ───────────────────────────────────────
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages

# ── Key concepts ─────────────────────────────────────────────────
# session_id / thread_id  → unique key per conversation
# history_messages_key    → MessagesPlaceholder name in prompt
# input_messages_key      → key for the new user message
# max_tokens + strategy   → how to trim when history is too long
# add_messages            → LangGraph reducer that appends messages
# checkpointer            → LangGraph persistent state across runs
```

---

*Generated from Udemy LangChain course slides — June 2026*
