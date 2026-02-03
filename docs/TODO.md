# Tarefas

## Passo 1
- [ ] Ajustar chunking para código real
- [ ] Criar scripts de indexação por commit
- [ ] Integrar oficialmente com Continue.dev
- [ ] Comparar qwen2.5 vs qwen3 no pipeline

## Passo 2
Agora que o ambiente está resolvido, o próximo gargalo real será:
- [ ] Indexar um repositório real
- [ ] Testar uma query simples
- [ ] Ajustar `similarity_top_k`
- [ ] Verificar se qwen2.5 já responde bem ou migrar para qwen3:4b

## Passo 3

Se quiser melhorar isso depois, opções sugeridas:

- [ ] Dar peso maior a arquivos `.py` (priorizar no ranking/similarity)
- [ ] Excluir `.txt` do índice
- [ ] Usar metadata filtering no retriever (ex.: filtrar por `file_extension`, `path` ou `lang`)
- [ ] Ajustar chunking por extensão (chunks menores para código, maiores para docs)
- [ ] Testar e medir impacto: remover `data/chroma/` e reindexar após mudanças

## Passo 4 - Manutenção Técnica

- [ ] Migrar de `google-generativeai` para `google-genai` (pacote descontinuado)
  - Atualizar imports em `app/llm_provider.py`
  - Testar compatibilidade com Gemini 2.5
  - Ver: https://github.com/google-gemini/deprecated-generative-ai-python

## Dicas / Observação sênior importante

Se você alterar qualquer um dos itens abaixo:
- o modelo de embedding
- o chunking
- o código de indexação/processamento

Observação importante: remova `data/chroma/` e reindexe. Índice antigo = resultados errados silenciosos.

### Comandos

**Indexação do repositório (PowerShell):** 
```powershell
python scripts/index_repo.py C:\desenv\img-converter --collection-name img_converter --exclude test ghostscript instaladores azure_theme
```

## Testes

Execute:
```powershell
python .\scripts\test_query_only_context.py
```

Sempre teste perguntas de 3 tipos:

1️⃣ Localização  
“Em qual arquivo ocorre X?”

2️⃣ Responsabilidade  
“Qual classe é responsável por Y?”

3️⃣ Fluxo  
“O que acontece quando Z é executado?”

Se o RAG responder bem esses três, você está bem servido.

## Teste API

1. Inicie o Ollama:
```bash
ollama serve
```
Deixe rodando em outro terminal.

2. Inicie a API:
```bash
python -m app.api
```
Você verá: `INFO:     Uvicorn running on http://0.0.0.0:8000`

3. Teste os endpoints

Opção A — Browser (mais fácil): acesse http://localhost:8000/docs e use o Swagger UI interativo para testar os endpoints.

Teste dos modelos disponiveis na minha chave
curl "https://generativelanguage.googleapis.com/v1/models?key="