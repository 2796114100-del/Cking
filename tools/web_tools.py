# tools/web_tools.py
# 联网搜索工具：用 DuckDuckGo 搜索互联网

from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """
    搜索互联网，返回搜索结果。
    当知识库没有相关信息时使用，比如最新资讯、实时价格、小众问题。
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return "没有搜索到相关结果。"

        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            snippet = r.get("body", "无摘要")
            link = r.get("href", "")
            output.append(f"【结果{i}】{title}\n{snippet}\n链接：{link}")

        return "\n\n".join(output)

    except Exception as e:
        return f"搜索出错：{e}"
