"""Die Hard Set 1: laser-safe art processing + target specs (targets.json) + drills (drills.json).
Art = GenerateImage illustrations (art/src). Vector is ONLY faint scoring outlines, hard cover, hostage hatch, markers, text."""
import json, cv2, numpy as np
SRC='art/src/'; OUT='art/'
def safe(img):  # BGR -> laser-safe: clamp red dominance, slight desaturate
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]
    m=(r+g+b)/3; k=0.75; r,g,b=[m+(c-m)*k for c in (r,g,b)]
    r=np.minimum(r,(g+b)/2+10)
    return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
def mask(img,xmax=None,xmin=None):
    m=(img.min(axis=2)<232).astype(np.uint8)*255
    if xmax is not None: m[:,xmax:]=0
    if xmin is not None: m[:,:xmin]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
    return cv2.approxPolyDP(c,3.0,True)[:,0,:].tolist()
# head (cx,cy,rx,ry) | shoulders (xl,xr,y) | belt (xl,xr,y) | chest centre ; image px 768x1024
C={'hans':dict(head=(375,78,48,62),sh=(275,520,165),belt=(285,475,500),chest=(380,265)),
 'karl':dict(head=(378,92,42,58),sh=(225,540,165),belt=(285,475,420),chest=(380,235)),
 'tony':dict(head=(380,88,40,60),sh=(215,540,185),belt=(285,475,450),chest=(380,255)),
 'franco':dict(head=(375,82,42,60),sh=(205,540,145),belt=(280,480,420),chest=(375,235)),
 'heinrich':dict(head=(375,78,40,60),sh=(215,530,145),belt=(280,480,470),chest=(375,250)),
 'eddie':dict(head=(380,90,45,62),sh=(255,510,165),belt=(290,470,415),chest=(380,255)),
 'theo':dict(head=(385,100,42,58),sh=(300,470,185),belt=(300,470,420),chest=(385,265)),
 'billclay':dict(head=(380,82,45,65),sh=(230,540,160),belt=(290,470,400),chest=(380,240)),
 'hans-holly':dict(head=(418,95,45,65),sh=(390,580,175),belt=(385,545,410),chest=(472,252),xmin=385),
 'partyguest':dict()}
IMG={}
for k in C:
    im=cv2.resize(cv2.imread(SRC+k+'.jpg'),(768,1024),interpolation=cv2.INTER_AREA); s=safe(im); cv2.imwrite(OUT+f'dh-{k}.png',s); IMG[k]=s
def zones_for(k,G,X,Y,S,crop=0):
    """Zones (inches) for character k placed with image px->in: x=X+(px-crop)*S, y=Y+py*S."""
    c=C[k]; T=lambda x,y:[round(X+(x-crop)*S,3),round(Y+y*S,3)]
    hx,hy,hrx,hry=c['head']; (sl,sr,sy),(bl,br,by)=c['sh'],c['belt']; cx,cy=c['chest']; crx=0.22*(sr-sl)
    sil=[T(*p) for p in mask(IMG[k],xmin=c.get('xmin'))]
    base=dict(kind='score',tier='tier1',group=G,subtle=True)
    return [dict(base,name=f'{G} -3',shape='poly',pts=sil,score=-3,pd=3,part='body'),
     dict(base,name=f'{G} -1',shape='ellipse',cx=T(hx,hy)[0],cy=T(hx,hy)[1],rx=round(hrx*S,3),ry=round(hry*S,3),score=-1,pd=1,part='head'),
     dict(base,name=f'{G} -1',shape='poly',pts=[T(sl+15,sy),T(sr-15,sy),T(br,by),T(bl,by)],score=-1,pd=1,part='body'),
     dict(base,name=f'{G} -0',shape='ellipse',cx=T(hx,hy+8)[0],cy=T(hx,hy+8)[1],rx=round(hrx*0.5*S,3),ry=round(hry*0.42*S,3),score=0,pd=0,part='head'),
     dict(base,name=f'{G} -0',shape='ellipse',cx=T(cx,cy)[0],cy=T(cx,cy)[1],rx=round(crx*S,3),ry=round(crx*1.25*S,3),score=0,pd=0,part='body')]
def hostage(k,G,X,Y,S,crop=0,xmax=None):
    T=lambda x,y:[round(X+(x-crop)*S,3),round(Y+y*S,3)]
    return dict(name=f'{G} NT',kind='noshoot',shape='poly',art=True,group=G,pts=[T(*p) for p in mask(IMG[k],xmax=xmax)],penalty=-5,ntSeconds=5)
LEG_T=[('tier1','Core head/chest: -0'),('tier1','Head, torso: -1 (+1 s)'),('tier1','Limbs, hands: -3 (+3 s)'),('#FFFFFF','Miss: +5 s')]
HC=('#000000','Black = hard cover: hit does not count'); NT=('noshoot','Hatched = HOSTAGE +5 s')
# letter portrait placement
S1=7.2/1024; X1=(8.5-768*S1)/2; Y1=1.9
DOC=json.load(open('targets.json')); T=DOC['targets']
for k in [k for k in T if k.startswith('dh-')]: del T[k]
SCALE='3 yd = ~30 yd sim (figure ~1/10 scale)'
def sheet(key,code,mid,name,drills,ins,zones,art,leg,dist=SCALE,layout=None):
    t=dict(code=code,name=name,markerIds=list(range(mid,mid+4)),scoring='idpa',set='diehard',drills=drills,distance=dist,instructions=ins,art=art,zones=zones,legend=[list(x) for x in leg])
    if layout: t['layout']=layout
    T[key]=t
A=lambda k:[dict(src=f'art/dh-{k}.png',x=round(X1,3),y=Y1,w=round(768*S1,3),h=7.2)]
def one(key,code,mid,name,ch,drills,ins,hc=None):
    z=zones_for(ch,'T1',X1,Y1,S1)
    if hc: z=[dict(name='HC',kind='hardcover',shape='rect',**dict(zip('xywh',hc)))]+z
    sheet(key,code,mid,name,drills,ins,z,A(ch),LEG_T+([HC] if hc else []))
one('dh-hans','LD-201',101,'Die Hard: Hans (HK P7)','hans',['dh-hans-mozambique','dh-course'],['Nakatomi 30th floor: the leader draws his P7.','Mozambique: 2 to the chest -0, then 1 to the head -0.','Outlines are faint on purpose: read the anatomy.','Say "start" or tap; gun holstered until the beep.'])
one('dh-karl','LD-202',105,'Die Hard: Karl (stairwell)','karl',['dh-stairwell','dh-course'],['Stairwell: Karl comes up the stairs, lower body behind the rail.','2 to the exposed chest/head. Black rail = hard cover.','Faint outlines = scoring zones on real anatomy.','Say "start" or tap.'],hc=(X1+170*S1,Y1+560*S1,430*S1,9.15-(Y1+560*S1)))
one('dh-tony','LD-203',109,'Die Hard: Tony (MP5)','tony',['dh-tony','dh-course'],['Thirty-first floor: Tony comes through the door.','2 to the chest -0. Gun hands are -3.','Faint outlines = scoring zones.','Say "start" or tap.'])
one('dh-franco','LD-204',113,'Die Hard: Franco (desk)','franco',['dh-franco','dh-course'],['Lobby: Franco behind the reception desk.','2 to exposed chest/head. Black desk = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'],hc=(X1+150*S1,Y1+600*S1,470*S1,9.15-(Y1+600*S1)))
one('dh-heinrich','LD-205',117,'Die Hard: Heinrich (pillar)','heinrich',['dh-heinrich','dh-course'],['Vault floor: Heinrich half behind a pillar.','2 to the exposed chest -0. Black pillar = hard cover.','Faint outlines = scoring zones.','Say "start" or tap.'],hc=(X1+150*S1,1.85,(160)*S1,7.3))
one('dh-eddie','LD-206',121,'Die Hard: Eddie (fake guard)','eddie',['dh-eddie'],['Lobby guard desk: is the "guard" armed and hostile?','GUN = 2 to the chest. HANDS UP = say "Drop it!" in 3 s.','Hit on a compliant call = +5 s.','Mic on. Say "start" or tap.'])
one('dh-theo','LD-207',125,'Die Hard: Theo (vault tech)','theo',['dh-theo'],['Vault: the tech has his hands up... for now.','HANDS UP = say "Show me your hands!" in 3 s, do NOT shoot.','GUN = 2 to the chest.','Mic on. Say "start" or tap.'])
one('dh-billclay','LD-208',129,'Die Hard: "Bill Clay" impostor','billclay',['dh-billclay','dh-course'],['Roof stairs: a "hostage" with an accent. Wait for the call.','HANDS UP = verbal "Get down!" within 3 s.','GUN = 2 chest + 1 head.','Hit on a compliant call = +5 s. Mic on.'])
z=[hostage('hans-holly','HOLLY',X1,Y1,S1,xmax=385)]+zones_for('hans-holly','T1',X1,Y1,S1)
sheet('dh-hans-holly','LD-209',133,'Die Hard: Hans holds Holly',['dh-hans-holly','dh-course'],['Window scene: Hans has Holly, pistol at her side.','1 shot to Hans head -0. Holly is hatched = HOSTAGE.','Any hit on Holly = +5 s and stage fail.','Say "start" or tap.'],z,A('hans-holly'),LEG_T+[NT])
# lobby: party guest (NT) + Tony, cropped 2-up on letter
S2=6.9/1024; CR=150; W2=470*S2; X2a=0.4+(7.7-2*W2)/2; X2b=X2a+W2; Y2=2.05
z=[hostage('partyguest','GUEST',X2a,Y2,S2,crop=CR)]+zones_for('tony','T1',X2b,Y2,S2,crop=CR)
art=[dict(src='art/dh-partyguest.png',x=round(X2a,3),y=Y2,w=round(W2,3),h=6.9,crop=[CR,0,620,1024]),dict(src='art/dh-tony.png',x=round(X2b,3),y=Y2,w=round(W2,3),h=6.9,crop=[CR,0,620,1024])]
sheet('dh-party','LD-210',137,'Die Hard: Christmas Party',['dh-party'],['30th floor party: a guest stands beside Tony.','2 to Tony only. Hatched white guest = HOSTAGE (+5 s).','Faint outlines = scoring zones.','Say "start" or tap.'],z,art,LEG_T+[NT])
# Nakatomi tabloid line-up
S3=5.9/1024; W3=470*S3; X3=0.4+(16.2-6*W3)/2; Y3=2.6
cast=[('hans','T1'),('karl','T2'),('franco','T3'),('eddie','T4'),('theo','T5'),('billclay','T6')]
z=[];art=[];tx=[]
for i,(k,g) in enumerate(cast):
    x=X3+i*W3; z+=zones_for(k,g,x,Y3,S3,crop=CR); art.append(dict(src=f'art/dh-{k}.png',x=round(x,3),y=Y3,w=round(W3,3),h=5.9,crop=[CR,0,620,1024]))
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
 dict(I,id='dh-hans-holly',name='Die Hard: Hans holds Holly (head shot)',target='dh-hans-holly',calls=[dict(group='T1',label='Hans head',say='Hans, head only',parts=['head'])],randomize=False,parTime=2.5,timeout=10,notes='1 shot to Hans head -0. Any hit on Holly (hatched) = +5 s non-threat.'),
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
    dict(name='6. The window: Hans holds Holly',target='dh-hans-holly',shots=1,order=['T1'],parts=['head'],startDelay=[2,4],parTime=2.5,timeout=10,brief='1 head shot. Do not hit Holly.')])]
json.dump(DR,open('drills.json','w'),indent=1)
print('ok',len([k for k in T if k.startswith('dh-')]),'dh sheets')
