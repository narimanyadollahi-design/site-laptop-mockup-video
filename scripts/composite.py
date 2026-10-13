"""Green-screen laptop mockup compositor: finds the 4 screen corners (chroma), perspective-warps each frame in, despills edges, adds a slow push-in."""
import cv2, numpy as np, subprocess, sys, glob
# usage: python3 composite.py BASE.png OUT_W OUT_H OUT.mp4 ZOOM_END [FRAMES_DIR] [FPS]
base_path, out_w, out_h, out_path, zoom_end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], float(sys.argv[5])
FD=sys.argv[6] if len(sys.argv)>6 else 'fr'; FPS=sys.argv[7] if len(sys.argv)>7 else '24'
S=2  # supersample
base=cv2.imread(base_path); H0,W0=base.shape[:2]
# upscale to cover out size *S
sc=max(out_w*S/W0, out_h*S/H0)
BW,BH=int(round(W0*sc)),int(round(H0*sc))
big=cv2.resize(base,(BW,BH),interpolation=cv2.INTER_LANCZOS4)
b,g,r=[big[:,:,i].astype(int) for i in range(3)]
mask=((g>170)&(r<120)&(b<120)&(g-r>90)&(g-b>90)).astype(np.uint8)*255
mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
cs,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
hull=cv2.convexHull(c)
# 4 extreme corners via approxPolyDP on hull
eps=0.01*cv2.arcLength(hull,True); q=cv2.approxPolyDP(hull,eps,True).reshape(-1,2)
while len(q)>4:
    eps*=1.3; q=cv2.approxPolyDP(hull,eps,True).reshape(-1,2)
if len(q)<4: raise SystemExit('corners<4')
q=q.astype(np.float32)
# order tl,tr,br,bl
s=q.sum(1); d=(q[:,0]-q[:,1]); 
tl=q[np.argmin(s)]; br=q[np.argmax(s)]; tr=q[np.argmax(d)]; bl=q[np.argmin(d)]
quad=np.array([tl,tr,br,bl],np.float32)
# expand quad by ~2px outward (cover green fringe)
cen=quad.mean(0); quad=cen+(quad-cen)*1.0; 
vec=quad-cen; quad=quad+vec/np.linalg.norm(vec,axis=1,keepdims=True)*2.5*S/2
print('quad',quad.tolist(),file=sys.stderr)
# screen mask polygon (feathered slightly)
poly=np.zeros((BH,BW),np.uint8); cv2.fillConvexPoly(poly,quad.astype(np.int32),255,lineType=cv2.LINE_AA)
poly=cv2.GaussianBlur(poly,(0,0),0.8).astype(np.float32)/255
# despill: base pixels outside poly near green edge -> reduce green
sp=cv2.dilate((poly>0).astype(np.uint8),np.ones((9,9),np.uint8))-(poly>0.99).astype(np.uint8)
bigf=big.copy()
gch=bigf[:,:,1].astype(int); lim=np.maximum(bigf[:,:,0],bigf[:,:,2]).astype(int)
fix=(sp>0)&(gch>lim)
bigf[:,:,1][fix]=lim[fix]
poly3=poly[:,:,None]
files=sorted(glob.glob(FD+'/*.jpg')); n=len(files)
scr=quad.mean(0)
ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{out_w}x{out_h}','-r',FPS,'-i','-',
  '-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',out_path],stdin=subprocess.PIPE)
# subtle glass sheen
yy,xx=np.mgrid[0:BH,0:BW].astype(np.float32)
for i,f in enumerate(files):
    fr=cv2.imread(f); fh,fw=fr.shape[:2]
    # prescale frame to roughly quad width
    qw=np.linalg.norm(quad[1]-quad[0]); 
    tw=int(min(fw,qw*1.15)); th=int(tw*fh/fw); fr2=cv2.resize(fr,(tw,th),interpolation=cv2.INTER_AREA)
    M=cv2.getPerspectiveTransform(np.array([[0,0],[tw,0],[tw,th],[0,th]],np.float32),quad)
    w=cv2.warpPerspective(fr2,M,(BW,BH),flags=cv2.INTER_LINEAR)
    out=(w*0.97*poly3+bigf*(1-poly3)).astype(np.uint8)   # slight dim to sit in scene
    t=i/(n-1); z=1+(zoom_end-1)*(t*t*(3-2*t))
    cw,ch=out_w*S/z,out_h*S/z
    # center: lerp from image center to screen center with zoom
    ctr=np.array([BW/2,BH/2])*(1-(z-1)/(zoom_end-1+1e-9)*0.6)+scr*((z-1)/(zoom_end-1+1e-9)*0.6)
    x0=min(max(ctr[0]-cw/2,0),BW-cw); y0=min(max(ctr[1]-ch/2,0),BH-ch)
    k=out_w*2/cw
    A=np.array([[k,0,-x0*k],[0,k,-y0*k]],np.float32)
    res=cv2.warpAffine(out,A,(out_w*2,out_h*2),flags=cv2.INTER_CUBIC)
    res=cv2.resize(res,(out_w,out_h),interpolation=cv2.INTER_AREA)
    # INTER_AREA unsupported in warpAffine -> fallback
    ff.stdin.write(res.tobytes())
ff.stdin.close(); ff.wait(); print('ok',out_path)
