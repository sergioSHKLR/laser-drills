import cv2,numpy as np,json
t=cv2.imread('target.png'); dpi=100
W,H=640,480
src=np.float32([[0,0],[850,0],[850,1100],[0,1100]])
dst=np.float32([[220,40],[440,55],[455,440],[205,430]])  # perspective, portrait target in landscape frame
M=cv2.getPerspectiveTransform(src,dst)
base=cv2.warpPerspective(t,M,(W,H),borderValue=(90,100,110))
base=cv2.GaussianBlur(base,(3,3),0)
rng=np.random.default_rng(1)
shots=[(4.25,5.5),(5.0,5.2),(4.25,7.2),(1.6,5.5),(6.8,8.0)]
out=[]
def save(img,name):
    noisy=np.clip(img.astype(int)+rng.integers(-6,7,img.shape),0,255).astype(np.uint8)
    rgba=cv2.cvtColor(noisy,cv2.COLOR_BGR2RGBA); rgba.tofile(name+'.rgba'); out.append(name)
for k in range(3): save(base,f'f{len(out)}')
for (x,y) in shots:
    p=cv2.perspectiveTransform(np.float32([[[x*dpi,y*dpi]]]),M)[0][0]
    f=base.copy(); cv2.circle(f,(int(p[0]),int(p[1])),3,(60,60,255),-1); cv2.circle(f,(int(p[0]),int(p[1])),1,(220,220,255),-1)
    save(f,f'f{len(out)}'); save(base,f'f{len(out)}'); save(base,f'f{len(out)}')
cv2.imwrite('sample_frame_hit.png',cv2.cvtColor(np.fromfile('f3.rgba',np.uint8).reshape(H,W,4),cv2.COLOR_RGBA2BGR))
json.dump({'w':W,'h':H,'frames':out,'shots':shots},open('frames.json','w'))
