"""Qualification silhouette (LD-002, key 'silhouette'): clean vector line art from Sergio's design,
with a head box and center-mass rings (X/10/9/8). Rewrites the 'silhouette' spec in targets.json."""
import json
D=json.load(open('targets.json'))
# design coordinates (px in the reference drawing) -> inches, maximized inside the scan field
f=D['template']['field']; PAD=0.12
X0,X1,Y0,Y1=175,616,193,828
s=min((f['w']-2*PAD)/(X1-X0),(f['h']-2*PAD)/(Y1-Y0)); cx0=(X0+X1)/2
P=lambda x,y:[round(f['x']+f['w']/2+(x-cx0)*s,3),round(f['y']+PAD+(y-Y0)*s,3)]
L=lambda v:round(v*s,3)
BODY=[(359,370),(359,393),(236,447),(175,817),(231,828),(275,630),(292,703),(271,822),(519,822),(500,703),(516,630),(560,828),(616,817),(554,447),(434,393),(434,370)]
HEAD=dict(shape='ellipse',cx=P(397,285)[0],cy=P(397,285)[1],rx=L(67),ry=L(92))
RC=P(396,543)
def ring(n,r,sc): return dict(name=n,kind='score',shape='circle',cx=RC[0],cy=RC[1],r=L(r),score=sc,tier='tier5',subtle=True)
hb0,hb1=P(352,241),P(440,329)
zones=[
 dict(name='X',kind='score',shape='ellipse',cx=RC[0],cy=RC[1],rx=L(21),ry=L(28),score=10,tier='tier5',subtle=True,shade='#163A75',z=1,label=[RC[0],RC[1]+0.05]),
 ring('10',54,10),ring('9',85,9),ring('8',112,8),
 dict(name='HEAD BOX',kind='score',shape='rect',x=hb0[0],y=hb0[1],w=round(hb1[0]-hb0[0],3),h=round(hb1[1]-hb0[1],3),score=10,tier='tier5',subtle=True),
 dict(name='HEAD',kind='score',**HEAD,score=5,tier='tier1',subtle=True,shade='#AFC4E6',label=[HEAD['cx'],HEAD['cy']-HEAD['ry']+0.18]),
 dict(name='BODY',kind='score',shape='poly',pts=[P(*q) for q in BODY],score=5,tier='tier1',subtle=True,shade='#AFC4E6',label=[RC[0],P(0,780)[1]]),
]
for z in zones[1:4]: z['label']=[RC[0],round(RC[1]-z['r']+0.13,3)]
line=lambda z:{k:v for k,v in z.items() if k in('shape','cx','cy','r','rx','ry','x','y','w','h','pts')}
C5,C8,C9,C10,CX='#C9DDF0','#6FC3BA','#4F86C6','#1F4E9A','#0E2A55'
for z,cc in zip(zones,(CX,C10,C9,C8,C10,C5,C5)): z['shade']=cc
art=[dict(shape='poly',pts=[P(*q) for q in BODY],fill=C5),dict(HEAD,shape='ellipse',fill=C5)]+[dict(line(zones[i]),fill=c) for i,c in ((3,C8),(2,C9),(1,C10),(0,CX),(4,C10))]+[dict(shape='poly',pts=[P(*q) for q in BODY],open=True),
     dict(shape='poly',pts=[P(236,447),P(275,630)],open=True),dict(shape='poly',pts=[P(554,447),P(516,630)],open=True)]
t=D['targets']['silhouette']
t.update(name='Qualification Silhouette',distance='3-7 yd (scaled ~1/3)',drills=['single-draw','five-shot-par'],maxPerShot=10,
 instructions=['Center mass: X/10 ring 10, 9 ring 9, 8 ring 8.','Head box 10; rest of head and body 5.','Outside the silhouette: miss.','X (center oval) scores 10; count Xs for tiebreaks.'],
 zones=zones,lineart=art,
 legend=[[CX,'X (center oval): 10 pts (X = tiebreak)'],[C10,'10 ring, head box: 10 pts'],[C9,'9 ring: 9 pts'],[C8,'8 ring: 8 pts'],[C5,'Rest of head and body: 5 pts'],['#FFFFFF','Outside silhouette: miss, 0 pts']])
t['meta']=dict(category='tactical',paper='letter',people='single',features=[],weapon='pistol')
t.pop('art',None); t.pop('scoring',None)
json.dump(D,open('targets.json','w'),indent=1,ensure_ascii=False)
print('scale in/px',round(s,5),'ring8 r',L(112),'center',RC)
