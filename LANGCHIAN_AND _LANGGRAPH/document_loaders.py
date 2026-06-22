import os
import tempfile
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader,WebBaseLoader,DirectoryLoader,PyPDFLoader
from dotenv import load_dotenv
from bs4 import BeautifulSoup


load_dotenv()


def load_text_file():
    with tempfile.NamedTemporaryFile(delete=False,suffix=".txt") as temp_file:
        temp_file.write(
            b"hi i am gurunadh now i woking as the ai enginner"
            )
        
        temp_file_path = temp_file.name


    try:
        loader = TextLoader(temp_file_path)
        document = loader.load()


        print(f"Loaded {len(document)} document(s)")
        print(f"Content preview: {document[0].page_content[:100]}...")
        print(f"Metadata: {document[0].metadata}")

        # Print the loaded documents
        # for doc in documents:
        #     print("Document Content:")
        #     print(doc)
        #     print(doc.page_content)
    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)



def web_base_loader():
    loader = WebBaseLoader(
        "https://en.wikipedia.org/wiki/Web_scraping", bs_kwargs={"parse_only": None}
    )

    documents = loader.load()

    print(f"Loaded {len(documents)} document(s) from web")
    print(f"Source: {documents[0].metadata.get('source', 'N/A')}")
    print(f"Content length: {len(documents[0].page_content)} characters")
    print(f"Preview: {documents[0].page_content[:200]}...")


def lazy_loader():

    # Create temp directory with sample files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample files
        for i in range(5):
            path = Path(tmpdir) / f"doc_{i}.txt"
            path.write_text(f"This is document {i}. It contains sample content.")

        loader = DirectoryLoader(tmpdir, glob="*.txt", loader_cls=TextLoader)

        print("Initialized lazy loader for directory:", tmpdir)
        for doc in loader.lazy_load():
            print("Document Content Preview:", doc.page_content[:50], "...")
            print("Metadata:", doc.metadata["source"])



def document_stracture():

    doc = Document(
        page_content="This is a sample document.",
        metadata={
            "source": "manual_creation.txt",
            "author": "gurunadh",
            "length": 30,
            "tags": ["sample", "test"],
            "created_at": "2024-06-01",
        },
    )
    print("Document Structure:")
    print(f"  page_content (type): {type(doc.page_content)}")
    print(f"  page_content: {doc.page_content}")
    print(f"  metadata: {doc.metadata}")


def pdf_loader(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    print(f"Loaded {len(documents)} document(s) from PDF")
    for i, doc in enumerate(documents):
        print(f"Document {i+1} Content Preview: {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}")


if __name__ == "__main__":
    # load_text_file()
    # web_base_loader()
    # lazy_loader()
    # document_stracture()
    pdf_loader("C:\Learnings\GURUNADH_AI_ENGINEER.pdf")
