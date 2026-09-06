from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    query: str
    research_result: str
    analysis_result: str
    final_answer: str
    next_agent: str


def research_agent(state: State):
    print("\n===== Research Agent =====")
    result = "找到《立法法》第六条、第七条等相关条文。"
    return {"research_result": result}


def analysis_agent(state: State):
    print("\n===== Analysis Agent =====")
    research = state["research_result"]
    result = f"根据检索结果进行法律原则分析：{research}"
    return {"analysis_result": result}


def writer_agent(state: State):
    print("\n===== Writer Agent =====")
    analysis = state["analysis_result"]
    result = f"最终法律分析报告：{analysis}"
    return {"final_answer": result}


def supervisor(state: State):
    print("\n===== Supervisor =====")
    if not state["research_result"]:
        next_agent = "research"
    elif not state["analysis_result"]:
        next_agent = "analysis"
    else:
        next_agent = "writer"

    print("下一步 Agent：", next_agent)
    return {"next_agent": next_agent}


def route_agent(state: State):
    return state["next_agent"]


builder = StateGraph(State)

builder.add_node("supervisor", supervisor)
builder.add_node("research", research_agent)
builder.add_node("analysis", analysis_agent)
builder.add_node("writer", writer_agent)

# START → Supervisor
builder.add_edge(START, "supervisor")

# Supervisor → Agent

# Supervisor
#     ↓
# Research
#     ↓
# 回到 Supervisor
#     ↓
# Analysis
#     ↓
# 回到 Supervisor
#     ↓
# Writer
#     ↓
# break / END
builder.add_conditional_edges("supervisor", route_agent,
    {"research": "research", "analysis": "analysis", "writer": "writer"})

# Agent → Supervisor

builder.add_edge("research", "supervisor")
builder.add_edge("analysis", "supervisor")

# Writer 完成后结束
builder.add_edge("writer", END)

graph = builder.compile()

result = graph.invoke({
    "query": "分析《中华人民共和国立法法》的立法原则",
    "research_result": "",
    "analysis_result": "",
    "final_answer": "",
    "next_agent": ""
})

print("\n========== 最终答案 ==========")
print(result["final_answer"])
