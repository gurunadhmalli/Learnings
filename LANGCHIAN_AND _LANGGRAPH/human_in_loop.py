from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph,START,END
from typing_extensions import TypedDict
from typing import Literal
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


llm = init_chat_model(model="command-a-03-2025",model_provider="cohere")


class ApprovalState(TypedDict):
    request : str
    draft : str
    approved : bool
    feedback : str
    final : str


def demo_interrupt_for_approval():



    def create_draft(state:ApprovalState):
        response = llm.invoke(f"create professional response for : {state['request']}")

        return {"draft":response.content}


    def wait_for_approval(state:ApprovalState):
        """this node where we will interpt"""
        return state


    def finalize(state:ApprovalState):

        if state["approved"]:
            return {"final":state["draft"]}

        else:
            response = llm.invoke(f"revise the draft based on the feedback:\n\n"
                                  f"draft:{state['draft']}\n\n"
                                  f"feedback:{state['feedback']}")

            return {"final":response.content}



    graph = StateGraph(ApprovalState)


    graph.add_node("draft",create_draft)
    graph.add_node("approval",wait_for_approval)
    graph.add_node("finalize",finalize)


    graph.add_edge(START,"draft")
    graph.add_edge("draft","approval")
    graph.add_edge("approval","finalize")
    graph.add_edge("finalize",END)

    memory = MemorySaver()#save the intermedaite memory
    app = graph.compile(checkpointer=memory,interrupt_before=["approval"]) #interpt before approval node


    print("Human in the loop Approval Demo:\n")

    config = {"configurable":{"thread_id":"demo-1"}}


    print("Step:1 Running untill approval checkpoint")

    result = app.invoke(
        {
            "request" : "write a thank you email for the job interview",
            "draft" : "",
            "approved" : False,
            "feedback" : "",
            "final" : ""
            },
            config)

    print(f"\n draft created :\n {result['draft'][:200]}...")
    print("\n execution pause for the humun review")


    #step 2

    current_state = app.get_state(config) 
    print(f"\n Current node : {current_state.next}")


    #step3 simulate human feedback and provide continue

    app.update_state(config,
                     {
                         "approved":bool(input("apprve the workflow:")),  #REQUEST CHANGES
                         "feedback":"make it more concise and specific mention company culture"

                     })

     
    #continue executin

    final_result = app.invoke(None,config)
    print(f"\nfinal result:\n{final_result['final']}")


if __name__ == "__main__":
    demo_interrupt_for_approval()
    