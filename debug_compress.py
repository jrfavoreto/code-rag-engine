#!/usr/bin/env python3
from app.graph_storage import GraphStorage

storage = GraphStorage()

# Verificar se compress_pdf existe
all_nodes = storage.get_all_nodes(node_type="function")
compress_node = None

for node in all_nodes:
    if node.get('name') == 'compress_pdf':
        compress_node = node
        print(f"✅ Encontrado: {node.get('id')}")
        print(f"   Arquivo: {node.get('file_path')}")
        print(f"   Linha: {node.get('line_number')}")
        break

if compress_node:
    # Ver o que compress_pdf chama
    calls = storage.get_successors(compress_node['id'], relation_type='calls')
    print(f"\n📊 compress_pdf chama {len(calls)} funções:")
    for call in calls[:10]:
        print(f"   - {call.get('name')}")
    
    # Ver quem chama compress_pdf
    callers = storage.get_predecessors(compress_node['id'], relation_type='calls')
    print(f"\n📊 {len(callers)} funções chamam compress_pdf:")
    for caller in callers:
        print(f"   - {caller.get('name')}")
else:
    print("❌ compress_pdf não encontrado no banco!")
