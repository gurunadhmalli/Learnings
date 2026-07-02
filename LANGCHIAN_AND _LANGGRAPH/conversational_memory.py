from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory,BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage,trim_messages
from langchain_cohere import ChatCohere
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

def demo_multi_sessions():

    print("=" * 60)
    print("MULTIPLE CONVERSATION SESSIONS")
    print("Each user gets their own memory")
    print("=" * 60)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant. Remember user details."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    store: Dict[str, InMemoryChatMessageHistory] = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    # Simulate two users
    user_a_config = {"configurable": {"session_id": "user_a"}}
    user_b_config = {"configurable": {"session_id": "user_b"}}

    # User A conversation
    print("\n--- User A ---")
    print("User A: My favorite language is Python")
    resp = chain_with_history.invoke(
        {"input": "My favorite language is Python"}, config=user_a_config
    )
    print(f"AI: {resp}")

    # User B conversation
    print("\n--- User B ---")
    print("User B: I love JavaScript")
    resp = chain_with_history.invoke(
        {"input": "I love JavaScript"}, config=user_b_config
    )
    print(f"AI: {resp}")

    # Ask each user about their preference
    print("\n--- Asking each about their preference ---")

    print("\nUser A: What's my favorite language?")
    resp = chain_with_history.invoke(
        {"input": "What's my favorite language?"}, config=user_a_config
    )
    print(f"AI: {resp}")

    print("\nUser B: What's my favorite language?")
    resp = chain_with_history.invoke(
        {"input": "What's my favorite language?"}, config=user_b_config
    )
    print(f"AI: {resp}")

def demo_message_trimming():
    """Trim messages to fit context window."""

    print("=" * 60)
    print("MESSAGE TRIMMING")
    print("Keep conversation within token limits")
    print("=" * 60)

    # Simulate a long conversation
    messages = [
        SystemMessage(content="You are a helpful coding assistant."),
        HumanMessage(content="What is Python?"),
        AIMessage(
            content="Python is a high-level programming language known for readability and versatility. It's used in web development, data science, AI, and automation."
        ),
        HumanMessage(content="How do I install it?"),
        AIMessage(
            content="You can install Python from python.org or use package managers like apt, brew, or chocolatey. I recommend Python 3.12+ for new projects."
        ),
        HumanMessage(content="What about pip?"),
        AIMessage(
            content="Pip is Python's package installer. It comes with Python 3.4+. Use 'pip install package_name' to install packages. Consider using virtual environments with venv or uv."
        ),
        HumanMessage(content="Can you summarize everything we discussed?"),
    ]

    print(f"\nOriginal: {len(messages)} messages")

    # Trim to last N tokens
    trimmed = trim_messages(
        messages,
        max_tokens=60,
        strategy="last",
        token_counter=llm,
        include_system=True,  # Always keep system message
        allow_partial=False,
    )

    print(f"After trimming (max 60 tokens): {len(trimmed)} messages")
    print("\nTrimmed messages:")
    for msg in trimmed:
        role = type(msg).__name__.replace("Message", "")
        print(f"  {role}: {msg.content[:60]}...")

def demo_windowed_memory():
    """Implement sliding window memory manually."""

    print("=" * 60)
    print("WINDOWED MEMORY (Keep Last K)")
    print("Fixed-size conversation window")
    print("=" * 60)

    class WindowedChatHistory(InMemoryChatMessageHistory):
        """Chat history that keeps only last k message pairs."""

        k: int = 3  # Pydantic field - number of exchange pairs to keep

        def add_messages(self, messages):
            super().add_messages(messages)
            # Keep only last k pairs (2k messages: human + ai)
            if len(self.messages) > self.k * 2:
                self.messages = self.messages[-(self.k * 2) :]

    store: Dict[str, WindowedChatHistory] = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = WindowedChatHistory(k=2)
        return store[session_id]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    config = {"configurable": {"session_id": "windowed_test"}}

    # Simulate a conversation with more than 2 pairs
    exchanges = [
        "My name is Paulo",
        "I live in Seattle",
        "I work as an AI engineer",
        "I have 2 cats",
        "What do you remember about me?",
    ]

    print("\nConversation with k=2 window:")
    for i, msg in enumerate(exchanges, 1):
        print(f"\nUser: {msg}")
        response = chain_with_history.invoke({"input": msg}, config=config)
        print(f"AI: {response}")

        # Show window state after each exchange so students SEE it sliding
        history = store["windowed_test"].messages
        print(f"  [Window: {len(history)} msgs] ", end="")
        facts_in_memory = [
            m.content[:40] for m in history if isinstance(m, HumanMessage)
        ]
        print(f"Remembers: {facts_in_memory}")

    # Final state - show what survived and what was lost
    print("\n" + "=" * 60)
    print("RESULT: Window only kept last 2 exchanges!")
    print("Lost: name (Paulo), city (Seattle), AND job (AI engineer)")
    print("Kept: cats + the 'remember' question")
    print(
        "This is the tradeoff: fixed memory = predictable cost, but older context is lost."
    )


def demo_summary_memory():
    """End-to-end summary memory: auto-summarize old messages, keep recent ones verbatim."""

    print("=" * 60)
    print("SUMMARY MEMORY")
    print("Summarize older messages to save tokens")
    print("=" * 60)

    # --- Setup ---
    summary_llm = ChatCohere(model="command-a-03-2025", temperature=0)
    chat_llm = ChatCohere(model="command-a-03-2025", temperature=0.7)

    # The conversation prompt: summary of old context + recent messages
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. Be concise.\n\n"
                "Summary of earlier conversation:\n{summary}",
            ),
            MessagesPlaceholder(variable_name="recent_messages"),
            ("human", "{input}"),
        ]
    )

    chat_chain = chat_prompt | chat_llm | StrOutputParser()

    # The summarization prompt: compress messages into a running summary
    summarize_prompt = ChatPromptTemplate.from_template(
        "Condense the current summary and new messages into a single updated summary "
        "(2-3 sentences). Preserve all key facts about the user.\n\n"
        "Current summary:\n{current_summary}\n\n"
        "New messages:\n{new_messages}\n\n"
        "Updated summary:"
    )

    summarize_chain = summarize_prompt | summary_llm | StrOutputParser()

    # --- State ---
    running_summary = ""  # starts empty
    recent_messages = []  # full message objects
    MAX_RECENT = 4  # keep last 4 messages (2 exchanges) before summarizing

    # --- Conversation ---
    exchanges = [
        "My name is guru and I'm from kota",
        "I work as an AI engineer building RAG systems",
        "I have 2 friends named srinu and suneel",
        "I'm building a LangChain course for Udemy",
        "What do you know about me? List everything.",
    ]

    print(f"\nConfig: keep last {MAX_RECENT} messages, summarize the rest\n")

    for user_input in exchanges:
        print(f"User: {user_input}")

        # 1. Call the LLM with summary + recent messages + new input
        response = chat_chain.invoke(
            {
                "summary": (
                    running_summary if running_summary else "No prior conversation."
                ),
                "recent_messages": recent_messages,
                "input": user_input,
            }
        )
        print(f"AI: {response}")

        # 2. Add this exchange to recent messages
        recent_messages.append(HumanMessage(content=user_input))
        recent_messages.append(AIMessage(content=response))

        # 3. If recent messages exceed limit, summarize the oldest ones
        if len(recent_messages) > MAX_RECENT:
            # Take the oldest messages that will be summarized away
            messages_to_summarize = recent_messages[:-MAX_RECENT]
            formatted = "\n".join(
                f"{'Human' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
                for m in messages_to_summarize
            )

            # Update the running summary
            running_summary = summarize_chain.invoke(
                {
                    "current_summary": (
                        running_summary if running_summary else "None yet."
                    ),
                    "new_messages": formatted,
                }
            )

            # Keep only the most recent messages
            recent_messages = recent_messages[-MAX_RECENT:]

            print(
                f"  >>> Summarized! Compressed {len(messages_to_summarize)} old messages"
            )
            print(f"  >>> Summary: {running_summary}")
            print(f"  >>> Recent buffer: {len(recent_messages)} messages")
        print()

    # --- Final state ---
    print("=" * 60)
    print("FINAL MEMORY STATE")
    print("=" * 60)
    print(f"\nRunning summary (compressed old context):\n  {running_summary}")
    print(f"\nRecent messages kept verbatim ({len(recent_messages)}):")
    for msg in recent_messages:
        role = "Human" if isinstance(msg, HumanMessage) else "AI"
        print(f"  {role}: {msg.content[:80]}")
    print("\nKey insight: ALL facts preserved (name, city, job, cats, course)")
    print("But token cost stays bounded -- old messages are compressed, not deleted!")








if __name__ == "__main__":
    # demo_basic_memory()
    # demo_multi_sessions()
    # demo_message_trimming()
    # demo_windowed_memory()
    demo_summary_memory()