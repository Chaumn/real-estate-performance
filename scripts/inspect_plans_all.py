import json

def inspect_query(scale, q, confs):
    print(f"================ Scale {scale} - {q} ================")
    for conf in confs:
        path = f"results/benchmark/raw/{scale}_{q}_{conf}_run01.json"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            node = data[0]['Plan']
            print(f"[{conf}] Node: {node.get('Node Type')}, Total Cost: {node.get('Total Cost')}, Actual Rows: {node.get('Actual Rows')}, Hit Blocks: {node.get('Shared Hit Blocks')}, Read Blocks: {node.get('Shared Read Blocks')}")
            def dump_nodes(n, depth=1):
                plans = n.get('Plans', [])
                for p in plans:
                    idx_str = f" (index: {p.get('Index Name')})" if 'Index Name' in p else ""
                    print("  "*depth + f"-> {p.get('Node Type')}{idx_str}")
                    dump_nodes(p, depth+1)
            dump_nodes(node)
        except Exception as e:
            print(f"[{conf}] Error: {e}")

inspect_query(500000, "Q1", ["baseline", "indexed"])
inspect_query(500000, "Q3", ["A", "B", "C", "D"])
inspect_query(500000, "Q4", ["baseline", "indexed"])

