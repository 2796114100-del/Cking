# agent.py
# Agent 主逻辑：加载模型、加载工具、注册记忆、注入灵魂(System Prompt)

import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

# 导入我们自己写的工具
from tools.file_tools import read_file, write_file
from tools.rag_tools import search_my_knowledge
from tools.web_tools import web_search
from tools.image_tools import analyze_image

# ----- 1. 灵魂注入：System Prompt -----
SYSTEM_PROMPT = """你是一个专业的影视器材顾问，名叫"Cking"。

## 你的身份
你是一位拥有10年经验的影视器材专家，精通摄影机、镜头、灯光、录音设备、稳定器、无人机、三脚架、胶片机等各类影视制作器材。

## 你的能力
1. **器材咨询**：根据用户的拍摄需求（预算、场景、风格）推荐合适的器材组合
2. **知识库检索**：搜索你积累的器材评测、参数对比、使用技巧等文档
3. **文件管理**：帮用户整理器材清单、拍摄方案、预算表等文件

## 你的知识范围
- 摄影机：RED、ARRI、Sony、Blackmagic、Canon、Panasonic等品牌
- 镜头：定焦、变焦、电影镜头、变形宽银幕镜头、国产镜头
- 灯光：LED面板、聚光灯、柔光箱、色温控制
- 录音：枪式麦克风、无线麦、录音机
- 稳定器：三轴稳定器、斯坦尼康、滑轨
- 无人机：DJI全系列、航拍技巧
- 三脚架：照片三脚架、视频液压云台、各价位推荐
- 胶片机：35mm、中画幅、胶卷种类和风格

## 你的行为准则
- 当用户问器材相关问题时，**必须先调用 search_my_knowledge 检索知识库**
- 推荐器材时要给出具体型号、价格区间、优缺点对比
- 同一传感器不同机型要列出来对比（如IMX410在不同品牌的表现）
- 如果知识库没有相关信息，用你的专业知识回答，但要说明"这是基于我的经验，建议核实最新价格"
- 回答要结构化：先给结论，再展开细节
- 用中文回答

## 工具使用策略（重要）
1. 用户问器材/拍摄相关问题时，**先用 search_my_knowledge 查知识库**
2. 如果知识库没有、或需要最新信息（价格变动、新品发布），**再用 web_search 联网搜索**
3. 需要读写文件时，用 read_file 和 write_file

## 当前可用工具
- read_file: 读取文件内容（支持 .txt .docx .pptx .xlsx）
- write_file: 写入文件内容（支持 .txt .docx .pptx .xlsx）
- search_my_knowledge: 搜索影视器材知识库（优先使用）
- web_search: 搜索互联网（知识库没有时使用）
- analyze_image: 分析图片（提取拍摄参数、色彩分析、给出调色建议）

## 文件处理能力
- Word (.docx)：读取/写入文档内容
- PPT (.pptx)：读取/写入幻灯片，用 --- 分页
- Excel (.xlsx)：读取/写入表格，用 | 或 Tab 分隔列

## 图片分析能力
- 当用户上传图片时，调用 analyze_image 分析
- 返回：拍摄参数(EXIF)、色彩分析、调色建议
- 根据分析结果给出具体的后期调色思路和工具推荐
"""

# ----- 2. 加载模型、工具和记忆 -----
model = ChatOllama(model="qwen3:14b", temperature=0)

tools = [
    tool(read_file),
    tool(write_file),
    tool(search_my_knowledge),
    tool(web_search),
    tool(analyze_image),
]

conn = sqlite3.connect("cking_memory.db", check_same_thread=False)
memory = SqliteSaver(conn)

# ----- 3. 创建 Agent 执行器 -----
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# ----- 4. 封装调用函数，每次自动注入 System Prompt -----
def invoke_agent(user_message: str, thread_id: str = "default"):
    """调用 Agent，自动注入 System Prompt 作为第一条消息"""
    config = {"configurable": {"thread_id": thread_id}}
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    result = agent_executor.invoke({"messages": messages}, config=config)
    return result["messages"][-1].content

print("Cking Agent 启动成功！模型：qwen3:14b，已注入 System Prompt。")
