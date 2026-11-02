import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"

# Match file:///d:/Documents/PTIT%20DOC/IDS/real-estate-performance/... or file:///...
# Case 1: In markdown images: ![caption](file:///d:/.../results/...) -> ![caption](results/...)
# Case 2: In markdown links: [`label`](file:///d:/.../path) -> `path` or [label](path)

prefix_pattern = re.compile(r'file:///(?:d:/Documents/PTIT%20DOC/IDS/real-estate-performance/|d:/Documents/PTIT\s+DOC/IDS/real-estate-performance/|[dD]:/[^)\s"]*/real-estate-performance/)', re.IGNORECASE)

md_files = list(REPORT_DIR.glob("*.md"))
print(f"Scanning {len(md_files)} markdown files...")

total_replacements = 0

for f in md_files:
    content = f.read_text(encoding="utf-8")
    original = content
    
    # Replace image links: ![...](file:///.../results/...) -> ![...](results/...)
    content = prefix_pattern.sub('', content)
    
    # Also clean any remaining file:///d:/...
    content = re.sub(r'file:///[a-zA-Z]:/[^)\s"]*/([a-zA-Z0-9_\-./]+)', r'\1', content)
    content = re.sub(r'file:///[^)\s"]*/([a-zA-Z0-9_\-./]+)', r'\1', content)
    
    if content != original:
        f.write_text(content, encoding="utf-8")
        count = len(prefix_pattern.findall(original))
        total_replacements += count
        print(f"Cleaned {f.name} ({count} paths replaced)")

print(f"Done! Replaced {total_replacements} local file URLs.")

