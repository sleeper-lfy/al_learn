from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# Workflow = State + Node + Edge 构成的执行流程。

class State(TypedDict):
    text: str


def step1(state: State):
    return {"text": state["text"] + " → step1"}


def step2(state: State):
    return {"text": state["text"] + " → step2"}


def step3(state: State):
    return {"text": state["text"] + " → step3"}


builder = StateGraph(State)

builder.add_node("step1", step1)
builder.add_node("step2", step2)
builder.add_node("step3", step3)

builder.add_edge(START, "step1")
builder.add_edge("step1", "step2")
builder.add_edge("step2", "step3")
builder.add_edge("step3", END)

graph = builder.compile()

result = graph.invoke({"text": "开始"})

print(result)
