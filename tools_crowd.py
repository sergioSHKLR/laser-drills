"""Crowd Hunt (Self-Defense Training): BOLO-style description calls in a full-colour crowd.
15 GenerateImage people (art/src2/crowdA/B/C.jpg, 5 each, left->right) at three depths + faded backstop bystanders.
Per-person zones + attributes -> targets.json (people[]); drills -> drills.json. Calls are built at runtime by Core.crowdCalls."""
import json, cv2, numpy as np
from tools_diehard_safe import safe
SRC='art/src2/'
# attributes as rendered (checked by eye). skin: neutral BOLO descriptors. hat: None|'<color> ballcap'|'gray beanie'|'fedora'
P=[('crowdA',dict(sex='man',skin='dark',shirt='blue',jacket=None,hat='yellow ballcap',backpack='green',glasses=True,held='phone')),
 ('crowdA',dict(sex='woman',skin='medium',shirt='white',jacket='gray',hat=None,backpack=None,glasses=False,held='coffee')),
 ('crowdA',dict(sex='man',skin='dark',shirt='green',jacket=None,hat='blue ballcap',backpack=None,glasses=True,held='gun')),
 ('crowdA',dict(sex='woman',skin='light',shirt='yellow',jacket='black',hat='gray beanie',backpack='blue',glasses=False,held='phone')),
 ('crowdA',dict(sex='man',skin='medium',shirt='purple',jacket=None,hat=None,backpack='black',glasses=True,held='umbrella')),
 ('crowdB',dict(sex='man',skin='light',shirt='gray',jacket='blue',hat='black ballcap',backpack=None,glasses=False,held='soda can')),
 ('crowdB',dict(sex='man',skin='light',shirt='blue',jacket='brown',hat='fedora',backpack=None,glasses=True,held='gun')),
 ('crowdB',dict(sex='woman',skin='medium',shirt='orange',jacket=None,hat='green ballcap',backpack='gray',glasses=False,held='keys')),
 ('crowdB',dict(sex='man',skin='light',shirt='black',jacket='green',hat=None,backpack='yellow',glasses=True,held='phone')),
 ('crowdB',dict(sex='woman',skin='light',shirt='white',jacket=None,hat='blue ballcap',backpack=None,glasses=False,held='water bottle')),
 ('crowdC',dict(sex='woman',skin='light',shirt='green',jacket='gray',hat=None,backpack='blue',glasses=True,held='coffee')),
 ('crowdC',dict(sex='man',skin='medium',shirt='yellow',jacket=None,hat='black ballcap',backpack=None,glasses=False,held='gun')),
 ('crowdC',dict(sex='man',skin='dark',shirt='blue',jacket='black',hat='gray beanie',backpack='green',glasses=False,held='phone')),
 ('crowdC',dict(sex='woman',skin='dark',shirt='gray',jacket=None,hat='yellow ballcap',backpack=None,glasses=True,held='wallet')),
 ('crowdC',dict(sex='man',skin='medium',shirt='purple',jacket='blue',hat='fedora',backpack='black',glasses=False,held='coffee'))]
def people(src,minarea=20000):
    b=safe(cv2.imread(SRC+src+'.jpg')); m=(b.min(axis=2)<232).astype(np.uint8)*255; m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(m); idx=sorted([i for i in range(1,n) if st[i][4]>minarea],key=lambda i:st[i][0])
    return [(b[st[i][1]:st[i][1]+st[i][3],st[i][0]:st[i][0]+st[i][2]],lab[st[i][1]:st[i][1]+st[i][3],st[i][0]:st[i][0]+st[i][2]]==i) for i in idx]
CUT={s:people(s) for s in ('crowdA','crowdB','crowdC')}
assert all(len(v)==5 for v in CUT.values()), {k:len(v) for k,v in CUT.items()}
IMGS=[CUT[s][i%5] for i,(s,_) in enumerate(P)]
BYS=[x for s in ('bys-office','bys-party') for x in people(s)]
DPI=100
def build(key,code,mid,page,field,rows,bys_h,name,paper_note,SPREAD=1.0):
    fx,fy,fw,fh=field['x'],field['y'],field['w'],field['h']; W,H=int(fw*DPI),int(fh*DPI)
    can=np.full((H,W,3),255,np.uint8); zones=[]; ppl=[]
    order=[3,9,0,13,6,11,1,14,4,8,12,2,7,10,5]   # shuffle depths so groups/threats spread
    k=0; rowdefs=[]
    for (n,hin,feet) in rows: rowdefs.append((order[k:k+n],hin,feet)); k+=n
    def paste(im,mk,x0,y0,fade=1.0):
        h,w=mk.shape; reg=can[y0:y0+h,x0:x0+w]; f=im if fade==1 else (255-(255-im.astype(np.float32))*fade).astype(np.uint8); reg[mk]=f[mk]
    # backstop bystanders first (faded, smallest, between back-row slots)
    bh=int(bys_h*DPI); back_feet=int((rows[0][2])*DPI)
    def rowlayout(ids,hin):   # tight cluster: step = 78% of the mean figure width, centred, odd rows shifted half a step
        hp=int(hin*DPI); ws=[int(IMGS[p][1].shape[1]*hp/IMGS[p][1].shape[0]) for p in ids]; step=int(np.mean(ws)*(0.95 if hin==rowdefs[0][1] else 0.8)*SPREAD)
        tot=step*(len(ids)-1)+ws[-1]; x0=(W-tot)//2; return [x0+i*step for i in range(len(ids))],ws
    L0,w0=rowlayout(rowdefs[0][0],rowdefs[0][1]); nb=len(L0); bx=[L0[i]+w0[i]//2+(L0[i+1]-L0[i])//2 for i in range(nb-1)]
    for j,x in enumerate(bx):
        im,mk=BYS[j%len(BYS)]; sc=bh/mk.shape[0]; w=int(mk.shape[1]*sc); im=cv2.resize(im,(w,bh),interpolation=cv2.INTER_AREA); mk2=cv2.resize(mk.astype(np.uint8),(w,bh),interpolation=cv2.INTER_NEAREST)>0
        x0=x-w//2; y0=back_feet-bh-int(0.25*DPI); paste(im,mk2,x0,y0,0.4)
        cs,_=cv2.findContours(mk2.astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
        zones.append(dict(name=f'BYSTANDER {j+1}',kind='bystander',shape='poly',penalty=-10,pts=[[round(fx+(px+x0)/DPI,3),round(fy+(py+y0)/DPI,3)] for px,py in cv2.approxPolyDP(c,2.0,True)[:,0,:]]))
    pid=0
    for ids,hin,feet in rowdefs:
        hp=int(hin*DPI); n=len(ids); LX,_=rowlayout(ids,hin); ri=[r[0] for r in rowdefs].index(ids)
        for i,pi in enumerate(ids):
            im,mk=IMGS[pi]; sc=hp/mk.shape[0]; w=int(mk.shape[1]*sc); im=cv2.resize(im,(w,hp),interpolation=cv2.INTER_AREA); mk2=cv2.resize(mk.astype(np.uint8),(w,hp),interpolation=cv2.INTER_NEAREST)>0
            x0=max(0,min(W-w,LX[i])); y0=int(feet*DPI)-hp
            reg=can[y0:y0+hp,x0:x0+w]; reg[mk2]=im[mk2]
            pid+=1; G=f'P{pid:02d}'; T=lambda x,y:[round(fx+(x+x0)/DPI,3),round(fy+(y+y0)/DPI,3)]
            cs,_=cv2.findContours(mk2.astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); c=max(cs,key=cv2.contourArea)
            ys,xs=np.nonzero(mk2[:int(hp*0.1)]); hx=xs.mean(); ys2,xs2=np.nonzero(mk2[int(hp*0.18):int(hp*0.4)]);
            # chest x: median of the central band to ignore backpacks/arms
            cxs=np.median(xs2); hy=hp*0.065; cy=hp*0.29
            base=dict(kind='score',tier='tier1',group=G,subtle=True)
            zones+=[dict(base,name=f'{G} -3',shape='poly',pts=[T(*p) for p in cv2.approxPolyDP(c,2.0,True)[:,0,:]],score=-3,pd=3,part='body',sil=True),
             dict(base,name=f'{G} -1',shape='ellipse',cx=T(hx,hy)[0],cy=T(hx,hy)[1],rx=round(hp*0.045/DPI,3),ry=round(hp*0.06/DPI,3),score=-1,pd=1,part='head'),
             dict(base,name=f'{G} -0',shape='ellipse',cx=T(cxs,cy)[0],cy=T(cxs,cy)[1],rx=round(hp*0.05/DPI,3),ry=round(hp*0.07/DPI,3),score=0,pd=0,part='body')]
            for q in zones[-3:]: q['z']=ri*10+i
            ppl.append(dict(P[pi][1],group=G,x=round(fx+(x0+w/2)/DPI,3),y=round(fy+(y0+hp)/DPI,3),depth=['far','mid','near'][rowdefs.index((ids,hin,feet))]))
    cv2.imwrite(f'art/{key}.png',can)
    t=dict(code=code,name=name,markerIds=list(range(mid,mid+4)),scoring='idpa',set='crowd',category='training',drills=['crowd-l1','crowd-l2','crowd-l3'],
      distance='3-5 yd',instructions=['Hear/read the BOLO; find ONE person; 2 to chest.','Wrong person +5 s. Faded = BYSTANDER +10 s.','L1: 1 trait. L2: 2. L3: 3 or relative spot.',paper_note],
      art=[dict(src=f'art/{key}.png',x=fx,y=fy,w=fw,h=fh)],zones=zones,people=ppl,
      legend=[['tier1','Chest -0, head -1, body -3'],['#FFFFFF','Miss: +5 s'],['cover','Faded = BYSTANDER +10 s']])
    if page: t['layout']=dict(page=page,field=field)
    return t
DOC=json.load(open('targets.json')); T=DOC['targets']; F=DOC['template']['field']
fl=dict(x=0.4,y=1.95,w=7.7,h=7.1)
T['crowd']=build('crowd','LD-301',145,None,dict(F,**fl),[(6,1.9,2.2),(5,2.6,4.6),(4,3.3,7.05)],1.3,'Crowd Hunt (Letter)','Mic on for spoken calls. Say "start" or tap.')
ft=dict(x=0.4,y=1.95,w=16.2,h=7.25)
T['crowd-tabloid']=build('crowd-tabloid','LD-302',149,{'w':17,'h':11},ft,[(6,2.0,2.3),(5,2.7,4.75),(4,3.35,7.2)],1.4,'Crowd Hunt (Tabloid)','Print Tabloid 11x17 at 100%. Say "start" or tap.',SPREAD=1.25)
for k in ('crowd','crowd-tabloid'): T[k]['drills']=[f'crowd-l{i}' for i in (1,2,3)]
json.dump(DOC,open('targets.json','w'),indent=1)
D=json.load(open('drills.json')); D=[d for d in D if not d['id'].startswith('crowd-')]
for lv,par in ((1,4.0),(2,6.0),(3,9.0)):
    D.append(dict(id=f'crowd-l{lv}',name=f'Crowd Hunt L{lv} ('+['','one attribute','two attributes','three+ / relative position'][lv]+')',target='crowd',targets=['crowd','crowd-tabloid'],
      scoring='idpa',category='training',maxPerShot=0,startDelay=[2,4],parTime=par,timeout=30,crowd=dict(level=lv,rounds=3,shots=2,wrongPenalty=5),
      notes='Description is spoken and shown. Each call matches exactly one person. 2 shots per call, 3 random rounds. Wrong person +5 s, bystander +10 s (backstop failure).'))
json.dump(D,open('drills.json','w'),indent=1); print('ok crowd',len(T['crowd']['people']))
