# rag/vector_store.py
# 最终版：直接用 chromadb 原生客户端 + requests 调 Ollama API

import os
import requests
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

OLLAMA_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"

def get_embedding(text: str):
    """返回 Ollama 生成的单个向量（一维列表）"""
    resp = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "input": text})
    resp.raise_for_status()
    data = resp.json()
    return data["embeddings"][0]   # 取第一个向量，一维列表

def build_index(doc_folder: str, db_path: str):
    docs = []
    for root, _, files in os.walk(doc_folder):
        for file in files:
            if file.endswith(('.txt', '.md', '.py')):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                docs.append(Document(page_content=text, metadata={"source": file}))

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    # 用原生 chromadb 客户端
    client = chromadb.PersistentClient(path=db_path)
    try:
        client.delete_collection("my_knowledge")
    except:
        pass
    collection = client.create_collection("my_knowledge")

    for i, chunk in enumerate(chunks):
        text = chunk.page_content
        source = chunk.metadata.get("source", "未知")
        emb = get_embedding(text)
        collection.add(
            embeddings=[emb],
            documents=[text],
            metadatas=[{"source": source}],
            ids=[f"chunk_{i}"]
        )
        if (i + 1) % 10 == 0:
            print(f"已处理 {i+1}/{len(chunks)} 块...")

    print(f"知识库索引建立完成！共 {len(chunks)} 块。")

def load_index(db_path: str):
    client = chromadb.PersistentClient(path=db_path)
    return client.get_collection("my_knowledge")

def search_knowledge(query: str, db_path: str) -> str:
    collection = load_index(db_path)
    q_emb = get_embedding(query)
    results = collection.query(query_embeddings=[q_emb], n_results=3)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    if not docs:
        return "知识库中没有找到相关内容。"
    out = []
    for i, d in enumerate(docs):
        src = metas[i].get("source", "未知") if metas else "未知"
        out.append(f"【资料{i+1} 来源：{src}】\n{d}")
    return "\n\n".join(out)