from importlib.metadata import version
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

core_version = version("langchain-core")
lg_version = version("langgraph")

def main():
    print("Hello from LangChain and LangGraph!")
    print(f"LangChain Core: {core_version}")
    print(f"LangGraph: {lg_version}")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        max_tokens=1500
    )

    response = llm.invoke(
        "What are some of the pros and cons of Python as a programming language?"
    )

    print(response.content)
    print("Setup complete!")

if __name__ == "__main__":
    main()