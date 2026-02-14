# Graph Search - Fase 3 Implementation

## 📋 O que foi implementado

### 1. **GraphStorage** (`app/graph_storage.py`)
Camada de persistência em SQLite para grafo de dependências.

**Tabelas:**
- `nodes`: Funções, classes, módulos
- `edges`: Relações entre nodes (calls, imports, inherits)
- `graph_metadata`: Informações de meta-índice

**Operações:**
- CRUD de nodes e edges
- Query predecessors (quem chama)
- Query successors (o que é chamado)
- Análise de cadeias de chamadas (BFS)

### 2. **CodeGraphBuilder** (`app/code_graph.py`)
Extrator de relações de código usando Python AST.

**Suporta:**
- Definições de funções e classes
- Chamadas de funções
- Importações
- Assinaturas de funções

**Método principal:**
```python
builder = CodeGraphBuilder()
stats = builder.index_repository(repo_path)
# Total de nodes e edges extraídos
```

### 3. **GraphSearchEngine** (`app/graph_search.py`)
Engine para queries de grafo.

**Queries suportadas:**
- `find_callers()` - Quem chama uma função?
- `find_calls()` - O que uma função chama?
- `find_call_chain()` - Cadeia de chamadas (BFS)
- `get_impact_analysis()` - Se mudar isso, quem é afetado?
- `search()` - Query em linguagem natural

### 4. **Script de Teste** (`scripts/test_graph_search.py`)
Demonstra construção e queries do grafo.

## 🎯 Como Usar

### Test 1: Construir Grafo
```powershell
python scripts/test_graph_search.py
```

Testa:
1. Indexação do repositório
2. Extração de 100+ nodes e edges
3. Queries de exemplo

**Saída esperada:**
```
✓ Indexação completa!
  - Nodes extraídos: 42
  - Edges extraídos: 89
  - Arquivos processados: 9

📊 Estatísticas do Grafo:
  - Nodes por tipo: {'function': 40, 'class': 2}
  - Edges por tipo: {'calls': 85, 'imports': 4}
```

### Test 2: Queries Manuais
```powershell
python scripts/test_graph_search.py
# Selecione "Interactive Mode"

❓ Query: Quem chama compress_pdf()?
📊 Resultados (callers):
   • process_file - def process_file(...)
```

### Test 3: Uso Programático
```python
from app.code_graph import CodeGraphBuilder
from app.graph_search import GraphSearchEngine

# Indexar repo
builder = CodeGraphBuilder()
builder.index_repository(r"C:\meu_repo")

# Buscar relações
engine = GraphSearchEngine()
callers = engine.find_callers("compress_pdf")
chain = engine.find_call_chain("compress_pdf", max_depth=5)
impact = engine.get_impact_analysis("compress_pdf")
```

## 📊 Estrutura de Dados

### Node
```json
{
  "id": "path/to/file.py:function_name",
  "name": "function_name",
  "type": "function",  // ou "class", "module"
  "file_path": "path/to/file.py",
  "line_number": 42,
  "signature": "def function_name(arg1, arg2)"
}
```

### Edge
```json
{
  "source_id": "path/to/file.py:compress_pdf",
  "target_id": "path/to/file.py:process_file",
  "relation_type": "calls"  // ou "imports", "inherits"
}
```

## 🔄 Fluxo de Execução

```
Repository Path
    ↓
CodeGraphBuilder.index_repository()
    ↓
Parse cada arquivo Python com AST
    ↓
Extrair nodes (definições) + edges (relações)
    ↓
GraphStorage.add_node() / add_edge()
    ↓
Salvar em SQLite (data/code_graph.db)
    ↓
GraphSearchEngine.search()
    ↓
Retornar resultados (callers, chain, impact)
```

## 📈 Exemplos de Queries

### "Quem chama compress_pdf()?"
```python
engine.find_callers("compress_pdf")
→ [
    {"name": "process_file", "type": "function", ...},
    {"name": "main", "type": "function", ...}
  ]
```

### "Qual é a cadeia de chamadas de main()?"
```python
engine.find_call_chain("main", max_depth=5)
→ [
    {"depth": 0, "function": "main", ...},
    {"depth": 1, "function": "process_file", ...},
    {"depth": 2, "function": "compress_pdf", ...},
    {"depth": 3, "function": "os.remove", ...}
  ]
```

### "Se eu mudar compress_pdf(), quem é afetado?"
```python
engine.get_impact_analysis("compress_pdf")
→ {
    "function": "compress_pdf",
    "direct_callers": 2,
    "indirect_impact": 5,
    "affected_functions": ["process_file", "main"],
    "chain": [...]
  }
```

## 💾 Armazenamento

Arquivo: `data/code_graph.db`

**Vantagens SQLite:**
- ✅ Persistente (não perde ao desligar)
- ✅ Rápido para repos médios
- ✅ Queries SQL poderosas
- ✅ Zero dependências externas
- ✅ Fácil de backupear

**Desvantagens:**
- ❌ Menos otimizado que Neo4j para grafos muito grandes
- ❌ Queries complexas precisam mais JOINs

**Migração futura:**
Quando repo crescer, migrar para Neo4j:
```python
# Fase 5: Neo4j Migration
from app.graph_neo4j import GraphNeo4jStorage
storage = GraphNeo4jStorage("bolt://localhost:7687")
```

## 🚀 Integração com Query Classifier

O Query Classifier agora roteia queries GRAPH para o GraphSearchEngine:

```python
from app.query_classifier import QueryClassifier, QueryType
from app.graph_search import GraphSearchEngine

query = "Quem chama compress_pdf()?"
query_type = QueryClassifier.classify(query)

if query_type == QueryType.GRAPH:
    engine = GraphSearchEngine()
    results = engine.search(query)
elif query_type == QueryType.SEMANTIC:
    # Vector search (original)
    ...
```

## 📊 Status

✅ **Implementado:**
- Graph Storage (SQLite)
- Code Parser (Python AST)
- Graph Search Engine
- Node/Edge CRUD
- Caller/Callee finder
- Call chain analysis
- Impact analysis
- Integration com Query Classifier

⏳ **TODO (Fase 4+):**
- Suporte a JavaScript/TypeScript
- Neo4j migration
- Análise de data flow
- Análise de controle flow
- Visualização de grafo

## 🎓 Próximos Passos

1. ✅ **Implementado**: Query Classifier (Fase 2)
2. ✅ **Implementado**: Graph Search (Fase 3)
3. ⏳ **TODO**: Hybrid Search (Fase 4)
4. ⏳ **TODO**: MCP Server (Fase 5)

---

**Status**: Fase 3 ✅ CONCLUÍDA
**Qualidade**: ⭐⭐⭐⭐
**Próximo**: Hybrid Search (combinar Vector + Graph)
