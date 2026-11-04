"""Ankle Draw (Self-Defense): open single-level retail-store scene, no cover. Masked armed threats among relaxed shoppers
(baskets, phones, bags); every figure has the same medium skin tone so PID relies on hands, weapons and behavior.
Usage: python3 tools_ankle.py   (after tools_games.py)"""
import cv2,numpy as np,tools_games as G
from tools_games import safe,zone_mask,check_zones,LETTER,TAB,TABLAY,DPI
def split(path,thr=225):
    s=cv2.imread(path); m=(s.min(2)<thr).sum(0)>3; runs=[];st=None
    for x,v in enumerate(list(m)+[False]):
        if v and st is None: st=x
        if not v and st is not None:
            if x-st>40: runs.append((st,x))
            st=None
    out=[]
    for a,b in runs:
        c=s[:,max(0,a-4):b+4].copy(); mm=(c.min(2)<thr).astype(np.uint8); ys=np.where(mm.sum(1)>2)[0]; c=c[ys[0]:ys[-1]+1]
        mk=cv2.morphologyEx((c.min(2)<236).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
        n,lab,stt,_=cv2.connectedComponentsWithStats(mk); keep=[i for i in range(1,n) if stt[i][4]>800]
        c[~np.isin(lab,keep)]=255; out.append(c)
    return out
def cut(img,cap=30):   # laser-safe without the yellow-green cast: pull red down toward (g+b)/2+cap
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]; r=np.minimum(r,(g+b)/2+cap); return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
def alpha(r,thr=236):   # background = near-white pixels connected to the sprite border (keeps white shirts)
    w=(r.min(2)>=thr).astype(np.uint8); H,W=w.shape; ff=np.zeros((H+2,W+2),np.uint8); w2=w.copy()
    for p in [(0,0),(W-1,0),(0,H-1),(W-1,H-1)]+[(x,0) for x in range(0,W,7)]+[(x,H-1) for x in range(0,W,7)]+[(0,y) for y in range(0,H,7)]+[(W-1,y) for y in range(0,H,7)]:
        if w2[p[1],p[0]]==1: cv2.floodFill(w2,ff,p,2)
    return cv2.erode((w2!=2).astype(np.uint8),np.ones((3,3),np.uint8))>0
def paste(can,s,cx,cy,w,F,flip=False,thr=222):   # clipped version of tools_games.paste; tight alpha (no white halo)
    h=w*s.shape[0]/s.shape[1]; W,H=int(w*DPI),int(h*DPI); r=cv2.resize(s,(W,H),interpolation=cv2.INTER_AREA)
    if flip: r=r[:,::-1]
    x0=int((cx-w/2-F['x'])*DPI); y0=int((cy-h/2-F['y'])*DPI); Hc,Wc=can.shape[:2]
    a,b=max(0,-x0),max(0,-y0); X1,Y1=min(Wc,x0+W),min(Hc,y0+H); r=r[b:Y1-y0,a:X1-x0]; reg=can[y0+b:Y1,x0+a:X1]; m=alpha(r); reg[m]=r[m]
    return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
THR=split('art/src4/threats3.jpg'); NT=split('art/src4/shoppers.jpg')
def body(sp):   # head ellipse / torso rect fractions from the sprite silhouette
    m=sp.min(2)<236; H,W=m.shape; row=lambda f:np.where(m[int(f*H)])[0]
    h=row(.07); hx=(h.min()+h.max())/2/W; hw=(h.max()-h.min())/W
    r=row(.3); xs=np.split(r,np.where(np.diff(r)>3)[0]+1); t=max(xs,key=len)
    return dict(head=(hx,.075,max(.07,hw*.42),.055),torso=((t.min()+.12*(t.max()-t.min()))/W,.17,(t.max()-.12*(t.max()-t.min()))/W,.47))
def contour(mask,F,eps=3):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea); c=cv2.approxPolyDP(c,eps,True)[:,0]
    return [[round(F['x']+x/DPI,3),round(F['y']+y/DPI,3)] for x,y in c]
def scene(key,F,mk,code,threats,nts=(),lay=None):
    Wp,Hp=int(F['w']*DPI),int(F['h']*DPI); bg=cv2.resize(cv2.imread('art/src4/storebg2.jpg'),(Wp,Hp),interpolation=cv2.INTER_AREA)
    bg=safe(cv2.addWeighted(bg,0.75,np.full_like(bg,255),0.25,0)); can=bg.copy(); zones=[]
    CM=np.zeros((Hp,Wp),bool); ctop=lambda xa,xb:1e9
    for i,(ti,fx,fy,h,fl) in enumerate(threats):
        sp=cut(THR[ti]); w=h*sp.shape[1]/sp.shape[0]; x0,y0,x1,y1=paste(can,sp,F['x']+fx*F['w'],F['y']+fy*F['h']-h/2,w,F,flip=fl); W,H=x1-x0,y1-y0
        V=body(sp[:,::-1] if fl else sp); hx,hy,rx,ry=V['head']; a,b,c,d=V['torso']; n=f'T{i+1}'
        Z=lambda **k:zones.append(dict(kind='score',tier='tier1',group=n,subtle=True,art=True,noGrow=True,**k))
        Z(name=n+' -1',shape='ellipse',cx=round(x0+hx*W,3),cy=round(y0+hy*H,3),rx=round(rx*W*1.6,3),ry=round(ry*H*1.5,3),score=-1,pd=1,part='head')
        Z(name=n+' -0',shape='ellipse',cx=round(x0+hx*W,3),cy=round(y0+(hy+.01)*H,3),rx=round(rx*W*.8,3),ry=round(ry*H*.7,3),score=0,pd=0,part='head')
        tb,yb=y0+b*H,min(y0+d*H,ctop(x0+a*W,x0+c*W)-0.03)
        if yb-tb>0.25: Z(name=n+' -1',shape='rect',x=round(x0+a*W,3),y=round(tb,3),w=round((c-a)*W,3),h=round(yb-tb,3),score=-1,pd=1,part='body')
        ry0=min(.08*H,(yb-tb)/2-0.05)
        if ry0>0.12: Z(name=n+' -0',shape='ellipse',cx=round(x0+(a+c)/2*W,3),cy=round(tb+ry0+0.05,3),rx=round((c-a)*W*.3,3),ry=round(ry0,3),score=0,pd=0,part='body')
    for i,(ni,fx,fy,h,fl) in enumerate(nts):   # unarmed shoppers, open empty hands = NO-SHOOT
        sp=cut(NT[ni]); w=h*sp.shape[1]/sp.shape[0]; tmp=np.full_like(can,255)
        paste(tmp,sp,F['x']+fx*F['w'],F['y']+fy*F['h']-h/2,w,F,flip=fl); m=tmp.min(2)<255; can[m]=tmp[m]
        m2=m&~CM; zones.append(dict(name=f'NT{i+1} NO-SHOOT',kind='noshoot',shape='poly',pts=contour(m2,F),penalty=-10,group=f'NT{i+1}',tags=['civilian'],art=True,subtle=True))
    can=safe(can); sc=[z for z in zones if z['kind']=='score']; m=np.any([zone_mask(z,F,can.shape) for z in sc],axis=0); can=np.where(np.repeat(m[...,None],3,2),safe(can),can)
    check_zones(key,can,sc,F); cv2.imwrite(f'art/{key}.png',can)
    nm='Ankle Draw: Store'+(' (Tabloid)' if lay else '')
    t=dict(code=code,name=nm,markerIds=list(mk),scoring='idpa',category='training',distance='3 yd, shooter kneeling (aim slightly upward)',
        art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'])],zones=zones,
        instructions=['Voice start only: say "start". Gun in an ankle holster.','Start standing, seated or walking; beep: draw from a kneel.','Masked + gun pointed at you = THREAT.','Shoppers with baskets, phones, bags = NO-SHOOT -10.','Head/chest -0, torso -1.'],
        legend=[['tier1','Head / chest: -0'],['tier1','Head, torso: -1 (+1 s)'],['#FFFFFF','Miss: +5 s'],['noshoot','Shopper (basket / phone / bag) = NO-SHOOT: -10']],
        metaOverride=dict(category='self-defense',paper='tabloid' if lay else 'letter',people='multi',features=['no-shoot'],weapon='pistol'))
    if lay: t['layout']=lay
    sfx='-tab' if lay else ''; N=len(threats)
    def call(i,parts=None): k=dict(group=f'T{i+1}',label=f'Threat {i+1}',say=f'Threat {i+1}'); k.update(parts=parts) if parts else k.update(shots=2); return k
    pos=[('standing','Standing'),('seated','Seated'),('walking','Walking')]; D=[]
    for L,(p,P),par,cl in [(1,pos[0],4.0,[call(0)]),(2,pos[1],3.5,[call(1%N)]),(3,pos[2],3.0,[call(2%N)]),(4,('any','Random start'),2.5,[call(i,['head']) for i in range(N)])]:
        D.append(dict(id=f'ankle-{p}{sfx}',name=f'Ankle Draw L{L}: {P}'+(' (Tabloid)' if lay else ''),category='training',target=key,scoring='idpa',maxPerShot=0,voiceStart=True,startPos=p,
            startDelay=[2,4],randomize=L==4,parTime=par if L<4 else round(par*N/2+1.5,1),timeout=15,calls=cl if L<4 else cl[:1],
            notes=(f'{P} start, say "start". Beep: ankle draw, drop to a kneel, ' + ('2 to the called threat.' if L<4 else 'the app calls one threat: 1 head shot.'))+f' Par {par:.1f}s. Shoppers = -10.'))
    D.append(dict(id=f'ankle-all{sfx}',name='Ankle Draw: all threats'+(' (Tabloid)' if lay else ''),category='training',target=key,scoring='idpa',maxPerShot=0,voiceStart=True,startPos='any',
        startDelay=[2,4],randomize=True,parTime=round(2.5+1.0*N,1),timeout=20,calls=[call(i) for i in range(N)],notes='Random start position. Kneel, 2 to every threat in the called order. Shoppers = -10.'))
    G.upsert(key,t,D)
# threats/nts: (sprite, x-frac, foot y-frac, height in, flip)
scene('ankle',LETTER,(340,341,342,343),'LD-601',
    threats=[(0,.14,.86,3.4,False),(1,.5,.84,3.3,False),(2,.86,.86,3.4,False)],
    nts=[(0,.32,.86,3.2,False),(1,.68,.86,3.3,False)])
scene('ankle-tabloid',TAB,(344,345,346,347),'LD-602',lay=TABLAY,
    threats=[(0,.07,.86,3.4,False),(1,.29,.84,3.3,False),(2,.5,.86,3.4,False),(0,.71,.84,3.3,True),(1,.93,.86,3.4,True)],
    nts=[(0,.18,.86,3.2,False),(1,.395,.86,3.3,False),(2,.605,.86,3.2,True),(3,.82,.86,3.3,True)])
G.save(); print('ok ankle')
