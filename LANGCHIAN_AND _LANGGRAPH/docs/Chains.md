# LangChain LCEL (LangChain Expression Language) – Complete Learning Notes

# Table of Contents

1. Introduction to Chains
2. Legacy Chains vs LCEL
3. Understanding the Pipe (`|`) Operator
4. How Data Flows Through a Chain
5. Runnable Architecture
6. Chain Composition Patterns
   - Sequential
   - Parallel
   - Passthrough
7. Debugging Chains
8. Best Practices
9. Interview Questions
10. Complete Examples

---

# 1. Introduction to Chains

A chain is a workflow where the output of one component becomes the input of the next component.

Example:

User Question
→ Prompt Template
→ LLM
→ Output Parser
→ Final Answer

LangChain originally provided classes such as:

- LLMChain
- SequentialChain
- TransformChain

These are now considered legacy approaches.

The modern approach is LCEL (LangChain Expression Language).

---

# 2. Legacy Chains vs LCEL

## Legacy (Deprecated)

Older LangChain versions used:

### LLMChain

```python
from langchain.chains import LLMChain

chain = LLMChain(
    llm=llm,
    prompt=prompt
)
```

Problems:

- Less flexible
- Harder to compose
- Difficult debugging
- Complex nested chains

---

### SequentialChain

Used when multiple chains execute one after another.

```text
Input
 ↓
Chain 1
 ↓
Chain 2
 ↓
Chain 3
```

Problems:

- Verbose code
- Hard maintenance

---

### TransformChain

Used to transform data between steps.

Example:

```text
Text
 ↓
Clean Text
 ↓
LLM
```

Problems:

- Additional boilerplate
- Not easily composable

---

## LCEL (Current Standard)

LCEL uses the pipe operator.

```python
chain = prompt | model | parser
```

Advantages:

### Simpler

One line chain creation.

### Composable

Any runnable can be connected.

### Streamable

Supports streaming responses.

### Async Support

Works with async operations.

### Easier Debugging

Each component is a runnable.

### Better Performance

Optimized execution engine.

---

# 3. Understanding the Pipe Operator

The pipe operator:

```python
|
```

connects runnables together.

Example:

```python
chain = prompt | model | parser
```

Equivalent conceptual flow:

```text
prompt.invoke()
      ↓
model.invoke()
      ↓
parser.invoke()
```

Each stage receives the output from the previous stage.

---

## Why Pipe Operator is Powerful

Without LCEL:

```python
prompt_value = prompt.invoke(data)

response = model.invoke(prompt_value)

result = parser.invoke(response)
```

With LCEL:

```python
chain = prompt | model | parser

result = chain.invoke(data)
```

Much cleaner.

---

# 4. How Data Flows Through a Chain

Consider:

```python
chain = prompt | model | parser
```

Input:

```python
{
    "topic": "Artificial Intelligence"
}
```

Step 1:

Prompt template creates:

```text
Tell me about Artificial Intelligence
```

Step 2:

Model receives prompt.

Example:

```text
Artificial Intelligence is...
```

Step 3:

Parser converts response into desired format.

Example:

```python
"Artificial Intelligence is..."
```

Final Output:

```python
result
```

---

# 5. Runnable Architecture

A very important concept.

Everything in LCEL is a Runnable.

Examples:

```python
PromptTemplate
ChatPromptTemplate
ChatModel
OutputParser
RunnableLambda
RunnableParallel
RunnablePassthrough
```

All implement:

```python
.invoke()
.batch()
.stream()
.ainvoke()
```

---

## Runnable Sequence

When we write:

```python
prompt | model | parser
```

LangChain internally creates:

```python
RunnableSequence
```

Conceptually:

```text
RunnableSequence
 ├── Prompt
 ├── Model
 └── Parser
```

The entire chain is itself a runnable.

Therefore:

```python
chain.invoke()
chain.stream()
chain.batch()
```

all work.

---

# 6. Chain Composition Patterns

LCEL supports multiple composition styles.

---

# Sequential Pattern

Most common.

```python
chain = step1 | step2 | step3
```

Flow:

```text
Input
 ↓
Step1
 ↓
Step2
 ↓
Step3
 ↓
Output
```

Example:

```python
prompt | model | parser
```

Use Cases:

- Question answering
- Summarization
- Translation
- Classification

---

# Parallel Pattern (RunnableParallel)

Run multiple chains simultaneously.

Example:

```python
from langchain_core.runnables import RunnableParallel
```

```python
parallel_chain = RunnableParallel({
    "summary": summary_chain,
    "keywords": keywords_chain
})
```

Flow:

```text
           Input
          /     \
         /       \
Summary Chain   Keyword Chain
         \       /
          \     /
         Combined Output
```

Output:

```python
{
    "summary": "...",
    "keywords": "..."
}
```

Advantages:

### Faster

Independent tasks run together.

### Efficient

One input, multiple outputs.

### Cleaner Architecture

Avoids duplicate processing.

---

## Real Example

Document:

```text
AI is transforming industries...
```

Parallel Tasks:

1. Generate Summary
2. Extract Keywords
3. Detect Sentiment

Output:

```python
{
    "summary": "...",
    "keywords": [...],
    "sentiment": "positive"
}
```

---

# Passthrough Pattern

Used heavily in RAG.

Import:

```python
from langchain_core.runnables import RunnablePassthrough
```

Purpose:

Keep original input while adding new information.

---

Example

User asks:

```text
What is RAG?
```

Retriever finds:

```text
Relevant Context
```

Need both:

- Original Question
- Retrieved Context

Flow:

```text
Question
    ↓
RunnablePassthrough
    ↓
Retriever
    ↓
Context Added
```

Result:

```python
{
    "question": "What is RAG?",
    "context": "..."
}
```

Then:

```python
prompt | model
```

receives both values.

---

## RAG Example

```python
rag_chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
)
```

This is one of the most important LCEL patterns.

---

# 7. Debugging Chains

Debugging is essential when chains become complex.

Three major approaches were shown.

---

# Method 1: Verbose Logging

Simple debugging.

```python
langchain.debug = True
```

or

```python
verbose=True
```

Benefits:

- Shows execution flow
- Displays prompts
- Displays outputs

Good for beginners.

---

# Method 2: Callbacks

More flexible.

Callbacks allow intercepting events.

Examples:

- Chain Start
- Chain End
- LLM Start
- LLM End
- Tool Start
- Tool End

Example:

```python
callbacks=[handler]
```

Use Cases:

- Custom logging
- Monitoring
- Analytics
- Cost tracking

---

# Method 3: LangSmith

Professional debugging platform.

Capabilities:

### Trace Visualization

View complete chain execution.

### Latency Analysis

Find slow components.

### Cost Monitoring

Track token usage.

### Dataset Evaluation

Test prompts at scale.

### Experiment Tracking

Compare versions.

Recommended for production systems.

---

# 8. Best Practices

## Use LCEL

Prefer:

```python
prompt | model | parser
```

Avoid:

```python
LLMChain
SequentialChain
TransformChain
```

---

## Keep Chains Small

Good:

```python
prompt | model
```

Avoid huge chains.

---

## Use Output Parsers

Instead of raw text:

```python
model | parser
```

Benefits:

- Structured output
- JSON generation
- Reliable responses

---

## Use Parallelism

If tasks are independent:

```python
RunnableParallel
```

saves time.

---

## Use LangSmith

For serious applications.

---

# 9. Common Interview Questions

## What is LCEL?

LCEL stands for LangChain Expression Language.

A declarative way to compose chains using runnables and the pipe operator.

---

## Why replace LLMChain?

Because LCEL is:

- More composable
- More readable
- Faster
- Easier to debug

---

## What does `|` do?

It connects runnables and creates a RunnableSequence.

---

## What is RunnableParallel?

Runs multiple chains simultaneously and combines outputs.

---

## What is RunnablePassthrough?

Keeps the original input while adding new values.

Very common in RAG pipelines.

---

## Is the final chain also a runnable?

Yes.

```python
chain.invoke()
chain.stream()
chain.batch()
chain.ainvoke()
```

all work.

---

# 10. Complete Example

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model

prompt = ChatPromptTemplate.from_template(
    "Explain {topic} in simple terms."
)

model = init_chat_model(
    model="command-a-03-2025",
    model_provider="cohere"
)

parser = StrOutputParser()

chain = prompt | model | parser

response = chain.invoke(
    {"topic": "LCEL"}
)

print(response)
```

Flow:

```text
Input Dictionary
      ↓
Prompt Template
      ↓
Chat Model
      ↓
Output Parser
      ↓
Final String Output
```

---

# Final Summary

LCEL is the modern LangChain chaining system.

Core Formula:

```python
chain = prompt | model | parser
```

Key Concepts:

1. Everything is a Runnable.
2. Pipe operator creates RunnableSequence.
3. Data flows left → right.
4. Sequential = step-by-step execution.
5. Parallel = multiple chains together.
6. Passthrough = preserve original input.
7. LangSmith = production-grade debugging.
8. LCEL replaces LLMChain, SequentialChain and TransformChain.

If you master RunnableSequence, RunnableParallel, RunnablePassthrough, Output Parsers, and LangSmith, you will understand most modern LangChain applications including RAG systems, AI Agents, and production LLM workflows.
