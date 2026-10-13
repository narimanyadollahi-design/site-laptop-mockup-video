---
name: site-laptop-mockup-video
description: Turn a real website into a laptop-mockup reel (9:16 and 16:9) from a real scroll recording, not AI video. Use for web-design portfolio videos.
---
# Site → laptop mockup video (real recording, no AI-generated screen)
Why: AI video models morph/garble text on screens. Record the real site and composite it into a green-screen laptop photo.

1. Laptop plates: generate 9:16 and 16:9 laptop photos with a flat #00FF00 screen (prompts/laptop-green-screen.md).
2. Serve the site locally with HTTP Range support (scripts/serve.js) – scroll-scrubbed hero videos won't seek otherwise.
3. If the browser has no H.264 (Playwright Chromium), transcode the hero to VP9/WebM (-g 8) and serve it under the same filename with Content-Type video/webm.
4. Recording copy only: if the site smooths scroll→video with a rAF lerp and skips seeks while `seeking`, patch the COPY so progress = scroll progress and currentTime is set directly. Never ship that patch.
5. Record frame-by-frame (scripts/record.py): instant scrollTo, wait until video not seeking, screenshot. Output 24 fps to match the hero's source fps; hero = exactly 2 source frames per output frame, then eased tail. (Jitter came from slow-start easing + async seeks: duplicate/skipped frames.)
6. Composite (scripts/composite.py): detect green quad, warpPerspective at 2x supersample, despill edge, 1.12–1.18 slow zoom. Encode libx264 crf 17, yuv420p.
7. QA: frame-diff the recording; no spikes, dups only in the ease-out tail.
Deliver: vertical 1080x1920, horizontal 1920x1080.
