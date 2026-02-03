#!/usr/bin/env python3
"""
Example usage script for the Code RAG Engine.

This script demonstrates how to use the Code RAG Engine in your own projects.
Note: Requires network access to download embedding models on first run.
"""
import sys
from pathlib import Path

# Example 1: Simple API usage demonstration
def example_api_usage():
    """Show example API usage."""
    print("=" * 60)
    print("Example 1: Using the REST API")
    print("=" * 60)
    print("""
# 1. Start the API server
python -m app.api

# 2. Query the code repository (in another terminal)
curl -X POST "http://localhost:8000/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How does authentication work?",
    "similarity_top_k": 5,
    "return_context_only": true
  }'

# 3. Get formatted context for external LLM
curl "http://localhost:8000/context?query=login+function&top_k=3"
    """)


# Example 2: Python usage demonstration
def example_python_usage():
    """Show example Python usage."""
    print("\n" + "=" * 60)
    print("Example 2: Using Python directly")
    print("=" * 60)
    print("""
from app.query_engine import CodeQueryEngine

# Create query engine
engine = CodeQueryEngine(collection_name="code_repository")

# Get relevant context
result = engine.query(
    query="How does authentication work?",
    similarity_top_k=5,
    return_context_only=True
)

# Print results
for item in result['context']:
    print(f"File: {item['file_path']} (Score: {item['score']:.3f})")
    print(f"Code: {item['text'][:200]}...")
    print()

# Or get formatted context for external LLM
context = engine.retrieve_context(
    query="How does authentication work?",
    similarity_top_k=5
)
# Now use 'context' with your favorite LLM (GPT-4, Claude, etc.)
    """)


# Example 3: Indexing workflow
def example_indexing():
    """Show indexing workflow."""
    print("\n" + "=" * 60)
    print("Example 3: Indexing a Repository")
    print("=" * 60)
    print("""
# Method 1: Using the CLI script
python scripts/index_repo.py /path/to/your/repo

# Method 2: Using the CLI script with options
python scripts/index_repo.py /path/to/your/repo \\
    --collection-name my_project \\
    --exclude tests docs build

# Method 3: Using Python directly
from app.indexer import CodeIndexer

indexer = CodeIndexer()
index = indexer.index_repository(
    repo_path="/path/to/your/repo",
    collection_name="my_project",
    exclude_dirs=["tests", "docs", "build"]
)
print("Repository indexed successfully!")
    """)


# Example 4: Use cases
def example_use_cases():
    """Show practical use cases."""
    print("\n" + "=" * 60)
    print("Example 4: Practical Use Cases")
    print("=" * 60)
    print("""
# Use Case 1: Understanding a feature
engine = CodeQueryEngine()
result = engine.query("How does the caching system work?")

# Use Case 2: Finding implementations
context = engine.retrieve_context("Where is email validation implemented?")
# Use this context with your LLM of choice

# Use Case 3: Debugging
result = engine.query("Where can 'connection timeout' error occur?")

# Use Case 4: Code review assistance
result = engine.query("Find all authentication-related code")

# Use Case 5: Documentation generation
context = engine.retrieve_context("Get all API endpoint definitions")
# Feed to LLM: "Generate API documentation for: {context}"
    """)


# Example 5: Configuration
def example_configuration():
    """Show configuration options."""
    print("\n" + "=" * 60)
    print("Example 5: Configuration")
    print("=" * 60)
    print("""
# Create a .env file in the project root:
DATA_DIR=data
CHROMA_DIR=data/chroma
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
API_HOST=0.0.0.0
API_PORT=8000
SIMILARITY_TOP_K=5

# Or configure programmatically:
from app.config import settings

settings.CHUNK_SIZE = 1024
settings.SIMILARITY_TOP_K = 10
    """)


def main():
    """Run all examples."""
    print("\n")
    print("*" * 60)
    print("Code RAG Engine - Usage Examples")
    print("*" * 60)
    
    example_api_usage()
    example_python_usage()
    example_indexing()
    example_use_cases()
    example_configuration()
    
    print("\n" + "=" * 60)
    print("Getting Started")
    print("=" * 60)
    print("""
1. Install dependencies:
   pip install -r requirements.txt

2. Index your repository:
   python scripts/index_repo.py /path/to/your/repo

3. Start the API (optional):
   python -m app.api

4. Query your code:
   - Via API: See Example 1 above
   - Via Python: See Example 2 above

For more information, see README.md
    """)


if __name__ == "__main__":
    main()
