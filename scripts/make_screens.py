"""Take the demo screenshots (docs/screenshots) with headless Microsoft Edge (Windows).
Each shot loads the demo with sample orders (?sample=1) in a fresh browser profile.

    python scripts/make_screens.py
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
EDGE = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]
DESKTOP = (1600, 1200, 1)   # width, height, device scale
PHONE = (520, 1100, 2)      # saved as 1040 x 2200 (headless Edge won't go narrower than ~500px)

SHOTS = [
    ("1-home.png", "/", DESKTOP),
    ("2-menu.png", "/table/2", PHONE),
    ("3-my-orders.png", "/table/1/orders", PHONE),
    ("4-kitchen.png", "/kitchen", DESKTOP),
    ("5-dashboard.png", "/admin", DESKTOP),
    ("6-tables-qr.png", "/admin/tables", DESKTOP),
    ("7-menu-admin.png", "/admin/menu", DESKTOP),
]


def main() -> None:
    edge = next((p for p in EDGE if p.exists()), None)
    if edge is None:
        sys.exit("Microsoft Edge not found.")
    OUT.mkdir(parents=True, exist_ok=True)
    page = (ROOT / "index.html").as_uri()
    for name, route, (w, h, scale) in SHOTS:
        out = OUT / name
        out.unlink(missing_ok=True)
        profile = tempfile.mkdtemp(prefix="edge-shot-")
        subprocess.run(
            [str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
             f"--force-device-scale-factor={scale}", f"--window-size={w},{h}", "--virtual-time-budget=4000",
             f"--screenshot={out}", f"{page}?sample=1#{route}"],
            capture_output=True, timeout=90,
        )
        for _ in range(20):
            if out.exists():
                break
            time.sleep(0.5)
        img = Image.open(out).convert("RGB")
        if img.size != (w * scale, h * scale):
            img = img.crop((0, 0, w * scale, h * scale))
        img.save(out)
        print(f"{name} {img.size}")


if __name__ == "__main__":
    main()
