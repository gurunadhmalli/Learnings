from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage
from typing import Dict


from dotenv import load_dotenv
load_dotenv()


llm = init_chat_model(model="command-a-03-2025")


def demo_basic_memory():


    prompt = ChatPromptTemplate.from_messages([
        ("system", "you are an helpful assisant give me the consice ans"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),


    ])


    parser = StrOutputParser()

    chain = prompt | llm | parser



    store : Dict[str,InMemoryChatMessageHistory] = {}


    def get_session_history(session_id:str):

        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()

        return store[session_id]
    

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history"
    )


    config = {"configurable": {"session_id": "user_123"}}



    messages = [
        "Hi! My name is Paulo.",
        "I'm learning about LangChain.",
        "What's my name and what am I learning?",
    ]

    for msg in messages:
        responce = chain_with_history.invoke({"input":msg},config=config)
        print(responce)


    #showing the stored messages

    for msg in store["user_123"].messages:
        role = "Human" if isinstance(msg,HumanMessage) else "Ai"
        print(f"{role}:{msg.content[:50]}")




if __name__ == "__main__":
    demo_basic_memory()