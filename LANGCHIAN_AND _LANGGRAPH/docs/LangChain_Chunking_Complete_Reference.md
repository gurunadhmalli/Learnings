# LangChain Chunking Complete Reference

## Why Chunking Matters
Large documents cannot be embedded effectively as a single vector.

Pipeline:

Document -> Text Splitter -> Chunks -> Embeddings -> Vector Store -> Retrieval -> LLM

### Problems Without Chunking
- Poor retrieval
- Large context
- Higher embedding cost
- Low precision

### Good Chunking Goals
- Preserve meaning
- Improve retrieval
- Fit model context windows

---

## Chunk Size

### Too Small
- Missing context
- Incomplete answers

### Too Large
- Irrelevant information
- Retrieval noise

### Typical Values
- FAQ: 500-800
- Docs: 1000-1500
- Books: 800-1200
- Code: 1500-2000

---

## Chunk Overlap

Example:

Chunk 1:
Employee leave policy allows 20 days annual leave...

Chunk 2:
20 days annual leave plus additional benefits...

Benefits:
- Preserves context
- Better retrieval
- Prevents sentence cutting

Typical:
chunk_size=1000
chunk_overlap=200

---

## RecursiveCharacterTextSplitter

Most important splitter in LangChain.

Default separators:

['\n\n', '\n', ' ', '']

Order:
1. Paragraphs
2. Lines
3. Spaces
4. Characters

Example:

from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

Best for:
- PDFs
- Websites
- Articles
- General RAG

---

## CharacterTextSplitter

Simple separator based splitting.

Best for:
- Simple text files

---

## TokenTextSplitter

Splits using tokens rather than characters.

Best for:
- Strict token control
- LLM context management

---

## MarkdownHeaderTextSplitter

Uses markdown headers.

# Title
## Section
### Subsection

Best for:
- README files
- Documentation
- Wikis

Advantages:
- Preserves hierarchy
- Better retrieval

---

## MarkdownTextSplitter

Markdown aware splitting.

Handles:
- Headers
- Lists
- Tables
- Code blocks

---

## PythonCodeTextSplitter

Designed for code.

Splits around:
- Classes
- Functions
- Logical code blocks

Best for:
- GitHub repositories
- Code RAG

---

## RecursiveJsonSplitter

Preserves JSON hierarchy.

Best for:
- API responses
- Configuration files
- Nested JSON

---

## HTMLHeaderTextSplitter

Uses:
- h1
- h2
- h3

Maintains webpage structure.

Best for:
- Documentation websites

---

## HTMLSectionSplitter

Groups related HTML sections.

Better semantic grouping than basic splitting.

---

## LatexTextSplitter

Supports:

\section{}
\subsection{}

Best for:
- Research papers
- Academic documents

---

## NLTKTextSplitter

Sentence aware chunking.

Requires:
pip install nltk

---

## SpacyTextSplitter

Uses spaCy NLP.

Advantages:
- Better linguistic understanding
- Sentence aware chunks

Requires:
pip install spacy

---

## SemanticChunker

Advanced chunking.

Process:
1. Create embeddings
2. Measure similarity
3. Group by meaning

Example:

ML Topic
ML Topic
ML Topic

Food Topic
Food Topic

Advantages:
- Meaning based chunks
- Better retrieval quality

Disadvantages:
- Slower
- Requires embeddings
- Higher cost

Best for:
- Enterprise RAG
- Research systems

---

## Choosing the Right Splitter

PDFs:
RecursiveCharacterTextSplitter

Documentation:
MarkdownHeaderTextSplitter

Source Code:
PythonCodeTextSplitter

Websites:
HTMLHeaderTextSplitter

JSON:
RecursiveJsonSplitter

Research Papers:
LatexTextSplitter

Advanced RAG:
SemanticChunker

---

## Production Recommendation

Start with:

RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

Then optimize based on retrieval results.

---

## Interview Questions

1. Why is chunking required?
2. What is chunk overlap?
3. Why use RecursiveCharacterTextSplitter?
4. Difference between Character and Recursive splitter?
5. When should SemanticChunker be used?
6. Best chunker for Markdown?
7. Best chunker for code?

---

## Quick Revision

RecursiveCharacterTextSplitter -> General purpose

CharacterTextSplitter -> Simple

TokenTextSplitter -> Token based

MarkdownHeaderTextSplitter -> Markdown docs

MarkdownTextSplitter -> Markdown content

PythonCodeTextSplitter -> Code

RecursiveJsonSplitter -> JSON

HTMLHeaderTextSplitter -> HTML

LatexTextSplitter -> Research papers

NLTKTextSplitter -> Sentence aware

SpacyTextSplitter -> NLP aware

SemanticChunker -> Meaning based
