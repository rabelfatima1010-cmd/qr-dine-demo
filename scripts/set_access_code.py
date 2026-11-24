"""Change the demo's access code (not case-sensitive). Only its SHA-256 hash is stored in index.html.

    python scripts/set_access_code.py NEW-CODE
"""

import hashlib
import re
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "index.html"


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        sys.exit("Usage: python scripts/set_access_code.py NEW-CODE")
    code = sys.argv[1].strip().upper()
    digest = hashlib.sha256(code.encode()).hexdigest()
    html = PAGE.read_text(encoding="utf-8")
    html, n = re.subn(r"const ACCESS_CODE_SHA256 = '[0-9a-f]{64}';", f"const ACCESS_CODE_SHA256 = '{digest}';", html)
    if n != 1:
        sys.exit("Could not find ACCESS_CODE_SHA256 in index.html")
    PAGE.write_text(html, encoding="utf-8")
    print(f"Access code set to {code}. Commit and push to update the live demo.")


if __name__ == "__main__":
    main()
