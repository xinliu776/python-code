from mcp.server import MCPServer
import chromadb
from chromadb.utils import embedding_functions


query = "AI模型怎样连接外部工具？"

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
client = chromadb.PersistentClient(
    path="./chroma_db"
)
documents=[
"MCP是一种连接AI模型和外部工具的标准化协议",
"RAG通过检索外部知识来增强大模型的回答能力",
"Python是一种常用的编程语言"
]
collection = client.get_or_create_collection(
    name="knowledge_cn",
    embedding_function=embedding_function
)
if collection.count()==0:
   collection.add(ids=["1","2","3"],documents=documents)

mcp=MCPServer("calculator")
@mcp.tool()
def retrieve(
    query: str,
    n_results: int = 2,
    threshold: float = 0.5
) -> list[str]:

    result=collection.query(
        query_texts=[query],
        n_results=n_results
    )
    best_result=[]
    for document, distance in zip(
    result["documents"][0],
    result["distances"][0]
    ):
        if distance<threshold:
            best_result.append(document)
    return best_result
