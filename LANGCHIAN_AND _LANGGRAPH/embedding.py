from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv
import numpy as np

# Load environment variables from .env file
# This is where your COHERE_API_KEY is typically stored.
load_dotenv()


# ==========================================================
# INITIALIZE EMBEDDING MODEL
# ==========================================================
#
# Embedding models convert text into vectors (lists of numbers).
#
# Example:
#
# "Python is a programming language"
#
# becomes
#
# [0.23, -0.45, 0.11, ....]
#
# These vectors capture semantic meaning.
#
# Similar texts will produce similar vectors.
#
# ==========================================================

embeddings = CohereEmbeddings(
    model="embed-v4.0"
)


# ==========================================================
# BASIC SINGLE TEXT EMBEDDING
# ==========================================================
#
# Purpose:
# Learn how a single text is converted into a vector.
#
# embed_query():
# Used when embedding a user question/query.
#
# In RAG:
# User Question
#      ↓
# embed_query()
#      ↓
# Query Vector
#
# ==========================================================

def basic_embeddings():

    text = "my name is gurunadh"

    # Convert text into vector
    query_embedding = embeddings.embed_query(text)

    print("=" * 50)
    print("Embedding Information")
    print("=" * 50)

    # Vector magnitude (length of vector)
    #
    # norm() computes:
    #
    # sqrt(x1² + x2² + x3² + ...)
    #
    # This is heavily used in cosine similarity.
    #
    print(f"Vector Magnitude: {np.linalg.norm(query_embedding):.4f}")

    # Print last 5 values from vector
    print(f"Last 5 Vector Values: {query_embedding[-5:]}")

    # Number of dimensions
    print(f"Vector Dimensions: {len(query_embedding)}")


# ==========================================================
# BATCH DOCUMENT EMBEDDINGS
# ==========================================================
#
# embed_documents():
#
# Used when embedding multiple documents/chunks.
#
# In RAG:
#
# Document
#      ↓
# Chunking
#      ↓
# Chunk 1
# Chunk 2
# Chunk 3
#      ↓
# embed_documents()
#      ↓
# Vector Database
#
# ==========================================================

def basic_batch_embeddings():

    documents = [
        "my name is gurunadh",
        "MY NAME IS SUNEEL",
        "my name is srinu"
    ]

    # Convert all documents into vectors
    document_embeddings = embeddings.embed_documents(documents)

    print("=" * 50)
    print("Batch Embedding Information")
    print("=" * 50)

    for i, embedding in enumerate(document_embeddings):

        print(f"\nDocument Index: {i}")

        # Last 5 values from embedding
        print(f"Last 5 Values: {embedding[-5:]}")

        # Magnitude of vector
        print(f"Vector Magnitude: {np.linalg.norm(embedding):.4f}")

        # Number of dimensions
        print(f"Vector Length: {len(embedding)}")


# ==========================================================
# COSINE SIMILARITY FUNCTION
# ==========================================================
#
# Measures semantic similarity between vectors.
#
# Formula:
#
#           A · B
# --------------------------
# |A| × |B|
#
#
# Result:
#
# 1.0  -> Exactly Same Meaning
# 0.8  -> Very Similar
# 0.5  -> Somewhat Similar
# 0.0  -> Unrelated
# -1   -> Opposite
#
# ==========================================================

def cosine_similarity(v1, v2):

    return np.dot(v1, v2) / (
        np.linalg.norm(v1) *
        np.linalg.norm(v2)
    )


# ==========================================================
# MANUAL SIMILARITY SEARCH
# ==========================================================
#
# This simulates what a Vector Database does.
#
# RAG Retrieval Flow:
#
# User Question
#      ↓
# Query Embedding
#      ↓
# Compare with all document embeddings
#      ↓
# Similarity Scores
#      ↓
# Rank Results
#      ↓
# Retrieve Top Documents
#
# ==========================================================

def similarity_search():

    documents = [
        "python is a programming language",
        "deep learning can learn complex patterns",
        "machine learning is a sub branch of AI"
    ]

    query = "what is python?"

    print("=" * 50)
    print("Query")
    print("=" * 50)

    print(query)

    # --------------------------------------------------
    # Step 1: Embed User Question
    # --------------------------------------------------
    #
    # Convert question into vector.
    #
    query_embedding = embeddings.embed_query(query)

    # --------------------------------------------------
    # Step 2: Embed Documents
    # --------------------------------------------------
    #
    # Convert all documents into vectors.
    #
    document_embeddings = embeddings.embed_documents(documents)

    # --------------------------------------------------
    # Step 3: Compute Similarity Scores
    # --------------------------------------------------
    #
    # Compare query vector against each document vector.
    #
    similarities = [

        cosine_similarity(
            query_embedding,
            doc_embedding
        )

        for doc_embedding in document_embeddings
    ]

    # --------------------------------------------------
    # Step 4: Rank Documents
    # --------------------------------------------------
    #
    # zip():
    #
    # [
    #   ("python...", 0.92),
    #   ("deep learning...", 0.31),
    #   ("machine learning...", 0.45)
    # ]
    #
    # Sort by similarity score.
    #
    ranked_docs = sorted(
        zip(documents, similarities),
        key=lambda x: x[1],
        reverse=True
    )

    # --------------------------------------------------
    # Step 5: Display Results
    # --------------------------------------------------

    print("\n")
    print("=" * 50)
    print("Similarity Search Results")
    print("=" * 50)

    for rank, (doc, score) in enumerate(ranked_docs, start=1):

        print(f"\nRank #{rank}")

        print(f"Document:")
        print(doc)

        print(f"Similarity Score: {score:.4f}")

        # Interpretation
        if score > 0.8:
            print("Meaning: Very Similar")

        elif score > 0.5:
            print("Meaning: Moderately Similar")

        else:
            print("Meaning: Less Similar")


# ==========================================================
# PROGRAM ENTRY POINT
# ==========================================================
#
# Run whichever example you want to learn.
#
# ==========================================================

if __name__ == "__main__":

    # Learn single text embedding
    # basic_embeddings()

    # Learn batch embeddings
    # basic_batch_embeddings()

    # Learn retrieval using cosine similarity
    similarity_search()