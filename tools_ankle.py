"""Ankle Draw (Self-Defense): retail-store scene; kneel behind printed cover (counter / display rack / car door);
threats exposed above cover for an upward angle from the kneel; faint bystanders on the mezzanine/stock area = backstop.
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
def paste(can,s,cx,cy,w,F,flip=False,thr=238):   # clipped version of tools_games.paste
    h=w*s.shape[0]/s.shape[1]; W,H=int(w*DPI),int(h*DPI); r=cv2.resize(s,(W,H),interpolation=cv2.INTER_AREA)
    if flip: r=r[:,::-1]
    x0=int((cx-w/2-F['x'])*DPI); y0=int((cy-h/2-F['y'])*DPI); Hc,Wc=can.shape[:2]
    a,b=max(0,-x0),max(0,-y0); X1,Y1=min(Wc,x0+W),min(Hc,y0+H); r=r[b:Y1-y0,a:X1-x0]; reg=can[y0+b:Y1,x0+a:X1]; m=r.min(axis=2)<thr; reg[m]=r[m]
    return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
COV=dict(zip(('counter','rack','door'),split('art/src4/cover.jpg'))); THR=split('art/src4/threats.jpg'); CIV=split('art/src4/civ.jpg')
def body(sp):   # head ellipse / torso rect fractions from the sprite silhouette
    m=sp.min(2)<236; H,W=m.shape; row=lambda f:np.where(m[int(f*H)])[0]
    h=row(.07); hx=(h.min()+h.max())/2/W; hw=(h.max()-h.min())/W
    r=row(.3); xs=np.split(r,np.where(np.diff(r)>3)[0]+1); t=max(xs,key=len)
    return dict(head=(hx,.075,max(.07,hw*.42),.055),torso=((t.min()+.12*(t.max()-t.min()))/W,.17,(t.max()-.12*(t.max()-t.min()))/W,.47))
def contour(mask,F,eps=3):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea); c=cv2.approxPolyDP(c,eps,True)[:,0]
    return [[round(F['x']+x/DPI,3),round(F['y']+y/DPI,3)] for x,y in c]
def scene(key,F,mk,code,threats,covers,civs,lay=None):
    Wp,Hp=int(F['w']*DPI),int(F['h']*DPI); bg=cv2.resize(cv2.imread('art/src4/storebg.jpg'),(Wp,Hp),interpolation=cv2.INTER_AREA)
    bg=safe(cv2.addWeighted(bg,0.75,np.full_like(bg,255),0.25,0)); can=bg.copy(); zones=[]
    for i,(ci,fx,fy,h) in enumerate(civs):   # faint bystanders up on the mezzanine / stock area
        sp=CIV[ci]; sp=cv2.addWeighted(sp,0.35,np.full_like(sp,255),0.65,0); w=h*sp.shape[1]/sp.shape[0]; tmp=np.full_like(can,255)
        paste(tmp,sp,F['x']+fx*F['w'],F['y']+fy*F['h'],w,F); m=tmp.min(2)<238; can[m]=tmp[m]
        zones.append(dict(name=f'BYSTANDER {i+1}',kind='bystander',shape='poly',pts=contour(m,F),penalty=-10))
    CM=np.zeros((Hp,Wp),bool); CV=[]
    for nm,fx,fy,w in covers:
        sp=safe(COV[nm]); tmp=np.full_like(can,255); paste(tmp,sp,F['x']+fx*F['w'],F['y']+fy*F['h'],w,F); m=tmp.min(2)<238
        m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))>0; CM|=m; CV.append((nm,tmp,m))
    def ctop(xa,xb):   # highest cover pixel (inches) across the column span
        cols=CM[:,max(0,int((xa-F['x'])*DPI)):int((xb-F['x'])*DPI)]; r=np.where(cols.any(1))[0]; return F['y']+r[0]/DPI if len(r) else 1e9
    for i,(ti,fx,fy,h,fl) in enumerate(threats):
        sp=safe(THR[ti]); w=h*sp.shape[1]/sp.shape[0]; x0,y0,x1,y1=paste(can,sp,F['x']+fx*F['w'],F['y']+fy*F['h']-h/2,w,F,flip=fl); W,H=x1-x0,y1-y0
        V=body(sp[:,::-1] if fl else sp); hx,hy,rx,ry=V['head']; a,b,c,d=V['torso']; n=f'T{i+1}'
        Z=lambda **k:zones.append(dict(kind='score',tier='tier1',group=n,subtle=True,art=True,noGrow=True,**k))
        Z(name=n+' -1',shape='ellipse',cx=round(x0+hx*W,3),cy=round(y0+hy*H,3),rx=round(rx*W*1.6,3),ry=round(ry*H*1.5,3),score=-1,pd=1,part='head')
        Z(name=n+' -0',shape='ellipse',cx=round(x0+hx*W,3),cy=round(y0+(hy+.01)*H,3),rx=round(rx*W*.8,3),ry=round(ry*H*.7,3),score=0,pd=0,part='head')
        tb,yb=y0+b*H,min(y0+d*H,ctop(x0+a*W,x0+c*W)-0.03)
        if yb-tb>0.25: Z(name=n+' -1',shape='rect',x=round(x0+a*W,3),y=round(tb,3),w=round((c-a)*W,3),h=round(yb-tb,3),score=-1,pd=1,part='body')
        ry0=min(.08*H,(yb-tb)/2-0.05)
        if ry0>0.12: Z(name=n+' -0',shape='ellipse',cx=round(x0+(a+c)/2*W,3),cy=round(tb+ry0+0.05,3),rx=round((c-a)*W*.3,3),ry=round(ry0,3),score=0,pd=0,part='body')
    for nm,tmp,m in CV:   # cover pasted last: hides the lower threat; its silhouette = hard cover
        can[m]=np.where(tmp[m]<238,tmp[m],bg[m])
        zones.insert(0,dict(name='HC '+nm.upper(),kind='hardcover',shape='poly',pts=contour(m,F),art=True,subtle=True))
    can=safe(can); sc=[z for z in zones if z['kind']=='score']; m=np.any([zone_mask(z,F,can.shape) for z in sc],axis=0); can=np.where(np.repeat(m[...,None],3,2),safe(can),can)
    check_zones(key,can,sc,F); cv2.imwrite(f'art/{key}.png',can)
    nm='Ankle Draw: Store'+(' (Tabloid)' if lay else '')
    t=dict(code=code,name=nm,markerIds=list(mk),scoring='idpa',category='training',distance='3 yd, shooter kneeling (aim slightly upward)',
        art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'])],zones=zones,
        instructions=['Voice start only: say "start". Gun in an ankle holster.','Start standing, seated or walking (the drill says which); on the beep drop to a kneel behind the counter / rack / car door.','Threats show above cover: hits on cover do not count. Head -0/-1, chest -0/-1.','Faded people on the mezzanine = BYSTANDER +10 s (a high miss lands on them). Score shown at the end.'],
        legend=[['tier1','Head / chest: -0'],['tier1','Head, torso: -1 (+1 s)'],['#FFFFFF','Miss: +5 s'],['cover','Counter / rack / car door = hard cover'],['cover','Faded people above = BYSTANDER +10 s']],
        metaOverride=dict(category='self-defense',paper='tabloid' if lay else 'letter',people='multi',features=['backstop','hard cover'],weapon='pistol'))
    if lay: t['layout']=lay
    sfx='-tab' if lay else ''; N=len(threats); cv=[c[0] for c in covers]
    def call(i,parts=None): k=dict(group=f'T{i+1}',label=f'{cv[i%len(cv)]}',say=f'Threat {i+1}, {cv[i%len(cv)]}'); k.update(parts=parts) if parts else k.update(shots=2); return k
    pos=[('standing','Standing'),('seated','Seated'),('walking','Walking')]; D=[]
    for L,(p,P),par,cl in [(1,pos[0],4.0,[call(0)]),(2,pos[1],3.5,[call(1%N)]),(3,pos[2],3.0,[call(2%N)]),(4,('any','Random start'),2.5,[call(i,['head']) for i in range(N)])]:
        D.append(dict(id=f'ankle-{p}{sfx}',name=f'Ankle Draw L{L}: {P}'+(' (Tabloid)' if lay else ''),category='training',target=key,scoring='idpa',maxPerShot=0,voiceStart=True,startPos=p,
            startDelay=[2,4],randomize=L==4,parTime=par if L<4 else round(par*N/2+1.5,1),timeout=15,calls=cl if L<4 else cl[:1],
            notes=(f'{P} start, say "start". Beep: ankle draw, drop to a kneel behind cover, ' + ('2 to the called threat.' if L<4 else 'the app calls one threat: 1 head shot.'))+f' Par {par:.1f}s. Bystanders above = +10 s.'))
    D.append(dict(id=f'ankle-all{sfx}',name='Ankle Draw: all threats'+(' (Tabloid)' if lay else ''),category='training',target=key,scoring='idpa',maxPerShot=0,voiceStart=True,startPos='any',
        startDelay=[2,4],randomize=True,parTime=round(2.5+1.0*N,1),timeout=20,calls=[call(i) for i in range(N)],notes='Random start position. Kneel, 2 to every threat in the called order. Bystanders above = +10 s.'))
    G.upsert(key,t,D)
# threats: (sprite, x-frac, foot y-frac, height in, flip); covers: (name, cx frac, cy frac, width in); civs on mezzanine
scene('ankle',LETTER,(340,341,342,343),'LD-601',
    threats=[(0,.2,.83,3.6,False),(1,.52,.8,3.4,True),(2,.82,.83,3.6,True)],
    covers=[('counter',.2,.7,2.6),('rack',.52,.66,1.7),('door',.82,.66,2.2)],
    civs=[(0,.12,.16,1.4),(3,.45,.16,1.4),(1,.7,.16,1.35),(2,.92,.17,1.35)])
scene('ankle-tabloid',TAB,(344,345,346,347),'LD-602',lay=TABLAY,
    threats=[(0,.1,.83,3.6,False),(1,.3,.8,3.4,True),(2,.5,.83,3.6,False),(0,.7,.82,3.5,True),(1,.9,.8,3.4,False)],
    covers=[('counter',.1,.7,2.6),('rack',.3,.66,1.7),('door',.5,.66,2.2),('counter',.7,.64,2.6),('door',.9,.7,2.2)],
    civs=[(0,.06,.16,1.4),(3,.2,.16,1.4),(1,.4,.16,1.35),(2,.6,.17,1.35),(3,.78,.16,1.4),(0,.95,.16,1.4)])
G.save(); print('ok ankle')
