from typing_extensions import TypedDict,Annotated
from langgraph.graph import START,END,StateGraph,add_messages
from langchain_core.messages import BaseMessage,HumanMessage
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()
import operator



class SimpleState(TypedDict):
    input : str
    output : str
    step : int


def demo_basic_graph():

    def process(state:SimpleState):

        return {"output":state["input"].upper(),"step":state["step"]+1}
    


    #create a graph

    graph = StateGraph(SimpleState)


    #add node

    graph.add_node("process",process)

    #add edges

    graph.add_edge(START,"process")
    graph.add_edge("process",END)

    #we need to comile the graph
    app = graph.compile()


    #mermaid graph

    print(app.get_graph().draw_mermaid())


    #save as png
    png_bytes = app.get_graph().draw_mermaid_png()
    with open("graph.png","wb") as f:
        f.write(png_bytes)
    print("graph saved as the png bytes image")



    #run app

    result = app.invoke({"input":"hello","output":"","step":0})
    print(f"simple graph result : {result}")

    print(
    f"input: {result['input']}, output: {result['output']}, step: {result['step']}"
    )




# Define the shared state of the graph.
class AcumulatingState(TypedDict):

    # Accumulate lists by concatenating them.
    messages: Annotated[list[str], operator.add]

    # Accumulate integers by adding them.
    count: Annotated[int, operator.add]


def demo_accumated_state():

    # First node
    def step_one(state: AcumulatingState):

        # Returns a new message and increments count by 1.
        return {
            "messages": ["step one got executed"],
            "count": 1
        }

    # Second node
    def step_two(state: AcumulatingState):

        # Again returns one message and increments count by 1.
        return {
            "messages": ["step two got executed"],
            "count": 1
        }

    # Create the graph with the shared state.
    graph = StateGraph(AcumulatingState)

    # Register nodes.
    graph.add_node("step_one", step_one)
    graph.add_node("step_two", step_two)

    # Define execution order.
    graph.add_edge(START, "step_one")
    graph.add_edge("step_one", "step_two")
    graph.add_edge("step_two", END)

    # Compile the graph.
    app = graph.compile()

    # Print Mermaid graph.
    print(app.get_graph().draw_mermaid())

    # Save graph image.
    png_bytes = app.get_graph().draw_mermaid_png()

    with open("graph1.png", "wb") as f:
        f.write(png_bytes)

    print("PNG saved.")

    # Initial state.
    result = app.invoke({
        "messages": ["initial messages"],
        "count": 0
    })

    print("Accumulated State")

    print(f"messages: {result['messages']}")
    print(f"count: {result['count']}")


class MessageState(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]


def demo_messages_state():

    llm = init_chat_model(model="command-a-03-2025",model_provider="cohere",max_tokens=1000)

    def chat_node(state:MessageState):
        response = llm.invoke(state["messages"])
        return {"messages":[response]}
    

    graph = StateGraph(MessageState)
    graph.add_node("chat_node",chat_node)
    graph.add_edge(START,"chat_node")
    graph.add_edge("chat_node",END)

    app = graph.compile()
    result = app.invoke({"messages":[HumanMessage(content="what is the capital of india")]})

    for i in result["messages"]:
        role = "Human" if isinstance(i,HumanMessage) else "Ai"
        print(f"{role}:{i.content}")

    



def excercise_langraph_first():


    class QaState(TypedDict):
        topic : str
        question : str
        answer : str

    llm = init_chat_model(model="command-a-03-2025",model_provider="cohere",max_tokens=1000)

    def generate_questions(state:QaState):
        response = llm.invoke(f"generate three interesting questions about {state['topic']}\n"
                      "formatted: numbered list")

        return {"question": response.content}


    def answer_question(state:QaState):

        response = llm.invoke(f"generate the answer for the first question {state['question']}")

        return {"answer":response.content}


    graph = StateGraph(QaState)

    graph.add_node(generate_questions,"generate_questions")
    graph.add_node(answer_question,"answer_question")


    graph.add_edge(START,"generate_questions")
    graph.add_edge("generate_questions","answer_question")
    graph.add_edge("answer_question",END)


    app = graph.compile()

    result = app.invoke({"topic":"the future is about the renewel energey"})


    print("Excercise Result")

    print(f"topic: {result['topic']}")
    print(f"question: {result['question']}")
    print(f"answer: {result['answer']}")






if __name__ == "__main__":

    # demo_basic_graph()
    # demo_accumated_state()
    # demo_messages_state()
    excercise_langraph_first()
