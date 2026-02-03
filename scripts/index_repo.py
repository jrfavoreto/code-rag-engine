#!/usr/bin/env python3
"""
Script to index a code repository for RAG.

Usage:
    python scripts/index_repo.py /path/to/repository [--collection-name name]
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.indexer import CodeIndexer


def main():
    """Main function to index a repository."""
    parser = argparse.ArgumentParser(
        description="Index a code repository for RAG"
    )
    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the code repository to index"
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="code_repository",
        help="Name for the ChromaDB collection (default: code_repository)"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        help="Additional directories to exclude from indexing"
    )
    
    args = parser.parse_args()
    
    # Validate repository path
    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    if not repo_path.is_dir():
        print(f"Error: Repository path is not a directory: {repo_path}")
        sys.exit(1)
    
    # Create indexer
    print("Initializing Code RAG Indexer...")
    indexer = CodeIndexer()
    
    # Prepare exclusions - always start with defaults
    exclude_dirs = [
        "__pycache__", "node_modules", ".git", ".venv", "venv",
        "env", "build", "dist", ".pytest_cache", ".mypy_cache",
        ".tox", "htmlcov", ".eggs", "*.egg-info"
    ]
    
    # Add any additional exclusions from command line
    if args.exclude:
        exclude_dirs.extend(args.exclude)
    
    # Index repository
    try:
        print(f"\nIndexing repository: {repo_path}")
        print(f"Collection name: {args.collection_name}\n")
        
        index = indexer.index_repository(
            repo_path=str(repo_path),
            collection_name=args.collection_name,
            exclude_dirs=exclude_dirs
        )
        
        print("\n✓ Repository indexed successfully!")
        print(f"Collection: {args.collection_name}")
        print("\nYou can now query the repository using:")
        print("  - The FastAPI server: python -m app.api")
        print("  - Or directly with CodeQueryEngine in Python")
        
    except Exception as e:
        print(f"\n✗ Error indexing repository: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
