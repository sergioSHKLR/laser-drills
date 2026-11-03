# Render each target PDF, warp into a synthetic camera frame, and add 1-frame laser dots at known points.
import cv2,numpy as np,json,subprocess,os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DOC=json.load(open('../targets.json')); dpi=100; W,H=640,480
rng=np.random.default_rng(1)
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
 'idpa-multi':[(1.75,4.867,'T1 -0'),(4.25,4.867,'T2 -0'),(6.75,3.567,'T3 -0')],
 'idpa-all-tabloid':[(2.4,2.2+15/9,'T1 -0'),(6.3-0.5,4.0,'HC'),(14.1,2.2+3.3/9,'T4 -0'),(14.1,4.5,'HC'),(6.3,5.85+15/9,'T6 NT -3'),(14.1+5.5/9,5.85+(1.5+15)/9,'T8 NT -3'),(14.1-5.5/9-0.6,5.85+15/9,'T8 -1')],
 'idpa-all-letter':[(1.65,2.1+15/14,'T1 -0'),(6.55,4.48+15/14,'T7 -0'),(4.1,4.48+3.3/14,'T6 NT -3')],
 'hostage':[(5.3,6.5,-10),(4.25,2.85,5),(3.8,5.5,5)],
 'dh-hans':[(4.166,2.491,'T1 -0'),(4.257,3.939,'T1 -0'),(2.04,4.71,'BYSTANDER 1'),(1.0,4.0,'MISS')],
 'dh-karl':[(4.2,7.5,'HC'),(4.222,4.009,'T1 -0')],
 'dh-finale':[(4.38,5.37,'HOLLY NT'),(5.348,4.293,'T1 -0'),(3.159,3.127,'T2 -0')],
 'dh-nakatomi':[(9.825,3.165,'T4 -0'),(15.241,3.983,'T6 -0')],
 'clays':[(2.4,3.3,5),(6.0,5.75,2),(3.4,8.25,5),(3.4,7.4,5)],  # 3rd hit only scores via spread
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
