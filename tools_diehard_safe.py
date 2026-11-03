import cv2, numpy as np
KNEE,KEEP=25,0.2   # red-dominance soft knee: keeps full colour, compresses only warm skin highlights (max dom < 40)
def safe(img):
    b,g,r=[c.astype(np.float32) for c in cv2.split(img)]
    d=r-(g+b)/2; d2=np.minimum(np.where(d>KNEE,KNEE+(d-KNEE)*KEEP,d),36); r=r-(d-d2)
    return cv2.merge([np.clip(c,0,255).astype(np.uint8) for c in (b,g,r)])
