# mcp_server.py
# MCP Server：用标准协议暴露文件读写和知识库搜索工具

from mcp.server.fastmcp import FastMCP
from tools.file_tools import read_file, write_file
from tools.rag_tools import search_my_knowledge
from tools.web_tools import web_search
from tools.image_tools import analyze_image

# 创建 MCP 服务器实例
mcp = FastMCP(
    "Cking",
    instructions="一个能读写本地文件和搜索私有知识库的AI助手"
)

# ----- 注册工具 -----

@mcp.tool()
def read_file_tool(file_path: str) -> str:
    """读取指定路径的文件内容。支持 .txt 和 .docx Word文档格式。"""
    return read_file(file_path)

@mcp.tool()
def write_file_tool(file_path: str, content: str) -> str:
    """将内容写入指定路径的文件（覆盖写入）。支持 .txt 和 .docx Word文档格式。"""
    return write_file(file_path, content)

@mcp.tool()
def search_knowledge_tool(query: str) -> str:
    """搜索私有知识库，返回相关文档片段"""
    return search_my_knowledge(query)

@mcp.tool()
def web_search_tool(query: str) -> str:
    """搜索互联网，返回搜索结果。当知识库没有相关信息时使用。"""
    return web_search(query)

@mcp.tool()
def analyze_image_tool(image_path: str) -> str:
    """分析图片：提取拍摄参数(EXIF)、色彩分析、给出调色建议。传入图片文件路径。"""
    return analyze_image(image_path)

# ----- 启动 -----
if __name__ == "__main__":
    mcp.run(transport="stdio")