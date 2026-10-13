# site-laptop-mockup-video

Turn a **real website** into a cinematic **laptop-mockup video** (vertical 9:16 for Reels/TikTok, horizontal 16:9 for your site) using a **real scroll recording**, not AI video.

AI video models (Veo, Kling, Seedance, ...) garble text on screens and morph the page. This pipeline records your actual site frame by frame and composites it into a green-screen laptop photo, so every word and image is exactly what the site shows.

برای نمونه‌کار طراحی وب: اسکرول واقعی سایت را فریم‌به‌فریم ضبط می‌کند و روی عکس لپ‌تاپ با صفحهٔ سبز می‌چسباند. متن و تصویر صفحه دقیقاً همان سایت واقعی است. راهنمای فارسی در انتهای همین فایل است.

```
laptop plate (green screen) ──┐
                              ├─► composite.py ─► out.mp4 (1080x1920 / 1920x1080)
site ─► serve.js ─► record.py ─┘   (frames/0000.jpg ...)
```

## Requirements
- Python 3.9+, Node.js 16+, ffmpeg
- `pip install -r requirements.txt` then `python3 -m playwright install chromium`
- A laptop image with a flat pure-green (#00FF00) screen (see step 1)

## Quick start
```bash
# 1. make a laptop plate (any image tool) -> plate_v.png (9:16) and plate_h.png (16:9)
#    prompts: prompts/laptop-green-screen.md

# 2. serve your built/static site (Range support is required for scroll-scrubbed videos)
node scripts/serve.js ./my-site 8099 &

# 3. record the scroll, frame by frame
python3 scripts/record.py http://localhost:8099/ frames --hero-frames 170 --tail-frames 192

# 4. composite
python3 scripts/composite.py plate_v.png 1080 1920 out_vertical.mp4   1.18 frames 24
python3 scripts/composite.py plate_h.png 1920 1080 out_horizontal.mp4 1.12 frames 24
```
`composite.py` arguments: `PLATE OUT_W OUT_H OUT.mp4 ZOOM_END [FRAMES_DIR] [FPS]` (ZOOM_END = final push-in, 1.0 = no zoom).

## Options (`record.py`)
| flag | default | meaning |
|---|---|---|
| `--w / --h` | 1440 / 900 | browser viewport; keep ~16:10 to match a MacBook screen |
| `--hero-frames` | 170 | output frames spent inside the first `<video>`'s section (2 source frames per output frame at 24 fps) |
| `--tail-frames` | 192 | output frames for the rest of the page (eased, ends at rest) |
| `--hold` | 12 | still frames held at start and end |
| `--channel chrome` | – | use installed Google Chrome (H.264 support) |
| `--chromium PATH` | – | use a specific browser binary |

No `<video>` on the page? Then `heroRange` is 0 and the whole page is scrolled in `--tail-frames` frames; set it to your desired length (24 fps).

## Step by step
1. **Laptop plate.** Generate two images (Nano Banana / GPT Image / any photo): a laptop on a desk whose screen is a **perfectly flat #00FF00**, no glare, no reflections, all four corners visible. Use `prompts/laptop-green-screen.md`. A real photo with a green fill also works.
2. **Serve the site.** Use `scripts/serve.js <folder> <port>`. For a framework project, build a static export first. A normal dev server also works if it supports HTTP Range for video.
3. **Record.** `record.py` scrolls with `behavior:'instant'`, waits until the `<video>` has finished seeking, then screenshots. This is deterministic, so there are no dropped or duplicated frames.
4. **Composite.** `composite.py` detects the green quad, perspective-warps each frame in at 2x supersampling, removes green fringes, and adds a slow push-in. Output is H.264, yuv420p, `+faststart`.
5. **QA.** Compare consecutive frames: there should be no spikes; duplicates only in the final ease-out.

## Troubleshooting
| symptom | cause / fix |
|---|---|
| Hero video is black or frozen | Playwright's Chromium may lack H.264. Use `--channel chrome`, or transcode the hero to VP9/WebM (`ffmpeg -i hero.mp4 -c:v libvpx-vp9 -crf 38 -g 8 -an hero.webm`) and serve it under the same filename with `Content-Type: video/webm` (`serve.js` already serves `.mp4` as webm; edit the map if you need real mp4). |
| Video stutters / jumps while scrolling | Many sites smooth scroll to video time with a rAF lerp and skip seeks while `seeking`. In a **copy** of the site used only for recording, set progress = scroll progress and assign `video.currentTime` directly. Never ship that patch. |
| `corners<4` / mask not found | The screen is not a clean green. Regenerate the plate; remove glare and reflections. |
| Green edge visible | Increase the despill window in `composite.py` or shrink the page frame 1-2 px. |
| Text looks soft | Record at `--w 1920 --h 1200` (keep 16:10) and let the compositor downscale. |
| Vertical frame crops the screen | Make a plate where the laptop is smaller in the frame (generous margin). |
| Output too slow / too fast | Change `--hero-frames` / `--tail-frames`. At 24 fps, 24 frames = 1 second. |

## Notes and limits
- One scroll path per run. Click-through flows (menus, forms) are out of scope.
- Hero detection uses the first `<video>`; adapt `record.py` for canvas/WebGL heroes.
- Only record sites you own or have permission to show.
- Audio is not added. Mux a track with `ffmpeg -i out.mp4 -i music.mp3 -c:v copy -shortest final.mp4`.

## راهنمای فارسی
1. **تصویر لپ‌تاپ:** با پرامپت‌های `prompts/laptop-green-screen.md` دو عکس بسازید (عمودی ۹:۱۶ و افقی ۱۶:۹). صفحهٔ لپ‌تاپ باید سبز یکدست (#00FF00)، بدون بازتاب و با چهار گوشهٔ کاملاً دیده‌شده باشد.
2. **اجرای سایت:** `node scripts/serve.js ./my-site 8099` (سرور محلی با پشتیبانی از Range، لازم برای ویدیوهای اسکرول‌محور).
3. **ضبط:** `python3 scripts/record.py http://localhost:8099/ frames` — هر فریم جداگانه و بدون پرش ضبط می‌شود.
4. **ترکیب:** `python3 scripts/composite.py plate_v.png 1080 1920 out.mp4 1.18 frames 24`
5. **اگر ویدیوی هیرو پخش نشد:** از `--channel chrome` استفاده کنید یا ویدیو را به WebM تبدیل کنید.
6. **اگر هنگام اسکرول پرش دیدید:** در یک کپی از سایت (فقط برای ضبط) فیلتر نرم‌کنندهٔ اسکرول را حذف کنید تا زمان ویدیو مستقیم از موقعیت اسکرول بیاید.

## License
MIT
