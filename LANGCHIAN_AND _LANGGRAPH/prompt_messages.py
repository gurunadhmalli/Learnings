

from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ChatMessage, ToolMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Load environment variables from .env file (e.g., GOOGLE_API_KEY)
load_dotenv()


# ============================================================
# SECTION 1: Simple Single-String Prompt Template
# ============================================================
# `from_template` creates a prompt from a single string with placeholders.
# Use this when you only need a human message (no system message).

prompt = ChatPromptTemplate.from_template("tell me a {adjective} joke about {topic}")

# `format_messages` fills in the placeholders and returns a list of message objects
messages = prompt.format_messages(adjective="fun", topic="chickens")

print("--- Section 1: Simple Template ---")
print(messages)
# Output: [HumanMessage(content='tell me a fun joke about chickens')]


# ============================================================
# SECTION 2: Multi-Message Prompt Template (Translation Example)
# ============================================================
# `from_messages` creates a prompt from a list of (role, template) tuples.
# Roles: "system", "human", "ai"
# Use this when you need both a system message and a human message.

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant to translate {input_language} to {output_language}"),
        ("human", "Translate the following text: {text}"),
    ]
)

# Fill in all placeholders
messages = prompt.format_messages(
    input_language="English",
    output_language="Telugu",
    text="I called this obsession over dedication"
)

print("\n--- Section 2: Translation Template ---")
print(messages)

# Initialize the Gemini model via LangChain
# `init_chat_model` works with multiple providers (openai, google_genai, etc.)
model = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google_genai",
    max_tokens=1500
)

# Invoke the model with the formatted messages
response = model.invoke(messages)

print("\n--- Section 2: Translation Response ---")
print(response.content)


# ============================================================
# SECTION 3: Message Types Overview
# ============================================================
# LangChain supports different message types. Here's what each one is:
#
#   HumanMessage  - Message from the user/human
#   SystemMessage - Instruction/context set before the conversation
#   AIMessage     - Response from the AI model
#   ChatMessage   - Generic message with a custom role (e.g., "function", "tool")
#   ToolMessage   - Result returned from a tool/function call (used in agents)
#
# NOTE: This list is for reference only — it's not passed to the model here.

messages_reference = [
    HumanMessage(content="This is a human message"),
    SystemMessage(content="This is a system message"),
    AIMessage(content="This is an AI message"),
    ChatMessage(role="custom_role", content="This is a chat message with a custom role"),
    ToolMessage(content="This is the tool result", tool_call_id="tool_001"),
    # FIX: ToolMessage requires a `tool_call_id` argument — added above
]

print("\n--- Section 3: Message Types Reference ---")
for msg in messages_reference:
    print(f"{type(msg).__name__}: {msg.content}")


# ============================================================
# SECTION 4: Few-Shot Prompt Template (Antonyms Example)
# ============================================================
# Few-shot prompting gives the model examples to learn from before the actual query.
# Steps:
#   1. Define example input/output pairs
#   2. Create an example prompt template
#   3. Wrap them in FewShotChatMessagePromptTemplate
#   4. Combine with a system message and the actual user input

# Step 1: Define examples — each dict maps to the example_prompt's variables
examples = [
    {"input": "happy",  "output": "sad"},
    {"input": "tall",   "output": "short"},
    {"input": "fast",   "output": "slow"},
]

# Step 2: Template that formats each individual example as a human/ai exchange
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai",    "{output}"),
])

# Step 3: Combines all examples using the example_prompt format
fewshot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

# Step 4: Build the final prompt — system + few-shot examples + actual user input
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "Give me the opposite of the word."),
    fewshot_prompt,          # Inserts all formatted examples here
    ("human", "{input}"),    # The actual user query
])

# Invoke the model using the final prompt
# FIX: Use `final_prompt.format_messages(input="big")` or pass the full prompt via pipe.
# `final_prompt.format(input=...)` returns a string, not messages — use `invoke` correctly.
response = model.invoke(final_prompt.format_messages(input="big"))

print("\n--- Section 4: Few-Shot Antonym Response ---")
print(response.content)


# ============================================================
# SECTION 5: Composing Prompts with `+` Operator
# ============================================================
# You can combine two ChatPromptTemplates using `+`.
# This merges their message lists into a single prompt.

# System message template
sys_message = ChatPromptTemplate.from_messages([
    ("system", "This is your role: {role}")
])

# Human message template
human_msg = ChatPromptTemplate.from_messages([
    ("human", "This is the input: {input}")
])

# Merge both templates — final_msg contains both system and human messages
final_msg = sys_message + human_msg

# FIX: Typo fixed — "softwear" → "software"
formatted = final_msg.format_messages(
    role="Software Engineer",
    input="What are the software development principles?"
)

print("\n--- Section 5: Composed Prompt Messages ---")
for msg in formatted:
    print(f"{type(msg).__name__}: {msg.content}")