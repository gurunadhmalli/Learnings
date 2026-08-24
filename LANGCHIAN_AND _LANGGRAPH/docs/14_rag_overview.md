# RAG (Retrieval-Augmented Generation) – Detailed Learning Notes

---

# 1. What is RAG?

RAG (Retrieval-Augmented Generation) is a technique that combines:

1. **Information Retrieval**
2. **Large Language Models (LLMs)**

to generate answers based on external documents instead of relying only on the model's training data.

---

## Problem Without RAG

A normal LLM:

```
User Question
      ↓
     LLM
      ↓
   Answer
```

The model answers from:

- Pretrained knowledge
- Patterns learned during training

Limitations:

- Knowledge cutoff date
- No access to company documents
- Hallucinations
- Cannot answer document-specific questions

Example:

**Question:**

```
What is the return policy mentioned in my company handbook?
```

The LLM has never seen your handbook.

Possible outcome:

```
Hallucinated answer
```

---

## Solution: RAG

RAG gives the model access to external knowledge.

```
User Question
      ↓
Retrieve Relevant Documents
      ↓
Provide Context
      ↓
LLM Generates Answer
```

Now answers come from:

- PDFs
- DOCX files
- Databases
- Websites
- Internal company documents
- Knowledge bases

---

# 2. RAG Architecture

Based on the first slide.

---

## Complete Flow

```text
User Query
    ↓
Retriever
    ↓
Relevant Chunks
    ↓
Context + Query
    ↓
LLM
    ↓
Response
```

---

## Step 1: User Query

Example:

```text
What are the shipping charges?
```

User sends a question.

---

## Step 2: Retriever

Retriever searches the vector database.

Example:

Vector DB contains:

Chunk 1:
"Shipping charges within India are ₹100."

Chunk 2:
"International shipping charges are ₹500."

Chunk 3:
"Returns are accepted within 30 days."

Retriever finds the most relevant chunks.

Output:

```python
[
 "Shipping charges within India are ₹100.",
 "International shipping charges are ₹500."
]
```

---

## Step 3: Context + Query

Retriever output is combined with user question.

Prompt becomes:

```text
Context:

Shipping charges within India are ₹100.

International shipping charges are ₹500.

Question:

What are the shipping charges?
```

---

## Step 4: LLM

LLM reads:

- Context
- User Question

Then generates an answer.

---

## Step 5: Response

Output:

```text
Shipping charges within India are ₹100,
while international shipping charges are ₹500.
```

Grounded in documents.

---

# 3. What is a Vector Store?

Shown on the right side of the slide.

---

## Purpose

Stores embeddings for fast similarity search.

---

## Why Not Store Raw Text?

Searching millions of documents using keyword search is slow and inaccurate.

Instead:

```text
Text
 ↓
Embedding Model
 ↓
Vector
 ↓
Vector Database
```

---

## Example

Document:

```text
LangChain is a framework for LLM applications.
```

Embedding:

```python
[0.12, 0.89, -0.44, 0.67, ...]
```

Thousands of dimensions.

---

## Popular Vector Databases

### Local

- FAISS
- Chroma

### Cloud

- Pinecone
- Weaviate
- Qdrant
- Milvus

---

# 4. Why RAG Reduces Hallucinations

Key concept from slide.

---

Without RAG:

```text
Question
 ↓
LLM guesses
 ↓
Possible hallucination
```

---

With RAG:

```text
Question
 ↓
Retriever finds evidence
 ↓
LLM answers using evidence
```

---

Example:

Question:

```text
What is employee leave policy?
```

Retriever finds:

```text
Employees receive 20 annual leaves.
```

LLM answers:

```text
Employees receive 20 annual leaves annually.
```

Grounded answer.

---

# 5. Basic RAG Chain

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

# 6. Understanding Each Component

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

# 7. Parallel Input Processing

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

# 8. Prompt Template in RAG

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

# 9. Handling "I Don't Know"

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

# 10. Production Prompt Pattern

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

# 11. RAG with Sources

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

# 12. Full End-to-End RAG Pipeline

```text
Documents
    ↓
Load Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
Vector Store
    ↓
Retriever
    ↓
User Question
    ↓
Relevant Chunks
    ↓
Prompt Template
    ↓
LLM
    ↓
Output Parser
    ↓
Final Answer + Sources
```

---

# 13. LangChain LCEL Version

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