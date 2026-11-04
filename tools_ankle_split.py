import cv2,numpy as np
def split(path,thr=225):
    s=cv2.imread(path); m=(s.min(2)<thr).sum(0)>3; runs=[];st=None
    for x,v in enumerate(list(m)+[False]):
        if v and st is None: st=x
        if not v and st is not None:
            if x-st>40: runs.append((st,x))
            st=None
    out=[]
    for a,b in runs:
        c=s[:,max(0,a-4):b+4].copy(); mm=(c.min(2)<thr).astype(np.uint8); ys=np.where(mm.sum(1)>2)[0]; c=c[ys[0]:ys[-1]+1]
        mk=cv2.morphologyEx((c.min(2)<236).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
        n,lab,stt,_=cv2.connectedComponentsWithStats(mk); keep=[i for i in range(1,n) if stt[i][4]>800]
        c[~np.isin(lab,keep)]=255; out.append(c)
    return out
