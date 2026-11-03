"""Game / training targets composited from rendered sprites (art/src2/*), laser-safe. Writes targets.json + drills.json entries.
Usage: python3 tools_games.py [carnival battle cards maritime ct fof]  (default all)"""
import json,sys,cv2,numpy as np
DPI=150
DOC=json.load(open('targets.json')); T=DOC['targets']; DR=json.load(open('drills.json'))
def safe(img,cap=30):   # compress red-dominance (r-(g+b)/2) to <=cap so the red laser always stands out
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]; e=np.maximum(0,r-(g+b)/2-cap)
    b=np.minimum(255,b+2*e); g=np.minimum(255,g+0.3*e); d=r-(g+b)/2; r=r-np.maximum(0,d-cap)  # lighten (pale yellow) before cutting red
    return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
def reddom(img): b,g,r=[c.astype(np.float32) for c in cv2.split(img)]; return r-(g+b)/2
def sprite(path,crop_white=True,thr=235):
    s=cv2.imread(path)
    if crop_white:
        m=(s.min(axis=2)<thr).astype(np.uint8); ys,xs=np.nonzero(m); s=s[ys.min():ys.max()+1,xs.min():xs.max()+1]
    return s
def tint(s,rgb,lo=0.35):   # recolour a sprite by luminance into one laser-safe hue (keeps white background white)
    L=cv2.cvtColor(s,cv2.COLOR_BGR2GRAY).astype(np.float32)/255; k=lo+(1-lo)*L
    out=np.stack([k*rgb[2],k*rgb[1],k*rgb[0]],-1); out[L>0.93]=255; return np.clip(out,0,255).astype(np.uint8)
def paste(can,s,cx,cy,w,F,flip=False,thr=238):
    """paste sprite s centred at (cx,cy) inches (page coords) with width w inches; white = transparent. returns (x0,y0,x1,y1) in page inches"""
    h=w*s.shape[0]/s.shape[1]; W,H=int(w*DPI),int(h*DPI); r=cv2.resize(s,(W,H),interpolation=cv2.INTER_AREA)
    if flip: r=r[:,::-1]
    x0=int((cx-w/2-F['x'])*DPI); y0=int((cy-h/2-F['y'])*DPI); reg=can[y0:y0+H,x0:x0+W]; m=r.min(axis=2)<thr; reg[m]=r[m]
    return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
def zone_mask(z,F,shape):
    m=np.zeros(shape[:2],np.uint8); P=lambda x,y:(int((x-F['x'])*DPI),int((y-F['y'])*DPI))
    if z['shape']=='circle': cv2.circle(m,P(z['cx'],z['cy']),int(z['r']*DPI),1,-1)
    elif z['shape']=='ellipse': cv2.ellipse(m,P(z['cx'],z['cy']),(int(z['rx']*DPI),int(z['ry']*DPI)),z.get('rot',0),0,360,1,-1)
    elif z['shape']=='rect': cv2.rectangle(m,P(z['x'],z['y']),P(z['x']+z['w'],z['y']+z['h']),1,-1)
    else: cv2.fillPoly(m,[np.array([P(*p) for p in z['pts']],np.int32)],1)
    return m>0
def check_zones(key,can,zones,F,lim=40):
    """detection check: max red-dominance inside every scoring / no-shoot zone must stay < lim (laser adds ~+100)."""
    rd=reddom(can); rep=[]
    for z in zones:
        if z['kind'] in('decor',): continue
        v=float(rd[zone_mask(z,F,can.shape)].max()); rep.append((z['name'],round(v)))
        assert v<lim, f'{key}: zone {z["name"]} too red ({v:.0f})'
    print(f'{key}: zone red-dominance max {max(v for _,v in rep)} (limit {lim}); whole art max {rd.max():.0f}')
def upsert(key,t,drills):
    old=T.get(key,{}); t.setdefault('drills',[d['id'] for d in drills]); T[key]=t
    global DR; ids={d['id'] for d in drills}; DR=[d for d in DR if d['id'] not in ids]+drills
def save():
    json.dump(DOC,open('targets.json','w'),indent=1); json.dump(DR,open('drills.json','w'),indent=1)
LETTER=dict(x=0.4,y=1.85,w=7.7,h=7.3); TAB=dict(x=0.4,y=1.85,w=16.2,h=7.3)
TABLAY={'page':{'w':17,'h':11},'field':dict(TAB)}
def canvas(F,col=255): return np.full((int(F['h']*DPI),int(F['w']*DPI),3),col,np.uint8)
def put_text(can,F,txt,cx,cy,hin,col=(255,255,255),th=None):
    fs=hin*DPI/22; (tw,thh),_=cv2.getTextSize(txt,cv2.FONT_HERSHEY_DUPLEX,fs,th or max(2,int(fs*2)))
    cv2.putText(can,txt,(int((cx-F['x'])*DPI-tw/2),int((cy-F['y'])*DPI+thh/2)),cv2.FONT_HERSHEY_DUPLEX,fs,col,th or max(2,int(fs*2)),cv2.LINE_AA)

# ---------------------------------------------------------------- Carnival Shoot
def carnival():
    F=LETTER; A='/cursor/stores/store-3672b900-d5c8-4311-a0e7-7fbd1aa29536/grok-bot/agents/e444fe30-cded-4aff-8bbf-d24560138655/assets/c0c9b7c638d03d6c0419caaf65b9349168236eebdaaef7e06f503095bf0eac85.jpg'
    import os; bgp='art/src2/booth.jpg'
    if not os.path.exists(bgp): import shutil; shutil.copy(A,bgp)
    bg=cv2.resize(cv2.imread(bgp),(int(F['w']*DPI),int(F['h']*DPI)),interpolation=cv2.INTER_AREA); can=bg.copy()
    X=lambda f:F['x']+f*F['w']; Y=lambda f:F['y']+f*F['h']; zones=[]
    # SHOOT sign (navy board, cream letters)
    sx0,sy0,sx1,sy1=X(.36),Y(.19),X(.64),Y(.27)
    cv2.rectangle(can,(int((sx0-F['x'])*DPI),int((sy0-F['y'])*DPI)),(int((sx1-F['x'])*DPI),int((sy1-F['y'])*DPI)),(70,40,20),-1)
    put_text(can,F,'SHOOT',(sx0+sx1)/2,(sy0+sy1)/2,0.42,(225,240,250))
    pig=tint(sprite('art/src2/pig.jpg'),(190,210,245)); duck=tint(sprite('art/src2/duck.jpg'),(255,240,175),0.25)
    # flying pigs
    for i,(fx,fy,fl) in enumerate([(.17,.33,False),(.83,.33,True),(.5,.40,False)]):
        x0,y0,x1,y1=paste(can,pig,X(fx),Y(fy),1.55,F,flip=fl)
        zones.append(dict(name=f'PIG{i+1}',kind='score',shape='ellipse',cx=round((x0+x1)/2+(0.05 if fl else -0.05),3),cy=round((y0+y1)/2+0.12,3),rx=round((x1-x0)*0.36,3),ry=round((y1-y0)*0.3,3),score=3,tier='tier3',art=True,subtle=True,tags=['pig','P'+str(i+1)],group='P'+str(i+1)))
    # bullseyes (navy/blue/yellow)
    for i,fx in enumerate([.2,.8]):
        cx,cy=X(fx),Y(.56)
        for r,col,sc in [(0.78,(95,60,25),1),(0.52,(200,140,60),3),(0.26,(170,240,250),5)]:
            cv2.circle(can,(int((cx-F['x'])*DPI),int((cy-F['y'])*DPI)),int(r*DPI),col,-1); cv2.circle(can,(int((cx-F['x'])*DPI),int((cy-F['y'])*DPI)),int(r*DPI),(30,20,10),3)
            zones.append(dict(name=f'BULL{i+1} {sc}',kind='score',shape='circle',cx=round(cx,3),cy=round(cy,3),r=r,score=sc,tier='tier1',art=True,subtle=True,tags=['bull','B'+str(i+1)],group='B'+str(i+1)))
    # duck rail
    ry=Y(.80); cv2.rectangle(can,(int((X(.04)-F['x'])*DPI),int((ry+0.38-F['y'])*DPI)),(int((X(.96)-F['x'])*DPI),int((ry+0.5-F['y'])*DPI)),(40,40,40),-1)
    for i in range(5):
        fx=.12+i*.19; x0,y0,x1,y1=paste(can,duck,X(fx),ry,1.2,F,flip=(i%2==1))
        zones.append(dict(name=f'DUCK{i+1}',kind='score',shape='ellipse',cx=round(X(fx),3),cy=round(y0+(y1-y0)*0.33,3),rx=0.5,ry=0.28,score=2,tier='tier1',art=True,subtle=True,tags=['duck','D'+str(i+1)],group='D'+str(i+1)))
    can=np.where(np.repeat(np.any([zone_mask(z,F,can.shape) for z in zones],axis=0)[...,None],3,2),safe(can),can)
    check_zones('carnival',can,zones,F)
    cv2.imwrite('art/carnival.png',can)
    calls=[dict(say=f'duck {i}',tags=[f'D{i}']) for i in range(1,6)]+[dict(say=f'pig {i}',tags=[f'P{i}']) for i in range(1,4)]+[dict(say=f'bullseye {i}',tags=[f'B{i}']) for i in (1,2)]+[dict(say='all pigs',tags=['pig'],n=3),dict(say='any duck',tags=['duck']),dict(say='two ducks',tags=['duck'],n=2)]
    t=dict(code='LD-401',name='Carnival Shoot',markerIds=[300,301,302,303],distance='3-5 yd',set='games',art=[dict(src='art/carnival.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'],warm=True)],zones=zones,
        instructions=['Free fire: duck 2, pig 3, bullseye 5/3/1.','Called mode: the app calls "duck 3", "all pigs"...','Wrong item = -2. Red is decor only.','Mic on. Say "start" or tap.'])
    D=[dict(id='carnival-free',name='Carnival Shoot: free fire (60 s)',category='fun',target='carnival',shots=20,startDelay=[2,3],parTime=30,timeout=60,notes='Shoot anything: duck 2, pig 3, bullseye 5/3/1.'),
       dict(id='carnival-calls',name='Carnival Shoot: called shots',category='fun',target='carnival',shots=40,startDelay=[2,3],parTime=60,timeout=120,game=dict(type='calls',calls=calls,rounds=8,wrong=-2),notes='The app calls an item ("duck 3", "all pigs"); hit it to get the next call. Wrong item -2.')]
    upsert('carnival',t,D)
GAMES=dict(carnival=carnival)
if __name__=='__main__':
    for k in (sys.argv[1:] or list(GAMES)): GAMES[k]()
    save(); print('ok games')
