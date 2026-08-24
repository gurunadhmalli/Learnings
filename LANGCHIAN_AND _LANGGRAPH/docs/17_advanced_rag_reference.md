# Advanced RAG (Retrieval-Augmented Generation) — Complete Learning Reference

A developer-focused guide covering both foundational concepts and advanced retrieval techniques for production-grade RAG systems.

---

## Table of Contents

1. [Why Basic RAG Isn't Enough](#1-why-basic-rag-isnt-enough)  
2. [Advanced RAG Methods (from the slides)](#2-advanced-rag-methods-from-the-slides)  
   - 2.1 [Parent Document Retriever](#21-parent-document-retriever)  
   - 2.2 [Hybrid Search (BM25 \+ Semantic)](#22-hybrid-search-bm25--semantic)  
   - 2.3 [Contextual Compression](#23-contextual-compression)  
   - 2.4 [Self-Query Retriever](#24-self-query-retriever)  
   - 2.5 [Multi-Query Retriever](#25-multi-query-retriever)  
3. [Additional Advanced RAG Methods (beyond the slides)](#3-additional-advanced-rag-methods-beyond-the-slides)  
   - 3.1 [HyDE — Hypothetical Document Embeddings](#31-hyde--hypothetical-document-embeddings)  
   - 3.2 [RAG Fusion](#32-rag-fusion)  
   - 3.3 [Step-Back Prompting](#33-step-back-prompting)  
   - 3.4 [Corrective RAG (CRAG)](#34-corrective-rag-crag)  
   - 3.5 [Self-RAG](#35-self-rag)  
   - 3.6 [Agentic / Adaptive RAG](#36-agentic--adaptive-rag)  
   - 3.7 [Re-Ranking with Cross-Encoders](#37-re-ranking-with-cross-encoders)  
   - 3.8 [Sentence Window Retrieval](#38-sentence-window-retrieval)  
   - 3.9 [RAPTOR — Recursive Abstractive Processing](#39-raptor--recursive-abstractive-processing)  
   - 3.10 [Graph RAG](#310-graph-rag)  
4. [Choosing the Right Technique](#4-choosing-the-right-technique)  
5. [Combining Techniques — A Production Architecture](#5-combining-techniques--a-production-architecture)  
6. [Key Metrics for Evaluating RAG](#6-key-metrics-for-evaluating-rag)

---

## 1\. Why Basic RAG Isn't Enough

Basic RAG follows a simple pipeline: chunk documents → embed → store in a vector DB → retrieve top-k chunks → pass to LLM. While this works for demos, it breaks down in production due to four core limitations:

| \# | Limitation | Effect | Advanced Solution |
| :---- | :---- | :---- | :---- |
| 1 | **Single query perspective** | A single embedding vector misses documents that are relevant but phrased differently | Multi-Query Retriever |
| 2 | **No metadata filtering** | Retrieval is purely semantic; structured constraints (date, category, score) are ignored | Self-Query Retriever |
| 3 | **Full chunks returned** | Large irrelevant chunks add noise to the LLM context window | Contextual Compression |
| 4 | **Keyword OR semantic — not both** | Purely semantic search misses exact term/code/name matches | Hybrid Search (BM25 \+ Semantic) |

Understanding these four root causes is the foundation for selecting the right advanced technique.

---

## 2\. Advanced RAG Methods (from the slides)

### 2.1 Parent Document Retriever

#### The Problem It Solves

When chunks are large (e.g., 1000 characters), embeddings are diluted — they try to represent too many concepts at once, leading to imprecise similarity matches. When chunks are small (e.g., 200 characters), retrieval is precise but the LLM receives too little context to generate a complete answer.

#### How It Works

The idea is to **index small, retrieve large**:

Document

└── Parent Chunk (1000 chars)  ← stored but NOT indexed for search

    ├── Child 1 (200 chars)   ← indexed for vector similarity search

    ├── Child 2 (200 chars)   ← indexed

    ├── Child 3 (200 chars)   ← indexed

    ├── Child 4 (200 chars)   ← indexed

    └── Child 5 (200 chars)   ← indexed

Search Process:

  Step 1 → Search against small child chunks (precise matching)

  Step 2 → Return the full parent chunk (full context)

#### Why It Works

- **Small chunks** → precise semantic matching (the embedding captures a single, focused concept)  
- **Large parent chunks** → the LLM gets full context to generate an accurate answer  
- You get the **best of both worlds**: precision in retrieval \+ completeness in generation

#### Implementation Notes (LangChain)

from langchain.retrievers import ParentDocumentRetriever

from langchain.storage import InMemoryStore

from langchain.text\_splitter import RecursiveCharacterTextSplitter

parent\_splitter \= RecursiveCharacterTextSplitter(chunk\_size=1000)

child\_splitter \= RecursiveCharacterTextSplitter(chunk\_size=200)

store \= InMemoryStore()  \# or Redis, MongoDB for production

retriever \= ParentDocumentRetriever(

    vectorstore=vectorstore,

    docstore=store,

    child\_splitter=child\_splitter,

    parent\_splitter=parent\_splitter,

)

retriever.add\_documents(docs)

#### When to Use

- Long documents where context matters (legal, medical, research papers)  
- When retrieval precision is poor with large chunks  
- When LLM answers are incomplete due to small chunks

---

### 2.2 Hybrid Search (BM25 \+ Semantic)

#### The Problem It Solves

Pure semantic/vector search fails on **exact matches** — specific product codes, names, acronyms, or technical terms. Pure keyword search (BM25) fails on **conceptual queries** — synonyms, paraphrases, or intent-based questions. Neither alone is sufficient for real-world data.

#### How It Works

A single query is sent to **two retrievers in parallel**, and their results are combined:

Query

 ├──→ BM25 Retriever      (Keyword matching)   → weight: 40%

 │        Good for: exact terms, names, codes

 │

 └──→ Semantic Retriever  (Meaning-based)       → weight: 60%

          Good for: concepts, synonyms

          ↓ Both results ↓

    EnsembleRetriever (Weighted combination)

#### Weights Explained

The default weights shown (40% BM25 / 60% Semantic) reflect that most queries are conceptual. Adjust based on your domain:

- **Code/legal/medical** → increase BM25 weight (exact terms matter more)  
- **Conversational/Q\&A** → increase semantic weight

#### Score Fusion

The standard approach is **Reciprocal Rank Fusion (RRF)**, which combines the rank positions from both retrievers rather than raw scores (avoids scale mismatch issues between BM25 and cosine similarity scores).

from langchain.retrievers import EnsembleRetriever, BM25Retriever

from langchain\_community.vectorstores import FAISS

bm25\_retriever \= BM25Retriever.from\_documents(docs, k=5)

semantic\_retriever \= vectorstore.as\_retriever(search\_kwargs={"k": 5})

ensemble \= EnsembleRetriever(

    retrievers=\[bm25\_retriever, semantic\_retriever\],

    weights=\[0.4, 0.6\]

)

#### When to Use

- Mixed datasets with both structured identifiers and free-form text  
- Domains with technical jargon alongside conceptual queries  
- When you notice semantic search missing obvious keyword matches

---

### 2.3 Contextual Compression

#### The Problem It Solves

Even when the right chunk is retrieved, it often contains surrounding context (intro paragraphs, background info, unrelated content) that is irrelevant to the specific query. This **noise in the context window** degrades LLM answer quality and wastes tokens.

#### How It Works

Retrieved Chunks (k=10)          LLM Compressor          Compressed Output

┌─────────────────────┐              │                  ┌──────────────────────┐

│ Intro paragraph...  │              │                  │                      │

│ Background info...  │ ──────────→  │  Extracts only → │ Relevant answer here\!│

│ \[Relevant answer\!\]  │  (all 10    │  relevant parts  │ Another relevant bit │

│ More background...  │   chunks)   │                  │                      │

│ \[Another relevant\]  │              │                  └──────────────────────┘

│ Unrelated content.. │              │

└─────────────────────┘

The LLM Compressor reads each retrieved chunk and extracts **only the sentences/passages directly relevant** to the original query, discarding the rest.

#### Types of Compressors

| Compressor | How It Works | Cost |
| :---- | :---- | :---- |
| **LLMChainExtractor** | Uses LLM to extract relevant sentences | Higher (LLM call per chunk) |
| **LLMChainFilter** | Uses LLM to decide keep/drop per chunk (binary) | Medium |
| **EmbeddingsFilter** | Filters by cosine similarity threshold | Low (no LLM call) |
| **DocumentCompressorPipeline** | Chains multiple compressors | Flexible |

from langchain.retrievers import ContextualCompressionRetriever

from langchain.retrievers.document\_compressors import LLMChainExtractor

compressor \= LLMChainExtractor.from\_llm(llm)

compression\_retriever \= ContextualCompressionRetriever(

    base\_compressor=compressor,

    base\_retriever=base\_retriever  \# can wrap any retriever

)

#### When to Use

- When chunks are large and topically diverse  
- When LLM hallucinations correlate with noisy retrieved context  
- Cost-sensitive environments: use `EmbeddingsFilter` as a cheaper alternative

---

### 2.4 Self-Query Retriever

#### The Problem It Solves

Many user queries contain **structured constraints** mixed with semantic content: "Find sci-fi movies from 2020 with rating above 8." A pure vector search on this query attempts to find semantic similarity, completely ignoring the structured filters (year=2020, rating\>8).

#### How It Works

An LLM parses the user's natural language query and **automatically generates two components**:

User Query: "Find sci-fi movies from 2020 with rating above 8"

                          ↓

                   LLM Parses Query

                    ↙            ↘

   Semantic Query          Metadata Filter (auto-generated)

   "sci-fi movies"         genre: "sci-fi"

                           year: 2020

                           rating: \> 8

The vector store then executes a **filtered semantic search** — applying the metadata constraints before or during the semantic retrieval step.

#### Why It's Powerful

- Eliminates "noise" from irrelevant documents that happen to be semantically similar but don't meet structural criteria  
- The LLM understands AND, OR, NOT, range conditions (\>, \<, between)  
- The user gets to query naturally without writing filter syntax

#### Implementation Notes

from langchain.retrievers.self\_query.base import SelfQueryRetriever

from langchain.chains.query\_constructor.base import AttributeInfo

metadata\_field\_info \= \[

    AttributeInfo(name="genre", description="Movie genre", type="string"),

    AttributeInfo(name="year", description="Release year", type="integer"),

    AttributeInfo(name="rating", description="IMDb rating", type="float"),

\]

retriever \= SelfQueryRetriever.from\_llm(

    llm=llm,

    vectorstore=vectorstore,

    document\_contents="Movie descriptions",

    metadata\_field\_info=metadata\_field\_info,

)

#### When to Use

- Structured datasets (products, movies, papers, customer records) stored in vector DBs with metadata  
- Applications where users naturally include constraints in their queries  
- When you want to replace complex filter UI with natural language

---

### 2.5 Multi-Query Retriever

#### The Problem It Solves

A single query embedding represents one perspective on a topic. If the relevant documents use different terminology, the query embedding may not match them closely enough. Relevant documents get **missed** due to vocabulary mismatch.

#### How It Works

An LLM generates **multiple rephrased versions** of the original query. Each version is run independently against the vector store. Results are **merged and deduplicated**.

Original Query: "What are the benefits of exercise?"

                          ↓

                 LLM Generates Variations

                          ↓

  ┌─────────────────────────────────────────────────────────────┐

  │ 1\. "How does physical activity improve health?"             │

  │ 2\. "What positive effects does working out have?"           │

  │ 3\. "Why should people exercise regularly?"                  │

  └─────────────────────────────────────────────────────────────┘

         ↓               ↓               ↓

      Query 1         Query 2         Query 3

         ↓               ↓               ↓

      Results 1       Results 2       Results 3

                          ↓

               Merged Unique Docs (deduplicated)

#### Why It Works

- Different phrasings activate different regions of the embedding space  
- Documents phrased in formal, casual, or domain-specific language are all captured  
- Deduplication ensures no repeated content is passed to the LLM

from langchain.retrievers.multi\_query import MultiQueryRetriever

retriever \= MultiQueryRetriever.from\_llm(

    retriever=vectorstore.as\_retriever(),

    llm=llm

)

\# By default generates 3 query variations

#### Trade-offs

- **Latency**: 3x more vector DB calls (mitigated by async execution)  
- **Cost**: Extra LLM call for query generation  
- **Benefit**: Significantly higher recall on ambiguous or broad queries

#### When to Use

- Broad, open-ended questions where phrasing matters  
- Multilingual datasets  
- When recall is more important than latency

---

## 3\. Additional Advanced RAG Methods (beyond the slides)

### 3.1 HyDE — Hypothetical Document Embeddings

#### Core Idea

Instead of embedding the query directly, ask the LLM to **generate a hypothetical ideal answer** first, then embed *that* answer to search the vector store.

Query → LLM generates hypothetical answer → Embed hypothetical answer → Search

#### Why It Works

Queries are short and often phrased as questions. Documents are long and phrased as answers. The embedding space similarity between a question and its answer may be lower than the similarity between two answers on the same topic. HyDE bridges this gap by searching in "answer space."

from langchain.chains import HypotheticalDocumentEmbedder

hyde\_embedder \= HypotheticalDocumentEmbedder.from\_llm(

    llm=llm,

    base\_embeddings=embeddings,

    prompt\_template="Write a short passage that answers: {question}"

)

#### When to Use

- Low-resource scenarios where queries are very short  
- When standard semantic search shows poor recall  
- Domains where query phrasing differs significantly from document phrasing

---

### 3.2 RAG Fusion

#### Core Idea

Combines **Multi-Query** generation with **Reciprocal Rank Fusion (RRF)** scoring to produce a single, highly ranked list of documents.

Query → Generate N sub-queries → Retrieve for each → RRF fusion → Top-k docs

RRF score formula:

RRF(d) \= Σ  1 / (k \+ rank\_i(d))

Where `k` is a smoothing constant (typically 60\) and `rank_i(d)` is document d's rank in result list i.

#### Advantage over Multi-Query

RRF produces a **merged ranked list** (not just a deduplicated set), so documents appearing highly ranked across multiple query variations bubble to the top.

---

### 3.3 Step-Back Prompting

#### Core Idea

Before answering a specific question, prompt the LLM to first answer a **more abstract, general version** of the question. Use both the original and abstracted query for retrieval.

Specific: "What was Einstein's contribution to the photoelectric effect?"

Step-back: "What are the principles of quantum mechanics?"

→ Retrieve on both → LLM answers specific question with broad context

#### When to Use

- Complex reasoning questions requiring background knowledge  
- When specific queries return irrelevant results due to over-specificity

---

### 3.4 Corrective RAG (CRAG)

#### Core Idea

After retrieval, a **grading step** evaluates whether the retrieved documents are actually relevant. If they're not, the system triggers a corrective action: web search, query rewriting, or fallback to a broader retrieval.

Query → Retrieve → Grade relevance → 

   If GOOD:    Use documents → Generate answer

   If POOR:    Rewrite query / Web search → Retrieve again → Generate

   If AMBIGUOUS: Combine both paths

#### Why It Matters

Standard RAG blindly passes retrieved documents to the LLM regardless of quality. CRAG adds a **quality gate** that dramatically reduces hallucinations from irrelevant retrieved content.

---

### 3.5 Self-RAG

#### Core Idea

The LLM itself controls the retrieval process using **special reflection tokens**:

- `[Retrieve]` — decides whether retrieval is needed at all  
- `[IsRel]` — judges if retrieved docs are relevant  
- `[IsSup]` — judges if generated output is supported by the docs  
- `[IsUse]` — judges if the output is useful to the user

This creates a **self-reflective** generation loop rather than a fixed pipeline.

#### When to Use

- When you need fine-grained control over generation quality  
- When some queries don't need retrieval (factual, memorized knowledge)  
- Production systems where faithfulness to sources is critical

---

### 3.6 Agentic / Adaptive RAG

#### Core Idea

Instead of a fixed RAG pipeline, an **LLM agent** dynamically decides *how* to retrieve based on query complexity:

Query Complexity Classifier

   ├── Simple factual → Direct LLM answer (no retrieval)

   ├── Single-hop → Standard vector search

   ├── Multi-hop → Iterative retrieval (retrieve → reason → retrieve again)

   └── Complex → Full agent loop with tools (search, calculator, API calls)

#### Why It's the Future

Most RAG pipelines apply the same strategy to all queries. Adaptive RAG routes queries to the most efficient strategy, balancing **quality vs. cost vs. latency**.

---

### 3.7 Re-Ranking with Cross-Encoders

#### Core Idea

**Two-stage retrieval**:

1. Fast retrieval: Get top-100 candidates using bi-encoder (standard vector search)  
2. Precise re-ranking: Use a **cross-encoder** to re-score all 100 candidates, return top-5

Query \+ Doc → \[Cross-Encoder\] → Relevance score (0–1)

Cross-encoders process the query and document **together** (not independently), producing much higher quality relevance scores than bi-encoders.

from sentence\_transformers import CrossEncoder

cross\_encoder \= CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

scores \= cross\_encoder.predict(\[\[query, doc\] for doc in candidates\])

ranked \= sorted(zip(candidates, scores), key=lambda x: x\[1\], reverse=True)

#### When to Use

- When top-k retrieval quality is critical  
- Acceptable if you can afford the extra latency (cross-encoders are slower)

---

### 3.8 Sentence Window Retrieval

#### Core Idea

Similar in spirit to Parent Document Retriever, but simpler:

- Index individual **sentences** for maximum precision  
- At retrieval time, expand each matched sentence to include surrounding **context window** (e.g., ±2 sentences)

\[sentence-2\] \[sentence-1\] \[MATCHED SENTENCE\] \[sentence+1\] \[sentence+2\]

                             ↑ retrieved            ↑ context window added

#### Difference from Parent Document Retriever

- Parent Document uses a predefined hierarchical structure (child → parent chunk)  
- Sentence Window uses a sliding window centered on the matched sentence  
- Sentence Window is simpler to implement; Parent Document is more semantically coherent

---

### 3.9 RAPTOR — Recursive Abstractive Processing

#### Core Idea

Build a **tree of summaries** over your document corpus:

1. Cluster leaf-level chunks by topic  
2. Summarize each cluster → create a parent node  
3. Repeat recursively until a single root summary

At query time, search at multiple levels of the tree — from abstract (root) to specific (leaves).

         Root Summary

        /            \\

  Cluster A         Cluster B

  Summary           Summary

   /    \\             /   \\

Chunk1 Chunk2    Chunk3  Chunk4

#### When to Use

- Very large document corpora where a "big picture" understanding is needed  
- Multi-document summarization and Q\&A  
- When queries range from high-level ("what is this document about?") to specific

---

### 3.10 Graph RAG

#### Core Idea

Instead of treating documents as flat chunks, build a **knowledge graph** where entities (people, places, concepts) are nodes and their relationships are edges. Retrieval traverses the graph rather than just doing similarity search.

\[Einstein\] ──"worked on"──→ \[Photoelectric Effect\]

     │                              │

"colleague of"              "won Nobel for"

     │                              │

\[Bohr\]                          \[1921 Nobel Prize\]

#### Why It's Powerful

- Captures **multi-hop relationships** that flat vector search misses  
- Answers "How are X and Y related?" type queries naturally  
- Preserves structured knowledge that embeddings compress and lose

#### When to Use

- Knowledge-intensive domains (biomedical, legal, enterprise knowledge bases)  
- When multi-hop reasoning is required  
- Integration with tools like Microsoft GraphRAG, Neo4j, or LlamaIndex Knowledge Graph

---

## 4\. Choosing the Right Technique

| Problem | Technique |
| :---- | :---- |
| Retrieval finds right topic but loses context | Parent Document Retriever or Sentence Window |
| Missing exact terms/codes in semantic search | Hybrid Search (BM25 \+ Semantic) |
| Retrieved chunks have too much irrelevant content | Contextual Compression |
| User queries have structured filters (date, category) | Self-Query Retriever |
| Single query misses relevant but differently-phrased docs | Multi-Query or RAG Fusion |
| Query embeddings don't match document embeddings well | HyDE |
| Retrieved docs may be irrelevant or low quality | CRAG or Re-Ranking |
| Queries vary widely in complexity | Adaptive/Agentic RAG |
| Multi-hop reasoning across entities | Graph RAG |
| Very large corpora, high-level \+ low-level queries | RAPTOR |

---

## 5\. Combining Techniques — A Production Architecture

The most robust RAG systems combine multiple techniques in a pipeline:

User Query

    ↓

\[Self-Query Retriever\] — parse metadata filters from query

    ↓

\[Multi-Query Generator\] — generate 3 query variations

    ↓

\[Hybrid Search\] — BM25 \+ Semantic for each variation

    ↓

\[RRF Fusion\] — merge and rank all results

    ↓

\[Cross-Encoder Re-Ranking\] — re-rank top-50 to top-10

    ↓

\[Contextual Compression\] — extract only relevant passages

    ↓

\[LLM Generation\] — final answer with clean, precise context

This pipeline addresses all four basic RAG limitations simultaneously at the cost of higher latency, which can be mitigated through **async execution** and **caching**.

---

## 6\. Key Metrics for Evaluating RAG

| Metric | What It Measures | Tool |
| :---- | :---- | :---- |
| **Faithfulness** | Is the answer grounded in retrieved docs? | RAGAS |
| **Answer Relevance** | Does the answer address the question? | RAGAS |
| **Context Precision** | Are retrieved chunks actually relevant? | RAGAS |
| **Context Recall** | Were all relevant chunks retrieved? | RAGAS |
| **MRR** (Mean Reciprocal Rank) | How early does the first relevant doc appear? | Manual |
| **NDCG** | Graded relevance ranking quality | Manual |
| **Latency (P50/P95)** | End-to-end response time distribution | Monitoring |

---

**Learning Path Recommendation:**

1. Build basic RAG → understand its failures  
2. Add Hybrid Search → immediate retrieval quality boost  
3. Add Parent Document Retriever → better context quality  
4. Add Contextual Compression → cleaner LLM input  
5. Add Self-Query / Multi-Query → handle complex user inputs  
6. Evaluate with RAGAS → data-driven improvements  
7. Explore CRAG / Self-RAG / Agentic RAG → production robustness

