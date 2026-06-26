
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import CohereEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader,WebBaseLoader,DirectoryLoader,PyPDFLoader
import os
import tempfile
from dotenv import load_dotenv
load_dotenv()

# Exercise: Build a document Q&A system

# cohere_api_key = os.getenv("COHERE_API_KEY")
# embedding_model= CohereEmbeddings(
#     model="embed-v4.0",
#     cohere_api_key = cohere_api_key
# )


# llm = init_chat_model(model="command-a-03-2025",temperature = 0.2)

# def exercise_document_qa():
#     """
#     EXERCISE: Build a complete document Q&A system that:
#     1. Takes a text document as input
#     2. Splits and embeds it
#     3. Allows multiple questions
#     4. Returns answers with confidence scores
#     """

#     loder = TextLoader("C:\Learnings\RAG_Five_Paragraphs.txt")

#     document = loder.load()


#     splitter = RecursiveCharacterTextSplitter(chunk_size = 500,chunk_overlap = 50)

#     docs =Document(page_content=document,metadat = {"source":"C:\Learnings\RAG_Five_Paragraphs.txt"})

#     chunks = splitter.split_documents(docs)

#     vectore_store = Chroma.from_documents(
#         documents = chunks,
#         embedding= embedding_model,
#         persist_directory = tempfile.mkdtemp()

#     )

#     return vectore_store

# Exercise: Build a document Q&A system
def exercise_document_qa():
    """
    EXERCISE: Build a complete document Q&A system that:
    1. Takes a text document as input
    2. Splits and embeds it
    3. Allows multiple questions
    4. Returns answers with confidence scores
    """

    class DocumentQA:
        def __init__(self, document: str, source_name: str = "document"):
            # Split document
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            doc = Document(page_content=document, metadata={"source": source_name})
            chunks = splitter.split_documents([doc])

            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=CohereEmbeddings(model="embed-v4.0"),
            )
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

            # Create chain
            self.llm = init_chat_model(model="command-a-03-2025", temperature=0.2)

            self.prompt = ChatPromptTemplate.from_template(
                """
Answer based on the context. Rate your confidence (high/medium/low).

Context: {context}
Question: {question}

Format: [Confidence: X] Answer"""
            )

            def format_docs(docs):
                return "\n".join(d.page_content for d in docs)

            self.chain = (
                {
                    "context": self.retriever | format_docs,
                    "question": RunnablePassthrough(),
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )

        def ask(self, question: str) -> str:
            return self.chain.invoke(question)

    # Test
    test_doc = """
    The Python programming language was created by Guido van Rossum.
    First released in 1991, Python emphasizes code readability.
    Python 3.12 was released in October 2023 with improved error messages.
    The language is named after Monty Python, not the snake.
    """

    qa = DocumentQA(test_doc, "python_facts")

    print("Document Q&A System:\n")
    questions = [
        "Who created Python?",
        "When was Python 3.12 released?",
        "Why is Python named Python?",
    ]

    for q in questions:
        answer = qa.ask(q)
        print(f"Q: {q}")
        print(f"A: {answer}\n")
