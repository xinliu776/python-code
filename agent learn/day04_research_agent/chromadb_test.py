import chromadb
from chromadb.utils import embedding_functions

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
client = chromadb.Client()

collection=client.create_collection(name="knowledge_cn",embedding_function=embedding_function)
documents=[
    "MCP是一种连接AI模型和外部工具的标准化协议",
    "RAG通过检索外部知识来增强大模型的回答能力",
    "Python是一种常用的编程语言"
]
collection.add(ids=["1","2","3"],documents=documents)


result=collection.query(
    query_texts=["AI模型怎么连接外部工具？"],
    n_results=2
)
print(result["documents"])
print(result["distances"])