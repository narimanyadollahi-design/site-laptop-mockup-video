"""Deterministic frame-by-frame scroll recording of a site (Playwright, Chromium).
usage: python3 record.py URL OUT_DIR [--fps 24] [--hero-frames 170] [--tail-frames 192]
Per frame: instant scrollTo -> wait until <video> is not seeking (4 stable rAFs) -> screenshot.
Hero (first <video>'s section) advances 2 source-video frames per output frame; the rest eases out."""
import argparse, os
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('out')
ap.add_argument('--hero-frames',type=int,default=170); ap.add_argument('--tail-frames',type=int,default=192)
ap.add_argument('--hold',type=int,default=12); ap.add_argument('--w',type=int,default=1440); ap.add_argument('--h',type=int,default=900)
ap.add_argument('--chromium',default=os.environ.get('CHROMIUM'),help='path to a Chromium/Chrome binary (default: Playwright bundled)')
ap.add_argument('--channel',default=None,help="e.g. 'chrome' to use installed Google Chrome (has H.264)")
a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
WAIT="""new Promise(res=>{const v=document.querySelector('video');let st=0;const raf=()=>requestAnimationFrame(()=>{ if(v&&(v.seeking||v.readyState<2)) st=0; else st++; st>=4?res():raf();});raf();})"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=a.chromium,channel=a.channel,args=['--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':a.w,'height':a.h})
    pg.goto(a.url,wait_until='networkidle'); pg.wait_for_timeout(2500)
    mx=pg.evaluate("document.documentElement.scrollHeight-innerHeight")
    hr=pg.evaluate("(()=>{const v=document.querySelector('video');if(!v)return 0;const s=v.closest('section')||v.parentElement;return Math.max(0,s.offsetHeight-innerHeight)})()")
    end=mx*0.985; B=a.hero_frames; C=a.tail_frames
    ys=[0]*a.hold+[hr*k/B for k in range(B)]
    v0=hr/B
    for k in range(C):                       # cubic hermite: start with hero velocity, end at rest
        t=k/(C-1)
        ys.append((2*t**3-3*t**2+1)*hr+(t**3-2*t**2+t)*v0*C+(-2*t**3+3*t**2)*end)
    ys+=[end]*a.hold
    for i,y in enumerate(ys):
        pg.evaluate(f"window.scrollTo({{top:{y:.2f},behavior:'instant'}})")
        pg.evaluate(WAIT); pg.wait_for_timeout(40)
        pg.screenshot(path=f'{a.out}/{i:04d}.jpg',type='jpeg',quality=94)
    b.close()
print('frames',len(ys))
