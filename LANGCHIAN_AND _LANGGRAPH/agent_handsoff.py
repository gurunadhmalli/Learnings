from langgraph.graph import StateGraph,START,END,add_messages
from typing_extensions import TypedDict,Annotated,Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage,AIMessage,BaseMessage,SystemMessage
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import operator



load_dotenv()

llm = init_chat_model(model_provider="cohere",model = "command-a-03-2025")


class HandsoffState(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]
    current_agent : str
    handoff_reason : str
    context_summary : str


class HandoffDecision(BaseModel):
    handoff_to : Literal["sales","billing","support","stay","end"] = Field(
        description="which agent is hands of to"
    )
    context: str = Field(description="key context to pass to next agent")
    reason: str = Field(description="reason to give the next agent")



def create_customer_service_system():


    def traige_agent(state:HandsoffState):
        """intaite traige to route customer"""

        system = """you are an customer service traige agent. your job is
        1.understand the customer needs
        2.route the appropraite specialist:
         -sales : product questions ,purchases,upgrades
         -support : technical issues , bugs,how-to questions
         -billing : payment,invoices,refunds
         -end : simple questions you can answer directly 
         analyse the customer message and decide to where to route them"""
        
        handoff_llm = llm.with_structured_output(HandoffDecision)


        messages = [SystemMessage(content=system)]+state["messages"]

        decision = handoff_llm.invoke(messages)


        if decision.handoff_to == "end":
            #answe directly
            responce = llm.invoke(
                [SystemMessage(content="provide a brief helpful to customer"),*state["messages"]]
            )

            return {
                "messages":[AIMessage(content = f"[Traige] {responce.content}")],
                "current_agent": "end"
            }
        
        return {
            "current_agent":decision.handoff_to,
            "handoff_reason":decision.reason,
            "context_summary":decision.context,
            "messages":[AIMessage(content=f"[Traige] transfering to {decision.handoff_to}")]
        }
    

    def sales_agent(state: HandsoffState) -> dict:
        """Sales specialist."""
        system = f"""You are a sales specialist. Context from triage: {state.get('context_summary', 'None')}

            Help the customer with product questions and purchases.
            Be helpful and informative, not pushy."""

        response = llm.invoke([SystemMessage(content=system), *state["messages"], HumanMessage(content="Please assist me with this.")])

        return {
            "messages": [AIMessage(content=f"[Sales] {response.content}")],
            "current_agent": "sales_complete",
        }

    def support_agent(state: HandsoffState) -> dict:
        """Technical support specialist."""
        system = f"""You are a technical support specialist. Context from triage: {state.get('context_summary', 'None')}

        Help the customer with technical issues.
        Be patient and provide step-by-step guidance."""

        response = llm.invoke([SystemMessage(content=system), *state["messages"], HumanMessage(content="Please assist me with this.")])

        return {
            "messages": [AIMessage(content=f"[Support] {response.content}")],
            "current_agent": "support_complete",
        }

    def billing_agent(state: HandsoffState) -> dict:
        """Billing specialist."""
        system = f"""You are a billing specialist. Context from triage: {state.get('context_summary', 'None')}

        Help the customer with billing questions.
        Be clear about policies and next steps."""

        response = llm.invoke([SystemMessage(content=system), *state["messages"], HumanMessage(content="Please assist me with this.")])

        return {
            "messages": [AIMessage(content=f"[Billing] {response.content}")],
            "current_agent": "billing_complete",
        }

    def route_from_traige(state:HandsoffState):
        agent = state["current_agent"]

        if agent in ["sales","support","billing"]:
            return agent
        return "end"
    

    graph = StateGraph(HandsoffState)

    graph.add_node("traige_agent",traige_agent)
    graph.add_node("sales_agent",sales_agent)
    graph.add_node("support_agent",support_agent)
    graph.add_node("billing_agent",billing_agent)

    graph.add_edge(START,"traige_agent")
    graph.add_conditional_edges(
        "traige_agent",route_from_traige,{"sales":"sales_agent","support":"support_agent","billing":"billing_agent","end":END}
    )

    graph.add_edge("sales_agent",END)
    graph.add_edge("support_agent",END)
    graph.add_edge("billing_agent",END)

    return graph.compile()


def demo_handoffs():
    """Demo customer service handoffs."""

    agent = create_customer_service_system()

    print("Customer Service Handoff Demo:\n")

    queries = [
        "My app keeps crashing when I try to upload photos",
        "I want to upgrade to the premium plan",
        "I was charged twice for my subscription",
        "What time do you close?",
    ]

    for query in queries:
        print(f"Customer: {query}")

        result = agent.invoke(
            {
                "messages": [HumanMessage(content=query)],
                "current_agent": "",
                "handoff_reason": "",
                "context_summary": "",
            }
        )

        for msg in result["messages"]:
            if isinstance(msg, AIMessage):
                print(f"  {msg.content[:150]}...")

        print("-" * 50)


if __name__ == "__main__":
    demo_handoffs()