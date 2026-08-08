from typing_extensions import TypedDict, Annotated
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage,HumanMessage
from langgraph.graph import StateGraph,END,START
import operator
from dotenv import load_dotenv

load_dotenv()





class ConversationState(TypedDict):
    messages: Annotated[list, operator.add]
    sentiment : str
    response_count = int



def create_conversarion_graph():
    llm = init_chat_model(model="command-a-03-2025",model_provider="cohere",max_tokens=1000)


    def analyse_sentement(state:ConversationState):
        """This is use to analyse the sentemet of the messages"""

        last_message = state["messages"][-1]


        response = llm.invoke([
            SystemMessage(content = "Classify the sentent as the positive,negative and neutral only word reply"),
            HumanMessage(content=last_message),

            ]
          )


        return {"sentiment":response.content.lower().strip()}



    def generate_responce(state:ConversationState):
        """Generate the right responce according to the sentiment"""

        sentiment = state["sentiment"]
        last_message = state["messages"][-1]

        system_prompts = {
            "positive": "Respond enthusiastically and build on their positive energy.",
            "negative": "Respond empathetically and offer support.",
            "neutral": "Respond helpfully and informatively.",
        }


        prompt = system_prompts.get(sentiment,system_prompts["neutral"])
        response = llm.invoke([SystemMessage(content=prompt),HumanMessage(content=last_message)])

        return {
            "messages":[f"Ai:{response.content}"],"response_count":1
        }


    graph = StateGraph(ConversationState)

    graph.add_node(analyse_sentement,"analyse_sentement")
    graph.add_node(generate_responce,"generate_responce")

    graph.add_edge(START,"analyse_sentement")
    graph.add_edge("analyse_sentement","generate_responce")
    graph.add_edge("generate_responce",END)


    app = graph.compile()

    return app


def demo_conversation():

    app = create_conversarion_graph()


    test_messages = [
        "I just got promoted at work! I'm so excited!",
        "My computer crashed and I lost all my work...",
        "What's the weather like today?",
    ]


    for msg in test_messages:

        result = app.invoke(
            {"messages":[f"Human:{msg}"],
            "sentiment":"",
            "response_count":0}
        )

        print(f"Input: {msg}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Response: {result['messages'][-1]}")
        print("-" * 40)

if __name__ == "__main__":
    demo_conversation()






