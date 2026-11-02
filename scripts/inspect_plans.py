import json

with open('results/benchmark/raw/500000_Q2_baseline_run01.json', 'r', encoding='utf-8') as f:
    b = json.load(f)
with open('results/benchmark/raw/500000_Q2_indexed_run01.json', 'r', encoding='utf-8') as f:
    idx = json.load(f)

def print_plan_tree(plan, indent=0):
    node = plan.get('Plan', plan)
    ntype = node.get('Node Type', 'Unknown')
    arows = node.get('Actual Rows')
    cost = node.get('Total Cost')
    extra = []
    if 'Index Name' in node:
        extra.append(f"index={node['Index Name']}")
    if 'Sort Key' in node:
        extra.append(f"sort={node['Sort Key']}")
    extra_str = (" " + " ".join(extra)) if extra else ""
    print('  '*indent + f"- {ntype} (Rows: {arows}, Cost: {cost}){extra_str}")
    for p in node.get('Plans', []):
        print_plan_tree(p, indent+1)

print('=== Q2 Baseline (500k) ===')
print_plan_tree(b[0])

print('\n=== Q2 Indexed (500k) ===')
print_plan_tree(idx[0])

