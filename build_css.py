from pathlib import Path
import sys

try:
    from rcssmin import cssmin  # pip install rcssmin
except ImportError:
    print("Please 'pip install rcssmin' before running this script.", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "app/static" # adjust if necessary
ORDER_FILE = STATIC / "css" / "order.txt"
OUT_FILE = STATIC / "css" / "styles.min.css"

def read_order():
    if not ORDER_FILE.exists():
        raise FileNotFoundError(f"Missing {ORDER_FILE}")
    items = []
    for line in ORDER_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"): # ensure we don't get comments
            continue
        items.append(line)
    return items

def main():
    files = read_order()
    parts = []
    for rel in files:
        p = STATIC / rel
        if not p.exists():
            raise FileNotFoundError(f"CSS file listed but not found: {p}")
        parts.append(p.read_text(encoding="utf-8"))
    combined = "\n\n".join(parts)
    minimized = cssmin(combined)
    OUT_FILE.write_text(minimized, encoding="utf-8") # write minimized CSS

    original_kb = len(combined) / 1024
    min_kb = len(minimized) / 1024
    savings = ((original_kb - min_kb) / original_kb * 100) if original_kb else 0
    print(f"Wrote {OUT_FILE} ({min_kb:.1f} KB, saved {savings:.1f}%).") # savings, etc

if __name__ == "__main__":
    main()