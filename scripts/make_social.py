"""Render docs/social/slides.html into Instagram slides (1080x1350 PNG) and a LinkedIn
carousel PDF, saved in social-media-posts/, using headless Microsoft Edge (Windows).

    python scripts/make_social.py
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOCIAL = ROOT / "docs" / "social"
POSTS = ROOT / "social-media-posts"
OUT = POSTS / "instagram"
SLIDES = 9
EDGE = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def main() -> None:
    edge = next((p for p in EDGE if p.exists()), None)
    if edge is None:
        sys.exit("Microsoft Edge not found.")
    OUT.mkdir(parents=True, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="edge-social-")
    pages = []
    for i in range(1, SLIDES + 1):
        out = OUT / f"slide-{i}.png"
        out.unlink(missing_ok=True)
        url = (SOCIAL / "slides.html").as_uri() + f"?s={i}"
        subprocess.run(
            [str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
             "--force-device-scale-factor=1", "--window-size=1080,1350", "--virtual-time-budget=3000",
             f"--screenshot={out}", url],
            capture_output=True, timeout=90,
        )
        for _ in range(20):
            if out.exists():
                break
            time.sleep(0.5)
        img = Image.open(out).convert("RGB")
        if img.size != (1080, 1350):
            img = img.crop((0, 0, 1080, 1350))
        img.save(out)
        pages.append(img)
        print(f"slide-{i}.png")
    pdf = POSTS / "linkedin" / "linkedin-carousel.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=150)
    print(f"{pdf.relative_to(ROOT)} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
