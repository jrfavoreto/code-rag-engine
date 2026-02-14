# Plano de Evolução - Code RAG Engine

## 🎯 Visão Geral

Evoluir o projeto para ser um **RAG e/ou MCP** com capacidades superiores ao Copilot, refinando o contexto de repositórios de código (legado ou recente) para fornecer contexto preciso a LLMs e Agentes que sirvam como assistentes para desenvolvedores e arquitetos.

## 🏗️ Arquitetura Proposta

```
Dev Question
     ↓
┌─────────────────────┐
│  Query Classifier   │  ← Decide estratégia
└─────────────────────┘
          ↓
     ┌────┴────┐
     │ Router  │
     └────┬────┘
          ↓
    ┌─────┴─────┬─────────┬─────────┐
    │           │         │         │
┌───▼────┐ ┌───▼────┐ ┌──▼─────┐ ┌─▼──────┐
│ Vector │ │ Graph  │ │ Hybrid │ │ Regex  │
│ Search │ │ Search │ │  Mix   │ │ Search │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │           │          │
    └──────────┴───────────┴──────────┘
               ↓
        Context Ranker
               ↓
        Prompt Builder
               ↓
             LLM
```

## 📊 Estratégias de Busca

### 1️⃣ Vector Search (atual - ✅ implementado)
- **Bom para:** Perguntas semânticas ("Como funciona autenticação?")
- **Tecnologia:** ChromaDB + Embeddings (Ollama/nomic-embed-text)
- **Status:** Funcional

### 2️⃣ Graph Search (novo - crítico!)
- **Bom para:** Relações de código
  - "Quais funções chamam compress_pdf()?"
  - "Trace o fluxo de login até o banco"
  - "Quais classes herdam de BaseModel?"
- **Estrutura do Grafo:**
  - **Nós:** funções, classes, módulos, variáveis
  - **Arestas:** imports, calls, inheritance, references
- **Tecnologias:**
  - `networkx` - construção e query do grafo
  - `tree-sitter` - parsing AST
  - Neo4j (opcional) - persistência de grafo

### 3️⃣ Hybrid Search (melhor dos dois mundos)
- **Combina:**
  - Vector: contexto semântico
  - Graph: relações estruturais
- **Reranking:** combina scores de ambas estratégias
- **Algoritmos:** RRF (Reciprocal Rank Fusion), weighted scoring

### 4️⃣ Regex/AST Search (precisão cirúrgica)
- **Bom para:** Queries específicas
  - "Mostre todas as funções que usam requests.post"
  - "Liste variáveis globais em auth.py"
  - "Encontre todos os decorators @cached"
- **Tecnologia:** AST + regex patterns

## 🚀 Plano de Implementação (Faseado)

### **Fase 1: Foundation (Status: 80% completo ✅)**

#### Concluído:
- [x] Vector search com ChromaDB
- [x] Embeddings com Ollama (nomic-embed-text)
- [x] LLM providers (Ollama/Gemini)
- [x] API REST com FastAPI
- [x] Query filtering (min_score, max_context_chars)
- [x] Multi-provider support (Ollama local + Gemini remoto)

#### Pendente:
- [ ] **CodeSplitter com Tree-sitter** ← **PRÓXIMO PASSO CRÍTICO**
  - Chunks semânticos (funções/classes completas)
  - Suporte multi-linguagem (Python, JS, Java, etc)
  - Fallback para SentenceSplitter em não-código

**Arquivos a criar/modificar:**
- `app/code_splitter.py` - novo módulo
- `app/indexer.py` - integrar CodeSplitter
- `requirements.txt` - adicionar tree-sitter

---

### **Fase 2: Query Intelligence**

#### Objetivos:
- Classificar tipo de query automaticamente
- Rotear para estratégia apropriada
- Detectar intenção do usuário

#### Implementação:

**1. Query Classifier**
```python
# app/query_classifier.py
from enum import Enum

class QueryType(Enum):
    SEMANTIC = "semantic"      # "Como funciona X?"
    GRAPH = "graph"           # "Quem chama X?"
    REGEX = "regex"           # "Mostre função X"
    HYBRID = "hybrid"         # Combinação

class QueryClassifier:
    def __init__(self):
        self.patterns = {
            'graph': ['quem chama', 'quais funções', 'trace', 'fluxo', 'dependências'],
            'regex': ['mostre função', 'liste', 'encontre todos'],
            'semantic': ['como funciona', 'o que faz', 'explique', 'por que']
        }
    
    def classify(self, query: str) -> QueryType:
        # Análise de padrões + ML classifier opcional
        pass
```

**2. Query Router**
```python
# app/query_router.py
class QueryRouter:
    def route(self, query: str, query_type: QueryType):
        if query_type == QueryType.SEMANTIC:
            return self.vector_search(query)
        elif query_type == QueryType.GRAPH:
            return self.graph_search(query)
        elif query_type == QueryType.HYBRID:
            return self.hybrid_search(query)
        elif query_type == QueryType.REGEX:
            return self.regex_search(query)
```

**Arquivos a criar:**
- `app/query_classifier.py`
- `app/query_router.py`
- `app/query_types.py` (enums e types)

**Tecnologias:**
- Pattern matching
- NLP básico (spaCy opcional)
- ML classifier (scikit-learn opcional)

---

### **Fase 3: Graph Layer (Game Changer)**

#### Objetivos:
- Construir grafo de código a partir de AST
- Query baseado em relações
- Integração com vector search

#### Implementação:

**1. Code Graph Builder**
```python
# app/code_graph.py
import networkx as nx
from tree_sitter import Language, Parser

class CodeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.parser = self._setup_parser()
    
    def build_graph(self, repo_path: str):
        """Constrói grafo a partir do repositório"""
        # 1. Parse AST de cada arquivo
        # 2. Extrai nós (funções, classes, etc)
        # 3. Extrai arestas (calls, imports, etc)
        # 4. Persiste no Neo4j ou networkx
        pass
    
    def query_graph(self, query: dict):
        """Query no estilo Cypher"""
        # MATCH (f:Function)-[:CALLS]->(target:Function {name: 'compress_pdf'})
        # RETURN f
        pass
    
    def find_callers(self, function_name: str):
        """Encontra quem chama uma função"""
        pass
    
    def trace_execution_path(self, start_fn: str, end_fn: str):
        """Traça caminho entre duas funções"""
        pass
```

**2. AST Parser**
```python
# app/ast_parser.py
from tree_sitter import Language, Parser

class ASTParser:
    SUPPORTED_LANGUAGES = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java'
    }
    
    def parse_file(self, file_path: str):
        """Parse arquivo e extrai estruturas"""
        # Retorna: funções, classes, imports, calls
        pass
    
    def extract_functions(self, tree):
        """Extrai definições de função"""
        pass
    
    def extract_calls(self, tree):
        """Extrai chamadas de função"""
        pass
```

**Arquivos a criar:**
- `app/code_graph.py`
- `app/ast_parser.py`
- `app/graph_queries.py` (queries pré-definidas)

**Tecnologias:**
- `tree-sitter` - parsing AST
- `tree-sitter-python`, `-javascript`, etc - linguagens
- `networkx` - grafo em memória
- `neo4j` (opcional) - persistência de grafo

**Dependências:**
```bash
pip install tree-sitter
pip install tree-sitter-python
pip install tree-sitter-javascript
pip install networkx
pip install py2neo  # se usar Neo4j
```

---

### **Fase 4: Hybrid Search + Reranking**

#### Objetivos:
- Combinar resultados de vector + graph
- Reranking inteligente
- Deduplicação de contexto

#### Implementação:

**1. Hybrid Retriever**
```python
# app/hybrid_retriever.py
class HybridRetriever:
    def retrieve(self, query: str):
        # 1. Vector search
        vector_results = self.vector_search(query)
        
        # 2. Graph search (se aplicável)
        graph_results = self.graph_search(query)
        
        # 3. Combina resultados
        combined = self.merge_results(vector_results, graph_results)
        
        # 4. Rerank
        reranked = self.rerank(combined, query)
        
        return reranked
```

**2. Reranker**
```python
# app/reranker.py
class ContextReranker:
    def rerank(self, results: list, query: str):
        """Reranking usando:
        - Similarity score
        - Graph importance (PageRank)
        - Recency
        - File importance
        """
        # RRF: Reciprocal Rank Fusion
        # score = sum(1 / (k + rank_i))
        pass
```

**Arquivos a criar:**
- `app/hybrid_retriever.py`
- `app/reranker.py`
- `app/fusion.py` (algoritmos de fusão)

**Algoritmos:**
- RRF (Reciprocal Rank Fusion)
- Weighted scoring
- Cross-encoder (opcional, mais lento)

---

### **Fase 5: MCP Server (IDE Integration)**

#### Objetivos:
- Integração com IDEs (VSCode, Cursor, Windsurf)
- Protocolo MCP (Model Context Protocol)
- Tools e Resources para agentes

#### Implementação:

**1. MCP Server**
```python
# app/mcp_server.py
from mcp import Server, Tool, Resource

server = Server("code-rag")

@server.tool()
async def analyze_code(file_path: str, query: str):
    """Analisa código e retorna contexto relevante"""
    pass

@server.tool()
async def trace_function(function_name: str):
    """Traça execução de função"""
    pass

@server.resource("code://context")
async def get_context(query: str):
    """Retorna contexto do repositório"""
    pass

if __name__ == "__main__":
    server.run()
```

**2. VSCode Extension (opcional)**
```typescript
// Integração com VSCode
// Permite queries diretas na IDE
```

**Arquivos a criar:**
- `app/mcp_server.py`
- `mcp_config.json`
- Documentação de integração

**Tecnologias:**
- MCP SDK
- Stdio transport
- WebSocket (opcional)

---

## 💡 Diferenciais vs GitHub Copilot

| Feature | GitHub Copilot | Code RAG Engine |
|---------|----------------|-----------------|
| **Contexto** | Janela limitada (~10KB) | Repositório completo |
| **Relações de código** | ❌ Não entende | ✅ Grafo de dependências |
| **Código legado** | ⚠️ Limitado | ✅ Indexado e navegável |
| **Privacidade** | ☁️ Cloud (Microsoft) | ✅ 100% Local |
| **Customização** | ❌ Fechado | ✅ Totalmente personalizável |
| **Multi-repo** | ❌ | ✅ Suporta múltiplos repos |
| **Análise estrutural** | ❌ | ✅ AST + Grafo |
| **LLM Choice** | GPT-4 apenas | ✅ Ollama, Gemini, qualquer |
| **Custo** | $10-20/mês | ✅ Grátis (se usar Ollama) |
| **Trace de execução** | ❌ | ✅ Path finding no grafo |

## 🎯 Prioridades de Implementação

### **Curto Prazo (1-2 semanas)**
1. ✅ **CodeSplitter + Tree-sitter** - Base sólida para chunking semântico
2. ⏳ **Query Classifier** - Inteligência básica de roteamento
3. ⏳ **AST Parser** - Preparação para grafo

### **Médio Prazo (1 mês)**
4. ⏳ **Code Graph** - Construção inicial do grafo
5. ⏳ **Graph Queries** - Queries básicas (callers, callees)
6. ⏳ **Hybrid Search** - Combinar vector + graph

### **Longo Prazo (2-3 meses)**
7. ⏳ **Context Reranker** - Refinamento de resultados
8. ⏳ **MCP Server** - Integração com IDEs
9. ⏳ **Multi-repo Support** - Indexar múltiplos repositórios
10. ⏳ **Advanced Analytics** - Métricas de código, complexidade

## 📚 Tecnologias e Dependências

### **Core Stack (atual)**
- Python 3.10+
- LlamaIndex
- ChromaDB
- FastAPI
- Ollama (embeddings + LLM local)
- Gemini (LLM remoto)

### **Novos Componentes**
```bash
# Parsing & AST
pip install tree-sitter
pip install tree-sitter-python
pip install tree-sitter-javascript
pip install tree-sitter-typescript
pip install tree-sitter-java

# Grafo
pip install networkx
pip install py2neo  # Neo4j client (opcional)

# NLP & ML (opcional)
pip install spacy
pip install scikit-learn

# MCP
pip install mcp
```

### **Infraestrutura (opcional)**
- Neo4j - Grafo persistente
- Redis - Cache
- PostgreSQL - Metadados

## 🔬 Casos de Uso Avançados

### **1. Análise de Impacto**
```
Query: "Se eu modificar a função login(), o que vai quebrar?"
↓
Graph Search: Encontra todos os callers de login()
↓
Vector Search: Contexto semântico dos callers
↓
LLM: Analisa impacto e sugere testes
```

### **2. Refactoring Assistant**
```
Query: "Como posso melhorar a função compress_pdf()?"
↓
Vector: Contexto da função
Graph: Dependências e chamadores
AST: Métricas de complexidade
↓
LLM: Sugestões de refactoring
```

### **3. Bug Tracing**
```
Query: "Trace o bug de NullPointer em user_service.py"
↓
Graph: Trace execution path
Vector: Contexto de erros similares
↓
LLM: Hipóteses e soluções
```

### **4. Documentation Generator**
```
Query: "Documente o módulo de autenticação"
↓
Graph: Mapeia todas as funções do módulo
Vector: Exemplos de uso
↓
LLM: Gera documentação completa
```

## 📈 Métricas de Sucesso

### **Qualidade do RAG**
- **Precision@K**: % de chunks relevantes nos top K
- **Recall**: % de chunks relevantes recuperados
- **MRR** (Mean Reciprocal Rank): Posição média do primeiro resultado relevante

### **Performance**
- Tempo de indexação: < 1min para 10K arquivos
- Tempo de query: < 2s para vector + graph
- Memória: < 4GB para repo médio

### **Adoção**
- Satisfação dos devs (pesquisa)
- Redução de tempo para onboarding
- Aumento de produtividade (commits/dia)

## 🔐 Considerações de Segurança

1. **Dados sensíveis**: Filtrar secrets antes de indexar
2. **Acesso**: RBAC no MCP server
3. **API Keys**: Nunca commitar .env
4. **Local-first**: Embeddings e LLM podem rodar 100% local

## 📝 Próximos Passos Imediatos

1. **CodeSplitter Implementation**
   - Criar `app/code_splitter.py`
   - Integrar tree-sitter
   - Testar com Python, JS, Java
   
2. **Documentação**
   - Atualizar README com novas features
   - Criar guia de contribuição
   - Adicionar exemplos de queries avançadas

3. **Testes**
   - Unit tests para cada módulo
   - Integration tests para pipeline completo
   - Benchmark de performance

---

## 🎓 Recursos de Aprendizado

- **Tree-sitter**: https://tree-sitter.github.io/
- **NetworkX**: https://networkx.org/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **RAG Best Practices**: LlamaIndex docs
- **Code Analysis**: Static analysis tools (pylint, ast module)

---

**Versão**: 1.0  
**Data**: Fevereiro 2026  
**Autor**: Code RAG Engine Team
