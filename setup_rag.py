# setup_rag.py
from rag.vector_store import build_index

if __name__ == "__main__":
    build_index(doc_folder="./docs", db_path="./chroma_db")
    print("知识库索引建立完成！")