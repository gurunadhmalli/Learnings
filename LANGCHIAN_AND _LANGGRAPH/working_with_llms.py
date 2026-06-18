"""
=========================================================
LangChain init_chat_model() Examples
=========================================================

Topics Covered:
1. Basic model initialization
2. Switching between models
3. Comparing multiple models
4. Working with SystemMessage and HumanMessage
5. Multi-turn conversation

Author: Gurunadh
=========================================================
"""

# Import required libraries
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
import os

# Load environment variables from .env file
load_dotenv()


# =========================================================
# Example 1: Basic Model Initialization
# =========================================================
def demo_init_chat_models():
    """
    Demonstrates how to initialize a chat model and
    invoke it with a simple string prompt.
    """

    print("\n" + "=" * 60)
    print("DEMO 1 : BASIC MODEL INITIALIZATION")
    print("=" * 60)

    # Create Gemini model
    model = init_chat_model(
        model="gemini-2.5-flash",
        model_provider="google_genai",
        max_tokens=1500,
        streaming=True,
        max_retries=3
    )

    print("\nModel Initialized Successfully")
    print("Model Name       : gemini-2.5-flash")
    print("Provider         : Google Gemini")
    print("Max Tokens       : 1500")
    print("Streaming        : True")
    print("Max Retries      : 3")

    question = "What is AI?"

    print("\nSending Prompt:")
    print(question)

    response = model.invoke(question)

    print("\nModel Response:")
    print("-" * 60)
    print(response.content)
    print("-" * 60)


# =========================================================
# Example 2: Model Switching
# =========================================================
def demo_init_chat_models1():
    """
    Demonstrates how to switch between Gemini and Cohere.
    """

    print("\n" + "=" * 60)
    print("DEMO 2 : MODEL SWITCHING")
    print("=" * 60)

    # Gemini Model
    gemini = init_chat_model(
        model="gemini-2.5-flash",
        model_provider="google_genai",
        max_tokens=500,
        streaming=True,
        max_retries=3
    )

    prompt = "What is AI?"

    print("\nPrompt:", prompt)

    response = gemini.invoke(prompt)

    print("\nResponse From Gemini")
    print("-" * 60)
    print(response.content)
    print("-" * 60)

    # Check if Cohere API Key exists
    if os.getenv("COHERE_API_KEY"):

        print("\nCOHERE_API_KEY Found")

        cohere = init_chat_model(
            model="command-a-03-2025",
            model_provider="cohere",
            max_tokens=500,
            streaming=True,
            max_retries=3
        )

        response = cohere.invoke(prompt)

        print("\nResponse From Cohere")
        print("-" * 60)
        print(response.content)
        print("-" * 60)

    else:
        print("\nCOHERE_API_KEY Not Found")
        print("Skipping Cohere Model...")


# =========================================================
# Example 3: Comparing Multiple Models
# =========================================================
def comparison_models():
    """
    Compares responses from multiple models
    using the same prompt.
    """

    print("\n" + "=" * 60)
    print("DEMO 3 : MODEL COMPARISON")
    print("=" * 60)

    prompt = "What is the use of Computer Vision?"

    print(f"\nPrompt: {prompt}\n")

    models = {
        "gemini-2.5-flash": init_chat_model(
            model="gemini-2.5-flash",
            model_provider="google_genai",
            max_tokens=500,
            streaming=True,
            max_retries=3
        ),

        "command-a-03-2025": init_chat_model(
            model="command-a-03-2025",
            model_provider="cohere",
            max_tokens=500,
            streaming=True,
            max_retries=3
        )
    }

    # Loop through each model
    for model_name, model in models.items():

        print("\n" + "=" * 60)
        print(f"Running Model : {model_name}")
        print("=" * 60)

        response = model.invoke(prompt)

        print("\nResponse:")
        print("-" * 60)
        print(response.content)
        print("-" * 60)


# =========================================================
# Example 4: Working with Messages
# =========================================================
def demo_messages():
    """
    Demonstrates:
    1. System Message
    2. Human Message
    3. Multi-turn conversation
    """

    print("\n" + "=" * 60)
    print("DEMO 4 : MESSAGE BASED CONVERSATION")
    print("=" * 60)

    model = init_chat_model(
        model="gemini-2.5-flash",
        model_provider="google_genai",
        max_tokens=1500
    )

    # Create messages list
    messages = [
        SystemMessage(
            content="You are a teacher and should only teach AI topics."
        ),
        HumanMessage(
            content="What is AI?"
        )
    ]

    print("\nMessages Sent To Model")
    print("-" * 60)

    print("\nSystem Message:")
    print(messages[0].content)

    print("\nHuman Message:")
    print(messages[1].content)

    print("-" * 60)

    # First model response
    response = model.invoke(messages)

    print("\nAssistant Response:")
    print("-" * 60)
    print(response.content)
    print("-" * 60)

    # =====================================================
    # Multi-turn Conversation
    # =====================================================

    print("\nAdding Assistant Response To Chat History")

    messages.append(response)

    print("Adding New Human Question")

    messages.append(
        HumanMessage(
            content="What is a transistor?"
        )
    )

    print("\nUpdated Conversation History")
    print("-" * 60)

    for index, msg in enumerate(messages, start=1):
        print(f"\nMessage {index}")
        print(msg)

    print("-" * 60)

    print("\nSending Complete Conversation Back To Model...")

    second_response = model.invoke(messages)

    print("\nAssistant Second Response")
    print("-" * 60)
    print(second_response.content)
    print("-" * 60)


# =========================================================
# Main Function
# =========================================================
if __name__ == "__main__":

    print("\n" + "#" * 70)
    print("LANGCHAIN INIT_CHAT_MODEL DEMONSTRATIONS")
    print("#" * 70)

    # Uncomment any function to test

    # demo_init_chat_models()

    # demo_init_chat_models1()

    # comparison_models()

    demo_messages()

    print("\n" + "#" * 70)
    print("PROGRAM EXECUTION COMPLETED")
    print("#" * 70)