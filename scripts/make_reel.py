"""Make the Instagram demo reel (1080x1920 MP4, no music) by driving the real app.

    pip install playwright pillow      (uses your installed Microsoft Edge; no browser download)
    python scripts/make_reel.py

Output: social-media-posts/instagram-reels/qr-dine-demo-reel.mp4 (+ cover.png).
Add music from Instagram's own library when posting.
"""

import functools
import http.server
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "social-media-posts" / "instagram-reels"
UNLOCK_HASH_JS = "ACCESS_CODE_SHA256"   # read from the page, so the reel never needs the code itself
FPS = 30
FADE = 0.35


# ---------- 1. capture the real app ----------
def serve(folder: Path) -> tuple[http.server.ThreadingHTTPServer, str]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=str(folder))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/index.html"


def capture(shots: Path) -> None:
    srv, base = serve(ROOT)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            ctx = browser.new_context(device_scale_factor=2, viewport={"width": 390, "height": 844})
            phone = ctx.new_page()
            phone.goto(base + "#/")
            # fresh demo data, already unlocked (so no code popup in the video)
            phone.evaluate(f"localStorage.clear(); localStorage.setItem('qrdine_unlocked', {UNLOCK_HASH_JS});")
            phone.goto(base + "?fresh=1#/table/3")
            phone.reload()
            phone.wait_for_timeout(800)

            kitchen = ctx.new_page()
            kitchen.set_viewport_size({"width": 1280, "height": 800})
            kitchen.goto(base + "#/kitchen")
            kitchen.wait_for_timeout(500)

            def snap(page, name, wait=450):
                page.wait_for_timeout(wait)
                page.screenshot(path=str(shots / name))

            def click(page, sel):
                page.locator(sel).first.click()

            ids = phone.evaluate("S.menu.map(m => m.id)")
            snap(phone, "01-menu.png", 1200)
            for i in (3, 3, 8, 11):                       # 2x burger, lemonade, brownie
                phone.evaluate(f"document.querySelector('[data-a=inc][data-id=\"{ids[i]}\"]').click()")
            click(phone, "[data-a=cat][data-v=Mains]")
            phone.evaluate("document.querySelector('.c2-sec').scrollIntoView(); scrollBy(0, -12)")
            snap(phone, "02-added.png", 900)

            click(phone, ".c2-cartbar")
            phone.fill("#note", "No onions please")
            snap(phone, "03-cart.png")

            click(phone, "[data-a=place]")
            kitchen.wait_for_timeout(900)
            snap(kitchen, "04-kitchen-new.png", 300)

            click(kitchen, "[data-a=kstatus][data-v=preparing]")
            kitchen.wait_for_timeout(300)
            click(kitchen, "[data-a=kstatus][data-v=ready]")
            phone.wait_for_timeout(900)
            phone.evaluate("document.getElementById('toast').classList.remove('show')")
            snap(phone, "05-ready.png")

            click(phone, "[data-a=call][data-type=waiter]")
            snap(phone, "06-phone-call.png", 350)
            kitchen.wait_for_timeout(900)
            snap(kitchen, "06-kitchen-call.png", 300)

            click(kitchen, "[data-a=kstatus][data-v=served]")
            click(kitchen, "[data-a=resolve]")
            phone.wait_for_timeout(700)
            click(phone, "[data-a=pay][data-m=online]")
            click(phone, "[data-a=paynow]")
            phone.wait_for_timeout(1700)
            click(phone, "[data-a=review]")
            phone.fill("#rtext", "Super fast and so easy!")
            snap(phone, "07-review.png")
            click(phone, "[data-a=sendreview]")
            snap(phone, "08-done.png", 600)

            owner = ctx.new_page()
            owner.set_viewport_size({"width": 1280, "height": 800})
            owner.goto(base + "?sample=1#/admin")
            snap(owner, "09-dashboard.png", 900)
            browser.close()
    finally:
        srv.shutdown()


# ---------- 2. scenes ----------
CSS = """
* { box-sizing:border-box; margin:0; padding:0; }
html, body { width:1080px; height:1920px; overflow:hidden; }
body { font-family:"Poppins","Segoe UI",system-ui,sans-serif; color:#fff;
  background:linear-gradient(160deg,#010001 0%,#3a0033 55%,#720063 100%); display:flex; flex-direction:column; align-items:center; }
.top { padding:120px 80px 0; text-align:center; width:100%; }
.kicker { font-size:30px; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:#ff7ad9; }
h1 { font-size:82px; line-height:1.08; font-weight:800; margin-top:18px; letter-spacing:-.01em; }
h1 .hl { color:#ff7ad9; }
.sub { font-size:36px; line-height:1.4; color:#ead7e6; margin-top:22px; }
.stage { flex:1; display:flex; align-items:center; justify-content:center; width:100%; padding:40px 0 60px; }
.phone { padding:16px; border-radius:72px; background:#130011; box-shadow:0 40px 120px rgba(0,0,0,.6), 0 0 0 3px rgba(255,255,255,.12); }
.phone img { display:block; width:100%; border-radius:58px; }
.tablet { padding:18px; border-radius:40px; background:#130011; box-shadow:0 40px 120px rgba(0,0,0,.6), 0 0 0 3px rgba(255,255,255,.12); }
.crop { border-radius:24px; background-repeat:no-repeat; }
.ping { margin-top:34px; display:inline-flex; gap:14px; align-items:center; font-size:34px; font-weight:700; padding:14px 30px; border-radius:999px; background:rgba(123,227,160,.16); color:#7be3a0; }
.brand { position:absolute; bottom:70px; font-size:30px; font-weight:700; color:#c3a2bd; }
.brand b { color:#fff; } .brand span { color:#ff7ad9; }
.cta { margin-top:60px; background:#fff; color:#3a0033; border-radius:36px; padding:54px 60px; text-align:center; width:880px; }
.cta .t { font-size:72px; font-weight:800; color:#720063; }
.cta .s { font-size:38px; margin-top:16px; line-height:1.35; }
.chips { display:flex; flex-wrap:wrap; gap:18px; justify-content:center; margin-top:56px; width:900px; }
.chip { border:2px solid rgba(255,255,255,.18); border-radius:999px; padding:14px 28px; font-size:32px; color:#ead7e6; background:rgba(255,255,255,.07); }
"""
FONT = '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap" rel="stylesheet">'
BRAND = '<div class="brand"><b>QR <span>Dine</span></b> · live demo</div>'


def phone(img, width=600):
    return f'<div class="phone" style="width:{width}px"><img src="{img}"></div>'


def tablet(img, x, y, w, h, width):
    """Show region (x,y,w,h in CSS px of a 1280x800 page captured at 2x) at the given width."""
    k = width / w
    return (f'<div class="tablet"><div class="crop" style="width:{width}px;height:{round(h * k)}px;'
            f'background-image:url({img});background-size:{1280 * k}px {800 * k}px;'
            f'background-position:{-x * k}px {-y * k}px"></div></div>')


def call_stage():
    strip = tablet("06-kitchen-call.png", 14, 82, 445, 64, 940)
    return (f'<div style="display:flex;flex-direction:column;align-items:center;gap:44px">'
            f'{phone("06-phone-call.png", 470)}{strip}</div>')


SCENES = [  # (seconds, kicker, title, subtitle, stage html)
    (3.4, "Smart QR ordering", 'Guests order from <span class="hl">their phone</span>', "No app. No waiting. Just scan the QR on the table.", phone("01-menu.png")),
    (2.8, "Step 1", "Pick the dishes", "Live menu with prices and sold-out items", phone("02-added.png")),
    (2.8, "Step 2", 'Add a note. <span class="hl">Order.</span>', "“No onions please” goes straight to the chef", phone("03-cart.png")),
    (3.2, "Step 3", 'The kitchen gets it <span class="hl">instantly</span>', "New order pops up with a sound alert",
     tablet("04-kitchen-new.png", 12, 0, 418, 420, 900)),
    (2.8, "Step 4", "Track it live", "Received → Preparing → Ready", phone("05-ready.png")),
    (2.8, "Step 5", 'Call a waiter in <span class="hl">one tap</span>', "Requests show up on the kitchen screen", call_stage()),
    (2.8, "Step 6", "Pay & leave a review", "Online, cash at the table or at the counter", phone("07-review.png")),
    (3.2, "For the owner", 'Every sale, <span class="hl">live</span>', "Sales, best sellers, reviews and table requests", tablet("09-dashboard.png", 266, 112, 490, 350, 940)),
]
CTA_SECONDS = 3.8


def scene_html(kicker, title, sub, stage):
    return (f'<!doctype html><html><head><meta charset="utf-8">{FONT}<style>{CSS}</style></head><body>'
            f'<div class="top"><div class="kicker">{kicker}</div><h1>{title}</h1><p class="sub">{sub}</p></div>'
            f'<div class="stage">{stage}</div>{BRAND}</body></html>')


def cta_html():
    chips = "".join(f'<span class="chip">{c}</span>' for c in
                    ["📋 Digital menu", "👨‍🍳 Kitchen screen", "🙋 Waiter calls", "💳 Payments", "⭐ Reviews", "📊 Dashboard"])
    return (f'<!doctype html><html><head><meta charset="utf-8">{FONT}<style>{CSS}</style></head><body>'
            f'<div class="top" style="padding-top:300px"><div class="kicker">Your turn</div>'
            f'<h1>Want this for <span class="hl">your</span> restaurant?</h1>'
            f'<p class="sub">Built around your brand, your menu and your payment methods.</p></div>'
            f'<div class="cta"><div class="t">DM us “QRDINE”</div><div class="s">for the live demo link &amp; access code</div></div>'
            f'<div class="chips">{chips}</div>{BRAND}</body></html>')


def render_scenes(shots: Path) -> list[tuple[Path, float]]:
    pages = [(scene_html(k, t, s, st), d) for d, k, t, s, st in SCENES] + [(cta_html(), CTA_SECONDS)]
    out = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        for i, (html, secs) in enumerate(pages, 1):
            f = shots / f"scene-{i:02d}.html"
            f.write_text(html, encoding="utf-8")
            page.goto(f.as_uri())
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(300)
            png = shots / f"scene-{i:02d}.png"
            page.screenshot(path=str(png))
            out.append((png, secs))
        browser.close()
    return out


# ---------- 3. video ----------
def make_video(scenes: list[tuple[Path, float]], dest: Path) -> None:
    args, filters = ["ffmpeg", "-y", "-loglevel", "error"], []
    for png, _ in scenes:
        args += ["-i", str(png)]          # one still frame; zoompan turns it into exactly n frames
    for i, (_, secs) in enumerate(scenes):
        n = round(secs * FPS)
        filters.append(  # gentle push-in; upscale first so the zoom is smooth
            f"[{i}:v]scale=2160:3840,zoompan=z='1+0.035*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={n}:s=1080x1920:fps={FPS},setsar=1,format=yuv420p,trim=end_frame={n},setpts=PTS-STARTPTS[v{i}]")
    prev, t = "[v0]", scenes[0][1]
    for i in range(1, len(scenes)):
        label = f"[x{i}]"
        filters.append(f"{prev}[v{i}]xfade=transition=fade:duration={FADE}:offset={t - FADE:.3f}{label}")
        prev, t = label, t + scenes[i][1] - FADE
    args += ["-f", "lavfi", "-t", f"{t:.3f}", "-i", "anullsrc=r=44100:cl=stereo",
             "-filter_complex", ";".join(filters), "-map", prev, "-map", f"{len(scenes)}:a",
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(dest)]
    subprocess.run(args, check=True)
    print(f"{dest.relative_to(ROOT)} ({t:.1f}s)")


def main() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")
    OUT.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="reel-"))
    capture(work)
    scenes = render_scenes(work)
    shutil.copy(scenes[0][0], OUT / "cover.png")
    make_video(scenes, OUT / "qr-dine-demo-reel.mp4")
    print(f"frames kept in {work}")


if __name__ == "__main__":
    main()
