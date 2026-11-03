"""Writes IDPA-style and hostage target specs into targets.json (geometry is generated, then stored as plain data).
IDPA-style shapes are our own simplified, approximate artwork - NOT official IDPA dimensions or art."""
import json
D=json.load(open('targets.json'))
def threat(cx,top,s,tag='',grp=None):
    """Simplified IDPA-style threat, real-size 18x30in scaled by s (in per real in). Returns zones (outer first)."""
    X=lambda x:round(cx+x*s,3); Y=lambda y:round(top+y*s,3)
    g={'group':grp} if grp else {}
    out=[[X(-3),Y(0)],[X(3),Y(0)],[X(3),Y(6.5)],[X(1.5),Y(7.5)],[X(8),Y(8.5)],[X(9),Y(10)],[X(9),Y(30)],[X(-9),Y(30)],[X(-9),Y(10)],[X(-8),Y(8.5)],[X(-1.5),Y(7.5)],[X(-3),Y(6.5)]]
    L=lambda x,y:[X(x),Y(y)]
    return [
     dict(name=tag+'-3',kind='score',shape='poly',pts=out,score=-3,pd=3,tier='tier1',label=L(0,27.5),**g),
     dict(name=tag+'-1',kind='score',shape='rect',x=X(-2.6),y=Y(0.4),w=round(5.2*s,3),h=round(5.7*s,3),score=-1,pd=1,tier='tier3',label=L(0,5.2),**g),
     dict(name=tag+'-1',kind='score',shape='rect',x=X(-6),y=Y(9.5),w=round(12*s,3),h=round(16*s,3),score=-1,pd=1,tier='tier3',label=L(0,23.5),**g),
     dict(name=tag+'-0',kind='score',shape='circle',cx=X(0),cy=Y(3.1),r=round(2*s,3),score=0,pd=0,tier='tier5',**g),
     dict(name=tag+'-0',kind='score',shape='circle',cx=X(0),cy=Y(15),r=round(4*s,3),score=0,pd=0,tier='tier5',**g)]
S=1/4.5   # 30in target -> 6.67in tall; at 3 yd looks like ~13.5 yd
idpa_common=dict(scoring='idpa',drills=['idpa-course'])
T=D['targets']
T['idpa-threat']=dict(code='LD-101',name='IDPA-style Threat (1/4.5 scale)',markerIds=[17,18,19,20],distance='3 yd = ~13.5 yd sim',**idpa_common,
  instructions=['Scored as points down (PD): -0 / -1 / -3.','Each PD = +1 s. Miss = 5 PD.','Body -0 is the 8in circle, head -0 the 4in circle.','Approximate IDPA-style art, not official.'],
  zones=threat(4.25,2.15,S))
hc=threat(4.25,2.15,S)
hc.append(dict(name='HC',kind='hardcover',shape='rect',x=4.25-1*S,y=2.15+17*S,w=10*S+0.1,h=13*S+0.05,label=[4.25+4*S,2.15+24*S]))
T['idpa-hardcover']=dict(code='LD-102',name='IDPA-style Partial Hard Cover',markerIds=[21,22,23,24],distance='3 yd = ~13.5 yd sim',**idpa_common,
  instructions=['Black = hard cover: hits there do not count.','A hit only in hard cover = miss (5 PD).','Work the exposed -0 circle and head.','Each PD = +1 s.'],zones=hc)
nt=threat(4.25,2.15,S)
nt.append(dict(name='NT',kind='noshoot',shape='poly',penalty=-5,ntSeconds=5,
  pts=[[4.25+0.5*S,2.15+11*S],[4.25+3.5*S,2.15+9*S],[4.25+9.5*S,2.15+9.5*S],[4.25+11*S,2.15+13*S],[4.25+11*S,2.15+30*S],[4.25+0.5*S,2.15+30*S]],label=[4.25+6*S,2.15+20*S]))
T['idpa-nonthreat']=dict(code='LD-103',name='IDPA-style Threat + Non-Threat',markerIds=[25,26,27,28],distance='3 yd = ~13.5 yd sim',**idpa_common,
  instructions=['Hatched = NON-THREAT (open hands): +5 s per hit.','A hit on the non-threat gives no threat credit.','Take the exposed head or left body.','Each PD = +1 s. Miss = 5 PD.'],zones=nt)
m=[]
for i,cx in enumerate((1.75,4.25,6.75)):
    m+=threat(cx,3.4,1/9,tag=f'T{i+1} ',grp=f'T{i+1}')
T['idpa-multi']=dict(code='LD-104',name='IDPA-style Multiple Threats (1/9)',markerIds=[29,30,31,32],distance='3 yd = ~27 yd sim',**idpa_common,
  instructions=['Engage T1, T2, T3 left to right, 2 each.','Out-of-order engagement = PE (+3 s).','Each PD = +1 s. Miss = 5 PD.','Small scale: slow down, drive the dot.'],zones=m)
# Hostage (our 5/3/1 system)
h=[z for z in T['silhouette']['zones'] if z['kind']=='score']
h=json.loads(json.dumps(h))
h.append(dict(name='HOSTAGE',kind='noshoot',shape='poly',penalty=-10,label=[5.35,6.9],
  pts=[[4.45,4.95],[4.6,4.55],[5.0,4.3],[5.45,4.3],[5.85,4.55],[6.0,4.95],[5.85,5.4],[6.6,5.7],[6.9,6.3],[6.9,8.9],[4.2,8.9],[4.2,6.3],[4.55,5.7],[4.65,5.45]]))
T['hostage']=dict(code='LD-005',name='Hostage',markerIds=[33,34,35,36],distance='3-5 yd',drills=['hostage-head','five-shot-par'],
  instructions=['Hatched figure = HOSTAGE: -10 per hit.','Hostage overlaps the threat: overlap hits count as hostage.','Head A box and left body are clean shots.','Shoot START/STOP to begin.'],zones=h)
json.dump(D,open('targets.json','w'),indent=1)
dr=json.load(open('drills.json'))
dr=[d for d in dr if d['id'] not in('idpa-course','hostage-head')]
dr.append({"id":"hostage-head","name":"Hostage: 2 head shots (par 3s)","target":"hostage","shots":2,"startDelay":[2,4],"parTime":3.0,"timeout":10,"maxPerShot":5,"notes":"Precision under pressure; hostage hit = -10."})
dr.append({"id":"idpa-course","name":"IDPA-style familiarization course (5 stages)","type":"course","scoring":"idpa",
 "notes":"Time + points down. Swap the printed target before each stage; the app checks the target ID. Score = raw time + PD x1s + PE x3s + HNT x5s. Lower is better.",
 "stages":[
  {"name":"1. Basic threat","target":"idpa-threat","shots":2,"startDelay":[2,4],"parTime":3.0,"timeout":10,"brief":"From the beep: 2 shots to the body -0 circle."},
  {"name":"2. Partial hard cover","target":"idpa-hardcover","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"Lower body is behind black hard cover. 2 shots to exposed -0 / head."},
  {"name":"3. Non-threat (hostage)","target":"idpa-nonthreat","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"brief":"A non-threat covers the right side. 2 shots on the threat only."},
  {"name":"4. Head shots","target":"idpa-threat","shots":2,"startDelay":[2,4],"parTime":4.0,"timeout":10,"zoneHint":"head","brief":"2 shots to the head -0 (4in circle)."},
  {"name":"5. Multiple threats","target":"idpa-multi","shots":6,"order":["T1","T1","T2","T2","T3","T3"],"startDelay":[2,4],"parTime":8.0,"timeout":20,"brief":"2 shots each on T1, T2, T3 in order (left to right). Out of order = PE."}]})
for d in dr:
    if d['id']=='five-shot-par': d['notes']='Random delay, beep, 5 shots. Striker pistol: splits include rack time.'
json.dump(dr,open('drills.json','w'),indent=1)
