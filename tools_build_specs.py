"""Builds IDPA-style + hostage target specs into targets.json (geometry generated here, stored as plain data).
IDPA-style shapes are our own simplified artwork with approximate dimensions - not official IDPA art, logo or text."""
import json, math
D=json.load(open('targets.json')); T=D['targets']; PAL=D['template']['palette']
PAL.pop('control',None);PAL.pop('controlInk',None);PAL.update({"kraft":"#A99F8C","kraftLine":"#3B3326","pWhite":"#FFFFFF","p0":"#1F3A5F","backing":"#000000","handInk":"#FFFFFF"})
for k in [k for k in T if k.startswith('idpa-')]: del T[k]
def sil(cx,top,s,style='kraft',tag='',grp=None,kind='score'):
    X=lambda x:round(cx+x*s,3); Y=lambda y:round(top+y*s,3); P=lambda pts:[[X(a),Y(b)] for a,b in pts]
    tier={'kraft':('kraft','kraft','kraft'),'practice':('pWhite','pWhite','p0')}[style]
    g=dict(group=grp) if grp else {}
    def Z(name,pd,shape,ti,**kw):
        z=dict(name=tag+name,kind=kind,shape=shape,tier=ti,line='kraftLine' if style=='kraft' else 'outline',**g,**kw)
        if kind=='score': z.update(score=-pd,pd=pd)
        else: z.update(penalty=-5,ntSeconds=5,plain=True)
        return z
    outer=[(-3,0),(3,0),(3,6.5),(5,6.5),(9,10.5),(9,26),(6,30),(-6,30),(-9,26),(-9,10.5),(-5,6.5),(-3,6.5)]
    band=[(-4,8.5),(4,8.5),(6.5,11),(6.5,23),(4.5,25.5),(-4.5,25.5),(-6.5,23),(-6.5,11)]
    zs=[Z('-3',3,'poly',tier[0],pts=P(outer),label=[X(-7.6),Y(18)]),
            Z('-1',1,'rect',tier[1],x=X(-3),y=Y(0),w=round(6*s,3),h=round(6.5*s,3),label=[X(2.1),Y(1.1)]),
            Z('-1',1,'poly',tier[1],pts=P(band),label=[X(0),Y(23.3)]),
            Z('-0',0,'circle',tier[2],cx=X(0),cy=Y(3.3),r=round(2*s,3)),
            Z('-0',0,'circle',tier[2],cx=X(0),cy=Y(15),r=round(4*s,3))]
    for z,pt in zip(zs,['body','head','body','head','body']): z['part']=pt
    return zs
def hands(cx,top,s):
    out=[]
    def bar(bx,by,ang,L,w):
        a=math.radians(ang); dx,dy=math.sin(a),-math.cos(a); nx,ny=-dy,dx
        pts=[[bx+nx*w,by+ny*w],[bx+nx*w*0.8+dx*L,by+ny*w*0.8+dy*L],[bx+dx*(L+w*0.6),by+dy*(L+w*0.6)],[bx-nx*w*0.8+dx*L,by-ny*w*0.8+dy*L],[bx-nx*w,by-ny*w]]
        return dict(name='hand',kind='decor',shape='poly',pts=[[round(x,3),round(y,3)] for x,y in pts],fill="handInk",line="ink")
    for side in (-1,1):
        hx,hy=cx+side*2.7*s,top+16.5*s   # palm centre (real-inch offsets scaled)
        out.append(dict(name='hand',kind='decor',shape='ellipse',cx=round(hx,3),cy=round(hy,3),rx=round(1.6*s,3),ry=round(1.9*s,3),fill="handInk",line="ink"))
        for i,(off,ang,L) in enumerate([(-1.05,-14,2.3),(-0.35,-4,2.7),(0.35,4,2.8),(1.05,14,2.4)]):
            out.append(bar(hx+off*s,hy-1.0*s,ang,L*s,0.36*s))
        out.append(bar(hx-side*1.3*s,hy+0.4*s,-side*50,1.3*s,0.4*s))  # thumb toward body centre
    return out
S=1/4.5; CX,TOP=4.25,2.2
def cover(pts,label): return dict(name='HC',kind='hardcover',shape='poly',pts=[[round(CX+a*S,3),round(TOP+b*S,3)] for a,b in pts],label=[round(CX+label[0]*S,3),round(TOP+label[1]*S,3)])
base=dict(scoring='idpa',drills=['idpa-course'],distance='3 yd = ~13.5 yd sim (1/4.5 scale)')
PD=['Scored as points down: -0 / -1 / -3 (+1 s per PD).','Head: -0 circle, rest of head box -1. Miss = 5 PD.']
def add(key,code,name,ids,zones,ins,**kw): T[key]=dict(code=code,name=name,markerIds=ids,**{**base,**kw},instructions=ins,zones=zones)
add('idpa-threat','LD-101','IDPA-style Threat',[17,18,19,20],sil(CX,TOP,S),PD+['Classic kraft-style threat, own artwork.'])
add('idpa-hc-left','LD-102','IDPA-style Hard Cover: Left',[21,22,23,24],sil(CX,TOP,S)+[cover([(-10.5,5.5),(-0.6,5.5),(-0.6,31),(-10.5,31)],(-5,20))],
    ['Black = hard cover: hits there do not count.','Only the right half of the threat is exposed.']+PD[:1]+['Hit only in hard cover = miss (5 PD).'])
add('idpa-hc-lower','LD-103','IDPA-style Hard Cover: Lower',[25,26,27,28],sil(CX,TOP,S)+[cover([(-10.5,17.5),(7.5,17.5),(7.5,31),(-10.5,31)],(-1.5,24.5))],
    ['Lower body is behind hard cover (black).','Upper -0 arc and head are exposed.']+PD[:1]+['Hit only in hard cover = miss (5 PD).'])
add('idpa-hc-diagonal','LD-104','IDPA-style Hard Cover: Diagonal',[29,30,31,32],sil(CX,TOP,S)+[cover([(2.5,7.5),(10.5,7.5),(10.5,31),(-3,31)],(5.5,22))],
    ['Diagonal hard cover over the right side.','Precision on the exposed -0 edge.']+PD[:1]+['Hit only in hard cover = miss (5 PD).'])
add('idpa-nonthreat','LD-105','IDPA-style Non-Threat (open hands)',[49,50,51,52],sil(CX,TOP,S,kind='noshoot',tag='NT ')+hands(CX,TOP,S),
    ['Open hands = NON-THREAT. Do not shoot.','Any hit anywhere on it = +5 s (HNT).','Use as a no-shoot / shoot-through drill.','Pair with LD-106 for threat + non-threat.'])
add('idpa-practice','LD-106','IDPA-style Practice (dark -0)',[37,38,39,40],
    [dict(name='backing',kind='decor',shape='rect',x=0.75,y=1.95,w=7.0,h=7.15,fill='backing')]+sil(CX,TOP,S,style='practice'),
    ['White practice face on black backing.','-0 circles are DARK BLUE, not red: a red','zone would mask the red laser dot.']+PD[:1])
pair=sil(2.25,1.95,1/5,kind='noshoot',tag='NT ',grp='NT')+hands(2.25,1.95,1/5)+sil(6.15,1.95,1/5,tag='T1 ',grp='T1')
add('idpa-nt-pair','LD-107','IDPA-style Threat + Non-Threat',[41,42,43,44],pair,
    ['LEFT = non-threat (hands): +5 s per hit.','RIGHT = threat: score -0/-1/-3.','Miss on the threat = 5 PD.','1/5 scale: 3 yd = ~15 yd sim.'],distance='3 yd = ~15 yd sim (1/5 scale)')
m=[]
# tight, overlapping line: T2 stands in front of T1 and T3 (front figure owns the hit: z + sil)
for i,cx in [(0,2.95),(2,5.55),(1,4.25)]:
    zs=sil(cx,3.2 if i!=1 else 3.45,1/9,tag=f'T{i+1} ',grp=f'T{i+1}')
    for q in zs: q['z']=2 if i==1 else 1
    zs[0]['sil']=True; m+=zs
add('idpa-multi','LD-108','IDPA-style Multiple Threats',[45,46,47,48],m,
    ['Engage T1, T2, T3 left to right, 2 each.','Out-of-order engagement = PE (+3 s).','Each PD = +1 s. Miss = 5 PD.','1/9 scale: 3 yd = ~27 yd sim.'],distance='3 yd = ~27 yd sim (1/9 scale)')

# ---- all-variations sheet (letter landscape + tabloid landscape) ----
VAR=[('Regular','plain'),('Hard cover: vertical','hcv'),('Hard cover: lower','hcl'),('Head only','head'),
     ('Mozambique 2B+1H','plain'),('NON-THREAT','nt'),('Hard cover: diagonal','hcd'),('Behind non-threat','behind')]
def cell(i,name,v,cx,top,s):
    g=f'T{i}'; HC=lambda pts:dict(name='HC',kind='hardcover',shape='poly',pts=[[round(cx+a*s,3),round(top+b*s,3)] for a,b in pts])
    if v=='nt': return sil(cx,top,s,kind='noshoot',tag=f'{g} NT ',grp=g+'NT')+hands(cx,top,s)
    if v=='behind':  # threat partly hidden behind a non-threat standing in front (NT checked first)
        return sil(cx-5.5*s,top,s,tag=g+' ',grp=g)+sil(cx+5.5*s,top+1.5*s,s,kind='noshoot',tag=f'{g} NT ',grp=g+'NT')+hands(cx+5.5*s,top+1.5*s,s)
    z=sil(cx,top,s,tag=g+' ',grp=g)
    if v=='hcv': z.append(HC([(-10,5.5),(-0.6,5.5),(-0.6,31),(-10,31)]))
    if v=='hcl': z.append(HC([(-10,17.5),(10,17.5),(10,31),(-10,31)]))
    if v=='head': z.append(HC([(-10,7),(10,7),(10,31),(-10,31)]))
    if v=='hcd': z.append(HC([(2.5,7.5),(10,7.5),(10,31),(-3,31)]))
    return z
def allsheet(key,code,ids,W,H,s,xs,tops,lsz,dist):
    zones=[];texts=[]
    for i,(name,v) in enumerate(VAR):
        cx=xs[i%4]; top=tops[i//4]; zones+=cell(i+1,name,v,cx,top,s)
        texts.append(dict(x=cx,y=round(top-0.07,3),size=lsz,text=f'T{i+1}  {name}'))
    M_=0.4; fy=H-M_-1.2
    T[key]=dict(code=code,name='IDPA-style All Variations',markerIds=ids,scoring='idpa',drills=['idpa-all-calls' if key.endswith('tabloid') else 'idpa-all-calls-letter'],distance=dist,
      layout=dict(page=dict(w=W,h=H),field=dict(x=0.4,y=1.85,w=round(W-0.8,3),h=round(fy-0.15-1.85,3))),
      texts=texts,zones=zones,labelSize=lsz+1,
      instructions=['Drill calls targets in random order (spoken + on screen).','Mozambique (T5): 2 body, then 1 head, in order.',
        'T6 and the front figure on T8 are NON-THREATS: +5 s/hit.','Black = hard cover: hits there do not count.','Out of order / wrong Mozambique part = PE +3 s.'])
allsheet('idpa-all-tabloid','LD-110',[53,54,55,56],17,11,1/9,[2.5,6.25,10.0,13.75],[2.2,5.85],8,'3 yd = ~27 yd sim (1/9 scale)')
allsheet('idpa-all-letter','LD-111',[57,58,59,60],11,8.5,1/14,[2.75,4.5,6.25,8.25],[2.1,4.48],6,'3 yd = ~42 yd sim (1/14 scale)')
json.dump(D,open('targets.json','w'),indent=1)
dr=json.load(open('drills.json'))
for d in dr:
    if d['id']=='idpa-course':
        d['name']='IDPA-style familiarization course (7 stages)'
        d['stages']=[
 {"name":"1. Warm-up (practice face)","target":"idpa-practice","shots":3,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"3 shots to the dark body -0 circle. Learn the zones."},
 {"name":"2. Basic threat","target":"idpa-threat","shots":2,"startDelay":[2,4],"parTime":3.0,"timeout":10,"brief":"From the beep: 2 to the body -0."},
 {"name":"3. Head shots","target":"idpa-threat","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"2 to the head -0 circle; rest of the head box is -1."},
 {"name":"4. Hard cover: left","target":"idpa-hc-left","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"Left half is behind hard cover. 2 on the exposed -0."},
 {"name":"5. Hard cover: lower","target":"idpa-hc-lower","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"Lower body covered. 2 on the upper -0 or head."},
 {"name":"6. Hard cover: diagonal","target":"idpa-hc-diagonal","shots":2,"startDelay":[2,4],"parTime":4.5,"timeout":10,"brief":"Diagonal cover. 2 on the exposed -0 edge."},
 {"name":"7. Threat + non-threat","target":"idpa-nt-pair","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"2 on the RIGHT threat only. Hands = non-threat (+5 s)."},
 {"name":"8. Multiple threats","target":"idpa-multi","shots":6,"order":["T1","T1","T2","T2","T3","T3"],"startDelay":[2,4],"parTime":8.0,"timeout":20,"brief":"2 each on T1, T2, T3 in order. Out of order = PE."}]
        d['name']='IDPA-style familiarization course (8 stages)'
dr=[d for d in dr if d['id']!='idpa-all-calls']
CALLS=[{"group":"T1","label":"Regular","shots":2},{"group":"T2","label":"Vertical cover","shots":2},{"group":"T3","label":"Lower cover","shots":2},
 {"group":"T4","label":"Head only","shots":1,"parts":["head"]},{"group":"T5","label":"Mozambique","parts":["body","body","head"]},
 {"group":"T7","label":"Diagonal cover","shots":2},{"group":"T8","label":"Behind non-threat","shots":2}]
for tk,lab in (('idpa-all-tabloid','tabloid 11x17'),('idpa-all-letter','letter landscape')):
    dr.append({"id":"idpa-all-calls" if tk.endswith('tabloid') else "idpa-all-calls-letter","name":f"IDPA-style random calls ({lab})","target":tk,"scoring":"idpa","maxPerShot":0,
     "calls":CALLS,"randomize":True,"startDelay":[2,4],"parTime":15.0,"timeout":40,
     "notes":"Targets are called in random order (spoken + shown). Shoot only the called threats with the required shots; T5 Mozambique = 2 body then 1 head. T6 / front of T8 are non-threats (+5 s). Wrong order or Mozambique part = PE +3 s. Each PD = +1 s, miss = 5 PD."})
dr=[d for d in dr if not d['id'].startswith('shoot-dont-shoot')]
for tk,lab,sfx in (('idpa-all-tabloid','tabloid 11x17',''),('idpa-all-letter','letter landscape','-letter')):
    dr.append({"id":"shoot-dont-shoot"+sfx,"name":f"Shoot / don't-shoot: threat vs compliant ({lab})","target":tk,"scoring":"idpa","maxPerShot":0,
     "scenario":{"pool":["T1","T2","T3","T4","T5","T7","T8"],"count":4,"pCompliant":0.4,"threatShots":2,"window":3.0,"failCommand":3},
     "startDelay":[2,4],"parTime":10.0,"timeout":20,
     "notes":"At the beep 4 targets are called: 'GUN' = threat, shoot it 2x; 'HANDS UP' = compliant: do NOT shoot, give a verbal command ('Drop it!', 'Show me your hands!', 'Police, don't move!') within 3 s. Each hit on a compliant target = +5 s; each compliant target without a command in time = +3 s. Mic must be on. Only command phrases are heard while live."})
json.dump(dr,open('drills.json','w'),indent=1)
