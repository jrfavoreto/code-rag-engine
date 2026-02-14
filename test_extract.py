#!/usr/bin/env python3
from app.query_engine import CodeQueryEngine

engine = CodeQueryEngine(collection_name="img_converter")

queries = [
    "Quem chama compress_pdf?",
    "quem chama a função compress_pdf",
    "compress_pdf chama quais funções?",
]

for query in queries:
    print(f"\nQuery: '{query}'")
    func_name = engine._extract_function_name(query)
    print(f"  → Função extraída: '{func_name}'")
