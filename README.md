# site-laptop-mockup-video

Turn a real website into a cinematic laptop-mockup video, using a **real scroll recording** (Playwright) composited onto a green-screen laptop photo (OpenCV + ffmpeg). No AI video, so no garbled text on the screen.

برای نمونه‌کار طراحی وب: اسکرول واقعی سایت را فریم‌به‌فریم ضبط می‌کند و روی عکس لپ‌تاپ با صفحهٔ سبز می‌چسباند. متن‌ها و تصاویر صفحه دقیقاً همان سایت واقعی است.

## Pipeline
1. `prompts/laptop-green-screen.md` – make the laptop plates (Nano Banana / GPT Image).
2. `node scripts/serve.js ./site 8099` – local server with Range support.
3. `python3 scripts/record.py http://localhost:8099/ frames` – deterministic frame capture.
4. `python3 scripts/composite.py plate.png 1080 1920 out.mp4 1.18 frames 24`

Requires: Python 3, `playwright`, `opencv-python`, `numpy`, `ffmpeg`, Node.js.
See `SKILL.md` for the lessons (H.264 in Chromium, seek jitter, 24 fps matching).

License: MIT
