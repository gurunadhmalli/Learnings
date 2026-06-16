from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()



def demo_init_chat_models():
    model = init_chat_model(
        model="gemini-3.5-flash",
        model_provider="google_genai",
        max_tokens = 1500,
        streaming = True,
        max_retries = 3

    )

    responce = model.invoke("what is the ai?")
    print(responce.content)


if __name__ == "__main__":
    demo_init_chat_models()
