from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver


class State(TypedDict):
    count: int


def increment(state: State):
    return {"count": state["count"] + 1}


if __name__ == '__main__':
    builder = StateGraph(State)

    builder.add_node("increment", increment)

    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)
    config = {"configurable": {"thread_id": "user-001"}}

    with SqliteSaver.from_conn_string("data/checkpoint.db") as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        state = graph.get_state(config)
        print("Checkpoint：", state.values)

        result = graph.invoke({"count": 0}, config=config)

        print("执行结果：", result)

        state = graph.get_state(config)

        print("Checkpoint：", state.values)
