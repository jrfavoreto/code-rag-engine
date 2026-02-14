#!/usr/bin/env python3
from app.query_classifier import QueryClassifier

queries = [
    "Quem chama compress_pdf?",
    "Como funciona compress_pdf?",
    "Qual função é responsável por otimizar comprimento de arquivo PDF?",
    "Qual é o impacto de mudar compress_pdf?",
]

for query in queries:
    result = QueryClassifier.classify(query)
    print(f"Query: {query}")
    print(f"  → Classificação: {result}")
    print()
