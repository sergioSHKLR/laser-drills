"""Die Hard Set 1 (category Fun): full-colour GenerateImage illustrations (art/src2) + rendered cover objects
composited into one PNG per sheet; target specs (targets.json) + drills (drills.json).
Vector is ONLY faint scoring outlines, hostage hatch/outline, markers, text."""
import json, cv2, numpy as np
SRC='art/src2/'; OUT='art/'
KNEE,KEEP=25,0.2   # red-dominance soft knee: keeps full colour, compresses only warm skin highlights (max dom < 40)
def safe(img):
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]
    d=r-(g+b)/2; d2=np.where(d>KNEE,KNEE+(d-KNEE)*KEEP,d); r=r-(d-d2)
    return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
def load(k,size=(768,1024)): return cv2.resize(cv2.imread(SRC+k+'.jpg'),size,interpolation=cv2.INTER_AREA)
def mask(img,xmax=None,xmin=None):
    m=(img.min(axis=2)<232).astype(np.uint8)*255
    if xmax is not None: m[:,xmax:]=0
    if xmin is not None: m[:,:xmin]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
    return cv2.approxPolyDP(c,3.0,True)[:,0,:].tolist()
# hand-fit on the 768x1024 images: head (cx,cy,rx,ry) | shoulders (xl,xr,y) | belt (xl,xr,y) | chest -0 centre
C={'hans':dict(head=(372,78,44,60),sh=(285,500,170),belt=(275,490,505),chest=(385,290),rc=46),
 'karl':dict(head=(378,78,40,58),sh=(240,535,175),belt=(285,475,435),chest=(380,300),rc=55),
 'tony':dict(head=(380,95,40,60),sh=(240,530,180),belt=(290,480,440),chest=(385,300),rc=55),
 'franco':dict(head=(362,70,44,58),sh=(205,535,150),belt=(270,520,420),chest=(380,255),rc=60),
 'heinrich':dict(head=(363,78,40,58),sh=(240,515,150),belt=(315,500,410),chest=(395,300),rc=48),
 'eddie':dict(head=(375,88,44,55),sh=(260,505,165),belt=(285,490,410),chest=(385,300),rc=50),
 'theo':dict(head=(382,72,42,55),sh=(285,495,170),belt=(290,470,410),chest=(385,270),rc=48),
 'billclay':dict(head=(383,95,44,60),sh=(245,530,165),belt=(300,470,415),chest=(385,270),rc=50)}
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
for k,im in IMG.items(): cv2.imwrite(OUT+f'dh-{k}.png',im)
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
HC=('cover','Desk/rail/pillar/cabinet = hard cover'); NT=('noshoot','Hatched = HOSTAGE +5 s')
S1=7.2/1024; X1=(8.5-768*S1)/2; Y1=1.9
DOC=json.load(open('targets.json')); T=DOC['targets']
for k in [k for k in T if k.startswith('dh-')]: del T[k]
SCALE='3 yd = ~30 yd sim (figure ~1/10 scale)'
def sheet(key,code,mid,name,drills,ins,zones,art,leg,dist=SCALE,layout=None):
    t=dict(code=code,name=name,markerIds=list(range(mid,mid+4)),scoring='idpa',set='diehard',category='fun',drills=drills,distance=dist,instructions=ins,art=art,zones=zones,legend=[list(x) for x in leg])
    if layout: t['layout']=layout
    T[key]=t
A=lambda k:[dict(src=f'art/dh-{k}.png',x=round(X1,3),y=Y1,w=round(768*S1,3),h=7.2)]
def one(key,code,mid,name,ch,drills,ins):
    z=zones_for(ch,'T1',X1,Y1,S1)
    if ch in HCR: z=[hcz(ch,X1,Y1,S1)]+z
    sheet(key,code,mid,name,drills,ins,z,A(ch),LEG_T+([HC] if ch in HCR else []))
one('dh-hans','LD-201',101,'Die Hard: Hans (HK P7)','hans',['dh-hans-mozambique','dh-course'],['Nakatomi 30th floor: the leader draws his P7.','Mozambique: 2 to the chest -0, then 1 to the head -0.','Outlines are faint on purpose: read the anatomy.','Say "start" or tap; gun holstered until the beep.'])
one('dh-karl','LD-202',105,'Die Hard: Karl (MP5A3, stairwell)','karl',['dh-stairwell','dh-course'],['Stairwell: Karl comes up the stairs, lower body behind the rail.','2 to the exposed chest/head. Concrete rail = hard cover.','Faint outlines = scoring zones on real anatomy.','Say "start" or tap.'])
one('dh-tony','LD-203',109,'Die Hard: Tony (MP5A3, cabinet)','tony',['dh-tony','dh-course'],['31st floor: Tony behind a file cabinet.','2 to the exposed chest -0. Cabinet = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-franco','LD-204',113,'Die Hard: Franco (AUG, desk)','franco',['dh-franco','dh-course'],['Lobby: Franco behind the reception desk.','2 to exposed chest/head. Desk = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-heinrich','LD-205',117,'Die Hard: Heinrich (AUG, pillar)','heinrich',['dh-heinrich','dh-course'],['Vault floor: Heinrich half behind a pillar.','2 to the exposed chest -0. Marble pillar = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-eddie','LD-206',121,'Die Hard: Eddie (fake guard)','eddie',['dh-eddie'],['Lobby guard desk: is the "guard" armed and hostile?','GUN = 2 to the chest. HANDS UP = say "Drop it!" in 3 s.','Hit on a compliant call = +5 s.','Mic on. Say "start" or tap.'])
one('dh-theo','LD-207',125,'Die Hard: Theo (vault tech)','theo',['dh-theo'],['Vault: the tech has his hands up... for now.','HANDS UP = say "Show me your hands!" in 3 s, do NOT shoot.','GUN = 2 to the chest.','Mic on. Say "start" or tap.'])
one('dh-billclay','LD-208',129,'Die Hard: "Bill Clay" impostor','billclay',['dh-billclay','dh-course'],['Roof stairs: a "hostage" with an accent. Wait for the call.','HANDS UP = verbal "Get down!" within 3 s.','GUN = 2 chest + 1 head.','Hit on a compliant call = +5 s. Mic on.'])
# Roof finale (movie still): Eddie | Holly | Hans behind Holly. 1024x768 image on letter portrait.
FIN=safe(load('finale',(1024,768))); cv2.imwrite(OUT+'dh-finale.png',FIN)
S4=7.6/1024; X4=(8.5-7.6)/2; Y4=2.4
HOLLY=[(492,92),(530,78),(566,92),(578,140),(598,178),(606,240),(604,330),(588,420),(584,512),(562,522),(566,700),(548,726),(530,700),(516,726),(490,720),(486,522),(462,512),(452,420),(444,330),(448,230),(462,180),(484,160)]
cE=dict(head=(365,92,38,48),sh=(275,450,140),belt=(290,440,320),chest=(362,220),rc=38)
z=[hostage('finale','HOLLY',X4,Y4,S4,pts=HOLLY)]
zE=zones_for('finale','T2',X4,Y4,S4,img=FIN,xmax=462,c=cE)
zE[3].update(rx=round(18*S4,3),ry=round(22*S4,3))   # tight Eddie head -0
TH=lambda x,y:[round(X4+x*S4,3),round(Y4+y*S4,3)]
zH=[dict(kind='score',tier='tier1',group='T1',subtle=True,name='T1 -3',shape='poly',pts=[TH(*p) for p in mask(FIN,xmin=600)],score=-3,pd=3,part='body'),
 dict(kind='score',tier='tier1',group='T1',subtle=True,name='T1 -1',shape='ellipse',cx=TH(636,58)[0],cy=TH(636,58)[1],rx=round(36*S4,3),ry=round(48*S4,3),score=-1,pd=1,part='head'),
 dict(kind='score',tier='tier1',group='T1',subtle=True,name='T1 -1',shape='poly',pts=[TH(*p) for p in [(608,118),(722,140),(714,372),(608,372)]],score=-1,pd=1,part='body'),
 dict(kind='score',tier='tier1',group='T1',subtle=True,name='T1 -0',shape='ellipse',cx=TH(660,255)[0],cy=TH(660,255)[1],rx=round(32*S4,3),ry=round(52*S4,3),score=0,pd=0,part='body')]
z+=zE+zH
sheet('dh-finale','LD-209',133,'Die Hard: Roof Finale',['dh-finale','dh-course'],['Roof finale: Hans holds Holly at gunpoint; Eddie covers him.','Exactly 2: Hans exposed chest -0, then Eddie head -0.','Holly (hatched) = HOSTAGE: hit = +5 s and FAIL.','Say "start" or tap.'],z,[dict(src='art/dh-finale.png',x=round(X4,3),y=Y4,w=7.6,h=round(768*S4,3))],[LEG_T[0],LEG_T[1],LEG_T[2],LEG_T[3],NT])
# lobby: party guest (NT) + Tony, cropped 2-up on letter
S2=6.9/1024; CR=150; W2=470*S2; X2a=0.4+(7.7-2*W2)/2; X2b=X2a+W2; Y2=2.05
z=[hostage('partyguest','GUEST',X2a,Y2,S2,crop=CR)]+zones_for('tony','T1',X2b,Y2,S2,crop=CR,img=PLAIN['tony'],cover=False)
art=[dict(src='art/dh-partyguest.png',x=round(X2a,3),y=Y2,w=round(W2,3),h=6.9,crop=[CR,0,620,1024]),dict(src='art/dh-tony-plain.png',x=round(X2b,3),y=Y2,w=round(W2,3),h=6.9,crop=[CR,0,620,1024])]
sheet('dh-party','LD-210',137,'Die Hard: Christmas Party',['dh-party'],['30th floor party: a guest stands beside Tony.','2 to Tony only. Hatched white guest = HOSTAGE (+5 s).','Faint outlines = scoring zones.','Say "start" or tap.'],z,art,LEG_T+[NT])
# Nakatomi tabloid line-up
S3=5.9/1024; W3=470*S3; X3=0.4+(16.2-6*W3)/2; Y3=2.6
cast=[('hans','T1'),('karl','T2'),('franco','T3'),('eddie','T4'),('theo','T5'),('billclay','T6')]
z=[];art=[];tx=[]
for i,(k,g) in enumerate(cast):
    x=X3+i*W3; z+=zones_for(k,g,x,Y3,S3,crop=CR,img=PLAIN.get(k),cover=False); art.append(dict(src=f'art/dh-{k}{"-plain" if k in PLAIN else ""}.png',x=round(x,3),y=Y3,w=round(W3,3),h=5.9,crop=[CR,0,620,1024]))
    tx.append(dict(text=f'{g} {k.upper().replace("BILLCLAY","BILL CLAY")}',x=round(x+W3/2,3),y=2.35,size=11))
sheet('dh-nakatomi','LD-211',141,'Die Hard: Nakatomi Plaza line-up',['dh-nakatomi-calls','dh-nakatomi-sds'],['Six crew T1-T6; app calls names.','Calls: 2 chest; "head" = 1 head.','GUN = shoot; HANDS UP = verbal.','Mic on. Print Tabloid 11x17 at 100%.'],z,art,LEG_T,dist='3 yd = ~40 yd sim (1/13 scale)',layout={'page':{'w':17,'h':11},'field':{'x':0.4,'y':1.85,'w':16.2,'h':7.4}})
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
 dict(I,id='dh-nakatomi-calls',name='Die Hard: Nakatomi random calls (tabloid)',target='dh-nakatomi',randomize=True,parTime=12.0,timeout=30,
   calls=[dict(group='T1',label='Hans',say='Hans, head',parts=['head']),dict(group='T2',label='Karl',say='Karl',shots=2),dict(group='T3',label='Franco',say='Franco',shots=2),dict(group='T4',label='Eddie',say='Eddie',shots=2)],
   notes='Names are spoken in random order: Hans = 1 head shot, others 2 chest. Theo (T5) and Bill Clay (T6) are not called: hits on them still count as wrong target (PE).'),
 scen('dh-nakatomi-sds','Die Hard: Nakatomi shoot/don\'t-shoot (tabloid)','dh-nakatomi',{'T1':'Hans','T2':'Karl','T3':'Franco','T4':'Eddie','T5':'Theo','T6':'Bill Clay'},0.4,2,10.0,'4 crew are called: GUN = 2 shots, HANDS UP = verbal command within 3 s ("Drop it!", "Show me your hands!"). Hit on compliant = +5 s, late command = +3 s.',pool=('T1','T2','T3','T4','T5','T6'),count=4),
 dict(id='dh-course',name='Die Hard: Nakatomi Plaza story course (6 stages)',type='course',scoring='idpa',notes='Swap sheets between stages. Score = time + PD + PE x3 + hostage hits x5, summed.',
   stages=[dict(name='1. Party crashers: Tony',target='dh-tony',shots=2,startDelay=[2,4],parTime=2.5,timeout=10,brief='Tony through the door: 2 chest.'),
    dict(name='2. Vault floor: Heinrich behind pillar',target='dh-heinrich',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 on the exposed side.'),
    dict(name='3. Lobby: Franco at the desk',target='dh-franco',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 above the desk.'),
    dict(name='4. Stairwell: Karl',target='dh-karl',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,brief='2 above the rail.'),
    dict(name='5. The leader: Hans',target='dh-hans',shots=3,order=['T1','T1','T1'],parts=['body','body','head'],startDelay=[2,4],parTime=4.0,timeout=12,brief='Mozambique: 2 chest, 1 head.'),
    dict(name='6. Roof finale: Hans, Holly, Eddie',target='dh-finale',shots=2,order=['T1','T2'],parts=['body','head'],failOnNoShoot=True,startDelay=[2,4],parTime=3.0,timeout=10,brief='Hans center mass, then Eddie head. Do not hit Holly.')])]
for d in DR: d['category']='fun' if d['id'].startswith('dh-') else 'training'
json.dump(DR,open('drills.json','w'),indent=1)
print('ok',len([k for k in T if k.startswith('dh-')]),'dh sheets')
