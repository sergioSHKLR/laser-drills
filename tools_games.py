"""Game / training targets composited from rendered sprites (art/src2/*), laser-safe. Writes targets.json + drills.json entries.
Usage: python3 tools_games.py [carnival battle cards maritime ct fof]  (default all)"""
import json,sys,cv2,numpy as np
DPI=150
DOC=json.load(open('targets.json')); T=DOC['targets']; DR=json.load(open('drills.json'))
def safe(img,cap=30):   # compress red-dominance (r-(g+b)/2) to <=cap so the red laser always stands out
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]; e=np.maximum(0,r-(g+b)/2-cap)
    dg=np.minimum(255-g,2*e); g=g+dg; b=np.minimum(255,b+np.maximum(0,2*e-dg)); d=r-(g+b)/2; r=r-np.maximum(0,d-cap)  # lighten (pale yellow) before cutting red
    return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
def reddom(img): b,g,r=[c.astype(np.float32) for c in cv2.split(img)]; return r-(g+b)/2
def sprite(path,crop_white=True,thr=235):
    s=cv2.imread(path)
    if crop_white:
        m=(s.min(axis=2)<thr).astype(np.uint8); m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
        n,lab,st,_=cv2.connectedComponentsWithStats(m); H,W=m.shape
        keep=[i for i in range(1,n) if st[i][4]>1500 and not (st[i][0]<=1 or st[i][1]<=1 or st[i][0]+st[i][2]>=W-1 or st[i][1]+st[i][3]>=H-1)]
        x0=min(st[i][0] for i in keep); y0=min(st[i][1] for i in keep); x1=max(st[i][0]+st[i][2] for i in keep); y1=max(st[i][1]+st[i][3] for i in keep)
        s=s[y0:y1,x0:x1].copy(); s[(np.isin(lab[y0:y1,x0:x1],keep)==0)]=255
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
def check_zones(key,can,zones,F,lim=40,ignore=None):
    """detection check: max red-dominance inside every scoring / no-shoot zone must stay < lim (laser adds ~+100)."""
    rd=reddom(can); rep=[]
    for z in zones:
        if z['kind'] in('decor',): continue
        zm=zone_mask(z,F,can.shape)
        if ignore is not None: zm=zm&~ignore   # red decor (e.g. card pips) is non-scoring, excluded
        v=float(rd[zm].max()); rep.append((z['name'],round(v)))
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
    """Carnival booth traced from Sergio's reference flat illustration (art/src2/carnival_ref.png): same pink winged pigs,
    red/white/blue bullseyes, yellow ducks with orange beaks, dark rail and posts; striped background removed.
    Red rings are decor (non-scoring); scoring = pig 3, duck 2, bullseye white 3 / blue center 5."""
    F=LETTER; zones=[]
    ref=cv2.imread('art/src2/carnival_ref.png')[419:2075,92:1838].copy()
    ref[:, :180]=255; ref[:,1580:]=255                       # drop the frame edge lines
    ref[ref.min(2)>190]=255                                  # stripes (peach / off-white) -> plain white
    Wp,Hp=int(F['w']*DPI),int(F['h']*DPI); can=cv2.resize(ref,(Wp,Hp),interpolation=cv2.INTER_AREA)
    k=Wp/ref.shape[1]; b,g,r=[c.astype(int) for c in cv2.split(can)]
    def comps(m,minA):
        m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); cs=[c for c in cs if cv2.contourArea(c)>minA]
        return sorted(cs,key=lambda c:(round(cv2.boundingRect(c)[1]/60),cv2.boundingRect(c)[0]))
    IN=lambda x,y:(round(F['x']+x/DPI,3),round(F['y']+y/DPI,3))
    poly=lambda c:[list(IN(*p)) for p in cv2.approxPolyDP(c,2,True)[:,0]]
    pink=(r>190)&(b>170)&(g<190); yel=(r>200)&(g>190)&(b<120)
    blue=(b>180)&(r<90); red=(r>180)&(g<80)&(b<80)
    for i,c in enumerate(comps(pink,800)):   # pigs: body contour (+ wing, enclosed by outline close)
        zones.append(dict(name=f'PIG{i+1}',kind='score',shape='poly',pts=poly(c),score=3,tier='tier3',art=True,subtle=True,tags=['pig','P'+str(i+1)],group='P'+str(i+1)))
    for i,c in enumerate(comps(red,800)):
        (x,y),R=cv2.minEnclosingCircle(c); cx,cy=IN(x,y); Rin=R/DPI
        bl=[cv2.minEnclosingCircle(q)[1] for q in comps(blue&(np.hypot(*np.meshgrid(np.arange(Wp)-x,np.arange(Hp)-y))<R),50)]
        rb=(max(bl) if bl else R*0.3)/DPI
        rr_=[np.hypot(*(np.argwhere(red[int(y)-int(R):int(y)+int(R)+1,int(x)-int(R):int(x)+int(R)+1])-[R,R]).T).min()]
        rw=(rr_[0]-2)/DPI
        for rr,sc in [(rw,3),(rb,5)]:
            zones.append(dict(name=f'BULL{i+1} {sc}',kind='score',shape='circle',cx=cx,cy=cy,r=round(rr,3),score=sc,tier='tier1',art=True,subtle=True,tags=['bull','B'+str(i+1)],group='B'+str(i+1)))
    ds=comps(yel,800); ys=sorted(cv2.boundingRect(c)[1] for c in ds); mid=(ys[0]+ys[-1])/2
    for i,c in enumerate(ds):
        big=cv2.boundingRect(c)[1]>mid
        zones.append(dict(name=f'DUCK{i+1}',kind='score',shape='poly',pts=poly(c),score=2,tier='tier1',art=True,subtle=True,tags=['duck','D'+str(i+1),'big' if big else 'small'],group='D'+str(i+1)))
    rd=reddom(can); rep={z['name']:(round(float(rd[zone_mask(z,F,can.shape)].max())),round(float(np.median(rd[zone_mask(z,F,can.shape)])))) for z in zones}
    risk={n:v for n,v in rep.items() if v[1]>=40}
    print('carnival: zones',len(zones),'| red-dominance per zone (max, median)',rep,'| AT RISK (median>=40):',risk or 'none')
    json.dump(rep,open('/tmp/carnival_rd.json','w'))
    cv2.imwrite('art/carnival.png',can)
    calls=[dict(say=f'duck {i}',tags=[f'D{i}']) for i in range(1,8)]+[dict(say=f'pig {i}',tags=[f'P{i}']) for i in range(1,4)]+[dict(say=f'bullseye {i}',tags=[f'B{i}']) for i in range(1,6)]+[dict(say='all pigs',tags=['pig'],n=3),dict(say='any duck',tags=['duck']),dict(say='two ducks',tags=['duck'],n=2),dict(say='small duck',tags=['small']),dict(say='big duck',tags=['big'])]
    t=dict(code='LD-401',name='Carnival Shoot',markerIds=[300,301,302,303],distance='3-5 yd',set='games',art=[dict(src='art/carnival.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'],warm=True)],zones=zones,
        legend=[['#E99AD8','Flying pig (P1-P3): 3 pts'],['#1AA3E0','Bullseye blue center: 5 pts'],['#FFFFFF','Bullseye white ring: 3 pts'],['#E52020','Red ring: decor, 0 pts'],['#FFE600','Duck (D1-D4 rail, D5-D7 posts): 2 pts'],['#FFFFFF','Background: miss, 0 pts']],
        instructions=['Free fire: pig 3, duck 2, bullseye blue 5 / white 3 (red ring 0).','Pigs P1-3 left to right; bullseyes B1-B5 top row first.','Ducks D1-D4 on the rail, D5-D7 on posts.','Called mode: "duck 3", "all pigs"... wrong item -2.','Mic on. Say "start" or tap.'])
    D=[dict(id='carnival-free',name='Carnival Shoot: free fire (60 s)',category='fun',target='carnival',shots=20,startDelay=[2,3],parTime=30,timeout=60,notes='Shoot anything: pig 3, duck 2, bullseye blue 5 / white 3; red ring scores 0.'),
       dict(id='carnival-calls',name='Carnival Shoot: called shots',category='fun',target='carnival',shots=40,startDelay=[2,3],parTime=60,timeout=120,game=dict(type='calls',calls=calls,rounds=8,wrong=-2),notes='The app calls an item ("duck 3", "bullseye 5", "all pigs", "small duck"); hit it to get the next call. Wrong item -2.')]
    upsert('carnival',t,D)
GAMES=dict(carnival=carnival)

# ---------------------------------------------------------------- PIL helpers (vector-ish text / suit glyphs)
from PIL import Image,ImageDraw,ImageFont
def font(sz,bold=True): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if bold else ''),int(sz))
def pil(F,col=(255,255,255)): return Image.new('RGB',(int(F['w']*DPI),int(F['h']*DPI)),col)
def tocv(im): return cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR)
def ctext(d,xy,t,f,fill): d.text(xy,t,font=f,fill=fill,anchor='mm')

# ---------------------------------------------------------------- Sink-the-Ship (8x8 battleship grid)
def battle(key='battle',F=LETTER,mk=(304,305,306,307),code='LD-402',n=8):
    im=pil(F); d=ImageDraw.Draw(im); cell=min((F['w']-0.6)/n,(F['h']-0.6)/n); gx=F['x']+(F['w']-cell*n)/2+0.25; gy=F['y']+(F['h']-cell*n)/2+0.25
    P=lambda x,y:((x-F['x'])*DPI,(y-F['y'])*DPI); zones=[]
    for r in range(n):
        ctext(d,P(gx-0.27,gy+(r+.5)*cell),chr(65+r),font(0.34*DPI),(31,45,90))
        for c in range(n):
            x0,y0=gx+c*cell,gy+r*cell; col=(214,232,246) if (r+c)%2 else (190,216,238)
            d.rectangle([P(x0,y0),P(x0+cell,y0+cell)],fill=col,outline=(31,45,90),width=3)
            ctext(d,P(x0+cell/2,y0+cell/2),f'{chr(65+r)}{c+1}',font(0.16*DPI,False),(120,140,170))
            zones.append(dict(name=f'{chr(65+r)}{c+1}',kind='score',shape='rect',x=round(x0,3),y=round(y0,3),w=round(cell,3),h=round(cell,3),score=1,tier='tier1',subtle=True,art=True,noGrow=True,tags=[f'{chr(65+r)}{c+1}']))
    for c in range(n): ctext(d,P(gx+(c+.5)*cell,gy-0.27),str(c+1),font(0.34*DPI),(31,45,90))
    can=tocv(im); check_zones(key,can,zones,F); cv2.imwrite(f'art/{key}.png',can)
    ships=[dict(name='carrier',len=5),dict(name='battleship',len=4),dict(name='cruiser',len=3),dict(name='submarine',len=3),dict(name='destroyer',len=2)]
    t=dict(code=code,name='Sink-the-Ship (8x8)',markerIds=list(mk),distance='3-7 yd',set='games',art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'])],zones=zones,
        instructions=['The app hides a random fleet (5 ships, 17 cells).','Shoot a cell: it says hit, miss or "you sunk my cruiser".','Score = shots to sink the whole fleet (lower is better).','Timed mode: same game against a 3 min clock.'])
    D=[dict(id='battle-classic',name='Sink-the-Ship: sink the fleet',category='fun',target=key,shots=64,startDelay=[1,2],parTime=600,timeout=1800,game=dict(type='battle',rows=n,cols=n,ships=ships),notes='Random hidden fleet. Fewest shots wins.'),
       dict(id='battle-timed',name='Sink-the-Ship: timed (3 min)',category='fun',target=key,shots=64,startDelay=[1,2],parTime=180,timeout=180,game=dict(type='battle',rows=n,cols=n,ships=ships),notes='Sink as much as you can in 3 minutes.')]
    upsert(key,t,D)
GAMES['battle']=battle

# ---------------------------------------------------------------- Card game (52-card standard 2-colour deck; pastel-red hearts/diamonds, laser-safe; poker + call-out)
SUITS=[('S','\u2660','spades',(25,25,25)),('H','\u2665','hearts',(222,188,188)),('D','\u2666','diamonds',(222,188,188)),('C','\u2663','clubs',(25,25,25))]
RANKS=[('A','ace'),('2','two'),('3','three'),('4','four'),('5','five'),('6','six'),('7','seven'),('8','eight'),('9','nine'),('T','ten'),('J','jack'),('Q','queen'),('K','king')]
def cards(key='cards',F=LETTER,mk=(308,309,310,311),code='LD-403',grid=(8,7),lay=None):
    im=pil(F,(236,240,236)); d=ImageDraw.Draw(im); P=lambda x,y:((x-F['x'])*DPI,(y-F['y'])*DPI); zones=[]
    cols,rows=grid; cw,ch=F['w']/cols,F['h']/rows; w=min(cw*0.9,ch*0.9*0.7); h=w/0.7; i=0
    deck=[(r,s) for s in SUITS for r in RANKS]
    for k,(r,s) in enumerate(deck):
        row,col=divmod(k,cols); left=len(deck)-row*cols; off=(cols-min(cols,left))*cw/2
        cx=F['x']+off+(col+.5)*cw; cy=F['y']+(row+.5)*ch; x0,y0=cx-w/2,cy-h/2
        d.rounded_rectangle([P(x0,y0),P(x0+w,y0+h)],radius=0.07*DPI,fill=(255,255,255),outline=(90,90,90),width=3)
        rl='10' if r[0]=='T' else r[0]
        d.text(P(x0+0.06,y0+0.04),rl,font=font(w*0.27*DPI),fill=s[3]); d.text(P(x0+0.06,y0+0.04+w*0.3),s[1],font=font(w*0.22*DPI,False),fill=s[3])
        ctext(d,P(cx+w*0.08,cy+h*0.08),s[1],font(w*0.62*DPI,False),s[3])
        c=r[0]+s[0]; zones.append(dict(name=c,kind='score',shape='rect',x=round(x0,3),y=round(y0,3),w=round(w,3),h=round(h,3),score=1,tier='tier1',subtle=True,art=True,noGrow=True,tags=[c,s[2],r[1]+'s']))
    can=tocv(im); check_zones(key,can,zones,F); cv2.imwrite(f'art/{key}.png',can)
    calls=[dict(say=f'{rn} of {sw}',tags=[r+sc]) for r,rn in RANKS for sc,_,sw,_ in SUITS]+[dict(say=f'any {sw[:-1]}',tags=[sw]) for _,_,sw,_ in SUITS]+[dict(say=f'any {rn}',tags=[rn+'s']) for _,rn in RANKS[::3]]
    t=dict(code=code,name='Card Shoot'+(' (Tabloid)' if lay else ''),markerIds=list(mk),distance='3-5 yd',set='games',art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'])],zones=zones,
        instructions=['Standard deck: spades/clubs black, hearts/diamonds pastel red (laser-safe).','The whole card scores, pips included.','Poker: shoot 5 cards, the app scores your best hand.','Call-out: the app calls "queen of hearts", "any club"...','Wrong card -2.'])
    if lay: t['layout']=lay
    sfx='' if not lay else '-tab'
    D=[dict(id='cards-poker'+sfx,name='Card Shoot: poker hand'+(' (Tabloid)' if lay else ''),category='fun',target=key,shots=5,startDelay=[1,2],parTime=30,timeout=120,game=dict(type='poker'),notes='Shoot five different cards; score = hand rank x10 (royal flush 90).'),
       dict(id='cards-callout'+sfx,name='Card Shoot: call-out'+(' (Tabloid)' if lay else ''),category='fun',target=key,shots=40,startDelay=[1,2],parTime=60,timeout=180,game=dict(type='calls',calls=calls,rounds=8,wrong=-2),notes='Hit the called card ("queen of hearts", "any club").')]
    upsert(key,t,D)
GAMES['cards']=cards
GAMES['cards-tabloid']=lambda:cards('cards-tabloid',TAB,(336,337,338,339),'LD-404',(13,4),TABLAY)

# ---------------------------------------------------------------- Maritime Interdiction (light seascape; civilians no-shoot; go-fast / semi-sub hull -1, engine -0)
VESSEL=dict(  # threat zones in fractions of the cropped sprite: (fx0,fy0,fx1,fy1)
    gofast=dict(hull=(0.02,0.55,0.86,0.97),eng=(0.81,0.38,1.0,0.95),tags=['gofast','smuggler','fast']),
    semisub=dict(hull=(0.02,0.35,0.76,0.95),eng=(0.76,0.1,0.99,0.98),tags=['semisub','smuggler']),
    speedboat=dict(civ=True,tags=['speedboat','fast','civilian']),
    fishing=dict(civ=True,tags=['fishing','civilian']),sail=dict(civ=True,tags=['sailboat','civilian']),yacht=dict(civ=True,tags=['yacht','civilian']),
    jetski=dict(civ=True,tags=['jetski','civilian']),ferry=dict(civ=True,tags=['ferry','civilian']),kayaks=dict(civ=True,tags=['kayak','civilian']))
def seascape(F):
    h=int(F['h']*DPI); w=int(F['w']*DPI); can=np.zeros((h,w,3),np.uint8); hz=int(h*0.1)
    for y in range(h):
        if y<hz: c=(250,240,228)
        else: t=(y-hz)/(h-hz); c=(int(246-26*t),int(236-26*t),int(222-30*t))   # BGR pale sea
        can[y]=c
    cv2.line(can,(0,hz),(w,hz),(200,190,175),2)
    rng=np.random.default_rng(7)
    for _ in range(int(w*h/9000)):
        x,y=int(rng.integers(0,w)),int(rng.integers(hz+8,h)); L=int(rng.integers(10,40)); cv2.line(can,(x,y),(x+L,y),(214,200,186),2)
    return can
def maritime(key='maritime',F=LETTER,mk=(312,313,314,315),code='LD-501',place=None,lay=None):
    can=seascape(F); zones=[]; cnt={}
    for v,fx,fy,w,fl in place:
        sp=safe(sprite(f'art/src2/{v}.jpg')); x0,y0,x1,y1=paste(can,sp,F['x']+fx*F['w'],F['y']+fy*F['h'],w,F,flip=fl)
        V=VESSEL[v]; cnt[v]=cnt.get(v,0)+1; n=f'{v.upper()}{cnt[v]}'; W,H=x1-x0,y1-y0
        def R(b):
            a,b2,c,d=b
            if fl: a,c=1-c,1-a
            return dict(shape='rect',x=round(x0+a*W,3),y=round(y0+b2*H,3),w=round((c-a)*W,3),h=round((d-b2)*H,3))
        if V.get('civ'): zones.append(dict(name=n+' NS',kind='noshoot',penalty=-10,group=n,tags=V['tags']+[n],art=True,subtle=True,**R((0.03,0.05,0.97,0.97))))
        else:
            zones.append(dict(name=n+' ENGINE',kind='score',score=0,tier='tier5',z=2,group=n,part='engine',tags=V['tags']+[n,'engine'],art=True,subtle=True,noGrow=True,**R(V['eng'])))
            zones.append(dict(name=n+' HULL',kind='score',score=-1,tier='tier3',z=1,group=n,part='hull',tags=V['tags']+[n,'hull'],art=True,subtle=True,noGrow=True,**R(V['hull'])))
    check_zones(key,can,zones,F); cv2.imwrite(f'art/{key}.png',can)
    thr=sorted({z['group'] for z in zones if z['kind']=='score'})
    easy=[dict(say=f'disable {g[:-1].replace("GOFAST","go-fast").replace("SEMISUB","semi-sub").lower()} {g[-1]}, engine',tags=[g]) for g in thr]
    med=[dict(say='disable the semi-sub',tags=['semisub']),dict(say='disable a go-fast',tags=['gofast']),dict(say='stop all smugglers',tags=['smuggler'],n=len(thr))]
    hard=[dict(say='engage the smuggler',tags=['smuggler']),dict(say='stop the drug boat',tags=['gofast']),dict(say='fast mover with cargo, disable',tags=['gofast'])]
    sfx='-tab' if lay else ''; nm=' (Tabloid)' if lay else ''
    G=lambda c,r:dict(type='calls',calls=c,rounds=r,noShoot=-20,wrong=-2)
    t=dict(code=code,name='Maritime Interdiction'+nm,markerIds=list(mk),distance='5-10 yd',set=None,art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'])],zones=zones,
        instructions=['Engines = -0 (disabling fire), hull = -1.','All civilian craft (fishing, sail, yacht, jet ski, ferry, kayaks, sport boat) are NO-SHOOT: -20.','Decision mode: only fast boats with bales/drums are smugglers.','Mic on. Say "start" or tap.'])
    if lay: t['layout']=lay
    t.pop('set')
    D=[dict(id='mar-easy'+sfx,name='Maritime: easy (named target)'+nm,category='training',target=key,shots=20,startDelay=[2,3],parTime=30,timeout=60,game=G(easy,len(thr)),notes='The app names the boat. Aim at the engines.'),
       dict(id='mar-med'+sfx,name='Maritime: medium (by type)'+nm,category='training',target=key,shots=20,startDelay=[2,3],parTime=30,timeout=60,game=G(med,4),notes='The app calls a craft type. Civilians -20.'),
       dict(id='mar-decision'+sfx,name='Maritime: decision (smuggler or civilian?)'+nm,category='training',target=key,shots=20,startDelay=[2,4],parTime=20,timeout=45,game=G(hard,4),notes='Some fast boats are civilian (no cargo). Only engage boats with bales/drums or the semi-sub.')]
    upsert(key,t,D)
GAMES['maritime']=lambda:maritime(place=[('ferry',.22,.14,2.6,False),('sail',.55,.12,1.3,False),('yacht',.83,.15,2.4,True),
    ('gofast',.27,.38,3.0,False),('fishing',.77,.37,2.4,True),('semisub',.3,.62,3.3,False),('jetski',.8,.62,1.5,True),('kayaks',.22,.87,2.4,False),('speedboat',.72,.87,3.0,True)])
GAMES['maritime-tabloid']=lambda:maritime('maritime-tabloid',TAB,(316,317,318,319),'LD-502',lay=TABLAY,place=[
    ('ferry',.12,.15,3.0,False),('sail',.33,.12,1.4,False),('yacht',.55,.15,2.8,True),('fishing',.83,.16,2.6,True),
    ('gofast',.15,.48,3.2,False),('speedboat',.43,.47,3.2,True),('semisub',.72,.48,3.6,False),('jetski',.95,.47,1.2,True),
    ('kayaks',.13,.83,2.6,False),('gofast',.42,.83,3.2,True),('jetski',.62,.82,1.5,False),('speedboat',.83,.83,3.0,False)])

# ---------------------------------------------------------------- Counter-Terror (market street; militants by kit; civilians no-shoot; vest = head-only)
FIG=dict(  # head ellipse (fx,fy,frx,fry), torso rect (fx0,fy0,fx1,fy1) in cropped-sprite fractions
    hamas=dict(head=(.47,.07,.13,.06),torso=(.15,.14,.8,.5),tags=['hamas','headband','camo','ak'],say='green headband'),
    hezb=dict(head=(.6,.15,.12,.06),torso=(.3,.22,.9,.52),tags=['hezbollah','olive','rpg'],say='olive with R P G'),
    irgc=dict(head=(.52,.07,.12,.06),torso=(.2,.14,.85,.5),tags=['irgc','uniform','cap'],say='uniform and cap'),
    houthi=dict(head=(.45,.07,.15,.06),torso=(.15,.14,.8,.5),tags=['houthi','thobe','jambiya','keffiyeh'],say='thobe and dagger'),
    vest=dict(head=(.45,.07,.13,.06),torso=(.08,.13,.92,.56),tags=['vest'],say='vest!'),
    civ1=dict(civ=True,tags=['civilian']),civ2=dict(civ=True,tags=['civilian']),civ3=dict(civ=True,tags=['civilian']))
def market(F):
    bg=cv2.resize(cv2.imread('art/src3/market.jpg'),(int(F['w']*DPI),int(F['h']*DPI)),interpolation=cv2.INTER_AREA)
    bg=cv2.addWeighted(bg,0.55,np.full_like(bg,255),0.45,0)
    # accent bunting along the top edge (red / butter-yellow / green) - decor only, above every zone
    W=bg.shape[1]; cols=[(40,40,200),(175,240,255),(80,150,40)]; n=int(W/40)
    cv2.line(bg,(0,12),(W,12),(60,60,60),2)
    for i in range(n): x=i*40; cv2.fillPoly(bg,[np.array([(x+3,12),(x+37,12),(x+20,52)],np.int32)],cols[i%3])
    return bg
def ct(key='ct',F=LETTER,mk=(320,321,322,323),code='LD-503',place=None,lay=None):
    can=market(F); zones=[]; cnt={}; vis=[]
    for nm,fx,fy,h,fl in place:
        sp=sprite(f'art/src3/{nm}.jpg'); w=h*sp.shape[1]/sp.shape[0]
        x0,y0,x1,y1=paste(can,sp,F['x']+fx*F['w'],F['y']+fy*F['h'],w,F,flip=fl); W,H=x1-x0,y1-y0
        V=FIG[nm]; base=nm.rstrip('0123456789'); cnt[base]=cnt.get(base,0)+1; n=f'{base.upper()}{cnt[base]}'
        X=lambda a:x0+((1-a) if fl else a)*W
        if V.get('civ'):
            zones.append(dict(name=n+' NS',kind='noshoot',penalty=-10,group=n,tags=V['tags']+[n],art=True,subtle=True,shape='rect',x=round(x0+.04*W,3),y=round(y0+.01*H,3),w=round(.92*W,3),h=round(.98*H,3)))
            continue
        hx,hy,rx,ry=V['head']; a,b,c,d=V['torso']
        if fl: a,c=1-c,1-a
        head=dict(name=n+' HEAD',kind='score',score=0,tier='tier5',z=2,group=n,shape='ellipse',cx=round(X(hx),3),cy=round(y0+hy*H,3),rx=round(rx*W,3),ry=round(ry*H,3),tags=V['tags']+[n,'militant'],art=True,subtle=True,noGrow=True)
        body=dict(shape='rect',x=round(x0+a*W,3),y=round(y0+b*H,3),w=round((c-a)*W,3),h=round((d-b)*H,3),group=n,art=True,subtle=True,noGrow=True)
        if base=='vest':
            head['headOnly']=True; head['tags']=['vest',n]
            zones+= [head,dict(name=n+' VEST',kind='score',score=-1,tier='tier3',z=1,tags=['vest-body'],**body)]
        else: zones+=[head,dict(name=n+' BODY',kind='score',score=-1,tier='tier3',z=1,tags=V['tags']+[n,'militant'],**body)]
    m=np.any([zone_mask(z,F,can.shape) for z in zones],axis=0)
    b,g,r=[c.astype(np.float32) for c in cv2.split(can)]; r2=np.minimum(r,(g+b)/2+28)  # cut red (skin -> neutral tan), no lime cast
    cs=cv2.merge([b,g,r2]).astype(np.uint8); can=np.where(np.repeat(m[...,None],3,2),cs,can)
    check_zones(key,can,zones,F); cv2.imwrite(f'art/{key}.png',can)
    present=[k for k in FIG if not FIG[k].get('civ') and any(z['group'].startswith(k.upper()) for z in zones)]
    calls=[dict(say=FIG[k]['say'],tags=[FIG[k]['tags'][0]]) for k in present]
    allm=[dict(say='all militants',tags=['militant'],n=sum(1 for z in zones if z['name'].endswith('BODY')))]
    sfx='-tab' if lay else ''; nmx=' (Tabloid)' if lay else ''
    G=lambda c,r:dict(type='calls',calls=c,rounds=r,noShoot=-20,vest=-5,wrong=-2)
    t=dict(code=code,name='Counter-Terror'+nmx,markerIds=list(mk),distance='5-7 yd',art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'],warm=True)],zones=zones,
        instructions=['Head -0, body -1. Militants are told apart by kit only.','Civilians are NO-SHOOT: -20.','Vest wearer: head shot only. Any body hit = VEST STRIKE (+5 s, -5).','Mic on. Say "start" or tap.'])
    if lay: t['layout']=lay
    D=[dict(id='ct-kit'+sfx,name='Counter-Terror: call by kit'+nmx,category='training',target=key,shots=20,startDelay=[2,3],parTime=30,timeout=60,game=G(calls,6),notes='The app calls a kit ("green headband", "thobe and dagger", "vest!"). Civilians -20.'),
       dict(id='ct-vest'+sfx,name='Counter-Terror: vest!'+nmx,category='training',target=key,shots=10,startDelay=[2,5],parTime=10,timeout=30,game=G([dict(say='vest!',tags=['vest'])],3),notes='Head-only on the vest wearer. Body hit = vest strike.'),
       dict(id='ct-clear'+sfx,name='Counter-Terror: clear the street'+nmx,category='training',target=key,shots=30,startDelay=[2,3],parTime=30,timeout=60,game=G(allm+[dict(say='vest!',tags=['vest'])],2),notes='Every militant, then the vest wearer (head only).')]
    upsert(key,t,D)
GAMES['ct']=lambda:ct(place=[('hamas',.12,.3,3.2,False),('civ1',.37,.33,2.6,False),('irgc',.62,.3,3.2,True),('civ2',.88,.33,2.6,False),
    ('hezb',.13,.76,3.3,False),('vest',.39,.76,3.3,False),('civ3',.64,.78,2.9,True),('houthi',.88,.76,3.3,True)])
GAMES['ct-tabloid']=lambda:ct('ct-tabloid',TAB,(324,325,326,327),'LD-504',lay=TABLAY,place=[
    ('hamas',.06,.3,3.2,False),('civ1',.19,.33,2.6,False),('irgc',.32,.3,3.2,True),('civ2',.45,.33,2.6,False),('houthi',.58,.3,3.2,False),('civ3',.72,.33,2.6,False),('hezb',.87,.3,3.2,True),
    ('hezb',.07,.76,3.3,False),('civ2',.2,.78,2.9,True),('vest',.34,.76,3.3,False),('civ1',.48,.78,2.9,True),('hamas',.62,.76,3.3,True),('civ3',.76,.78,2.9,False),('houthi',.92,.76,3.3,True)])

# ---------------------------------------------------------------- Friend or Foe (same camo; tape bands yellow / blue vs white; partial cover)
SOL=dict(  # head ellipse + torso rect in cropped-sprite fractions; side tag = tape colour
    y1=dict(head=(.4,.1,.14,.08),torso=(.08,.19,.66,.52),tape='yellow'),
    y2=dict(head=(.57,.14,.13,.09),torso=(.25,.24,.92,.62),tape='yellow'),
    w1=dict(head=(.37,.1,.14,.08),torso=(.1,.18,.62,.5),tape='white'),
    w2=dict(head=(.37,.14,.13,.09),torso=(.06,.25,.6,.63),tape='white'),
    b1=dict(head=(.47,.08,.14,.07),torso=(.15,.15,.85,.47),tape='blue'))
def fof(key='fof',F=LETTER,mk=(328,329,330,331),code='LD-505',rows=None,lay=None,drones=()):
    Wp,Hp=int(F['w']*DPI),int(F['h']*DPI); bg=cv2.resize(cv2.imread('art/src3/fofbg.jpg'),(Wp,Hp),interpolation=cv2.INTER_AREA)
    bg=cv2.addWeighted(bg,0.8,np.full_like(bg,255),0.2,0); can=bg.copy(); zones=[]; cnt={}
    def poly(pts): m=np.zeros((Hp,Wp),np.uint8); cv2.fillPoly(m,[np.array([(int(x*Wp),int(y*Hp)) for x,y in pts],np.int32)],1); return m>0
    sand=[(.03,.47),(.2,.45),(.5,.44),(.8,.45),(.98,.5),(.98,.62),(.03,.57)]; trench=[(0,.67),(.5,.72),(1,.81),(1,1),(0,1)]
    def top(pts,x):   # cover top edge y-fraction at x-fraction (piecewise linear over first points up to the right end)
        edge=[p for p in pts if p[1]<=min(q[1] for q in pts)+0.15][:5]; edge.sort()
        return float(np.interp(x,[p[0] for p in edge],[p[1] for p in edge]))
    for ri,(cover,figs) in enumerate(rows):
        for nm,fx,fy,h,fl in figs:
            sp=safe(sprite(f'art/src3/{nm}.jpg')); w=h*sp.shape[1]/sp.shape[0]
            x0,y0,x1,y1=paste(can,sp,F['x']+fx*F['w'],F['y']+fy*F['h']-h/2,w,F,flip=fl); W,H=x1-x0,y1-y0
            V=SOL[nm]; side=V['tape']; cnt[side]=cnt.get(side,0)+1; n=f'{side.upper()}{cnt[side]}'
            hx,hy,rx,ry=V['head']; a,b,c,d=V['torso']
            if fl: a,c,hx=1-c,1-a,1-hx
            yb=y0+d*H
            if cover: yb=min(yb,F['y']+top(cover,((x0+x1)/2-F['x'])/F['w'])*F['h']-0.03)
            tg=[side,n,'soldier']+(['allied'] if side in('yellow','blue') else ['opfor'])
            zones.append(dict(name=n+' HEAD',kind='score',score=0,tier='tier5',z=2*ri+2,group=n,shape='ellipse',cx=round(x0+hx*W,3),cy=round(y0+hy*H,3),rx=round(rx*W,3),ry=round(ry*H,3),tags=tg,art=True,subtle=True,noGrow=True))
            if yb>y0+b*H+0.1: zones.append(dict(name=n+' BODY',kind='score',score=-1,tier='tier3',z=2*ri+1,group=n,shape='rect',x=round(x0+a*W,3),y=round(y0+b*H,3),w=round((c-a)*W,3),h=round(yb-(y0+b*H),3),tags=tg,art=True,subtle=True,noGrow=True))
        if cover: m=poly(cover); can[m]=bg[m]
    import tools_ankle_split as TS
    DS=[TS.split(f'art/src5/drone{i}.png')[0] for i in range(4)]
    DN=[('FPV','fpv quad',5),('MAVIC','mavic quad',4),('HEXA','bomber hexacopter',3),('SHAHED','shahed',2)]
    for di,fx,fy,w in drones:
        sp=safe(DS[di]); tmp=np.full_like(can,255); paste(tmp,sp,F['x']+fx*F['w'],F['y']+fy*F['h'],w,F); m=tmp.min(2)<238; can[m]=tmp[m]
        mm=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
        cs,_=cv2.findContours(mm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=cv2.approxPolyDP(max(cs,key=cv2.contourArea),3,True)[:,0]
        nm,say,sc=DN[di]; cnt[nm]=cnt.get(nm,0)+1; n=f'{nm}{cnt[nm]}'
        zones.append(dict(name=n,kind='score',score=sc,tier='tier1',z=20,group=n,shape='poly',pts=[[round(F['x']+x/DPI,3),round(F['y']+y/DPI,3)] for x,y in c],tags=['drone',nm.lower(),n],art=True,subtle=True))
    for nmc,pts in (('SANDBAGS',SAND),('TRENCH',TR)):
        zones.append(dict(name=nmc,kind='hardcover',shape='poly',pts=[[round(F['x']+x*F['w'],3),round(F['y']+y*F['h'],3)] for x,y in pts],art=True,subtle=True))
    m=np.any([zone_mask(z,F,can.shape) for z in zones if z['kind']=='score'],axis=0)
    can=np.where(np.repeat(m[...,None],3,2),safe(can),can)
    check_zones(key,can,[z for z in zones if z['kind']=='score'],F); cv2.imwrite(f'art/{key}.png',can)
    sides=sorted({z['tags'][0] for z in zones if z['kind']=='score' and 'drone' not in z['tags']})
    A=[s for s in sides if s!='white']
    calls=[dict(say='friendlies '+' and '.join(A)+'. Engage white tape',tags=['white'],forbid=A),
           dict(say='friendlies white. Engage '+' and '.join(A)+' tape',tags=A,forbid=['white'])]+\
          [dict(say=f'engage {s} tape only',tags=[s],forbid=[o for o in sides if o!=s]) for s in sides]
    sfx='-tab' if lay else ''; nmx=' (Tabloid)' if lay else ''
    G=lambda c,r:dict(type='calls',calls=c,rounds=r,fratricide=-25,wrong=-2)
    t=dict(code=code,name='Friend or Foe'+nmx,markerIds=list(mk),distance='5-10 yd',art=[dict(src=f'art/{key}.png',x=F['x'],y=F['y'],w=F['w'],h=F['h'])],zones=zones,
        instructions=['Same camo on both sides: read the TAPE bands (yellow, blue, white).','Each round the app names the friendly side and the tape to engage.','Hitting a friendly = FRATRICIDE -25. Head -0, body -1.','Drones overhead are always hostile: FPV 5, Mavic 4, hexacopter 3, Shahed 2.','Sandbags / trench are hard cover (no score). Mic on, say "start".'],
        legend=[['tier5','Soldier head: -0'],['tier3','Soldier body: -1'],['noshoot','Friendly tape hit = FRATRICIDE -25'],['tier1','Drone: FPV 5 / Mavic 4 / hexa 3 / Shahed 2'],['cover','Sandbags / trench = hard cover'],['#FFFFFF','Outside: miss']])
    if lay: t['layout']=lay
    D=[dict(id='fof-sides'+sfx,name='Friend or Foe: sides'+nmx,category='training',target=key,shots=30,startDelay=[2,3],parTime=30,timeout=60,game=G(calls[:2],4),notes='The app assigns the friendly side each round. Fratricide -25.'),
       dict(id='fof-tape'+sfx,name='Friend or Foe: single tape'+nmx,category='training',target=key,shots=30,startDelay=[2,4],parTime=20,timeout=45,game=G(calls[2:],5),notes='Engage one tape colour only; all others are friendly. Fratricide -25.')]
    if drones:
        dc=[dict(say='drone! '+say,tags=[nm.lower()]) for nm,say,_ in DN]+[dict(say='any drone',tags=['drone'])]
        D.append(dict(id='fof-drones'+sfx,name='Friend or Foe: counter-drone'+nmx,category='training',target=key,shots=30,startDelay=[2,4],parTime=20,timeout=45,game=dict(type='calls',calls=dc,rounds=6,wrong=-2),notes='The app calls a drone type (FPV, Mavic, hexacopter, Shahed); hit it. Smaller drone = more points. Soldier hits count as wrong (-2).'))
    upsert(key,t,D)
SAND=[(0,.47),(.2,.45),(.5,.44),(.8,.45),(1,.5),(1,.62),(0,.58)]; TR=[(0,.67),(.5,.72),(1,.81),(1,1),(0,1)]
GAMES['fof']=lambda:fof(rows=[(None,[('b1',.3,.4,1.6,False),('w1',.68,.4,1.6,True)]),
    (SAND,[('y1',.13,.555,2.6,False),('w1',.5,.555,2.6,False),('b1',.87,.555,2.6,True)]),
    (TR,[('y2',.27,.9,2.9,False),('w2',.73,.93,2.9,True)])],
    drones=[(0,.1,.1,0.6),(1,.3,.08,0.9),(2,.55,.1,1.4),(3,.84,.09,1.9)])
GAMES['fof-tabloid']=lambda:fof('fof-tabloid',TAB,(332,333,334,335),'LD-506',lay=TABLAY,rows=[(None,[('b1',.17,.4,1.6,False),('w1',.37,.4,1.6,True),('y1',.57,.4,1.6,True),('w2',.78,.4,1.5,False)]),
    (SAND,[('y1',.07,.555,2.6,False),('w1',.27,.555,2.6,False),('b1',.47,.555,2.6,True),('w1',.67,.555,2.6,True),('y1',.88,.555,2.6,True)]),
    (TR,[('y2',.14,.9,2.9,False),('w2',.38,.92,2.9,True),('b1',.6,.95,3.0,False),('w2',.84,.95,2.9,False)])],
    drones=[(0,.06,.1,0.6),(1,.2,.08,0.9),(3,.36,.09,1.9),(0,.52,.08,0.55),(2,.68,.1,1.4),(1,.82,.08,0.85),(3,.95,.09,1.3)])
if __name__=='__main__':
    for k in (sys.argv[1:] or list(GAMES)): GAMES[k]()
    save(); print('ok games')
