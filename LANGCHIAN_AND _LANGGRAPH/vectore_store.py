
# =============================================================================
# IMPORTS
# =============================================================================

# LangChain Document object.
# Every piece of text stored in a vector database is usually wrapped
# inside a Document object. A Document contains:
#
# 1. page_content -> actual text
# 2. metadata     -> extra information about the text
#
# Example:
# Document(
#     page_content="Python is a programming language",
#     metadata={"source": "book"}
# )
#
from langchain_core.documents import Document


# Cohere embedding model.
#
# Converts text into vectors (lists of floating point numbers).
#
# Example:
#
# "Python is great"
#
# becomes:
#
# [0.23, -0.11, 0.98, ..., 0.45]
#
# These vectors capture semantic meaning.
#
from langchain_cohere import CohereEmbeddings


# Chroma Vector Database.
#
# Stores embeddings and performs similarity search.
#
# Think:
#
# Text
#  ↓
# Embeddings
#  ↓
# Chroma
#  ↓
# Similarity Search
#
from langchain_chroma import Chroma


# Creates temporary folders that are automatically deleted.
#
# Used here for examples/testing.
#
import tempfile


# Recursive Character Text Splitter.
#
# Used to break large documents into smaller chunks before embedding.
#
# Why?
#
# Embedding models work best on smaller pieces of text.
#
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter


# Load environment variables from .env
#
# Used to load:
#
# COHERE_API_KEY
#
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# EMBEDDING MODEL
# =============================================================================

# Create Cohere Embedding model.
#
# This model converts text into vectors.
#
# Example:
#
# "What is Python?"
#      ↓
# [0.12, 0.44, ..., 0.78]
#
embeddings = CohereEmbeddings(
    model="embed-v4.0"
)


# =============================================================================
# SAMPLE DOCUMENTS
# =============================================================================

# Small knowledge base used throughout the examples.
#
# Each Document contains:
#
# page_content -> searchable text
# metadata     -> information about that text
#
# Metadata is extremely important because later we can:
#
# - filter results
# - trace sources
# - perform access control
#
SAMPLE_DOCS = [

    Document(
        page_content="LangChain is a framework for developing applications powered by language models.",
        metadata={
            "source": "langchain_docs",
            "topic": "overview"
        },
    ),

    Document(
        page_content="LangGraph is a library for building stateful, multi-actor applications with LLMs.",
        metadata={
            "source": "langgraph_docs",
            "topic": "overview"
        },
    ),

    Document(
        page_content="Vector stores are databases optimized for storing and searching embeddings.",
        metadata={
            "source": "vector_guide",
            "topic": "database"
        },
    ),

    Document(
        page_content="RAG combines retrieval with generation for more accurate LLM responses.",
        metadata={
            "source": "rag_guide",
            "topic": "architecture"
        },
    ),

    Document(
        page_content="Embeddings convert text into numerical vectors for semantic similarity.",
        metadata={
            "source": "embeddings_guide",
            "topic": "fundamentals"
        },
    ),

    Document(
        page_content="Chroma is an open-source embedding database for AI applications.",
        metadata={
            "source": "chroma_docs",
            "topic": "database"
        },
    ),

    Document(
        page_content="FAISS is a library for efficient similarity search developed by Facebook.",
        metadata={
            "source": "faiss_docs",
            "topic": "database"
        },
    ),

    Document(
        page_content="Pinecone is a managed vector database service for production workloads.",
        metadata={
            "source": "pinecone_docs",
            "topic": "database"
        },
    ),
]


# =============================================================================
# BASIC CHROMA EXAMPLE
# =============================================================================

def chroma_basics():

    # Create a temporary folder.
    #
    # Chroma stores vectors on disk.
    #
    # This directory will be automatically deleted
    # after execution finishes.
    #
    with tempfile.TemporaryDirectory() as tmpdir:

        # --------------------------------------------------------
        # Create Vector Store
        # --------------------------------------------------------
        #
        # Flow:
        #
        # Documents
        #     ↓
        # Embedding Model
        #     ↓
        # Vectors
        #     ↓
        # Chroma Vector Database
        #
        vectorstore = Chroma.from_documents(
            documents=SAMPLE_DOCS,
            embedding=embeddings,
            collection_name="my_unique_collection_v1",
            persist_directory=tmpdir
        )

        print(
            f"Vector store created {vectorstore._collection.count()} documents."
        )

        # User question
        query = "What is LangChain?"

        # --------------------------------------------------------
        # Similarity Search
        # --------------------------------------------------------
        #
        # Query
        #   ↓
        # Query Embedding
        #   ↓
        # Compare against stored vectors
        #   ↓
        # Return most similar documents
        #
        results = vectorstore.similarity_search(
            query,
            k=2
        )

        print(f"Top 2 results for query '{query}':")

        for i, doc in enumerate(results):

            print(
                f"Result {i+1}: {doc.page_content} "
                f"(Source: {doc.metadata['source']})"
            )


# =============================================================================
# SIMILARITY SEARCH WITH SCORES
# =============================================================================

def similarity_search_with_scores():

    with tempfile.TemporaryDirectory() as tmpdir:

        vectorstore = Chroma.from_documents(
            documents=SAMPLE_DOCS,
            embedding=embeddings,
            persist_directory=tmpdir
        )

        query = "Explain vector stores."

        # Similarity search WITH scores.
        #
        # Returns:
        #
        # [
        #   (document, distance),
        #   (document, distance)
        # ]
        #
        results_with_scores = (
            vectorstore.similarity_search_with_score(
                query,
                k=3
            )
        )

        print(
            f"Top 3 results with scores for query '{query}':"
        )

        for i, (doc, score) in enumerate(results_with_scores):

            # Chroma returns distance.
            #
            # Smaller distance = better match.
            #
            # Convert distance into a similarity score.
            #
            final_score = 1 / (1 + score)

            print(
                f"Result {i+1}: "
                f"{doc.page_content} "
                f"(Score: {final_score:.4f})"
            )


# =============================================================================
# METADATA FILTERING
# =============================================================================

def metadata_filtering():

    with tempfile.TemporaryDirectory() as tmpdir:

        vectorstore = Chroma.from_documents(
            documents=SAMPLE_DOCS,
            embedding=embeddings,
            persist_directory=tmpdir
        )

        query = "What databases are available?"

        # --------------------------------------------------------
        # Search ALL documents
        # --------------------------------------------------------
        results = vectorstore.similarity_search(
            query,
            k=5
        )

        # --------------------------------------------------------
        # Search only documents
        # where topic == database
        # --------------------------------------------------------
        #
        # This reduces search space.
        #
        filter_criteria = {
            "topic": "database"
        }

        filtered_results = vectorstore.similarity_search(
            query,
            k=5,
            filter=filter_criteria
        )


# =============================================================================
# PERSISTENT CHROMA
# =============================================================================

def persist_chroma():

    # Folder where vectors are stored.
    #
    # Unlike temporary folders,
    # this survives application restarts.
    #
    persist_dir = "./chroma_db/"

    # Create database.
    vectorstore = Chroma.from_documents(
        documents=SAMPLE_DOCS,
        embedding=embeddings,
        persist_directory=persist_dir,
    )

    # Simulate application restart.
    del vectorstore

    # Reload vector store from disk.
    #
    # No re-embedding required.
    #
    reloaded = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

    # Search still works because vectors
    # were persisted.
    #
    results = reloaded.similarity_search(
        "LangChain",
        k=2
    )


# =============================================================================
# RETRIEVERS
# =============================================================================

def as_retriever():

    with tempfile.TemporaryDirectory() as tmpdir:

        vectorstore = Chroma.from_documents(
            documents=SAMPLE_DOCS,
            embedding=embeddings,
            persist_directory=tmpdir,
        )

        # --------------------------------------------------------
        # Convert Vector Store into Retriever
        # --------------------------------------------------------
        #
        # Vector Store:
        #     Stores vectors
        #
        # Retriever:
        #     Retrieves vectors
        #
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        docs = retriever.invoke(
            "How do I build AI applications?"
        )

        # --------------------------------------------------------
        # MMR Retriever
        # --------------------------------------------------------
        #
        # MMR = Maximum Marginal Relevance
        #
        # Goal:
        #
        # Return relevant AND diverse documents.
        #
        # Instead of:
        #
        # Doc1 = Python
        # Doc2 = Python
        # Doc3 = Python
        #
        # Return:
        #
        # Doc1 = Python
        # Doc2 = LangChain
        # Doc3 = RAG
        #
        mmr_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 3,
                "fetch_k": 5
            }
        )

        mmr_docs = mmr_retriever.invoke(
            "vector databases and embeddings"
        )


# =============================================================================
# COMPLETE RAG-LIKE PIPELINE
# =============================================================================

def exercise_vector_store_setup():

    def create_retriever(

        texts: list[str],

        chunk_size: int = 500,

        chunk_overlap: int = 50,

        k: int = 3

    ):

        # --------------------------------------------------------
        # Convert text into Documents
        # --------------------------------------------------------
        docs = [
            Document(page_content=t)
            for t in texts
        ]

        # --------------------------------------------------------
        # Chunking
        # --------------------------------------------------------
        #
        # Large text
        #
        # 2000 chars
        #
        # becomes:
        #
        # Chunk 1
        # Chunk 2
        # Chunk 3
        #
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        split_docs = splitter.split_documents(
            docs
        )

        # --------------------------------------------------------
        # Create Vector Store
        # --------------------------------------------------------
        #
        # Chunks
        #   ↓
        # Embeddings
        #   ↓
        # Chroma
        #
        vectorstore = Chroma.from_documents(
            documents=split_docs,
            embedding=embeddings
        )

        # --------------------------------------------------------
        # Return Retriever
        # --------------------------------------------------------
        #
        # Retriever becomes the retrieval
        # component of a RAG application.
        #
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    sample_texts = [
        "Python is a versatile programming language...",
        "JavaScript is the language of the web...",
        "Rust is a systems programming language..."
    ]

    retriever = create_retriever(
        sample_texts,
        chunk_size=200,
        chunk_overlap=20,
        k=2
    )

    # Query
    #
    # User Question
    #      ↓
    # Retriever
    #      ↓
    # Relevant Chunks
    #
    results = retriever.invoke(
        "What's good for web development?"
    )


if __name__ == "__main__":

    # Basic Chroma Example
    # chroma_basics()

    # Similarity Search + Scores
    # similarity_search_with_scores()

    # Metadata Filtering
    # metadata_filtering()

    # Persistence Example
    # persist_chroma()

    # Retriever Example
    # as_retriever()

    # Full Pipeline Example
    exercise_vector_store_setup()
