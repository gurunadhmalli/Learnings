# Load environment variables from the .env file
# (e.g., GOOGLE_API_KEY)
from dotenv import load_dotenv

# Import the Google Gemini chat model wrapper from LangChain
from langchain_google_genai import ChatGoogleGenerativeAI

# Import ChatPromptTemplate to create dynamic prompts with placeholders
from langchain_core.prompts import ChatPromptTemplate

# Import StrOutputParser to convert the model's output into a plain string
from langchain_core.output_parsers import StrOutputParser


# Load all environment variables from the .env file into the application
load_dotenv()


def demo_basic_chain():
    """
    Demonstrates a basic LCEL (LangChain Expression Language) pipeline.

    Flow:
    User Input --> Prompt Template --> Gemini Model --> Output Parser --> Final String Output
    """

    # Create a prompt template with a variable placeholder {question}.
    # The value for 'question' will be provided when invoking the chain.
    prompt = ChatPromptTemplate.from_template(
        "You're a helpful assistant that can answer the following question: {question}"
    )

    # Initialize the Gemini model with the desired configuration.
    # - model: Gemini model to use
    # - max_tokens: Maximum number of tokens to generate
    # - temperature: Controls randomness (0 = deterministic, 1 = more creative)
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        max_tokens=1500,
        temperature=0.5
    )

    # Create an output parser that converts the AIMessage object
    # returned by the model into a plain Python string.
    parser = StrOutputParser()

    # Build the LCEL chain using the pipe (|) operator.
    # Data flows from left to right:
    # Prompt --> Model --> Parser
    chain = prompt | model | parser

    # Execute the chain by passing the value for the {question} placeholder.
    result = chain.invoke(
        {"question": "What is LangChain?"}
    )

    # Display the final parsed output.
    print(result)

    # Return the chain object so it can be reused elsewhere.
    return chain


# This block executes only when this file is run directly.
# It will not execute if this file is imported as a module.




def demo_basic_batch_chain():
    """
    Demonstrates batch processing using LCEL (LangChain Expression Language).

    Instead of invoking the chain one request at a time, `batch()`
    allows multiple inputs to be processed in a single call.

    Flow:
    List of Inputs --> Prompt Template --> Gemini Model
                   --> Output Parser --> List of String Outputs
    """

    # Create a prompt template with a variable placeholder {text}.
    # Each dictionary passed to the batch() method must contain
    # a value for this placeholder.
    prompt = ChatPromptTemplate.from_template(
        "You're a helpful assistant. Translate the following question into Telugu: {text}"
    )

    # Initialize the Gemini model.
    # - model: Specifies which Gemini model to use.
    # - max_tokens: Maximum number of tokens the model can generate.
    # - temperature: Controls randomness in the output.
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        max_tokens=1500,
        temperature=0.5
    )

    # Convert the AIMessage response returned by the model
    # into a plain Python string.
    parser = StrOutputParser()

    # Build the LCEL chain.
    # The output of each component becomes the input to the next.
    #
    # Prompt Template --> Gemini Model --> String Output Parser
    chain = prompt | model | parser

    # Prepare multiple inputs for batch execution.
    # Each dictionary corresponds to one execution of the chain.
    inputs = [
        {"text": "What is your name?"},
        {"text": "Who are you?"},
        {"text": "What is your educational qualification?"}
    ]

    # Execute the chain for all inputs at once.
    # The batch() method returns a list of outputs in the
    # same order as the input list.
    results = chain.batch(inputs)

    # Display each input alongside its translated output.
    # zip() pairs each input dictionary with its corresponding result.
    for input_item, output in zip(inputs, results):
        print(f"Input: {input_item['text']}")
        print(f"Output: {output}")
        print("-" * 50)

    # Return the chain object so it can be reused elsewhere.
    return chain



def demo_steam():
    prompt = ChatPromptTemplate.from_template("you are an helpful assitnact write about this topic{question}")
    model = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",tempareture = 100.0,max_tokens = 1500)
    parser = StrOutputParser()

    chain = prompt | model | parser


    for chunk in chain.stream({"question":"what is the python?"}):
        print(chunk, end = "",flush = True)

    print()



# This block executes only when this Python file
# is run directly, not when it is imported as a module.
# if __name__ == "__main__":
print(demo_steam())