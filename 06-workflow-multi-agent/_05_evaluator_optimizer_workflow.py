from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# =========================
# 1. 定义 State
# =========================

class State(TypedDict):
    query: str
    answer: str
    evaluation: str
    iteration: int


MAX_ITERATIONS = 3


# =========================
# 2. Generate
# =========================

def generate_node(state: State):
    iteration = state["iteration"]

    print(f"\n===== Generate 第 {iteration} 次 =====")

    # 为了演示循环，这里故意让前两次生成“不合格”
    if iteration == 1:
        answer = "立法法是我国的一部法律。"
    elif iteration == 2:
        answer = "《中华人民共和国立法法》规定了立法活动的基本制度。"
    else:
        answer = ("《中华人民共和国立法法》是规范立法活动、"
                  "完善国家立法制度的重要法律。")

    print("生成答案：", answer)
    return {"answer": answer}


# =========================
# 3. Evaluate
# =========================

def evaluate_node(state: State):
    answer = state["answer"]

    print("\n===== Evaluate =====")

    # 简单模拟一个评估器
    if "立法活动" in answer and "法律" in answer:
        evaluation = "PASS"
    else:
        evaluation = "FAIL"

    print("评估结果：", evaluation)
    return {"evaluation": evaluation}


# =========================
# 4. Router
# =========================

def route_after_evaluate(state: State):
    # 如果已经达到最大次数
    if state["iteration"] >= MAX_ITERATIONS:
        print("\n达到最大迭代次数，强制结束")
        return "end"

    # Evaluator 判断
    if state["evaluation"] == "PASS":
        return "end"

    return "optimize"


# =========================
# 5. Optimize
# =========================

def optimize_node(state: State):
    print("\n===== Optimize =====")
    iteration = state["iteration"] + 1
    print("优化答案，准备重新生成")
    print("下一次 iteration：", iteration)
    return {"iteration": iteration}


# =========================
# 6. 构建 Graph
# =========================

builder = StateGraph(State)

builder.add_node("generate", generate_node)
builder.add_node("evaluate", evaluate_node)
builder.add_node("optimize", optimize_node)

# 开始
builder.add_edge(START, "generate")

# Generate → Evaluate
builder.add_edge("generate", "evaluate")

# Evaluate → 根据结果选择路径
builder.add_conditional_edges("evaluate", route_after_evaluate, {"optimize": "optimize", "end": END})

# Optimize → Generate
builder.add_edge("optimize", "generate")

graph = builder.compile()

# =========================
# 7. 执行
# =========================

result = graph.invoke({"query": "中华人民共和国立法法的作用是什么？", "answer": "", "evaluation": "", "iteration": 1})

print("\n======================")
print("最终结果")
print("======================")

print("Answer:", result["answer"])
print("Iteration:", result["iteration"])
print("Evaluation:", result["evaluation"])
