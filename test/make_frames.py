# Render each target PDF, warp into a synthetic camera frame, and add 1-frame laser dots at known points.
import cv2,numpy as np,json,subprocess,os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DOC=json.load(open('../targets.json')); dpi=100; W,H=640,480
rng=np.random.default_rng(1)
from matplotlib.path import Path as _P
def Z(key,name,i=0):
    zs=[z for z in DOC['targets'][key]['zones'] if z['name']==name]; z=zs[i]
    if 'cx' in z: return (round(z['cx'],3),round(z['cy'],3))
    if z['shape']=='rect': return (z['x']+z['w']/2,z['y']+z['h']/2)
    P=_P(z['pts']); xs=[q[0] for q in z['pts']]; ys=[q[1] for q in z['pts']]; cx=sum(xs)/len(xs)
    for dy in [0.5,0.4,0.6,0.3,0.7]:
        y=min(ys)+(max(ys)-min(ys))*dy
        for dx in [0,0.1,-0.1,0.2,-0.2]:
            if P.contains_point((cx+dx,y)): return (round(cx+dx,3),round(y,3))
    raise Exception(name)
def S(key,*names): return [(*Z(key,n.split('#')[0],int(n.split('#')[1]) if '#' in n else 0),n.split('#')[0]) for n in names]
# (target, [(x,y,expected)])  expected = score, zone name or 'MISS'
CASES={
 'bullseye':[(4.25,5.5,5),(5.4,5.5,3),(4.25,7.9,1),(1.0,3.0,0)],
 'silhouette':[(4.25,5.6,5),(4.25,2.85,5),(3.1,7.5,3),(6.0,6.5,-5),(2.4,8.7,1)],
 'five-dot':[(2.2,3.2,5),(6.3,3.2,5),(4.25,5.4,5),(5.6,7.6,0),(2.2,7.6,0)],  # seq: last two out of order
 'idpa-threat':[(4.25,5.53,'-0'),(4.25,2.93,'-0'),(4.81,2.31,'-1'),(5.36,5.53,'-1'),(6.03,5.53,'-3'),(1.0,4.0,'MISS')],
 'idpa-hc-left':[(3.14,5.53,'HC'),(4.69,5.53,'-0')],
 'idpa-hc-lower':[(4.25,7.09,'HC'),(4.25,4.87,'-0')],
 'idpa-hc-diagonal':[(5.81,6.64,'HC'),(3.6,5.53,'-0')],
 'idpa-nonthreat':[(4.25,2.93,'NT -3'),(1.0,4.0,'MISS')],
 'idpa-practice':[(4.25,5.53,'-0'),(1.0,4.0,'MISS')],
 'idpa-nt-pair':[(2.25,4.95,'NT -3'),(6.15,4.95,'T1 -0')],
 'idpa-multi':[(2.95,4.867,'T1 -0'),(4.25,5.117,'T2 -0'),(5.55,3.567,'T3 -0')],
 'idpa-all-tabloid':S('idpa-all-tabloid','T1 -0#1','HC','T4 -0#0','T6 NT -3','T7 -0#1')+[(12.4,7.5,'T8 -3'),(13.9,7.5,'T8 NT -3')],
 'idpa-all-letter':[(2.75,2.1+15/14,'T1 -0'),(6.25,4.48+15/14,'T7 -0'),(4.5,4.48+3.3/14,'T6 NT -3')],
 'hostage':[(5.3,6.5,-10),(4.25,2.85,5),(3.8,5.5,5)],
 'dh-hans':S('dh-hans','T1 -0#0','T1 -0#1','BYSTANDER 1')+[(1.0,4.0,'MISS')],
 'dh-karl':S('dh-karl','HC','T1 -0#1'),
 'dh-finale':S('dh-finale','HOLLY NT','T1 -0#0','T2 -0#0'),
 'dh-nakatomi':S('dh-nakatomi','T4 -0#1','T6 -0#1','T3 -0#1','POWELL FRIENDLY'),
 'dh-uli':S('dh-uli','T1 -0#1','BYSTANDER 2'),
 'dh-powell':S('dh-powell','POWELL FRIENDLY'),
 'dh-lobby':S('dh-lobby','T1 -0#1','POWELL FRIENDLY'),
 'clays':[(2.45,3.55,5),(5.85,5.15,5),(5.85,6.45,2),(2.95+1.15,7.55-0.3,3),(7.6,2.5,0)],  # 1-2 dome 5; 4th orange rim via spread 3
}
meta={'w':W,'h':H,'sets':{}}
for key,shots in CASES.items():
    pg=DOC['targets'][key].get('layout',{}).get('page',DOC['template']['page']); PWp,PHp=int(pg['w']*dpi),int(pg['h']*dpi)
    src=np.float32([[0,0],[PWp,0],[PWp,PHp],[0,PHp]])
    dst=np.float32([[215,30],[445,48],[460,445],[200,435]]) if PHp>PWp else np.float32([[25,70],[615,55],[625,420],[15,430]])
    M=cv2.getPerspectiveTransform(src,dst)
    subprocess.run(['pdftoppm','-r',str(dpi),'-png','-singlefile',f'../targets/{key}-letter.pdf','/tmp/tgt'],check=True)
    page=cv2.resize(cv2.imread('/tmp/tgt.png'),(PWp,PHp))
    base=cv2.GaussianBlur(cv2.warpPerspective(page,M,(W,H),borderValue=(90,100,110)),(3,3),0)
    frames=[]
    def save(img):
        n=f'{key}_{len(frames)}'; noisy=np.clip(img.astype(int)+rng.integers(-6,7,img.shape),0,255).astype(np.uint8)
        cv2.cvtColor(noisy,cv2.COLOR_BGR2RGBA).tofile(n+'.rgba'); frames.append(n)
    for _ in range(3): save(base)
    for x,y,_ in shots:
        p=cv2.perspectiveTransform(np.float32([[[x*dpi,y*dpi]]]),M)[0][0]; f=base.copy()
        cv2.circle(f,(int(p[0]),int(p[1])),3,(60,60,255),-1); cv2.circle(f,(int(p[0]),int(p[1])),1,(220,220,255),-1)
        save(f); save(base); save(base)
    meta['sets'][key]={'frames':frames,'shots':shots}
json.dump(meta,open('frames.json','w'))
