import os
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server

# 親ディレクトリをパスに追加してインポート
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence import SQLiteDocumentRepository
from infrastructure.models import EmbeddingModel
from application.use_cases import SearchDocumentsUseCase, SearchDocumentsRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "mcp_server.log")),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("techdoc")

DB_PATH = os.path.join(os.path.dirname(__file__), "techdocs.db")

# 依存性を初期化
_repository = SQLiteDocumentRepository(DB_PATH)
_embedding_model = EmbeddingModel()
_search_use_case = SearchDocumentsUseCase(_repository, _embedding_model)


async def search_docs(query: str, category: str = None, top_k: int = 5):
    """Search technical documentation using vector similarity"""
    logger.info(f"Search request - Query: '{query}', Category: {category}, Top K: {top_k}")
    
    # ユースケースを実行
    request = SearchDocumentsRequest(query=query, category=category, top_k=top_k)
    response = _search_use_case.execute(request)

    # レスポンスをフォーマット
    results = [
        {
            "path": result.path,
            "category": result.category,
            "content": result.text,
            "score": result.score
        }
        for result in response.results
    ]
    logger.info(f"Found {len(results)} results")
    
    return results


async def main():
    logger.info("Starting techdoc MCP server...")
    server = Server(
        "techdoc",
        version="1.0.0"
    )

    @server.list_resources()
    async def list_resources():
        """Provide information about available documentation"""
        logger.info("list_resources called")
        return [
            {
                "uri": "techdoc://search",
                "name": "Technical Documentation Search",
                "description": "Search across TypeScript, Python, AWS CDK, and Vue documentation using semantic search",
                "mimeType": "application/json"
            }
        ]

    @server.list_tools()
    async def list_tools():
        logger.info("list_tools called")
        return [
            {
                "name": "search_docs",
                "description": "**IMPORTANT: Use this tool for ALL questions about TypeScript, Python, AWS CDK, or Vue.js.** Searches indexed local documentation and returns relevant content. Use when users ask about: TypeScript (generics, types, interfaces, classes), Python (decorators, async, functions), AWS CDK (constructs, stacks, Lambda), Vue.js (components, composables, reactivity). Always prefer this tool over general knowledge for these topics.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The user's question or search terms",
                        },
                        "category": {
                            "type": "string",
                            "enum": ["typescript", "python", "cdk", "vue"],
                            "description": "Filter by category: typescript, python, cdk, or vue",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results (1-10, default 5)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10
                        },
                    },
                    "required": ["query"],
                },
            }
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        logger.info(f"call_tool invoked - Tool: {name}, Arguments: {arguments}")
        if name == "search_docs":
            query = arguments["query"]
            category = arguments.get("category")
            top_k = arguments.get("top_k", 5)
            results = await search_docs(query, category, top_k)
            
            # Format results as readable text
            if not results:
                logger.info("No results found")
                return [{"type": "text", "text": "No results found."}]
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                content_preview = result["content"][:1500] if len(result["content"]) > 1500 else result["content"]
                formatted_results.append(
                    f"=== Result {i} (Score: {result['score']:.4f}) ===\n"
                    f"Category: {result['category']}\n"
                    f"Path: {result['path']}\n\n"
                    f"{content_preview}\n"
                    f"{'...(truncated)' if len(result['content']) > 1500 else ''}\n"
                    f"{'='*80}\n"
                )
            
            logger.info(f"Returning {len(formatted_results)} formatted results")
            return [{"type": "text", "text": "\n".join(formatted_results)}]
        else:
            logger.error(f"Unknown tool requested: {name}")
            raise ValueError(f"Unknown tool: {name}")

    logger.info("Starting server event loop...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    
    logger.info("techdoc MCP server starting...")
    logger.info(f"Database path: {DB_PATH}")
    logger.info(f"Database exists: {os.path.exists(DB_PATH)}")
    
    asyncio.run(main())
