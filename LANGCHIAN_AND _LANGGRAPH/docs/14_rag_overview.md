# RAG (Retrieval-Augmented Generation) – Detailed Learning Notes

---

This file focuses on the **hands-on / code side** of building a basic RAG chain in LangChain — chain structure, components, parallel input processing, prompt patterns, sources, and the final LCEL implementation.

For the conceptual fundamentals — what RAG is, why it exists, RAG architecture, what a vector store is, and why RAG reduces hallucinations — see [16_rag.md](16_rag.md) (sections 1–7 and 17) for the full breakdown.

---

# 1. Basic RAG Chain

From the second slide.

---

## Chain Structure

```text
{
 context,
 question
}
     ↓
Prompt
     ↓
LLM
     ↓
Parser
```

---

# 2. Understanding Each Component

---

## Context

Retrieved documents.

Example:

```text
Shipping charges within India are ₹100.
```

---

## Question

User input.

Example:

```text
What are the shipping charges?
```

---

## Prompt

Combines:

```text
Context
+
Question
```

into a structured instruction.

---

## LLM

Reads prompt and generates answer.

Examples:

- GPT
- Claude
- Command-R
- Llama

---

## Output Parser

Converts raw LLM output into desired format.

Examples:

### String Output

```python
StrOutputParser()
```

Output:

```text
Shipping charges are ₹100.
```

---

### JSON Output

```json
{
  "shipping_charge": 100
}
```

---

# 3. Parallel Input Processing

Shown in slide.

---

## Why Parallel?

We need:

1. Retrieved context
2. Original question

Both at the same time.

---

## LangChain Flow

```text
Question
   ↓
 ┌─────────────┐
 │             │
 ↓             ↓
Retriever   RunnablePassthrough
 ↓             ↓
Context    Original Question
     ↓
Merge
```

---

## RunnablePassthrough

Passes input unchanged.

Example:

Input:

```python
"What is shipping cost?"
```

Output:

```python
"What is shipping cost?"
```

No modification.

---

## Retriever

Same input:

```python
"What is shipping cost?"
```

Returns:

```python
"Shipping charges are ₹100."
```

---

## Combined Result

```python
{
   "context":"Shipping charges are ₹100",
   "question":"What is shipping cost?"
}
```

---

# 4. Prompt Template in RAG

From slide.

---

Basic Prompt:

```text
Answer based only on:

{context}

Question:
{question}
```

---

Example

```text
Context:
Shipping charges are ₹100.

Question:
What are shipping charges?
```

---

LLM Answer:

```text
Shipping charges are ₹100.
```

---

# 5. Handling "I Don't Know"

One of the most important concepts in RAG.

---

## Without Instruction

Prompt:

```text
Context:
Shipping charges are ₹100.

Question:
What is Quantum Computing?
```

LLM may answer:

```text
Quantum computing uses qubits...
```

Hallucination.

---

## Why?

Because LLM tries to be helpful.

Even if answer is not in context.

---

# Better Prompt

```text
Answer ONLY using the provided context.

If the answer is not available,
respond with:

"I don't have information about that."
```

---

Example

Context:

```text
Shipping charges are ₹100.
```

Question:

```text
What is Quantum Computing?
```

Answer:

```text
I don't have information about that.
```

Correct behavior.

---

# 6. Production Prompt Pattern

Recommended prompt:

```text
You are a helpful assistant.

Answer ONLY from the provided context.

If the answer cannot be found in the context,
say:

"I don't have information about that."

Context:
{context}

Question:
{question}
```

---

# 7. RAG with Sources

Fourth slide.

---

## Problem

Users may ask:

```text
How do I know this answer is correct?
```

---

## Solution

Return sources.

---

Retriever Output

```python
[
 {
  "content":"Shipping charges are ₹100",
  "source":"policy.pdf"
 },
 {
  "content":"International shipping is ₹500",
  "source":"pricing.pdf"
 }
]
```

---

# format_docs_with_sources()

Adds source metadata.

Example:

Before:

```text
Shipping charges are ₹100.
```

After:

```text
[Source: policy.pdf]

Shipping charges are ₹100.
```

---

## Formatted Context

```text
[Source: policy.pdf]

Shipping charges are ₹100.

[Source: pricing.pdf]

International shipping is ₹500.
```

---

# Response with Sources

```text
Domestic shipping charges are ₹100.

Source:
policy.pdf
```

---

# Why Sources Matter

Benefits:

### 1. Trust

Users can verify answers.

---

### 2. Transparency

Shows where information came from.

---

### 3. Debugging

Easy to identify wrong documents.

---

### 4. Compliance

Useful for legal and enterprise systems.

---

### 5. Auditability

Can trace every answer.

---

# 8. Full End-to-End Pipeline

(see [16_rag.md](16_rag.md) section 7 for the full indexing + retrieval + generation pipeline diagram)

---

# 9. LangChain LCEL Version

Typical LCEL chain:

```python
rag_chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)
```

---

## Step-by-Step

### RunnablePassthrough

```python
"What is shipping cost?"
```

passes unchanged.

---

### Retriever

Searches vector DB.

Returns:

```python
"Shipping charges are ₹100."
```

---

### Prompt

Creates:

```text
Context:
Shipping charges are ₹100.

Question:
What is shipping cost?
```

---

### LLM

Generates answer.

---

### Parser

Converts output to string.

---

# Interview Questions

### Q1. Why do we need RAG?

To provide external knowledge and reduce hallucinations.

---

### Q2. What is a Retriever?

A component that finds relevant chunks from a vector database.

---

### Q3. What is a Vector Store?

A database optimized for storing and searching embeddings.

---

### Q4. What is RunnablePassthrough?

A LangChain runnable that forwards input unchanged.

---

### Q5. Why include sources in RAG?

To improve trust, transparency, and answer verification.

---

### Q6. How do we prevent hallucinations in RAG?

By:

1. Strong prompt instructions
2. Limiting answers to retrieved context
3. Returning "I don't know" when context is missing

---

# Key Takeaways

✅ RAG = Retriever + LLM

✅ Vector DB stores embeddings

✅ Retriever fetches relevant chunks

✅ Context + Question form the prompt

✅ RunnablePassthrough keeps original question

✅ Prompt engineering reduces hallucinations

✅ "I don't know" handling is critical

✅ Sources improve trust and explainability

✅ LCEL RAG Chain:

```python
{
   "context": retriever,
   "question": RunnablePassthrough()
}
| prompt
| llm
| StrOutputParser()
```

This is the foundation of almost every production-grade RAG system built using LangChain, Cohere, OpenAI, Claude, Chroma, FAISS, Pinecone, Qdrant, or Weaviate.
