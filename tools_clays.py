"""Shotgun Clays (lifelike): rendered bright-orange clay pigeons (GenerateImage art/src2/clay.jpg) in flight,
composited at field size. Scoring: clay (orange disc, grows by spread) 5 pts; dashed pattern ring 2 pts."""
import json,cv2,numpy as np,sys
DARK='--orange-only' not in sys.argv   # variant: black dome (scoring core) if bright orange defeats the laser detector
DPI=150; F=dict(x=0.4,y=1.85,w=7.7,h=7.3); W,H=int(F['w']*DPI),int(F['h']*DPI)
src=cv2.imread('art/src2/clay.jpg'); m=(src.min(axis=2)<235).astype(np.uint8); ys,xs=np.nonzero(m); src=src[ys.min():ys.max()+1,xs.min():xs.max()+1]
can=np.full((H,W,3),255,np.uint8)
CL=[(2.45,3.55,-12),(5.85,5.15,9),(2.95,7.55,-4)]; RX,RY,RR=1.15,0.5,1.45   # centre (in), tilt (deg); clay half-axes; pattern ring radius
zones=[]
for i,(cx,cy,ang) in enumerate(CL):
    w,h=int(2*RX*DPI),int(2*RY*DPI); c=cv2.resize(src,(w,h),interpolation=cv2.INTER_AREA)
    if DARK:   # black dome over the centre 55%
        mk=np.zeros((h,w),np.uint8); cv2.ellipse(mk,(w//2,h//2),(int(w*0.28),int(h*0.28)),0,0,360,1,-1); c[mk>0]=(c[mk>0]*0.12).astype(np.uint8)
    M=cv2.getRotationMatrix2D((w/2,h/2),ang,1.0); pad=int(max(w,h)*0.2)
    big=np.full((h+2*pad,w+2*pad,3),255,np.uint8); big[pad:pad+h,pad:pad+w]=c
    M=cv2.getRotationMatrix2D(((w+2*pad)/2,(h+2*pad)/2),ang,1.0); r=cv2.warpAffine(big,M,(w+2*pad,h+2*pad),borderValue=(255,255,255),flags=cv2.INTER_LINEAR)
    x0=int((cx-F['x'])*DPI-r.shape[1]/2); y0=int((cy-F['y'])*DPI-r.shape[0]/2); reg=can[y0:y0+r.shape[0],x0:x0+r.shape[1]]
    msk=r.min(axis=2)<240; reg[msk]=r[msk]
    zones.append(dict(name=f'Ring{i+1}',kind='score',shape='circle',cx=cx,cy=cy,r=RR,score=2,tier='tier1',dashed=True,noGrow=True,subtle=True))
for i,(cx,cy,ang) in enumerate(CL):
    zones.append(dict(name=f'Clay{i+1}',kind='score',shape='ellipse',cx=cx,cy=cy,rx=RX*0.97,ry=RY*0.97,rot=ang,score=3,tier='tier3',art=True))
    if DARK: zones.append(dict(name=f'Dome{i+1}',kind='score',shape='ellipse',cx=cx,cy=cy,rx=RX*0.56,ry=RY*0.56,rot=ang,score=5,tier='tier5',art=True,noGrow=True))
cv2.imwrite('art/clays.png',can)
DOC=json.load(open('targets.json')); t=DOC['targets']['clays']
t.update(zones=zones,art=[dict(src='art/clays.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'],warm=True)],
  instructions=['Shotgun mode: clay zones grow by the 0.55in spread.','Dashed ring = pattern edge: 2 pts (fixed size).',('Black dome 5 pts (aim here: lasers read reliably on black). Orange clay (incl. spread) 3 pts.' if DARK else 'Clay (incl. spread) 5 pts.'),'Mount, swing, shoot each clay once.'])
json.dump(DOC,open('targets.json','w'),indent=1); print('ok clays',DARK)
