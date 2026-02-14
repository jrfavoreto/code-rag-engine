# Unified Indexing Architecture

## Overview

The code-rag-engine now implements **unified dual-output indexing** where vector and graph extraction happen during a **single repository walk**, eliminating redundant file processing.

### Architecture Pattern

```
Before (Inefficient - 2 passes):
┌─────────────────────────────────────┐
│ Pass 1: Repository Walk             │
│ └─ Files → Vector Index (ChromaDB)  │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ Pass 2: Repository Walk             │
│ └─ Files → Graph Analysis (SQLite)  │
└─────────────────────────────────────┘

After (Optimized - 1 pass):
┌──────────────────────────────────────────────────────────┐
│ Single Repository Walk                                   │
│ ├─ Code Files Loop:                                      │
│ │  ├─ Split for vectors → ChromaDB                       │
│ │  └─ Parse AST for relations → SQLite (same iteration) │
│ │                                                         │
│ └─ Text Files Loop:                                      │
│    └─ Split for vectors → ChromaDB                       │
└──────────────────────────────────────────────────────────┘
```

## Implementation Details

### Files Modified

#### 1. `app/indexer.py`
**Changes:**
- Added imports: `CodeGraphBuilder`, `GraphStorage`
- Added `graph_storage` and `graph_builder` initialization in `__init__`
- Refactored `index_repository()` method to:
  - Collect code and text files in single walk
  - Process code files with dual indexing (vector + graph)
  - Process text files with vector only
  - Return tuple: `(VectorStoreIndex, stats_dict)`

**Key Method:** `index_repository(repo_path, collection_name, exclude_dirs)`

Returns:
```python
stats = {
    "vector_chunks": int,      # Total chunks for vector search
    "graph_nodes": int,        # Code entities extracted (functions/classes)
    "graph_edges": int,        # Relations extracted (calls/imports)
    "files_processed": int,    # Total files indexed
    "collection_name": str
}
```

#### 2. `app/code_graph.py`
**Added Method:** `analyze_file(file_path, content, language, collection_name)`

- Analyzes single file for graph relations
- Parses Python AST for function/class definitions and calls
- Persists directly to GraphStorage
- Returns tuple: `(nodes_added, edges_added)`

**Usage in unified indexer:**
```python
graph_nodes, graph_edges = self.graph_builder.analyze_file(
    file_path=str(file_path),
    content=content,
    language=language,
    collection_name=collection_name
)
```

#### 3. `app/graph_storage.py`
**Added Method:** `clear_graphs(collection_name: str = None)`

- Clears graph data for specific collection or entire database
- Called at start of reindex to ensure clean state
- Filters by collection name in node/edge metadata

#### 4. `scripts/index_repo.py`
**Changes:**
- Updated to handle tuple return from `index_repository()`
- Displays unified statistics:
  ```
  Files processed: N
  Vector chunks: M
  Graph nodes: P
  Graph edges: Q
  ```

## Processing Flow

### Step 1: Collection Phase (Single Walk)

```
for file in repo:
  if file.suffix in code_languages:
    code_files.append(file)
  elif file.suffix in text_extensions:
    text_files.append(file)
```

### Step 2: Code File Processing (Dual Output)

```
for code_file in code_files:
  content = read_file(code_file)
  
  # VECTOR: Split for semantic chunks
  chunks = splitter.split_document(content)
  documents.append(chunks)
  
  # GRAPH: Extract code relations (SAME ITERATION)
  nodes, edges = graph_builder.analyze_file(
    file_path, content, language, collection_name
  )
  graph_storage.persist(nodes, edges)
```

### Step 3: Text File Processing (Vector Only)

```
for text_file in text_files:
  content = read_file(text_file)
  chunks = sentence_splitter.split_document(content)
  documents.append(chunks)
  # No graph extraction for text files
```

### Step 4: Vector Index Creation

```
chroma_collection = chroma_client.create_collection(collection_name)
vector_store = ChromaVectorStore(chroma_collection)
index = VectorStoreIndex(nodes=documents, storage_context=storage_context)
```

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| File I/O | 2 × file reads | 1 × file read |
| Parsing | Done twice | Done once |
| Memory | Peak during pass 2 | Steady throughout |
| Time | 2 walks + overhead | 1 walk only |
| Cache Efficiency | File cache flushed | File cache reused |

## Configuration

### From `app/config.py`:

```python
# Graph storage location
GRAPH_DB_PATH: str = str(Path("data/code_graph.db"))

# Vector processing (CodeSplitter)
USE_CODE_SPLITTER: bool = True
CODE_CHUNK_LINES: int = 40
CODE_CHUNK_OVERLAP: int = 15
CODE_MAX_CHARS: int = 1500

# Vector processing (fallback)
CHUNK_SIZE: int = 1024
CHUNK_OVERLAP: int = 20
```

## Testing

Run unified indexing:

```bash
python scripts/index_repo.py /path/to/repo --collection-name my_collection
```

Expected output:
```
============================================================
🚀 Indexing repository: /path/to/repo
📚 Collection: my_collection
============================================================

Found 45 code files + 12 text files
Total: 57 files

📝 Processing code files (vector + graph):
--------------------------------------------
  ✓ app/main.py
    └─ Vector: 8 chunks | Graph: 5 nodes, 12 edges
  ✓ app/utils.py
    └─ Vector: 5 chunks | Graph: 3 nodes, 6 edges
  ...

📖 Processing text files (vector only):
--------------------------------------------
  ✓ README.md: 3 chunks
  ✓ docs/API.md: 5 chunks
  ...

============================================================
📊 Statistics:
  • Files processed: 57
  • Vector chunks: 247
  • Graph nodes: 120
  • Graph edges: 340
============================================================

✅ Indexing complete!
```

## Query Integration

After unified indexing, queries can:

1. **Vector Search** (semantic): Use ChromaDB vector store
   ```python
   results = index.as_query_engine().query("how does authentication work?")
   ```

2. **Graph Search** (structural): Use SQLite relations
   ```python
   graph_search = GraphSearchEngine(graph_storage)
   callers = graph_search.find_callers("authenticate_user")
   ```

3. **Hybrid Search** (combined): Route via QueryClassifier
   ```python
   classifier = QueryClassifier()
   query_type = classifier.classify("who calls authenticate?")
   # Result: GRAPH type → uses graph_search
   ```

## Performance Characteristics

**I/O Complexity:**
- File reads: O(n) where n = number of files (single pass)
- AST parsing: O(m) where m = total code lines
- Vector chunking: O(m) where m = total code lines

**Memory Usage:**
- Peak during vector index creation (stores all chunks)
- Graph storage: Streamed to SQLite (constant memory)

**Time Estimate (img-converter repo, 45 files):**
- File I/O: ~100ms
- AST parsing: ~200ms
- Vector chunking: ~300ms
- Vector indexing: ~1-2s
- **Total: 1.6-2.6 seconds**

## Future Optimizations

1. **Parallel Processing**: Process multiple files concurrently
2. **Incremental Indexing**: Only reprocess changed files
3. **Batch Graph Operations**: Buffer SQLite writes
4. **Lazy Vector Creation**: Stream to ChromaDB instead of buffering

## Architectural Notes

The unified approach maintains:
- **Separation of concerns**: Vector and graph remain independent
- **Modularity**: Each component (splitter, extractor) is swappable
- **Scalability**: Single pass enables efficient batch processing
- **Fault tolerance**: Errors in graph don't block vector indexing and vice-versa
