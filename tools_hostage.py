"""Hostage (LD-005, key 'hostage'): the threat is the new Qualification Silhouette (head box, X/10/9/8 colored rings,
5 zone); a hostage silhouette stands in front, overlapping the threat's right side as a NO-HIT zone (-10).
Rewrites the 'hostage' spec in targets.json (run after tools_silhouette.py)."""
import json
D=json.load(open('targets.json'))
f=D['template']['field']; PAD=0.12
X0,X1,Y0,Y1=175,700,193,828
s=min((f['w']-2*PAD)/(X1-X0),(f['h']-2*PAD)/(Y1-Y0)); cx0=(X0+X1)/2
P=lambda x,y:[round(f['x']+f['w']/2+(x-cx0)*s,3),round(f['y']+PAD+(y-Y0)*s,3)]
L=lambda v:round(v*s,3)
BODY=[(359,370),(359,393),(236,447),(175,817),(231,828),(275,630),(292,703),(271,822),(519,822),(500,703),(516,630),(560,828),(616,817),(554,447),(434,393),(434,370)]
HEAD=dict(shape='ellipse',cx=P(397,285)[0],cy=P(397,285)[1],rx=L(67),ry=L(92))
RC=P(396,543)
C5,C8,C9,C10,CX='#C9DDF0','#6FC3BA','#4F86C6','#1F4E9A','#0E2A55'
def ring(n,r,sc,c): return dict(name=n,kind='score',shape='circle',cx=RC[0],cy=RC[1],r=L(r),score=sc,tier='tier5',subtle=True,shade=c,group='T')
hb0,hb1=P(352,241),P(440,329)
# hostage: head + shoulders/torso in front, lower right (covers the right edge of the 8/9 rings, X and head box stay clear)
HH=dict(shape='ellipse',cx=P(585,440)[0],cy=P(585,440)[1],rx=L(52),ry=L(70))
HB=[(545,505),(545,520),(470,560),(462,828),(700,828),(700,560),(625,520),(625,505)]
host=[dict(name='HOSTAGE',kind='noshoot',shape='poly',pts=[P(*q) for q in HB],penalty=-10,z=10,group='H',label=[P(585,700)[0],P(585,700)[1]]),
      dict(name='HOSTAGE',kind='noshoot',**HH,penalty=-10,z=10,group='H')]
zones=[dict(name='X',kind='score',shape='ellipse',cx=RC[0],cy=RC[1],rx=L(21),ry=L(28),score=10,tier='tier5',subtle=True,shade=CX,z=1,group='T',label=[RC[0],RC[1]+0.05]),
 ring('10',54,10,C10),ring('9',85,9,C9),ring('8',112,8,C8),
 dict(name='HEAD BOX',kind='score',shape='rect',x=hb0[0],y=hb0[1],w=round(hb1[0]-hb0[0],3),h=round(hb1[1]-hb0[1],3),score=10,tier='tier5',subtle=True,shade=C10,group='T'),
 dict(name='HEAD',kind='score',**HEAD,score=5,tier='tier1',subtle=True,shade=C5,group='T',label=[HEAD['cx'],HEAD['cy']-HEAD['ry']+0.18]),
 dict(name='BODY',kind='score',shape='poly',pts=[P(*q) for q in BODY],score=5,tier='tier1',subtle=True,shade=C5,group='T',label=[P(300,780)[0],P(300,780)[1]])]+host
for z in zones[1:4]: z['label']=[RC[0],round(RC[1]-z['r']+0.13,3)]
line=lambda z:{k:v for k,v in z.items() if k in('shape','cx','cy','r','rx','ry','x','y','w','h','pts')}
art=[dict(shape='poly',pts=[P(*q) for q in BODY],fill=C5),dict(HEAD,fill=C5)]+[dict(line(zones[i]),fill=c) for i,c in ((3,C8),(2,C9),(1,C10),(0,CX),(4,C10))]+\
    [dict(shape='poly',pts=[P(*q) for q in BODY],open=True),dict(shape='poly',pts=[P(236,447),P(275,630)],open=True),dict(shape='poly',pts=[P(554,447),P(516,630)],open=True),
     dict(shape='poly',pts=[P(*q) for q in HB],fill='#FFFFFF'),dict(HH,fill='#FFFFFF')]
t=D['targets']['hostage']
t.update(name='Hostage',distance='3-5 yd',drills=['hostage-head','hostage-cm','five-shot-par'],maxPerShot=10,zones=zones,lineart=art,
 instructions=['Threat = Qualification Silhouette: X/10 ring 10, 9, 8; head box 10; rest 5.','White figure in front = HOSTAGE: -10 per hit (overlap hits count as hostage).','Head box and left center mass are clean shots.','Mic on. Say "start" or tap.'],
 legend=[[CX,'X / 10 ring / head box: 10'],[C9,'9 ring: 9'],[C8,'8 ring: 8'],[C5,'Rest of head and body: 5'],['noshoot','White figure = HOSTAGE: -10'],['#FFFFFF','Outside: miss']])
t['meta']=dict(category='tactical',paper='letter',people='multi',features=['hostage','no-shoot'],weapon='pistol')
t.pop('art',None); t.pop('scoring',None)
json.dump(D,open('targets.json','w'),indent=1,ensure_ascii=False)
R=json.load(open('drills.json')); R=[d for d in R if d['id']!='hostage-cm']
R.append(dict(id='hostage-cm',name='Hostage: 2 center mass (par 3s)',target='hostage',shots=2,startDelay=[2,4],parTime=3.0,timeout=10,maxPerShot=10,category='training',notes='Two to the threat\'s exposed center mass (X/10/9); the hostage covers his right side. Hostage hit = -10.'))
for d in R:
    if d['id']=='hostage-head': d.update(maxPerShot=10,notes='Two in the head box (10 each); hostage hit = -10.')
json.dump(R,open('drills.json','w'),indent=1)
print('hostage ok', 'X at',RC)
