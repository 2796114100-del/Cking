# tools/rag_tools.py
# 把 RAG 搜索包装成 Agent 可以调用的工具

from rag.vector_store import search_knowledge

# 知识库存放路径，我们后面会在配置里统一管理，先写死
DB_PATH = "./chroma_db"

def search_my_knowledge(query: str) -> str:
    """
    搜索我提供的私有知识库，返回与问题相关的文档片段。
    当你需要查找技术资料、背景知识、或者我提供的文档内容时，请使用这个工具。
    """
    return search_knowledge(query, DB_PATH)