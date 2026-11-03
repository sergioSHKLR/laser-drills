# Render each target PDF, warp into a synthetic camera frame, and add 1-frame laser dots at known points.
import cv2,numpy as np,json,subprocess,os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DOC=json.load(open('../targets.json')); dpi=100; W,H=640,480
rng=np.random.default_rng(1)
# (target, [(x,y,expected)])  expected = score or 'CTRL'
CASES={
 'bullseye':[(4.25,5.5,5),(5.4,5.5,3),(4.25,7.9,1),(1.0,3.0,0),(7.4,8.5,'CTRL')],
 'silhouette':[(4.25,5.6,5),(4.25,2.85,5),(3.1,7.5,3),(6.0,6.5,-5),(2.4,8.7,1)],
 'five-dot':[(2.2,3.2,5),(6.3,3.2,5),(4.25,5.4,5),(5.6,7.6,0),(2.2,7.6,0)],  # seq: last two out of order
 'idpa-threat':[(4.25,5.48,'-0'),(4.25,2.84,'-0'),(3.2,7.0,'-1'),(2.6,8.5,'-3'),(1.0,4.0,'MISS')],
 'idpa-hardcover':[(5.0,7.0,'HC'),(3.6,5.2,'-0'),(7.4,8.5,'CTRL')],
 'idpa-nonthreat':[(5.5,6.5,'NT'),(3.5,5.5,'-0')],
 'idpa-multi':[(1.75,5.07,'T1 -0'),(4.25,5.07,'T2 -0'),(6.75,3.744,'T3 -0')],
 'hostage':[(5.3,6.5,-10),(4.25,2.85,5),(3.8,5.5,5)],
 'clays':[(2.4,3.3,5),(6.0,5.75,2),(3.4,8.25,5),(3.4,7.4,5),(7.4,8.5,'CTRL')],  # 3rd hit only scores via spread
}
src=np.float32([[0,0],[850,0],[850,1100],[0,1100]])
dst=np.float32([[215,30],[445,48],[460,445],[200,435]])
M=cv2.getPerspectiveTransform(src,dst); meta={'w':W,'h':H,'sets':{}}
for key,shots in CASES.items():
    subprocess.run(['pdftoppm','-r',str(dpi),'-png','-singlefile',f'../targets/{key}-letter.pdf','/tmp/tgt'],check=True)
    page=cv2.resize(cv2.imread('/tmp/tgt.png'),(850,1100))
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
