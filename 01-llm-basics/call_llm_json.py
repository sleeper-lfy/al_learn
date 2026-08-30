"""call_llm_json.py：JSON / 结构化输出。

对应学习点：Structured Output、JSON Output。

结构化输出 = 约束 + 校验，两步缺一不可：
1. 约束：format 传 JSON Schema（或 "json"），让模型按结构生成
2. 校验：json.loads 解析 + 检查必需字段，失败要能报错/重试
"""

import json

import requests

URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:1.7b"
TIMEOUT = 120

SCHEMA = {
    "type": "object",
    "properties": {
        "project_name": {"type": "string"},
        "platforms": {"type": "array", "items": {"type": "string"}},
        "key_features": {"type": "array", "items": {"type": "string"}},
        "estimated_months": {"type": "integer"},
    },
    "required": ["project_name", "platforms", "key_features", "estimated_months"],
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "你是需求分析师，只输出符合要求的 JSON。"},
        {
            "role": "user",
            "content": "把需求抽取成 JSON：给公司内部做一个报销审批系统，"
            "支持手机端，审批流可配置，预计 3 个月交付。",
        },
    ],
    "stream": False,
    "format": SCHEMA,  # 约束层：JSON Schema 强制结构
}

response = requests.post(URL, json=payload, timeout=TIMEOUT)
response.raise_for_status()
content = response.json()["message"]["content"]

# 校验层 1：必须是合法 JSON
try:
    data = json.loads(content)
except json.JSONDecodeError as exc:
    print("模型输出不是合法 JSON，需要重试或加强约束。原文：")
    print(content)
    raise SystemExit(1) from exc

# 校验层 2：必需字段齐全
missing = set(SCHEMA["required"]) - set(data)
if missing:
    print(f"缺少必需字段：{missing}")
    raise SystemExit(1)

print(json.dumps(data, ensure_ascii=False, indent=2))
