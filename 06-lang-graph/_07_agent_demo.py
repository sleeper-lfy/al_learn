from typing import TypedDict

from langchain_ollama import ChatOllama

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

# ============================================================
# 1. LLM
# ============================================================

llm = ChatOllama(model="qwen3:1.7b", temperature=0)

# ============================================================
# 2. Memory
#
# 这里模拟一个长期 Memory。
#
# 真实项目中可以换成：
# InMemoryStore
# Redis
# PostgreSQL
# 向量数据库
# 等等
# ============================================================

memory_store = {"user-001": {"name": "张三", "job": "Java开发"}}


def get_memory(user_id: str):
    """
    获取用户长期记忆
    """
    return memory_store.get(user_id, {})


def update_memory(user_id: str, field: str, value: str):
    """
    修改用户长期记忆
    """
    if user_id not in memory_store:
        memory_store[user_id] = {}

    memory_store[user_id][field] = value

    return f"{field} 已修改为 {value}"


# ============================================================
# 3. State
# ============================================================

class State(TypedDict, total=False):
    # 用户身份
    user_id: str
    # 用户输入
    user_input: str
    # LLM 判断出来的意图
    intent: str
    # Tool 名称
    tool_name: str
    # Tool 参数
    tool_args: dict
    # 人工审核结果
    approved: bool
    # Tool 执行结果
    tool_result: str
    # Memory
    memory: dict
    # 最终回答
    final_answer: str


# ============================================================
# 4. Node：读取 Memory
# ============================================================

def load_memory(state: State):
    user_id = state["user_id"]
    memory = get_memory(user_id)
    print("\n========== Memory ==========")
    print(memory)

    return {"memory": memory}


# ============================================================
# 5. Node：LLM 判断
# 让 LLM 判断：
# 用户是在普通聊天？
# 还是想修改资料？
# ============================================================

def llm_decision(state: State):
    user_input = state["user_input"]
    memory = state.get("memory", {})
    prompt = f"""
你是一个用户资料管理 Agent。
当前用户资料：
{memory}
用户输入：
{user_input}
请判断用户意图。
只允许返回以下两个结果之一：
chat
update_profile
规则：
1. 如果用户只是询问信息，例如：
“我叫什么”
“我的职业是什么”
返回 chat
2. 如果用户要求修改自己的资料，例如：
“把我的职业改成 Python 开发”
返回 update_profile
只返回一个结果，不要解释。
"""

    response = llm.invoke(prompt)
    intent = response.content.strip()
    print("\n========== LLM Decision ==========")
    print("LLM:", intent)
    # 防止模型输出额外内容
    if "update_profile" in intent:
        intent = "update_profile"
    else:
        intent = "chat"
    # 如果是修改资料
    if intent == "update_profile":

        # Demo 为了简单，直接从用户输入中判断职业
        if "Python" in user_input:
            value = "Python开发"

        elif "Java" in user_input:
            value = "Java开发"

        elif "Go" in user_input:
            value = "Go开发"

        else:
            value = "未知"

        return {"intent": "update_profile", "tool_name": "update_profile",
            "tool_args": {"field": "job", "value": value}}

    return {"intent": "chat"}


# ============================================================
# 6. Conditional Edge
# LLM 决定：
# chat
# update_profile
# ============================================================

def route_intent(state: State):
    if state["intent"] == "update_profile":
        return "human_review"
    return "final_llm"


# ============================================================
# 7. Human Review
# 这里暂停 Graph
# ============================================================

def human_review(state: State):
    tool_name = state["tool_name"]
    tool_args = state["tool_args"]

    print("\n================================")
    print("⚠️  Human Review")
    print("================================")
    print("准备执行 Tool：", tool_name)
    print("Tool 参数：", tool_args)
    result = interrupt({"message": "Agent 请求修改用户资料，是否允许？", "tool": tool_name, "args": tool_args})
    return {"approved": result}


# ============================================================
# 8. Conditional Edge
# Human Review：
# True  → Tool
# False → Final LLM
# ============================================================

def route_approval(state: State):
    if state["approved"]:
        return "execute_tool"
    return "final_llm"


# ============================================================
# 9. Tool
# 真正修改 Memory
# ============================================================

def execute_tool(state: State):
    user_id = state["user_id"]
    field = state["tool_args"]["field"]
    value = state["tool_args"]["value"]
    print("\n========== Tool ==========")
    result = update_memory(user_id, field, value)
    print(result)
    return {"tool_result": result}


# ============================================================
# 10. Final LLM
# 最终生成用户看到的回答
# ============================================================

def final_llm(state: State):
    memory = get_memory(state["user_id"])
    tool_result = state.get("tool_result", "")
    approved = state.get("approved", True)
    prompt = f"""
你是一个友好的 AI 助手。
用户：
{state["user_input"]}
当前用户长期资料：
{memory}
Tool 执行结果：
{tool_result}
人工审核结果：
{approved}
请根据这些信息回答用户。
如果 Tool 执行成功，就告诉用户修改成功。
如果人工拒绝，就告诉用户这次修改没有执行。
如果只是普通问题，就直接根据用户资料回答。
不要提及：
State
Checkpoint
Thread
Graph
Tool
Memory
直接自然地回答用户。
"""

    response = llm.invoke(prompt)
    print("\n========== Final LLM ==========")
    return {"final_answer": response.content}


# ============================================================
# 11. 创建 Graph
# ============================================================

builder = StateGraph(State)

# Node

builder.add_node("load_memory", load_memory)

builder.add_node("llm_decision", llm_decision)

builder.add_node("human_review", human_review)

builder.add_node("execute_tool", execute_tool)

builder.add_node("final_llm", final_llm)

# ============================================================
# Edge
# ============================================================

builder.add_edge(START, "load_memory")
builder.add_edge("load_memory", "llm_decision")
# ============================================================
# Conditional Edge ①
# ============================================================

builder.add_conditional_edges("llm_decision", route_intent)
# Human Review
builder.add_conditional_edges("human_review", route_approval)

# Tool → Final LLM
builder.add_edge("execute_tool", "final_llm")

# Final
builder.add_edge("final_llm", END)

# ============================================================
# 12. Checkpointer
# ============================================================

checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# 13. Thread 001
# ============================================================

thread_001 = {"configurable": {"thread_id": "thread-001"}}

# ============================================================
# 14. 第一次对话
# ============================================================

print("\n\n")
print("########################################")
print("# Thread 001")
print("########################################")

result = graph.invoke({"user_id": "user-001", "user_input": "我叫什么"}, config=thread_001)

print("\nAI：")
print(result["final_answer"])

# ============================================================
# 15. 第二次对话
#
# 注意：
# 还是 thread-001
#
# 所以属于同一个 Thread
# ============================================================

result = graph.invoke({"user_id": "user-001", "user_input": "把我的职业改成 Python 开发"}, config=thread_001)

# 这里执行到 interrupt 后会暂停
#
# 所以这里不会得到最终结果
#
# 下面模拟人工批准
# ============================================================

print("\n\n等待人工确认...")

# ============================================================
# 16. Human Resume
# ============================================================

result = graph.invoke(Command(resume=True), config=thread_001)

print("\nAI：")
print(result["final_answer"])

# ============================================================
# 17. Thread 002
#
# 新的 Thread
# ============================================================

thread_002 = {"configurable": {"thread_id": "thread-002"}}

print("\n\n")
print("########################################")
print("# Thread 002")
print("########################################")

result = graph.invoke({"user_id": "user-001", "user_input": "我的职业是什么？"}, config=thread_002)

print("\nAI：")
print(result["final_answer"])

# ============================================================
# 18. 查看最终 Memory
# ============================================================

print("\n\n")
print("########################################")
print("# Final Memory")
print("########################################")

print(memory_store["user-001"])
