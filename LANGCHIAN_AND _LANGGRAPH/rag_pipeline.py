from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tempfile
from langchain_chroma import Chroma

from langchain_cohere import CohereEmbeddings

from langchain.chat_models import init_chat_model

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_BASE = """# LangChain Framework

LangChain is a framework for developing applications powered by language models. It was created by Harrison Chase in October 2022.

## Core Components

1. **Models**: LangChain supports various LLM providers including OpenAI, Anthropic, and local models.

2. **Prompts**: Templates for structuring inputs to language models.

3. **Chains**: Sequences of calls to models and other components.

4. **Agents**: Systems that use LLMs to determine which actions to take.

5. **Memory**: Components for persisting state between chain/agent calls.

## LangGraph

LangGraph is a library for building stateful, multi-actor applications. Key features:
- State management
- Cycles and loops
- Human-in-the-loop
- Persistence

## Pricing

LangChain itself is open source and free. LangSmith (the observability platform) has a free tier and paid plans starting at $39/month.

## Getting Started

Install with: pip install langchain langchain-openai
Create your first chain in under 10 lines of code.
"""
import os
cohere_api_key = os.getenv("COHERE_API_KEY")
embedding_model= CohereEmbeddings(
    model="embed-v4.0",
    cohere_api_key = cohere_api_key
)


llm = init_chat_model(model="command-a-03-2025",temperature = 0.2)


def create_kb():


    splitter = RecursiveCharacterTextSplitter(chunk_size = 500,chunk_overlap = 50)

    doc =Document(page_content=KNOWLEDGE_BASE,metadat = {"source":"langchian_knowledge.md"})


    chunks = splitter.split_documents([doc])

    vectore_store = Chroma.from_documents(
        documents = chunks,
        embedding= embedding_model,
        persist_directory = tempfile.mkdtemp()

    )

    return vectore_store


def demo_basic_rag():

    vectore_store = create_kb()

    retriver = vectore_store.as_retriever(search_type = "similarity",search_kwargs = {"k":2})

    prompt = ChatPromptTemplate.from_template(
        """
Answer the question based only on the following context:

{context}

Question: {question}

Answer:


Make sure to answer in a concise manner, 
and if you don't know the answer, just say "I don't know."""
    )

    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])
    


    rag_chain = (
        {"context":retriver|format_docs,"question":RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
        
    questions = [
        "What is LangChain?",
        "Who created LangChain?",
        "What is LangGraph used for?",
    ]

    for q in questions:
        answer = rag_chain.invoke(q)
        print(f"Q:{q}")
        print(f"A:{answer}\n")






if __name__ == "__main__":
    demo_basic_rag()
