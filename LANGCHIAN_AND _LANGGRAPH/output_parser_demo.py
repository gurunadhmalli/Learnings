"""
output_parser_demo.py

This file demonstrates four different ways to get outputs from an LLM:

1. Raw LLM Output (AIMessage)
2. StrOutputParser (String Output)
3. JsonOutputParser (Dictionary Output)
4. PydanticOutputParser (Pydantic Object Output)
5. Structured Output (Recommended Modern Approach)

Author: Gurunadh
"""

# ============================================================
# Load environment variables from .env file
# ============================================================
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# LangChain Imports
# ============================================================
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
    PydanticOutputParser
)

# ============================================================
# Pydantic Imports
# ============================================================
from pydantic import BaseModel, Field


# ============================================================
# Create LLM
# ============================================================
# This creates a Cohere chat model object.
# The model will be reused across all examples.
# ============================================================

llm = init_chat_model(
    model="command-a-03-2025",
    model_provider="cohere",
    max_tokens=1000
)


# ============================================================
# Example 1 : Raw LLM Output
# ============================================================
# By default, chat models return an AIMessage object.
# ============================================================

def raw_output_demo():

    prompt = ChatPromptTemplate.from_template(
        "Tell me about {topic}"
    )

    chain = prompt | llm

    response = chain.invoke({
        "topic": "Artificial Intelligence"
    })

    print("\n========== RAW OUTPUT ==========")
    print(response)
    print(type(response))


# ============================================================
# Example 2 : String Output Parser
# ============================================================
# Converts AIMessage -> String
#
# Output:
# "Artificial Intelligence is..."
#
# Type:
# str (or TextAccessor in newer versions)
# ============================================================

def string_output_demo():

    prompt = ChatPromptTemplate.from_template(
        "Tell me about {topic}"
    )

    parser = StrOutputParser()

    chain = prompt | llm | parser

    response = chain.invoke({
        "topic": "Artificial Intelligence"
    })

    print("\n========== STRING OUTPUT ==========")
    print(response)
    print(type(response))


# ============================================================
# Example 3 : JSON Output Parser
# ============================================================
# Converts LLM response into Python Dictionary.
#
# Output:
# {
#   "name": "Gurunadh",
#   "age": 22
# }
#
# Type:
# dict
# ============================================================

def json_output_demo():

    prompt = ChatPromptTemplate.from_template(
        """
        Return the person's details in JSON format.

        Description:
        {description}
        """
    )

    parser = JsonOutputParser()

    chain = prompt | llm | parser

    result = chain.invoke({
        "description": "My name is Gurunadh and I am 22 years old."
    })

    print("\n========== JSON OUTPUT ==========")
    print(result)
    print(type(result))


# ============================================================
# Create Pydantic Schema
# ============================================================
# This schema defines the structure we expect.
# ============================================================

class Person(BaseModel):

    # Person name
    name: str = Field(
        description="name of the person"
    )

    # Person age
    age: int = Field(
        description="age of the person"
    )


# ============================================================
# Example 4 : Pydantic Output Parser
# ============================================================
# Converts LLM output into a Pydantic object.
#
# Output:
# Person(name='Srinu', age=26)
#
# Type:
# Person
# ============================================================

def pydantic_output_demo():

    parser = PydanticOutputParser(
        pydantic_object=Person
    )

    prompt = ChatPromptTemplate.from_template(
        """
        Extract the person's information.

        {format_instructions}

        Description:
        {description}
        """
    ).partial(
        format_instructions=parser.get_format_instructions()
    )

    chain = prompt | llm | parser

    result = chain.invoke({
        "description": "My name is Srinu and I am 26 years old."
    })

    print("\n========== PYDANTIC OUTPUT ==========")
    print(result)
    print(type(result))

    print("\nName:", result.name)
    print("Age :", result.age)


# ============================================================
# Example 5 : Structured Output (Recommended)
# ============================================================
# Modern LangChain approach.
#
# No parser needed.
#
# LangChain automatically:
# 1. Creates schema instructions
# 2. Sends schema to model
# 3. Validates response
# 4. Returns Person object
#
# Output:
# Person(name='Srinu', age=26)
# ============================================================

def structured_output_demo():

    structured_llm = llm.with_structured_output(
        Person
    )

    result = structured_llm.invoke(
        "My name is Srinu and I am 26 years old."
    )

    print("\n========== STRUCTURED OUTPUT ==========")
    print(result)
    print(type(result))

    print("\nName:", result.name)
    print("Age :", result.age)


# ============================================================
# Main Function
# ============================================================

if __name__ == "__main__":

    # Uncomment the demo you want to run

    # raw_output_demo()

    # string_output_demo()

    # json_output_demo()

    # pydantic_output_demo()

    structured_output_demo()