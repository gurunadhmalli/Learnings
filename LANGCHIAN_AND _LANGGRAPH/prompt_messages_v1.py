

from langchain_core.prompts import (
    ChatPromptTemplate,           # Main class for building prompt templates
    FewShotChatMessagePromptTemplate,  # For few-shot examples
    MessagesPlaceholder,          # For injecting dynamic message history
)
from langchain_core.messages import (
    SystemMessage,   # Sets AI behavior/persona before conversation
    HumanMessage,    # Represents user input
    AIMessage,       # Represents past AI responses (used in history)
)
from langchain.chat_models import init_chat_model  # Universal model loader
from dotenv import load_dotenv

# Load GOOGLE_API_KEY from .env file
load_dotenv()


# ─────────────────────────────────────────────
# HELPER: Initialize Gemini Model
# ─────────────────────────────────────────────
# We define a reusable function so every demo uses the same model.
# `init_chat_model` works with multiple providers — just change
# model_provider to switch between "openai", "google_genai", etc.

def get_model(temperature: float = 0.0):
    """Returns a Gemini 2.5 Flash chat model instance."""
    return init_chat_model(
        model="gemini-2.5-flash",        # Gemini model name
        model_provider="google_genai",   # Provider: Google Generative AI
        max_tokens=1500,                 # Max tokens in the response
        temperature=temperature,         # 0 = deterministic, 1 = creative
    )


# ─────────────────────────────────────────────
# DEMO 1: Basic ChatPromptTemplate
# ─────────────────────────────────────────────
def demo_basic_templates():
    """
    Demonstrates two ways to create prompt templates:
    1. from_template  → single string with one human message
    2. from_messages  → list of (role, content) tuples for multi-turn setup
    """

    # --- 1a. Simple single-string template ---
    # Use `from_template` when you only need a human message.
    # Placeholders use {curly_brace} syntax.
    simple = ChatPromptTemplate.from_template("Translate '{text}' to {language}")

    # `format_messages` fills placeholders → returns a list of message objects
    messages = simple.format_messages(text="Hello, world!", language="French")
    print("Simple template:")
    print(f"  {messages}")
    # Output: [HumanMessage(content="Translate 'Hello, world!' to French")]

    # --- 1b. Multi-message template ---
    # Use `from_messages` when you need a system + human message.
    # Each tuple is (role, template_string).
    multi = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a translator. Be concise."),
            ("human", "Translate '{text}' to {language}"),
        ]
    )

    messages = multi.format_messages(text="Good morning", language="Japanese")
    print("\nMulti-message template:")
    for msg in messages:
        print(f"  {type(msg).__name__}: {msg.content}")
    # Output:
    #   SystemMessage: You are a translator. Be concise.
    #   HumanMessage: Translate 'Good morning' to Japanese


# ─────────────────────────────────────────────
# DEMO 2: Message Types with Gemini
# ─────────────────────────────────────────────
def demo_message_types():
    """
    Shows how to manually build a conversation using message objects
    and pass them directly to the model.

    Message types:
      SystemMessage → sets the AI's role/behavior
      HumanMessage  → user's question or input
      AIMessage     → AI's previous reply (used for multi-turn history)
    """

    model = get_model(temperature=0)

    # Build a multi-turn conversation manually.
    # The model sees the full history and continues from the last HumanMessage.
    messages = [
        SystemMessage(content="You are a math tutor. Be brief."),
        HumanMessage(content="What's 5 * 5?"),
        AIMessage(content="25"),                    # Simulated past AI response
        HumanMessage(content="And if I add 10?"),   # The new question
    ]

    # `invoke` sends the entire conversation and returns the next AI response
    response = model.invoke(messages)
    print(f"Conversation result: {response.content}")
    # Gemini sees: 5*5=25, then 25+10=35


# ─────────────────────────────────────────────
# DEMO 3: MessagesPlaceholder (Dynamic History)
# ─────────────────────────────────────────────
def demo_messages_placeholder():
    """
    MessagesPlaceholder lets you inject a dynamic list of messages
    (e.g., conversation history) into a fixed template at runtime.

    This is essential for chatbots and memory-based applications.
    """

    # `MessagesPlaceholder` reserves a slot in the prompt for a list of messages.
    # At runtime, pass a list of HumanMessage/AIMessage objects for `history`.
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="history"),  # Dynamic history goes here
            ("human", "{question}"),                       # Current user question
        ]
    )

    # Simulate previous conversation turns
    history = [
        HumanMessage(content="My name is Ravi"),
        AIMessage(content="Nice to meet you, Ravi!"),
    ]

    # Preview the final formatted messages
    messages = prompt.format_messages(history=history, question="What's my name?")
    print("With history placeholder:")
    for msg in messages:
        print(f"  {type(msg).__name__}: {msg.content[:60]}")

    # --- LangChain pipe operator `|` ---
    # `prompt | model` creates a chain: prompt formats input, then model processes it.
    model = get_model(temperature=0)
    chain = prompt | model

    response = chain.invoke({
        "history": history,
        "question": "What's my name?"
    })
    print(f"\nResponse: {response.content}")
    # Gemini should recall "Ravi" from the history


# ─────────────────────────────────────────────
# DEMO 4: Few-Shot Prompting
# ─────────────────────────────────────────────
def demo_few_shot():
    """
    Few-shot prompting gives the model worked examples before the real query.
    This guides the model's output format and behavior.

    Steps:
      1. Define example dicts with input/output keys
      2. Create an example_prompt to format each example
      3. Wrap in FewShotChatMessagePromptTemplate
      4. Combine with system message + actual user input
    """

    # Step 1: Example pairs — keys must match the example_prompt placeholders
    examples = [
        {"word": "happy",  "opposite": "sad"},
        {"word": "fast",   "opposite": "slow"},
        {"word": "big",    "opposite": "small"},
    ]

    # Step 2: Template that formats ONE example as a human/ai exchange
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "What's the opposite of '{word}'?"),
            ("ai",    "The opposite of '{word}' is '{opposite}'."),
        ]
    )

    # Step 3: Expands all examples using the example_prompt format
    # This inserts all 3 examples as alternating human/ai messages
    few_shot = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    # Step 4: Final prompt = system instruction + examples + actual user query
    final_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You give the opposite of words. Follow the examples."),
            few_shot,                                      # Inserts all example messages here
            ("human", "What's the opposite of '{word}'?"), # Real question
        ]
    )

    # Chain the prompt with the Gemini model
    model = get_model(temperature=0)
    chain = final_prompt | model

    response = chain.invoke({"word": "bright"})
    print(f"Few-shot result: {response.content}")
    # Expected: "The opposite of 'bright' is 'dark'." (following the example format)


# ─────────────────────────────────────────────
# DEMO 5: Prompt Composition with `+`
# ─────────────────────────────────────────────
def demo_prompt_composition():
    """
    You can compose two ChatPromptTemplates using the `+` operator.
    This merges their message lists into a single combined prompt.

    Useful for:
      - Building reusable prompt "modules" (persona, task, constraints)
      - Mixing and matching prompt components dynamically
    """

    # Reusable persona/system prompt — defines WHO the AI is
    persona = ChatPromptTemplate.from_messages(
        [("system", "You are a {role}. Your tone is {tone}.")]
    )

    # Reusable task prompt — defines WHAT the AI should do
    task = ChatPromptTemplate.from_messages(
        [("human", "{task}")]
    )

    # `+` merges the two prompts:
    # full_prompt = [SystemMessage from persona] + [HumanMessage from task]
    full_prompt = persona + task

    # Chain with Gemini — temperature=0.7 for more creative responses
    model = get_model(temperature=0.7)
    chain = full_prompt | model

    # --- Test 1: Pirate persona ---
    response = chain.invoke({
        "role": "pirate captain",
        "tone": "adventurous",
        "task": "Tell me about your ship",
    })
    print(f"Pirate: {response.content[:120]}...")

    # --- Test 2: Scientist persona ---
    response = chain.invoke({
        "role": "scientist",
        "tone": "precise and academic",
        "task": "Explain photosynthesis in one sentence",
    })
    print(f"\nScientist: {response.content[:120]}...")


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 50)
    print("Demo 1: Basic Templates")
    print("=" * 50)
    demo_basic_templates()

    print("\n" + "=" * 50)
    print("Demo 2: Message Types")
    print("=" * 50)
    demo_message_types()

    print("\n" + "=" * 50)
    print("Demo 3: MessagesPlaceholder")
    print("=" * 50)
    demo_messages_placeholder()

    print("\n" + "=" * 50)
    print("Demo 4: Few-Shot Prompting")
    print("=" * 50)
    demo_few_shot()

    print("\n" + "=" * 50)
    print("Demo 5: Prompt Composition")
    print("=" * 50)
    demo_prompt_composition()