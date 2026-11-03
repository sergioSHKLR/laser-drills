# Stress test: laser dots placed only on orange clay pixels (bright & dim dot variants, with/without white core).
import cv2,numpy as np,json,subprocess
dpi=100;W,H=640,480;PW,PH=850,1100
M=cv2.getPerspectiveTransform(np.float32([[0,0],[PW,0],[PW,PH],[0,PH]]),np.float32([[215,30],[445,48],[460,445],[200,435]]))
subprocess.run(['pdftoppm','-r','100','-png','-singlefile','../targets/clays-letter.pdf','/tmp/cl'],check=True)
base=cv2.GaussianBlur(cv2.warpPerspective(cv2.resize(cv2.imread('/tmp/cl.png'),(PW,PH)),M,(W,H)),(3,3),0)
import sys
o=(base.max(2)<70) if 'dome' in sys.argv else (base[:,:,2].astype(int)-base[:,:,:2].mean(2)>80)
o[:100]=0;o[380:]=0;o[:,:255]=0;o[:,405:]=0
ys,xs=np.nonzero(o); rng=np.random.default_rng(3); idx=rng.choice(len(xs),40,replace=False)
VAR={'bright+core':((60,60,255),(220,220,255)),'bright-nocore':((60,60,255),None),'dim-nocore':((50,50,215),None)}
out={}
for v,(c,core) in VAR.items():
    fr=[base.copy()]*3
    for i in idx:
        f=base.copy(); cv2.circle(f,(int(xs[i]),int(ys[i])),3,c,-1)
        if core: cv2.circle(f,(int(xs[i]),int(ys[i])),1,core,-1)
        fr+= [f,base,base]
    np.stack([cv2.cvtColor(x,cv2.COLOR_BGR2RGBA) for x in fr]).tofile(f'/tmp/sw_{v}.rgba'); out[v]=len(fr)
print('bg sample BGR',base[ys[idx[0]],xs[idx[0]]]); json.dump(out,open('/tmp/sw.json','w'))
