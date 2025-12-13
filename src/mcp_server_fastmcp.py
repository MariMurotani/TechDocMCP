import os
import sqlite3
import logging
from typing import Optional
import re

import sqlite_vec
from fastmcp import FastMCP
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "mcp_server_fastmcp.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("techdoc")

DB_PATH = os.path.join(os.path.dirname(__file__), "techdocs.db")

# Initialize FastMCP
mcp = FastMCP("techdoc")


def _search_docs_internal(query: str, category: str, top_k: int = 5) -> str:
    """Internal search function used by all tool variants."""
    logger.info(f"Search request - Query: '{query}', Category: {category}, Top K: {top_k}")
    
    # Load model and encode query
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    q_vec = model.encode(query).astype("float32")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    # Build SQL query
    sql = """
        SELECT documents.url, documents.category, documents.text, documents.path,
               vec_distance_L2(doc_embeddings.embedding, ?) AS score
        FROM doc_embeddings
        JOIN documents ON doc_embeddings.rowid = documents.id
        WHERE documents.category = ?
        ORDER BY score ASC LIMIT ?
    """

    params = [q_vec.tobytes(), category, min(top_k, 10)]

    # Execute query
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    if not rows:
        logger.info("No results found")
        return "No results found."

    def _path_to_url(path: str) -> str:
        # Convert /Users/.../docs/<category>/<domain>/<rest>.html -> https://<domain>/<rest>
        m = re.search(r"/docs/[^/]+/([^/]+)/(.*)$", path)
        if not m:
            return path
        domain, rest = m.group(1), m.group(2)
        if rest.endswith(".html"):
            rest = rest[:-5]
        elif rest.endswith(".md"):
            rest = rest[:-3]
        return f"https://{domain}/{rest}"

    # Format results
    formatted_results = []
    for i, (url, cat, text, path, score) in enumerate(rows, 1):
        eff_url = url or _path_to_url(path)
        content_preview = text[:1500] if len(text) > 1500 else text
        formatted_results.append(
            f"=== Result {i} (Score: {score:.4f}) ===\n"
            f"Category: {cat}\n"
            f"URL: {eff_url}\n\n"
            f"{content_preview}\n"
            f"{'...(truncated)' if len(text) > 1500 else ''}\n"
            f"{'='*80}\n"
        )
    
    logger.info(f"Found {len(rows)} results")
    return "\n".join(formatted_results)


@mcp.tool()
def pytool(query: str, top_k: int = 5) -> str:
    """Search Python documentation.
    
    Use this tool when users ask about Python topics like:
    - Decorators, classes, functions
    - Async/await, asyncio
    - Type hints, data structures
    - Standard library modules
    
    Args:
        query: The user's question about Python (e.g., 'Python decorators', 'asyncio usage')
        top_k: Number of results to return (1-10, default 5)
    
    Returns:
        Relevant Python documentation content
    """
    logger.info(f"pytool called with query='{query}', top_k={top_k}")
    return _search_docs_internal(query, "python", top_k)


@mcp.tool()
def tytool(query: str, top_k: int = 5) -> str:
    """Search TypeScript documentation.
    
    Use this tool when users ask about TypeScript topics like:
    - Generics, types, interfaces
    - Classes, functions, modules
    - Type inference, utility types
    - Enums, decorators
    
    Args:
        query: The user's question about TypeScript (e.g., 'TypeScript generics', 'interface vs type')
        top_k: Number of results to return (1-10, default 5)
    
    Returns:
        Relevant TypeScript documentation content
    """
    logger.info(f"tytool called with query='{query}', top_k={top_k}")
    return _search_docs_internal(query, "typescript", top_k)


@mcp.tool()
def cdktool(query: str, top_k: int = 5) -> str:
    """Search AWS CDK documentation.
    
    Use this tool when users ask about AWS CDK topics like:
    - Constructs, stacks, apps
    - Lambda functions, S3 buckets
    - API Gateway, DynamoDB
    - CDK best practices
    
    Args:
        query: The user's question about AWS CDK (e.g., 'CDK Lambda function', 'CDK stack deployment')
        top_k: Number of results to return (1-10, default 5)
    
    Returns:
        Relevant AWS CDK documentation content
    """
    logger.info(f"cdktool called with query='{query}', top_k={top_k}")
    return _search_docs_internal(query, "cdk", top_k)


@mcp.tool()
def vuetool(query: str, top_k: int = 5) -> str:
    """Search Vue.js documentation.
    
    Use this tool when users ask about Vue.js topics like:
    - Components, composables
    - Composition API, Options API
    - Reactivity, refs, computed
    - Vue Router, Pinia
    
    Args:
        query: The user's question about Vue.js (e.g., 'Vue composables', 'Vue reactivity system')
        top_k: Number of results to return (1-10, default 5)
    
    Returns:
        Relevant Vue.js documentation content
    """
    logger.info(f"vuetool called with query='{query}', top_k={top_k}")
    return _search_docs_internal(query, "vue", top_k)


@mcp.tool()
def awstool(query: str, top_k: int = 5) -> str:
    """Search AWS Design documentation.
    
    Use this tool when users ask about AWS Design topics like:
    - AWS architecture patterns
    - Best practices and design principles
    - Well-Architected Framework
    - Service design and integration
    
    Args:
        query: The user's question about AWS Design (e.g., 'AWS architecture patterns', 'Well-Architected Framework')
        top_k: Number of results to return (1-10, default 5)
    
    Returns:
        Relevant AWS Design documentation content
    """
    logger.info(f"awstool called with query='{query}', top_k={top_k}")
    return _search_docs_internal(query, "aws_design", top_k)


if __name__ == "__main__":
    logger.info("techdoc FastMCP server starting...")
    logger.info(f"Database path: {DB_PATH}")
    logger.info(f"Database exists: {os.path.exists(DB_PATH)}")
    
    # Run the server
    mcp.run()
