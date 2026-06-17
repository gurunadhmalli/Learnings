from langchain.chat_models import init_chat_model

from dotenv import load_dotenv

load_dotenv()


# Function definition
def exceircise_with_model():

    # Nested function that takes:
    # question -> the prompt to send to the LLM
    # model_names -> list of model names
    def get_response(question: str, model_names: list[str]):

        # Empty dictionary to store responses
        # Format:
        # {
        #   "model_name": "response text"
        # }
        responses = {}

        # Loop through each model name in the list
        for model_name in model_names:

            # Initialize the chat model
            model = init_chat_model(
                model=model_name,               # e.g. "gemini-2.5-flash"
                max_tokens=1000,               # Maximum tokens in response
                model_provider="google_genai"  # Provider is Google Gemini
            )

            # Send the question to the model
            response = model.invoke(question)

            # Store only the text content of the response
            # Example:
            # responses["gemini-2.5-flash"] = "AI is ..."
            responses[model_name] = response.content

        # Return all collected responses
        return responses

    # Call get_response()
    # question = "what is the ai"
    # model list = ["gemini-2.5-flash"]
    results = get_response(
        "what is the ai",
        ["gemini-2.5-flash"]
    )

    # Iterate through dictionary items
    for model, answer in results.items():

        # Print model name and response
        print(f"Response from {model} : {answer}\n")


if __name__ == "__main__":
    exceircise_with_model()



        