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


from langchain.chat_models import init_chat_model


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
    model = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",tempareture = 1.0,max_tokens = 1500)
    parser = StrOutputParser()

    chain = prompt | model | parser


    for chunk in chain.stream({"question":"what is the python?"}):
        print(chunk, end = "",flush = True)

    print()






def demo_input_output_schema():
    # Create a prompt template with one input variable: {question}
    # The user will provide a value for "question", and it will be
    # inserted into the template before sending it to the model.
    prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. Write about this topic: {question}"
    )

    # Initialize the Google Gemini language model.
    # - model: specifies which Gemini model to use.
    # - temperature: controls creativity (higher = more random).
    # - max_tokens: maximum number of tokens the model can generate.
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        temperature=1.0,      # (Correct spelling: temperature)
        max_tokens=1500
    )

    # Output parser converts the raw LLM response into a plain string.
    parser = StrOutputParser()

    # Create a LangChain Expression Language (LCEL) pipeline.
    # Flow: User Input --> Prompt --> Gemini Model --> String Parser
    chain = prompt | model | parser

    # Generate the JSON schema that describes the expected input format.
    # Since the prompt contains {question}, the input schema will expect
    # a field named "question" of type string.
    input_schema = chain.input_schema.model_json_schema()

    # Generate the JSON schema that describes the output format.
    # Because we use StrOutputParser(), the final output is simply a string.
    output_schema = chain.output_schema.model_json_schema()

    # Print the input schema.
    print(f"This is the input schema:\n{input_schema}")

    # Print the output schema.
    print(f"\nThis is the output schema:\n{output_schema}")


def excercise_chain():
    prompt = ChatPromptTemplate.from_template("you are an helpful assitnact take the product name {p_name} and audience {audience} return just tag line")
    model = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",tempareture = 1.0,max_tokens = 1500)
    parser = StrOutputParser()


    chain = prompt | model | parser

    result = chain.invoke({"p_name":"AI Course","audience":"developers"})
    print(result)
    return chain


def demo_init_chat():
    # Create a prompt template with a placeholder variable {question}.
    # The value provided for "question" during chain execution will be
    # automatically inserted into this template.
    prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. Answer the question: {question}"
    )

    # Initialize a chat model using the generic `init_chat_model()` helper.
    # - model_provider: Specifies which AI provider to use (Google Gemini).
    # - model: The specific Gemini model to load.
    # - temperature: Controls the randomness/creativity of the responses.
    #                Lower values produce more deterministic answers,
    #                while higher values generate more diverse outputs.
    # - max_tokens: Maximum number of tokens the model is allowed to generate.
    #
    # Note: The correct parameter name is `temperature`, not `tempareture`.
    model = init_chat_model(
        model_provider="google_genai",
        model="gemini-3.5-flash",
        temperature=1.0,
        max_tokens=1500
    )

    # Create an output parser that converts the model's response
    # into a plain Python string.
    parser = StrOutputParser()

    # Build the LangChain pipeline using the pipe operator (`|`).
    # Data flow:
    # User Input --> Prompt Template --> Chat Model --> String Parser
    chain = prompt | model | parser

    # Execute the chain by providing the required input variable.
    # The dictionary key "question" matches the placeholder {question}
    # used in the prompt template.
    result = chain.invoke({
        "question": "What is Python?"
    })

    # Print the final parsed response generated by the AI model.
    print(result)

    # Return the complete chain object so that it can be reused
    # elsewhere in the program without rebuilding it.
    return chain
    



# This block executes only when this Python file
# is run directly, not when it is imported as a module.
if __name__ == "__main__":
    demo_init_chat()
