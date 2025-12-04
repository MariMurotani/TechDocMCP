import os
import sqlite3

import sqlite_vec
from mcp.server import Server
from mcp.server.stdio import stdio_server
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join(os.path.dirname(__file__), "techdocs.db")


async def search_docs(query: str, category: str = None, top_k: int = 5):
    """Search technical documentation using vector similarity"""
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    q_vec = model.encode(query).astype("float32")

    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    sql = """
        SELECT documents.path, documents.category,
               vec_distance_L2(doc_embeddings.embedding, ?) AS score
        FROM doc_embeddings
        JOIN documents ON doc_embeddings.rowid = documents.id
    """

    params = [q_vec.tobytes()]

    if category:
        sql += " WHERE documents.category = ?"
        params.append(category)

    sql += " ORDER BY score ASC LIMIT ?"
    params.append(top_k)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [{"path": r[0], "category": r[1], "score": float(r[2])} for r in rows]


async def main():
    server = Server("techdocs-mcp-server")

    @server.list_tools()
    async def list_tools():
        return [
            {
                "name": "search_docs",
                "description": "Search technical documentation (TypeScript, Python, CDK, Vue) using semantic search",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "category": {
                            "type": "string",
                            "enum": ["typescript", "python", "cdk", "vue"],
                            "description": "Optional: Filter by documentation category",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            }
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "search_docs":
            query = arguments["query"]
            category = arguments.get("category")
            top_k = arguments.get("top_k", 5)
            results = await search_docs(query, category, top_k)
            return [{"type": "text", "text": str(results)}]
        else:
            raise ValueError(f"Unknown tool: {name}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
