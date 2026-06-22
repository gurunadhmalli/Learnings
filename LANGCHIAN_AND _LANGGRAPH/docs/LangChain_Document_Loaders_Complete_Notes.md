# LangChain Document Loaders – Complete Learning Notes

# Table of Contents
1. What is a Document Loader?
2. Why Document Loaders are Needed
3. LangChain Document Object
4. Document Loader Workflow
5. Core Document Loaders
6. PyPDFLoader
7. PyMuPDFLoader
8. UnstructuredPDFLoader
9. TextLoader
10. WebBaseLoader
11. DirectoryLoader
12. Metadata Explained
13. Choosing the Right Loader
14. Real-World RAG Pipeline
15. Best Practices
16. Interview Questions

---

# 1. What is a Document Loader?

A Document Loader is the first component in a LangChain data pipeline.

Its job is to:

- Read data from a source
- Extract content
- Convert it into LangChain Document objects

Without a loader, LangChain cannot understand your PDFs, websites, text files, Word documents, or CSV files.

---

# 2. Why Document Loaders are Needed

LLMs cannot directly read:

- PDF files
- Word files
- Excel files
- Websites
- CSV files

The loader converts them into:

```python
Document(
    page_content="actual text",
    metadata={}
)
```

This standardized format allows every downstream LangChain component to work consistently.

---

# 3. LangChain Document Object

Every loader returns:

```python
List[Document]
```

Each document contains:

## page_content

The actual extracted text.

Example:

```python
doc.page_content
```

Output:

```text
Artificial Intelligence is transforming industries...
```

## metadata

Extra information about the source.

Example:

```python
doc.metadata
```

Output:

```python
{
    "source": "report.pdf",
    "page": 5
}
```

Common metadata:

- source
- page
- title
- author
- creation date
- URL

---

# 4. Document Loader Workflow

```text
Raw File
    ↓
Document Loader
    ↓
List[Document]
    ↓
Text Splitter
    ↓
Embeddings
    ↓
Vector Database
    ↓
Retriever
    ↓
LLM
```

In RAG systems the loader is always Step 1.

---

# 5. Core Document Loaders

## PyPDFLoader

Used for:

```text
.pdf
```

## TextLoader

Used for:

```text
.txt
```

## DirectoryLoader

Loads multiple files from folders.

## WebBaseLoader

Loads webpages.

## UnstructuredLoader

Loads complex documents.

---

# 6. PyPDFLoader

Most commonly used PDF loader.

Import:

```python
from langchain_community.document_loaders import PyPDFLoader
```

Example:

```python
loader = PyPDFLoader("report.pdf")

docs = loader.load()
```

Returns:

```python
List[Document]
```

Usually:

```python
1 page = 1 document
```

Advantages:

- Simple
- Fast
- Lightweight

Limitations:

- Doesn't preserve complex layouts well
- Struggles with scanned PDFs
- Not ideal for tables

Best for:

- Digital PDFs
- Research papers
- Reports
- Manuals

---

# 7. PyMuPDFLoader

Built on:

```text
PyMuPDF (fitz)
```

Import:

```python
from langchain_community.document_loaders import PyMuPDFLoader
```

Example:

```python
loader = PyMuPDFLoader("report.pdf")

docs = loader.load()
```

Advantages:

- Very fast
- Better metadata
- Better text extraction
- Handles large PDF collections efficiently

Metadata example:

```python
{
    "source": "report.pdf",
    "page": 10,
    "total_pages": 100
}
```

Best for:

- Production systems
- High-volume document ingestion
- Enterprise RAG systems

---

# 8. UnstructuredPDFLoader

Used for complex layouts.

Import:

```python
from langchain_community.document_loaders import UnstructuredPDFLoader
```

Example:

```python
loader = UnstructuredPDFLoader("complex.pdf")

docs = loader.load()
```

Handles:

- Tables
- Headers
- Footers
- Multi-column layouts
- Forms

Advantages:

- Rich extraction
- Better structure preservation

Disadvantages:

- Slower
- More dependencies
- Higher memory usage

Best for:

- Financial reports
- Invoices
- Contracts
- Complex enterprise documents

---

# 9. TextLoader

Used for plain text files.

Example:

```python
from langchain_community.document_loaders import TextLoader

loader = TextLoader("notes.txt")

docs = loader.load()
```

Best for:

- Logs
- Notes
- Text datasets
- Documentation

---

# 10. WebBaseLoader

Loads webpage content.

Example:

```python
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader(
    "https://example.com"
)

docs = loader.load()
```

Flow:

```text
URL
 ↓
WebBaseLoader
 ↓
Document
```

Multiple URLs:

```python
loader = WebBaseLoader(
    [
        "https://site1.com",
        "https://site2.com"
    ]
)
```

Use cases:

- News articles
- Blogs
- Documentation sites
- Knowledge bases

---

# 11. DirectoryLoader

Loads many files automatically.

Folder:

```text
docs/
├── report.pdf
├── guide.pdf
├── notes.txt
├── summary.pdf
```

Example:

```python
from langchain_community.document_loaders import DirectoryLoader

loader = DirectoryLoader(
    "docs/"
)

docs = loader.load()
```

PDF only:

```python
loader = DirectoryLoader(
    "docs/",
    glob="**/*.pdf"
)
```

Explanation:

```text
*.pdf
```

Current folder PDFs only.

```text
**/*.pdf
```

All PDFs recursively.

Very useful when ingesting thousands of files.

---

# 12. Metadata Explained

Metadata is extremely important in RAG.

Example:

```python
{
    "source": "employee_handbook.pdf",
    "page": 25
}
```

Benefits:

- Source citations
- Page references
- Filtering
- Traceability

Example answer:

```text
According to page 25 of employee_handbook.pdf...
```

Without metadata:

- Hard to verify answers
- No source attribution

---

# 13. Choosing the Right Loader

## Simple Digital PDF

Use:

```text
PyPDFLoader
```

## Large PDF Collections

Use:

```text
PyMuPDFLoader
```

## Complex Layouts

Use:

```text
UnstructuredPDFLoader
```

## Websites

Use:

```text
WebBaseLoader
```

## Multiple Files

Use:

```text
DirectoryLoader
```

## Plain Text

Use:

```text
TextLoader
```

---

# 14. Real-World RAG Pipeline

Example:

```python
loader = PyPDFLoader("policy.pdf")

docs = loader.load()
```

Then:

```python
split_docs = splitter.split_documents(docs)
```

Then:

```python
vector_store.add_documents(split_docs)
```

Then:

```python
retriever = vector_store.as_retriever()
```

Then:

```python
response = retriever.invoke(question)
```

Pipeline:

```text
PDF
 ↓
Loader
 ↓
Documents
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector DB
 ↓
Retriever
 ↓
LLM
```

---

# 15. Best Practices

1. Start with PyPDFLoader.
2. Move to PyMuPDFLoader if performance matters.
3. Use UnstructuredPDFLoader for complex layouts.
4. Always inspect extracted text.
5. Preserve metadata.
6. Clean noisy text before chunking.
7. Use DirectoryLoader for large repositories.
8. Store metadata inside vector databases.

---

# 16. Interview Questions

## What does a document loader do?

Converts raw data into LangChain Document objects.

## What does a loader return?

```python
List[Document]
```

## Difference between page_content and metadata?

page_content = actual text

metadata = information about source

## When should you use PyMuPDFLoader?

When performance and metadata quality are important.

## When should you use UnstructuredPDFLoader?

For tables, forms, invoices, and complex layouts.

## What is DirectoryLoader?

A loader that automatically loads multiple files from a directory.

## Why is metadata important?

It provides source tracking, citations, filtering, and traceability.

---

# Quick Revision

```text
PyPDFLoader
    Simple PDFs

PyMuPDFLoader
    Faster PDFs
    Better metadata

UnstructuredPDFLoader
    Complex PDFs

TextLoader
    TXT files

WebBaseLoader
    Websites

DirectoryLoader
    Multiple files
```

The document loader is the ENTRY POINT of every LangChain RAG pipeline. If the loader extracts poor-quality text, every later step (chunking, embeddings, retrieval, and generation) will also suffer.
