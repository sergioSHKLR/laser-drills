"""Die Hard Set 1 (category Fun): full-colour GenerateImage illustrations (art/src2) + rendered cover objects
composited into one PNG per sheet; target specs (targets.json) + drills (drills.json).
Vector is ONLY faint scoring outlines (hostages/bystanders are NOT marked on the art), markers, text."""
import json, cv2, numpy as np
SRC='art/src2/'; OUT='art/'
KNEE,KEEP=25,0.2   # red-dominance soft knee: keeps full colour, compresses only warm skin highlights (max dom < 40)
def safe(img):
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]
    d=r-(g+b)/2; d2=np.minimum(np.where(d>KNEE,KNEE+(d-KNEE)*KEEP,d),36); r=r-(d-d2)
    return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
def whiten(im):   # generated sources with a faint textured backdrop: everything outside the figures -> pure white
    m=(im.min(axis=2)<215).astype(np.uint8); m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(m); keep=np.isin(lab,[i for i in range(1,n) if st[i][4]>4000])
    cs,_=cv2.findContours(keep.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); f=np.zeros_like(m); cv2.drawContours(f,cs,-1,1,-1)
    f=cv2.dilate(f,np.ones((3,3),np.uint8)); out=im.copy(); out[f==0]=255; return out
WHITEN={'eddie','finale','hans','karl','tony','powell','uli','theo','franco','heinrich','billclay','partyguest'}
def load(k,size=(768,1024)):
    im=cv2.resize(cv2.imread(SRC+k+'.jpg'),size,interpolation=cv2.INTER_AREA); return whiten(im) if k in WHITEN else im
def mask(img,xmax=None,xmin=None):
    m=(img.min(axis=2)<232).astype(np.uint8)*255
    if xmax is not None: m[:,xmax:]=0
    if xmin is not None: m[:,:xmin]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
    return cv2.approxPolyDP(c,3.0,True)[:,0,:].tolist()
# hand-fit on the 768x1024 images: head (cx,cy,rx,ry) | shoulders (xl,xr,y) | belt (xl,xr,y) | chest -0 centre
C={'hans':dict(head=(378,92,48,62),sh=(250,545,190),belt=(265,500,520),chest=(395,320),rc=50),
 'karl':dict(head=(370,48,40,56),sh=(220,550,175),belt=(285,480,420),chest=(370,275),rc=52),
 'tony':dict(head=(382,72,42,55),sh=(235,545,175),belt=(290,480,440),chest=(385,330),rc=52),
 'franco':dict(head=(362,70,44,58),sh=(205,535,150),belt=(270,520,420),chest=(380,255),rc=60),
 'heinrich':dict(head=(363,78,40,58),sh=(240,515,150),belt=(315,500,410),chest=(395,300),rc=48),
 'eddie':dict(head=(366,88,40,54),sh=(185,520,170),belt=(225,485,465),chest=(366,320),rc=48),
 'theo':dict(head=(382,72,42,55),sh=(285,495,170),belt=(290,470,410),chest=(385,270),rc=48),
 'billclay':dict(head=(383,95,44,60),sh=(245,530,165),belt=(300,470,415),chest=(385,270),rc=50),
 'uli':dict(head=(366,58,46,62),sh=(180,550,148),belt=(230,500,505),chest=(366,272),rc=52),
 'powell':dict(head=(366,62,50,66),sh=(218,522,165),belt=(218,516,455),chest=(366,295),rc=58)}
IMG={k:safe(load(k)) for k in list(C)+['partyguest']}
# cover objects: (src, crop box in source px, placement box in figure px) -> composited in front of the figure
COV={'karl':('cv-rail',(40,170,1250,560),(110,500,660,1024)),
 'tony':('cv-cabinet',(145,90,720,1040),(215,470,555,1024)),
 'franco':('cv-desk',(95,345,1190,670),(120,430,650,1024)),
 'heinrich':('cv-pillar',(215,18,505,1262),(120,0,330,1024))}
HCR={}
PLAIN={k:IMG[k] for k in COV}
for k,im in PLAIN.items(): cv2.imwrite(OUT+f'dh-{k}-plain.png',im)
for k,(cv,(x0,y0,x1,y1),(px0,py0,px1,py1)) in COV.items():
    o=safe(cv2.imread(SRC+cv+'.jpg'))[y0:y1,x0:x1]; IMG[k]=IMG[k].copy(); IMG[k][py0:py1,px0:px1]=cv2.resize(o,(px1-px0,py1-py0),interpolation=cv2.INTER_AREA); HCR[k]=(px0,py0,px1,py1)
# backstop: faded, smaller bystanders BEHIND the threat (depth). Zones from the unfaded layer; scoring checks them only after threat zones.
BYS={'hans':'bys-office','karl':'bys-office','tony':'bys-party','franco':'bys-office','heinrich':'bys-party','uli':'bys-party','powell':'bys-office'}
BZ={}; FADE=0.42
def people(src):
    b=safe(cv2.imread(SRC+src+'.jpg')); m=(b.min(axis=2)<232).astype(np.uint8)*255; m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(m); ps=sorted([st[i] for i in range(1,n) if st[i][4]>20000],key=lambda r:r[0])
    return [(b[y:y+h,x:x+w],(lab[y:y+h,x:x+w]==i0)) for (x,y,w,h,_),i0 in [(r,[i for i in range(1,n) if (st[i]==r).all()][0]) for r in ps]]
for k,src in BYS.items():
    fig=IMG[k]; fm=cv2.dilate((fig.min(axis=2)<240).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
    bg=np.full_like(fig,255); polys=[]; ppl=people(src); H=400; FEET=640
    xs=[8,590,300] if len(ppl)==3 else [8,600]   # left edge, right edge, (middle behind the threat)
    order=[0,len(ppl)-1]+([1] if len(ppl)==3 else [])
    for xi,pi in zip(xs,order):
        im,mk=ppl[pi]; h,w=mk.shape; sc=H/h; W=int(w*sc); im=cv2.resize(im,(W,H),interpolation=cv2.INTER_AREA); mk=cv2.resize(mk.astype(np.uint8),(W,H),interpolation=cv2.INTER_NEAREST)
        x0=min(xi,768-W-4); y0=FEET-H; reg=bg[y0:y0+H,x0:x0+W]; f=(255-(255-im.astype(np.float32))*FADE).astype(np.uint8)
        reg[mk>0]=f[mk>0]
        cs,_=cv2.findContours(mk*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
        polys.append((cv2.approxPolyDP(c,2.5,True)[:,0,:]+[x0,y0]).tolist())
    out=np.where(fm[...,None],fig,bg); cv2.imwrite(OUT+f'dh-{k}.png',out); BZ[k]=polys
for k,im in IMG.items():
    if k not in BYS: cv2.imwrite(OUT+f'dh-{k}.png',im)
def byz(k,X,Y,S):
    return [dict(name=f'BYSTANDER {i+1}',kind='bystander',shape='poly',pts=[[round(X+x*S,3),round(Y+y*S,3)] for x,y in p],penalty=-10) for i,p in enumerate(BZ.get(k,[]))]
def zones_for(k,G,X,Y,S,crop=0,img=None,xmin=None,xmax=None,c=None,cover=True):
    """Zones (inches) for character k placed with image px->in: x=X+(px-crop)*S, y=Y+py*S."""
    c=c or C[k]; T=lambda x,y:[round(X+(x-crop)*S,3),round(Y+y*S,3)]
    hx,hy,hrx,hry=c['head']; (sl,sr,sy),(bl,br,by)=c['sh'],c['belt']; cx,cy=c['chest']; rc=c['rc']
    im=IMG[k] if img is None else img
    if cover and k in HCR: im=im.copy(); x0,y0,x1,y1=HCR[k]; im[y0:y1,x0:x1]=255   # silhouette = person only (cover handled by HC)
    sil=[T(*p) for p in mask(im,xmin=xmin,xmax=xmax)]
    base=dict(kind='score',tier='tier1',group=G,subtle=True)
    return [dict(base,name=f'{G} -3',shape='poly',pts=sil,score=-3,pd=3,part='body'),
     dict(base,name=f'{G} -1',shape='ellipse',cx=T(hx,hy)[0],cy=T(hx,hy)[1],rx=round(hrx*S,3),ry=round(hry*S,3),score=-1,pd=1,part='head'),
     dict(base,name=f'{G} -1',shape='poly',pts=[T(sl+15,sy),T(sr-15,sy),T(br,by),T(bl,by)],score=-1,pd=1,part='body'),
     dict(base,name=f'{G} -0',shape='ellipse',cx=T(hx,hy+6)[0],cy=T(hx,hy+6)[1],rx=round(hrx*0.5*S,3),ry=round(hry*0.42*S,3),score=0,pd=0,part='head'),
     dict(base,name=f'{G} -0',shape='ellipse',cx=T(cx,cy)[0],cy=T(cx,cy)[1],rx=round(rc*S,3),ry=round(rc*1.25*S,3),score=0,pd=0,part='body')]
def hcz(k,X,Y,S,crop=0):
    x0,y0,x1,y1=HCR[k]; return dict(name='HC',kind='hardcover',shape='rect',x=round(X+(x0-crop)*S,3),y=round(Y+y0*S,3),w=round((x1-x0)*S,3),h=round((y1-y0)*S,3),art=True)
def hostage(k,G,X,Y,S,crop=0,xmax=None,pts=None):
    T=lambda x,y:[round(X+(x-crop)*S,3),round(Y+y*S,3)]
    return dict(name=f'{G} NT',kind='noshoot',shape='poly',art=True,group=G,pts=[T(*p) for p in (pts or mask(IMG[k],xmax=xmax))],penalty=-5,ntSeconds=5)
LEG_T=[('tier1','Core head/chest: -0'),('tier1','Head, torso: -1 (+1 s)'),('tier1','Limbs, hands: -3 (+3 s)'),('#FFFFFF','Miss: +5 s')]
HC=('cover','Desk/rail/pillar/cabinet = hard cover'); NT=('noshoot','Unarmed (phone, drink, wallet) = NO-SHOOT +5 s'); BY=('cover','Faded people behind = BYSTANDER +10 s, backstop fail')
FL=(0.4,1.85,7.7,7.3); PAD=0.06   # letter scan field; art fills it (markers/quiet zones and text sit outside the field)
def bbox(im,thr=236):
    d=im.min(axis=2)<thr; cs=np.nonzero(d.sum(0)>2)[0]; rs=np.nonzero(d.sum(1)>2)[0]; return int(cs[0]),int(rs[0]),int(cs[-1])+1,int(rs[-1])+1
def fit(bw,bh,field=FL,pad=PAD):
    fx,fy,fw,fh=field; fw-=2*pad; fh-=2*pad; S=min(fw/bw,fh/bh); return S,fx+pad+(fw-bw*S)/2,fy+pad+(fh-bh*S)/2
DOC=json.load(open('targets.json')); T=DOC['targets']
for k in [k for k in T if k.startswith('dh-')]: del T[k]
SCALE='3 yd = ~30 yd sim (figure ~1/10 scale)'
def sheet(key,code,mid,name,drills,ins,zones,art,leg,dist=SCALE,layout=None):
    t=dict(code=code,name=name,markerIds=list(range(mid,mid+4)),scoring='idpa',set='diehard',category='fun',drills=drills,distance=dist,instructions=ins,art=art,zones=zones,legend=[list(x) for x in leg])
    if layout: t['layout']=layout
    T[key]=t
def solo(ch):
    x0,y0,x1,y1=bbox(cv2.imread(OUT+f'dh-{ch}.png')); S,X,Y=fit(x1-x0,y1-y0); Yo=Y-y0*S
    art=[dict(src=f'art/dh-{ch}.png',x=round(X,3),y=round(Y,3),w=round((x1-x0)*S,3),h=round((y1-y0)*S,3),crop=[x0,y0,x1,y1])]
    return S,X,Yo,x0,art
FF=('noshoot','Police officer = FRIENDLY: hit = +10 s, FAIL')
def friendly(k,X,Y,S,crop=0,img=None,xmin=None,xmax=None):
    T=lambda x,y:[round(X+(x-crop)*S,3),round(Y+y*S,3)]
    return dict(name='POWELL FRIENDLY',kind='noshoot',friendly=True,shape='poly',art=True,group='POWELL',pts=[T(*p) for p in mask(IMG[k] if img is None else img,xmin=xmin,xmax=xmax)],penalty=-10,ntSeconds=10)
def one(key,code,mid,name,ch,drills,ins):
    S,X,Yo,cr,art=solo(ch)
    z=zones_for(ch,'T1',X,Yo,S,crop=cr)
    if ch in HCR: z=[hcz(ch,X,Yo,S,crop=cr)]+z
    z+=byz(ch,X-cr*S,Yo,S)
    sheet(key,code,mid,name,drills,ins,z,art,LEG_T+([HC] if ch in HCR else [])+([BY] if ch in BZ else []))
one('dh-hans','LD-201',101,'Die Hard: Hans (HK P7)','hans',['dh-hans-mozambique','dh-course'],['Nakatomi 30th floor: the leader draws his P7.','Mozambique: 2 to the chest -0, then 1 to the head -0.','Outlines are faint on purpose: read the anatomy.','Say "start" or tap; gun holstered until the beep.'])
one('dh-karl','LD-202',105,'Die Hard: Karl (MP5A3, stairwell)','karl',['dh-stairwell','dh-course'],['Stairwell: Karl comes up the stairs, lower body behind the rail.','2 to the exposed chest/head. Concrete rail = hard cover.','Faint outlines = scoring zones on real anatomy.','Say "start" or tap.'])
one('dh-tony','LD-203',109,'Die Hard: Tony (MP5A3, cabinet)','tony',['dh-tony','dh-course'],['31st floor: Tony behind a file cabinet.','2 to the exposed chest -0. Cabinet = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-franco','LD-204',113,'Die Hard: Franco (AUG, desk)','franco',['dh-franco','dh-course'],['Lobby: Franco behind the reception desk.','2 to exposed chest/head. Desk = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-heinrich','LD-205',117,'Die Hard: Heinrich (AUG, pillar)','heinrich',['dh-heinrich','dh-course'],['Vault floor: Heinrich half behind a pillar.','2 to the exposed chest -0. Marble pillar = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-eddie','LD-206',121,'Die Hard: Eddie (fake guard)','eddie',['dh-eddie'],['Lobby guard desk: is the "guard" armed and hostile?','GUN = 2 to the chest. HANDS UP = say "Drop it!" in 3 s.','Hit on a compliant call = +5 s.','Mic on. Say "start" or tap.'])
one('dh-theo','LD-207',125,'Die Hard: Theo (vault tech)','theo',['dh-theo'],['Vault: the tech has his hands up... for now.','HANDS UP = say "Show me your hands!" in 3 s, do NOT shoot.','GUN = 2 to the chest.','Mic on. Say "start" or tap.'])
one('dh-uli','LD-212',157,'Die Hard: Uli (AUG, lobby)','uli',['dh-uli','dh-course'],['Lobby: the quiet one with the AUG.','2 to the chest -0 (vest: aim center).','Faint outlines = scoring zones.','Say "start" or tap.'])
S,X,Yo,cr,art=solo('powell')
sheet('dh-powell','LD-213',153,'Die Hard: Sgt. Powell (FRIENDLY)',['dh-powell'],['LAPD sergeant arrives: FRIENDLY, do not shoot.','Hold fire 4 s, say "Police! Friendly!"','Any hit = friendly fire +10 s and FAIL.','Say "start" or tap.'],[friendly('powell',X,Yo,S,crop=cr)]+byz('powell',X-cr*S,Yo,S),art,[FF,BY,LEG_T[3]])
one('dh-billclay','LD-208',129,'Die Hard: "Bill Clay" impostor','billclay',['dh-billclay','dh-course'],['Roof stairs: a "hostage" with an accent. Wait for the call.','HANDS UP = verbal "Get down!" within 3 s.','GUN = 2 chest + 1 head.','Hit on a compliant call = +5 s. Mic on.'])
# Roof finale: Eddie | Holly | Hans behind Holly (right hand on her shoulder, pistol at her head, right half of torso exposed). 1024x768 source.
FIN=safe(load('finale',(1024,768))); cv2.imwrite(OUT+'dh-finale.png',FIN)
fx0,fy0,fx1,fy1=bbox(FIN); S4,X4,Y4=fit(fx1-fx0,fy1-fy0)
TH=lambda x,y:[round(X4+(x-fx0)*S4,3),round(Y4+(y-fy0)*S4,3)]
HOLLY=[(600,95),(640,70),(690,85),(705,140),(715,185),(745,215),(760,160),(795,170),(785,235),(770,280),(730,300),(722,410),(715,530),(690,535),(688,700),(690,728),(655,728),(645,560),(632,728),(605,728),(598,560),(582,530),(575,410),(580,300),(545,295),(525,240),(512,165),(535,155),(560,225),(595,185),(588,140)]
cE=dict(head=(290,55,40,48),sh=(195,420,120),belt=(195,400,340),chest=(290,232),rc=40)
z=[hostage('finale','HOLLY',X4,Y4-fy0*S4,S4,crop=fx0,pts=HOLLY)]
zE=zones_for('finale','T2',X4,Y4-fy0*S4,S4,crop=fx0,img=FIN,xmax=470,c=cE)
zE[3].update(rx=round(18*S4,3),ry=round(22*S4,3))   # tight Eddie head -0
HANS=[(728,40),(760,15),(795,25),(802,95),(845,120),(860,180),(862,255),(840,265),(840,390),(845,690),(800,705),(770,560),(745,690),(705,690),(718,420),(728,300),(770,280),(786,235),(760,205),(735,150),(728,100)]
G1=dict(kind='score',tier='tier1',group='T1',subtle=True)
zH=[dict(G1,name='T1 -3',shape='poly',pts=[TH(*p) for p in HANS],score=-3,pd=3,part='body'),
 dict(G1,name='T1 -1',shape='ellipse',cx=TH(760,62)[0],cy=TH(760,62)[1],rx=round(32*S4,3),ry=round(44*S4,3),score=-1,pd=1,part='head'),
 dict(G1,name='T1 -1',shape='poly',pts=[TH(*p) for p in [(770,240),(800,150),(850,170),(840,390),(745,390)]],score=-1,pd=1,part='body'),
 dict(G1,name='T1 -0',shape='ellipse',cx=TH(800,250)[0],cy=TH(800,250)[1],rx=round(28*S4,3),ry=round(40*S4,3),score=0,pd=0,part='body')]
z+=zE+zH
sheet('dh-finale','LD-209',133,'Die Hard: Roof Finale',['dh-finale','dh-course'],['Roof finale: Hans shields behind Holly; Eddie (MP5A3 at low ready) covers him.','Exactly 2: Hans exposed side-chest -0, then Eddie head -0.','Holly = HOSTAGE: any hit = +5 s and FAIL.','Say "start" or tap.'],z,[dict(src='art/dh-finale.png',x=round(X4,3),y=round(Y4,3),w=round((fx1-fx0)*S4,3),h=round((fy1-fy0)*S4,3),crop=[fx0,fy0,fx1,fy1])],[LEG_T[0],LEG_T[1],LEG_T[2],LEG_T[3],NT])
# 2-up sheets (left person | right person), each cropped to its own content, scaled to fill the field
def twoup(L,R):
    bl=[bbox(L[0]),bbox(R[0])]; y0=min(b[1] for b in bl); y1=max(b[3] for b in bl); wl=bl[0][2]-bl[0][0]; wr=bl[1][2]-bl[1][0]
    S,X,Y=fit(wl+wr+20,y1-y0); Xa=X; Xb=X+(wl+20)*S; Yo=Y-y0*S
    art=[dict(src=s,x=round(x,3),y=round(Y,3),w=round(w*S,3),h=round((y1-y0)*S,3),crop=[b[0],y0,b[2],y1]) for s,x,w,b in ((L[1],Xa,wl,bl[0]),(R[1],Xb,wr,bl[1]))]
    return S,Xa,Xb,Yo,bl[0][0],bl[1][0],art
S2,X2a,X2b,Yo,ca,cb,art=twoup((IMG['partyguest'],'art/dh-partyguest.png'),(PLAIN['tony'],'art/dh-tony-plain.png'))
z=[hostage('partyguest','GUEST',X2a,Yo,S2,crop=ca)]+zones_for('tony','T1',X2b,Yo,S2,crop=cb,img=PLAIN['tony'],cover=False)
sheet('dh-party','LD-210',137,'Die Hard: Christmas Party',['dh-party'],['30th floor party: a guest stands beside Tony.','Find the gun: 2 to the armed man only. Unarmed guest = +5 s.','Faint outlines = scoring zones.','Say "start" or tap.'],z,art,LEG_T+[NT])
cv2.imwrite(OUT+'dh-powell-plain.png',IMG['powell']); cv2.imwrite(OUT+'dh-uli-plain.png',IMG['uli'])
S2,X2a,X2b,Yo,ca,cb,art=twoup((IMG['powell'],'art/dh-powell-plain.png'),(IMG['uli'],'art/dh-uli-plain.png'))
z=[friendly('powell',X2a,Yo,S2,crop=ca)]+zones_for('uli','T1',X2b,Yo,S2,crop=cb,img=IMG['uli'],cover=False)
sheet('dh-lobby','LD-214',161,'Die Hard: Lobby (Powell arrives)',['dh-lobby','dh-course'],['Lobby: Sgt. Powell walks in as Uli opens up.','2 to Uli only. Powell = FRIENDLY.','Hit on Powell = +10 s and FAIL.','Say "start" or tap.'],z,art,LEG_T+[FF])
# Nakatomi tabloid line-up: 8 people, tight and overlapping (each stands slightly in front of its left neighbour); Powell (friendly) frontmost at the right
cast=[('hans','T1'),('karl','T2'),('uli','T3'),('franco','T4'),('eddie','T5'),('theo','T6'),('billclay','T7'),('powell','POWELL')]
STEP=262; boxes={k:bbox(PLAIN.get(k,IMG[k])) for k,_ in cast}
cxs=[i*STEP for i in range(len(cast))]; L0=min(c-(384-boxes[k][0]) for c,(k,_) in zip(cxs,cast)); R0=max(c+(boxes[k][2]-384) for c,(k,_) in zip(cxs,cast))
yt=min(b[1] for b in boxes.values()); yb=max(b[3] for b in boxes.values()); NW=R0-L0; NH=yb-yt
FN=(0.4,2.12,16.2,7.0); S3,X3,Y3=fit(NW,NH,FN,0.05)
z=[];tx=[]; can=np.full((NH,NW,3),255,np.uint8)
for i,(k,g) in enumerate(cast):
    src=PLAIN.get(k,IMG[k]); m=np.zeros(src.shape[:2],np.uint8); cv2.fillPoly(m,[np.array(mask(src),np.int32)],1)
    ox=cxs[i]-384-L0   # canvas x of the source image's left edge
    sx0=max(0,-ox); sx1=min(768,NW-ox); reg=can[:,ox+sx0:ox+sx1]; mm=m[yt:yb,sx0:sx1]>0; reg[mm]=src[yt:yb,sx0:sx1][mm]
    x=X3+ox*S3; Yz=Y3-yt*S3
    if k=='powell': zz=[dict(friendly(k,x,Yz,S3,img=src),z=i)]
    else:
        zz=zones_for(k,g,x,Yz,S3,img=PLAIN.get(k),cover=False)
        for q in zz: q['z']=i
        zz[0]['sil']=True
    z+=zz
    tx.append(dict(text=('POWELL (FRIENDLY)' if k=='powell' else f'{g} {k.upper().replace("BILLCLAY","BILL CLAY")}'),x=round(x+384*S3,3),y=2.05,size=10))
cv2.imwrite(OUT+'dh-nakatomi.png',can); art=[dict(src='art/dh-nakatomi.png',x=round(X3,3),y=round(Y3,3),w=round(NW*S3,3),h=round(NH*S3,3))]
sheet('dh-nakatomi','LD-211',141,'Die Hard: Nakatomi Plaza line-up',['dh-nakatomi-calls','dh-nakatomi-sds'],['Seven crew T1-T7 + Sgt. Powell (FRIENDLY, +10 s).','Overlaps: the front person takes the hit.','Calls: 2 chest; "head" = 1 head. HANDS UP = verbal.','Mic on. Print Tabloid 11x17 at 100%.'],z,art,LEG_T[:3]+[FF],dist=f'3 yd = ~{round(3*70/(NH*S3*0.95))} yd sim (1/{round(70/(NH*S3*0.95))} scale)',layout={'page':{'w':17,'h':11},'field':{'x':0.4,'y':1.85,'w':16.2,'h':7.3}})
T['dh-nakatomi']['texts']=tx
json.dump(DOC,open('targets.json','w'),indent=1)
# drills
DR=[d for d in json.load(open('drills.json')) if not d['id'].startswith('dh-')]
seen=set();DR=[d for d in DR if not (d['id'] in seen or seen.add(d['id']))]  # drop duplicated entries
I=dict(scoring='idpa',maxPerShot=0,startDelay=[2,4])
def scen(id,name,tgt,names,pc,ts,par,notes,pool=('T1',),count=1):
    return dict(I,id=id,name=name,target=tgt,scenario=dict(pool=list(pool),count=count,pCompliant=pc,threatShots=ts,window=3.0,failCommand=3,allowAllCompliant=count==1,names=names),parTime=par,timeout=15,notes=notes)
DR+=[
 dict(I,id='dh-hans-mozambique',name='Die Hard: Hans Mozambique',target='dh-hans',calls=[dict(group='T1',label='Hans',say='Hans! Mozambique',parts=['body','body','head'])],randomize=False,parTime=4.0,timeout=12,notes='Hans draws the P7. 2 chest -0 then 1 head -0. Wrong part order = PE +3 s.'),
 dict(I,id='dh-stairwell',name='Die Hard: Stairwell (Karl)',target='dh-karl',shots=2,parTime=3.0,timeout=10,notes='Karl coming up the stairs. 2 on the exposed chest/head; the black rail is hard cover.'),
 dict(I,id='dh-tony',name='Die Hard: 31st floor (Tony)',target='dh-tony',shots=2,parTime=2.5,timeout=10,notes='Tony through the door. 2 to the chest -0.'),
 dict(I,id='dh-franco',name='Die Hard: Lobby desk (Franco)',target='dh-franco',shots=2,parTime=3.0,timeout=10,notes='Franco behind the desk with an AUG. 2 on exposed upper body; desk = hard cover.'),
 dict(I,id='dh-heinrich',name='Die Hard: Pillar (Heinrich)',target='dh-heinrich',shots=2,parTime=3.0,timeout=10,notes='Heinrich half behind a pillar. 2 on the exposed side.'),
 scen('dh-eddie','Die Hard: The guard (Eddie) shoot/don\'t-shoot','dh-eddie',{'T1':'Guard'},0.5,2,3.0,'Called GUN: 2 to the chest. Called HANDS UP: do not shoot, say "Drop it!" / "Show me your hands!" within 3 s.'),
 scen('dh-theo','Die Hard: Vault tech (Theo) shoot/don\'t-shoot','dh-theo',{'T1':'Theo'},0.7,2,3.0,'Mostly compliant. HANDS UP: verbal command within 3 s. GUN: 2 to the chest.'),
 scen('dh-billclay','Die Hard: "Bill Clay" impostor','dh-billclay',{'T1':'Bill Clay'},0.5,3,4.0,'The leader posing as a hostage. HANDS UP: "Get down!" within 3 s. GUN: 3 shots (2 chest + head).'),
 dict(I,id='dh-finale',name='Die Hard: Roof Finale',target='dh-finale',calls=[dict(group='T1',label='Hans',say='Hans, center mass',parts=['body']),dict(group='T2',label='Eddie',say='Eddie, head',parts=['head'])],randomize=False,shots=2,failOnNoShoot=True,parTime=3.0,timeout=10,notes='Exactly 2 shots: Hans exposed center mass -0, then Eddie head -0. Any hit on Holly = +5 s and stage FAIL.'),
 dict(I,id='dh-party',name='Die Hard: Christmas party',target='dh-party',shots=2,order=['T1','T1'],parTime=3.0,timeout=10,notes='2 on Tony only. The hatched guest is a hostage: +5 s per hit.'),
 dict(I,id='dh-uli',name='Die Hard: Lobby (Uli)',target='dh-uli',shots=2,parTime=2.5,timeout=10,notes='Uli with the AUG. 2 to the chest -0.'),
 dict(I,id='dh-powell',name='Die Hard: Friendly ID (Sgt. Powell)',target='dh-powell',shots=0,parTime=4.0,timeout=4,failOnFriendly=True,notes='Hold fire: the officer is FRIENDLY. Say "Police! Friendly!". Clean run = 4.00 s hold. Any hit = friendly fire +10 s and FAIL (the run ends on the shot).'),
 dict(I,id='dh-lobby',name='Die Hard: Lobby, Powell arrives',target='dh-lobby',shots=2,order=['T1','T1'],failOnFriendly=True,parTime=3.0,timeout=10,notes='2 on Uli only. Sgt. Powell is FRIENDLY: hit = +10 s and FAIL.'),
 dict(I,id='dh-nakatomi-calls',name='Die Hard: Nakatomi random calls (tabloid)',target='dh-nakatomi',randomize=True,parTime=12.0,timeout=30,
   calls=[dict(group='T1',label='Hans',say='Hans, head',parts=['head']),dict(group='T2',label='Karl',say='Karl',shots=2),dict(group='T4',label='Franco',say='Franco',shots=2),dict(group='T3',label='Uli',say='Uli',shots=2),dict(group='T5',label='Eddie',say='Eddie',shots=2)],
   failOnFriendly=True,notes='Names are spoken in random order: Hans = 1 head shot, others 2 chest. Theo (T6) and Bill Clay (T7) are not called (PE if hit). Sgt. Powell is FRIENDLY: +10 s and FAIL.'),
 scen('dh-nakatomi-sds','Die Hard: Nakatomi shoot/don\'t-shoot (tabloid)','dh-nakatomi',{'T1':'Hans','T2':'Karl','T3':'Uli','T4':'Franco','T5':'Eddie','T6':'Theo','T7':'Bill Clay'},0.4,2,10.0,'4 crew are called: GUN = 2 shots, HANDS UP = verbal command within 3 s ("Drop it!", "Show me your hands!"). Hit on compliant = +5 s, late command = +3 s.',pool=('T1','T2','T3','T4','T5','T6','T7'),count=4),
 dict(id='dh-course',name='Die Hard: Nakatomi Plaza story course (7 stages)',type='course',scoring='idpa',notes='Swap sheets between stages. Score = time + PD + PE x3 + hostage hits x5, summed.',
   stages=[dict(name='1. Party crashers: Tony',target='dh-tony',shots=2,startDelay=[2,4],parTime=2.5,timeout=10,brief='Tony through the door: 2 chest.'),
    dict(name='2. Vault floor: Heinrich behind pillar',target='dh-heinrich',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 on the exposed side.'),
    dict(name='3. Lobby: Franco at the desk',target='dh-franco',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 above the desk.'),
    dict(name='3b. Lobby: Uli as Powell arrives',target='dh-lobby',shots=2,order=['T1','T1'],failOnFriendly=True,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 on Uli. Powell is friendly.'),
    dict(name='4. Stairwell: Karl',target='dh-karl',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 above the rail.'),
    dict(name='5. The leader: Hans',target='dh-hans',shots=3,order=['T1','T1','T1'],parts=['body','body','head'],startDelay=[2,4],parTime=4.0,timeout=12,brief='Mozambique: 2 chest, 1 head.'),
    dict(name='6. Roof finale: Hans, Holly, Eddie',target='dh-finale',shots=2,order=['T1','T2'],parts=['body','head'],failOnNoShoot=True,startDelay=[2,4],parTime=3.0,timeout=10,brief='Hans center mass, then Eddie head. Do not hit Holly.')])]
for d in DR: d['category']='fun' if d['id'].startswith('dh-') else 'training'
json.dump(DR,open('drills.json','w'),indent=1)
print('ok',len([k for k in T if k.startswith('dh-')]),'dh sheets')
