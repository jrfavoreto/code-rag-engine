# Code RAG Engine

Sistema de RAG (Retrieval-Augmented Generation) especializado em repositórios de código.

## Objetivo

Criar um RAG especializado em repositórios de código que:
- **Indexa** o projeto
- **Recupera** somente o contexto relevante
- **Entrega** esse contexto já refinado
- Para ser usado por **qualquer LLM** (local ou remoto)
- **Economizando tokens** e tempo de raciocínio

## Tecnologias

- **Python 3.10+**
- **LlamaIndex** - Núcleo do RAG
- **ChromaDB** - Armazenamento vetorial local
- **FastAPI** - API REST limpa e eficiente
- **Ollama** - Integração com LLMs locais (opcional)

## Estrutura do Projeto

```
code-rag-engine/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configurações da aplicação
│   ├── indexer.py         # Indexação de repositórios
│   ├── query_engine.py    # Motor de consultas RAG
│   └── api.py             # API FastAPI
├── scripts/
│   └── index_repo.py      # Script CLI para indexar repositórios
├── data/                  # Dados e índices (ignorado pelo git)
├── requirements.txt       # Dependências Python
└── README.md
```

## Instalação

### PowerShell (Windows)

1. Clone o repositório:
```bash
git clone https://github.com/jrfavoreto/code-rag-engine.git
cd code-rag-engine
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Verifique o Python ativo (opcional):
```bash
python --version
where python
```

4. Ativar o ambiente virtual python

* Ativar : 

```bash
# PowerShell (Windows)
.\.venv\Scripts\Activate.ps1
# Bash/Zsh (Linux/Mac)
source .venv/bin/activate
```

* Desativar: 

```bash
deactivate
```

* se aparecer erro de execução de scripts:

```bash
# Execute como Administrador (uma vez apenas)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

5. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Ollama rodando

* Verificação

```bash
# Teste se o Ollama responde
curl http://localhost:11434

# Ou liste os modelos disponíveis
ollama list

# Se aparecer algo como, tá ok:
Ollama is running
```

* Subir o Ollama

```bash
ollama serve
```

## Uso

### 1. Indexar um Repositório

* Use o script CLI para indexar um repositório de código:

```bash
python scripts/index_repo.py /caminho/para/repositorio
```

* Exemplo real:
```bash
python scripts/index_repo.py C:\desenv\img-converter --collection-name img_converter --exclude test ghostscript instaladores azure_theme
```

Opções adicionais:
```bash
# Especificar nome da coleção
python scripts/index_repo.py /caminho/para/repo --collection-name meu_projeto

# Excluir diretórios adicionais
python scripts/index_repo.py /caminho/para/repo --exclude tests docs
```

### 2. Iniciar a API

Inicie o servidor FastAPI:

```bash
python -m app.api
```

A API estará disponível em `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

### 3. Consultar o Código

#### Via API REST

**Obter contexto relevante:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Como funciona a autenticação?",
    "similarity_top_k": 5,
    "return_context_only": true
  }'
```

**Obter contexto formatado (texto simples):**
```bash
curl "http://localhost:8000/context?query=função+de+login&top_k=3"
```

#### Via Python

```python
from app.query_engine import CodeQueryEngine

# Criar engine de consulta
engine = CodeQueryEngine(collection_name="code_repository")

# Obter contexto relevante
result = engine.query(
    query="Como funciona a autenticação?",
    similarity_top_k=5,
    return_context_only=True
)

# Ou obter contexto formatado para usar com LLM externo
context = engine.retrieve_context(
    query="Como funciona a autenticação?",
    similarity_top_k=5
)
print(context)
```

## Configuração

Você pode configurar o sistema criando um arquivo `.env`:

```env
# Diretórios
DATA_DIR=data
CHROMA_DIR=data/chroma

# Modelo de embedding
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Ollama (opcional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Indexação
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# API
API_HOST=0.0.0.0
API_PORT=8000

# Consultas
SIMILARITY_TOP_K=5
```

## Fluxo de Trabalho

1. **Indexação**: O sistema percorre o repositório, identifica arquivos de código e cria embeddings vetoriais
2. **Armazenamento**: Os vetores são armazenados no ChromaDB para recuperação eficiente
3. **Consulta**: Quando você faz uma pergunta, o sistema:
   - Converte a pergunta em embedding vetorial
   - Busca os chunks de código mais similares
   - Retorna o contexto relevante
4. **Uso com LLM**: O contexto pode ser usado com qualquer LLM (GPT-4, Claude, Llama, etc.)

## Tipos de Arquivo Suportados

O indexador reconhece automaticamente arquivos de código comuns:
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`, `.hpp`)
- C# (`.cs`)
- Go (`.go`)
- Rust (`.rs`)
- Ruby (`.rb`)
- PHP (`.php`)
- E muitos outros...

## Endpoints da API

- `GET /` - Health check
- `GET /health` - Status da aplicação
- `POST /query` - Consultar código com opção de resposta LLM
- `GET /context` - Obter contexto formatado (ideal para LLMs externos)

## Exemplos de Uso

### Exemplo 1: Entender uma feature
```python
engine = CodeQueryEngine()
result = engine.query("Como funciona o sistema de cache?")
```

### Exemplo 2: Encontrar implementações
```python
context = engine.retrieve_context("Onde está implementada a validação de email?")
# Use o contexto com seu LLM favorito
```

### Exemplo 3: Debug
```python
result = engine.query("Onde o erro 'connection timeout' pode ocorrer?")
```

## Vantagens

- ✅ **Economia de tokens**: Envia apenas código relevante para o LLM
- ✅ **Velocidade**: Busca vetorial rápida com ChromaDB
- ✅ **Flexibilidade**: Use com qualquer LLM (local ou cloud)
- ✅ **Privacidade**: Dados e índices ficam localmente
- ✅ **Escalável**: Funciona com repositórios grandes

## Desenvolvimento

Para contribuir ou desenvolver:

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt

# Executar testes (quando disponíveis)
pytest

# Executar linter
ruff check .
```

## Licença

[Definir licença]

## Autor

jrfavoreto
