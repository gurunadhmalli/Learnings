from typing_extensions import TypedDict,Annotated
from langgraph.graph import START,END,StateGraph
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




class AcumulatingState(TypedDict):
    messages: Annotated[list[str], operator.add] #list concated when merged
    count : Annotated[int,operator.add]




def demo_accumated_state():

    def step_one(state:AcumulatingState):

        return {
            "messages":["step one got excuted"],
            "count":1
        }
    
    def step_two(state:AcumulatingState):

        return {
            "messages":["step two got excuted"],
            "count":1
        }


    graph = StateGraph(AcumulatingState)

    graph.add_node("step_one",step_one)
    graph.add_node("step_two",step_two)

    graph.add_edge(START,"step_one")
    graph.add_edge("step_one","step_two")
    graph.add_edge("step_two",END)


    app = graph.compile()


    print(app.get_graph().draw_mermaid())

    png_bytes = app.get_graph().draw_mermaid_png()

    with open("graph1.png","wb") as f:
        f.write(png_bytes)
    print("png bytes are saved")



    result = app.invoke({
        "messages":["intail messages"],
        "count":0
    })

    print("accumelated state")

    print(f"messages:{result['messages']}")
    print(f"count : {result['count']}")









if __name__ == "__main__":
    # demo_basic_graph()
    demo_accumated_state()
