from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# RunnableParallel     -> Run multiple chains simultaneously
# RunnableLambda       -> Wrap normal Python functions into LCEL chains
# RunnablePassthrough  -> Pass input unchanged to the next step
from langchain_core.runnables import (
    RunnableParallel,
    RunnableLambda,
    RunnablePassthrough,
    RunnableBranch,
)

from dotenv import load_dotenv


# ============================================================
# Load environment variables from .env file
# Example:
# COHERE_API_KEY=xxxxxxxxxxxxxxxx
# ============================================================
load_dotenv()


# ============================================================
# Initialize Chat Model
#
# temperature=0.5
# Lower value -> More deterministic
# Higher value -> More creative
# ============================================================
model = init_chat_model(
    model="command-a-03-2025",
    temperature=0.5,
)


# ============================================================
# BASIC CHAIN
#
# Flow:
#
# Input
#   ↓
# Prompt Template
#   ↓
# LLM
#   ↓
# Output Parser
#   ↓
# Final String
# ============================================================
def demo_basis_chain():

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(
        "summarize the text {text}"
    )

    # Convert AIMessage → string
    parser = StrOutputParser()

    # LCEL Chain
    # prompt output becomes model input
    # model output becomes parser input
    chain = prompt | model | parser

    # Execute chain
    result = chain.invoke(
        {
            "text": (
                "You are a curious builder who turned "
                "from traditional engineering into AI."
            )
        }
    )

    print(result)


# ============================================================
# PARALLEL CHAIN
#
# Flow:
#
#                  Input Text
#                       |
#       --------------------------------
#       |              |              |
#       ↓              ↓              ↓
#
#  Summary      Sentiment       Keywords
#
#       ↓              ↓              ↓
#
#       -------- Combined Output ------
#
# ============================================================
def demo_parallel_chain():

    # Prompt for summary generation
    summary_prompt = ChatPromptTemplate.from_template(
        "Summarize the text {text} in one line."
    )

    # Prompt for sentiment analysis
    sentiment_prompt = ChatPromptTemplate.from_template(
        "Give the sentiment of the text {text} in one line."
    )

    # Prompt for keyword extraction
    keyword_prompt = ChatPromptTemplate.from_template(
        "Extract 5 keywords from the text {text}. "
        "Return them as comma separated values."
    )

    parser = StrOutputParser()

    # RunnableParallel executes all branches simultaneously
    analysis_chain = RunnableParallel(

        # Branch 1
        summary=summary_prompt | model | parser,

        # Branch 2
        sentiment=sentiment_prompt | model | parser,

        # Branch 3
        keywords=keyword_prompt | model | parser,
    )

    # Same input goes to all branches
    results = analysis_chain.invoke(
        {
            "text": """
            Gurunadh Malli is a highly motivated and self-driven
            aspiring AI Engineer focused on building intelligent,
            production-grade AI systems.
            """
        }
    )

    print("Analysis Chain Result\n")

    print(f"Summary   : {results['summary']}")
    print(f"Sentiment : {results['sentiment']}")
    print(f"Keywords  : {results['keywords']}")


# ============================================================
# PASSTHROUGH CHAIN
#
# Purpose:
# Demonstrates how to keep original input while
# generating additional data (retrieved context).
#
# Flow:
#
# Question
#    ↓
#
# RunnableParallel
# ├── Retriever
# └── Passthrough
#
#    ↓
#
# Merge Data
#
#    ↓
#
# Prompt
#    ↓
# LLM
#    ↓
# Parser
#    ↓
# Answer
# ============================================================
def demo_passthrough_chain():

    prompt = ChatPromptTemplate.from_template(
        "Original question: {question}\n"
        "Context: {context}\n\n"
        "Answer the question based on the context."
    )

    # Simulated Retriever
    def fake_retriever(input_dict):

        # Normally vector database search happens here
        return "LangChain was created by Harrison Chase in 2022."

    chain = (

        # Create two parallel outputs
        RunnableParallel(

            # Context branch
            context=RunnableLambda(fake_retriever),

            # Pass original input unchanged
            question=RunnablePassthrough(),
        )

        # Reshape data
        | RunnableLambda(
            lambda x: {
                "context": x["context"],
                "question": x["question"]["question"],
            }
        )

        # Build final prompt
        | prompt

        # Send prompt to model
        | model

        # Convert AIMessage -> string
        | StrOutputParser()
    )

    result = chain.invoke(
        {
            "question": "Who created LangChain?"
        }
    )

    print(f"Answer: {result}")


# ============================================================
# BRANCHING CHAIN
#
# Purpose:
# Route request to different chains
# based on classification.
#
# Flow:
#
# User Question
#       ↓
#
# Classifier
#       ↓
#
# Is Code Question?
#
#     /      \
#   Yes      No
#   ↓         ↓
#
# Code     General
# Chain     Chain
#
#      ↓
#   Response
# ============================================================
def demo_chain_branching():

    # Prompt used for coding questions
    code_prompt = ChatPromptTemplate.from_template(
        "You are a coding expert. Help with: {input}"
    )

    # Prompt used for general questions
    general_prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. Answer: {input}"
    )

    # Classification Prompt
    classifier_prompt = ChatPromptTemplate.from_template(
        "Classify this as 'code' or 'general': {input}\n"
        "Return only the classification."
    )

    # Classifier Chain
    classifier = (
        classifier_prompt
        | model
        | StrOutputParser()
    )

    # Function that decides routing
    def is_code_question(input_dict):

        classification = classifier.invoke(input_dict)

        return "code" in classification.lower()

    # Conditional Routing
    branch = RunnableBranch(

        # If condition is True
        (
            is_code_question,
            code_prompt | model | StrOutputParser(),
        ),

        # Default route
        general_prompt | model | StrOutputParser(),
    )

    questions = [
        "How do I write a for loop in Python?",
        "What's the weather like today?",
    ]

    for q in questions:

        result = branch.invoke(
            {
                "input": q
            }
        )

        print(f"Q: {q}")
        print(f"A: {result}\n")


# ============================================================
# DEBUGGING CHAIN
#
# Demonstrates:
#
# 1. Schema inspection
# 2. Config metadata
# 3. Intermediate step logging
#
# ============================================================
def demo_debugging():

    prompt = ChatPromptTemplate.from_template(
        "Say hello to {name}"
    )

    chain = (
        prompt
        | model
        | StrOutputParser()
    )

    # ------------------------------------------------
    # View expected input structure
    # ------------------------------------------------
    print(
        "Chain input schema:",
        chain.input_schema.model_json_schema()
    )

    # ------------------------------------------------
    # View expected output structure
    # ------------------------------------------------
    print(
        "Chain output schema:",
        chain.output_schema.model_json_schema()
    )

    # ------------------------------------------------
    # Add metadata for tracing
    # Useful in LangSmith
    # ------------------------------------------------
    result = chain.with_config(
        run_name="greeting_chain"
    ).invoke(
        {
            "name": "Alice"
        }
    )

    print(f"Greeting: {result}")

    # ------------------------------------------------
    # Debug helper function
    # ------------------------------------------------
    def log_step(x, step_name=""):

        print(
            f"[{step_name}] "
            f"{type(x).__name__}: "
            f"{str(x)[:100]}"
        )

        return x

    # ------------------------------------------------
    # Debug chain
    # ------------------------------------------------
    debug_chain = (

        prompt

        # Inspect prompt output
        | RunnableLambda(
            lambda x: log_step(
                x,
                "after_prompt"
            )
        )

        # Model call
        | model

        # Inspect model output
        | RunnableLambda(
            lambda x: log_step(
                x,
                "after_model"
            )
        )

        # Convert AIMessage → String
        | StrOutputParser()
    )

    print("\nDebug chain execution:")

    result = debug_chain.invoke(
        {
            "name": "Debug"
        }
    )

    print(f"Greeting: {result}")


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":

    # demo_basis_chain()

    demo_parallel_chain()

    # demo_passthrough_chain()

    # demo_chain_branching()

    # demo_debugging()