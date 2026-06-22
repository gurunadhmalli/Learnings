# Embeddings, Vectors, Similarity Search & Vector Databases

## The Complete Deep-Dive Guide for RAG Systems

---

# Table of Contents

1. Why We Need Vectors
2. What is a Vector?
3. Magnitude and Direction
4. GPS Analogy
5. Dimensions
6. Understanding AI Vectors
7. Semantic Meaning
8. Similarity in Vector Space
9. Distance Metrics
10. Embeddings
11. How Embedding Models Work
12. Word Embeddings
13. Sentence Embeddings
14. Document Embeddings
15. Chunk Embeddings in RAG
16. Vector Databases
17. Vector Search
18. Similarity Search Process
19. Why Vector Search Beats Keyword Search
20. Complete RAG Flow with Embeddings
21. Interview Questions

---

# 1. Why We Need Vectors

Computers understand:

```text
Numbers
```

Humans understand:

```text
Language
Meaning
Concepts
Ideas
```

Example:

```text
Dog
Cat
Puppy
Animal
```

Humans instantly know:

```text
Dog and Puppy are related
```

A computer doesn't.

We need a way to convert meaning into numbers.

That is why vectors exist.

---

# 2. What is a Vector?

A vector has two things:

```text
Magnitude
Direction
```

Example from the slide:

```text
Campsite 1 ---------> Campsite 2
```

Distance:

```text
3.4 miles
```

Direction:

```text
Toward Campsite 2
```

Vector:

```text
Magnitude = 3.4
Direction = East
```

Unlike a simple number:

```text
3.4
```

a vector contains both:

```text
How much?
Which direction?
```

---

# 3. Magnitude and Direction

Consider:

```text
5 km
```

This is not enough.

We need:

```text
5 km North
```

Now it becomes a vector.

---

Mathematically:

```text
Vector = Magnitude + Direction
```

---

# 4. GPS Analogy

Slide:

```text
New York
=
[40.7128, -74.0060]

London
=
[51.5074, -0.1278]
```

These numbers are coordinates.

They uniquely identify locations.

---

Similarly:

```text
Dog
```

can have coordinates in AI space.

Example:

```text
[0.23, -0.45, 0.67, ...]
```

These coordinates represent meaning.

---

# 5. Dimensions

Think of dimensions as features.

---

## 1D

Single number

```text
[5]
```

Example:

```text
Temperature
```

---

## 2D

```text
[x, y]
```

Example:

```text
Map Location
```

---

## 3D

```text
[x, y, z]
```

Example:

```text
Space Position
```

---

# AI Embeddings

Instead of:

```text
2 dimensions
```

we may have:

```text
384 dimensions
768 dimensions
1024 dimensions
1536 dimensions
3072 dimensions
```

Each dimension captures some aspect of meaning.

---

# 6. Understanding AI Vectors

From slide:

```text
[3, 2, 1500, 2005, 0.8, 0.3, 0.9]
```

House Example:

```text
Bedrooms
Bathrooms
Square Feet
Year Built
Kitchen Quality
Location Score
Condition
```

Each value represents one feature.

Together:

```text
Entire House Description
```

---

Similarly:

```text
Dog
```

is represented by hundreds or thousands of dimensions.

---

# 7. Semantic Meaning

This is the most important concept.

---

Traditional Storage

```text
Dog
```

Stored as characters:

```text
D
O
G
```

Computer sees:

```text
Text
```

---

Embedding Storage

```text
Dog
```

Stored as:

```text
[0.12, 0.54, -0.23, ...]
```

Computer sees:

```text
Meaning
```

---

# 8. Similarity in Vector Space

Slide:

```text
Lake
Water
```

appear close together.

Why?

Because they are related concepts.

---

Meanwhile:

```text
Lake
Car
```

appear far apart.

Because meanings differ.

---

Vector Space:

```text
Dog      Puppy

      Cat

           Animal


               Car
```

Related concepts cluster together.

---

# 9. Distance Metrics

The closer vectors are:

```text
More Similar
```

The farther apart:

```text
Less Similar
```

---

# Euclidean Distance

Standard geometric distance.

Formula:

```text
√((x2-x1)^2 + (y2-y1)^2)
```

---

Example:

```text
Dog  ---- Puppy

Distance = Small
```

---

```text
Dog -------------------- Car
```

Distance = Large

---

# Cosine Similarity

Most common in RAG.

Measures angle.

Not absolute distance.

---

Values:

```text
1.0 = Identical
0.8 = Very Similar
0.5 = Somewhat Similar
0.0 = Unrelated
-1 = Opposite
```

---

# 10. Embeddings

Embedding:

```text
Text → Vector
```

Example:

```text
Dog
```

↓

```text
[0.51, -0.34, 0.72, ...]
```

---

The vector captures meaning.

Not spelling.

---

# 11. How Embedding Models Work

Input:

```text
The dog chased the ball.
```

Embedding Model:

```text
text-embedding-3-large
bge-large
e5-large
Cohere Embed
```

Output:

```text
[0.234, -0.183, 0.671, ...]
```

---

# 12. Word Embeddings

Single word.

Example:

```text
Dog
Cat
Puppy
```

Converted to vectors.

---

Related words:

```text
Dog ↔ Puppy
```

Near each other.

---

# 13. Sentence Embeddings

Entire sentence.

Example:

```text
How do I reset my password?
```

↓

```text
[0.11, 0.34, ...]
```

---

Another sentence:

```text
Password reset instructions
```

↓

Very similar vector.

---

# 14. Document Embeddings

Entire document.

Example:

```text
Employee Handbook
```

↓

Vector.

---

Problem:

Large documents lose detail.

Which is why we chunk.

---

# 15. Chunk Embeddings in RAG

Instead of:

```text
Entire PDF
```

we use:

```text
Chunk 1
Chunk 2
Chunk 3
```

Each chunk gets its own embedding.

---

Example:

```text
Chunk:
Leave Policy
```

↓

```text
Vector A
```

---

```text
Chunk:
Travel Policy
```

↓

```text
Vector B
```

---

Stored separately.

---

# 16. Vector Databases

Traditional DB stores:

```text
Rows
Columns
```

---

Vector DB stores:

```text
Embeddings
```

---

Examples:

```text
FAISS
Chroma
Qdrant
Pinecone
Milvus
Weaviate
```

---

Stored Data:

```json
{
 "text":"Employees get 12 leaves",
 "embedding":[0.23,-0.12,...],
 "source":"policy.pdf"
}
```

---

# 17. Vector Search

User asks:

```text
How many casual leaves?
```

---

Query converted into vector.

```text
Question
      ↓
Embedding
      ↓
Vector
```

---

Search:

```text
Find nearest vectors
```

---

Returns:

```text
Leave Policy Chunk
```

---

# 18. Similarity Search Process

Step 1

```text
User Query
```

↓

Step 2

```text
Embedding
```

↓

Step 3

```text
Vector Search
```

↓

Step 4

```text
Nearest Chunks
```

↓

Step 5

```text
LLM
```

↓

Step 6

```text
Answer
```

---

# 19. Why Vector Search Beats Keyword Search

Keyword Search:

Query:

```text
Automobile
```

Document:

```text
Car
```

Fails.

Different words.

---

Vector Search:

Understands:

```text
Automobile ≈ Car
```

because meanings are similar.

---

# 20. Complete RAG Flow

```text
PDF
 ↓

Chunking
 ↓

Chunk 1
Chunk 2
Chunk 3

 ↓

Embedding Model
 ↓

Vectors

 ↓

Vector Database

=================================

User Question
 ↓

Embedding Model
 ↓

Question Vector

 ↓

Similarity Search

 ↓

Top K Chunks

 ↓

Prompt

Question
+
Retrieved Chunks

 ↓

LLM

 ↓

Answer
```

---

# Golden Rule

RAG does NOT search text.

RAG searches vectors.

---

Traditional Search:

```text
Text → Match Words
```

RAG Search:

```text
Text → Embedding
      ↓
Meaning
      ↓
Similarity Search
```

---

# Interview Question

Q: Why do we need embeddings in RAG?

Answer:

Embeddings convert text into high-dimensional vectors that capture semantic meaning. Similar meanings produce similar vectors, allowing vector databases to perform semantic search and retrieve relevant chunks even when exact keywords are different.

---

# One-Line Summary

```text
Embeddings convert meaning into numbers.

Vector databases store those meanings.

Similarity search finds related meanings.

RAG uses those meanings to retrieve
the right context before generating answers.
```
