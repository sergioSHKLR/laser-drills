# Generates target PDF, target PNG (for tests) and icons. Layout in inches, letter page.
import json, numpy as np, cv2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
T=json.load(open('targets.json'))['bullseye']
W,H=8.5,11.0
WORDS=[[1,0,0,0,0],[1,0,1,1,1],[0,1,0,0,1],[0,1,1,1,0]]
def marker(mid):  # 7x7, 1=white
    m=np.zeros((7,7),int)
    for i in range(5):
        w=WORDS[(mid>>(2*(4-i)))&3]
        for j in range(5): m[i+1][j+1]=w[j]
    return m
def png(dpi=100):
    img=np.full((int(H*dpi),int(W*dpi),3),255,np.uint8)
    P=lambda x,y:(int(round(x*dpi)),int(round(y*dpi)))
    for mk in T['markers']:
        m=marker(mk['id']); s=mk['size']/7
        for i in range(7):
            for j in range(7):
                if not m[i][j]: cv2.rectangle(img,P(mk['x']+j*s,mk['y']+i*s),P(mk['x']+(j+1)*s,mk['y']+(i+1)*s),(0,0,0),-1)
    for z in sorted(T['zones'],key=lambda z:-z['r']):
        cv2.circle(img,P(z['cx'],z['cy']),int(z['r']*dpi),(60,60,60) if z['score']==max(q['score'] for q in T['zones']) else (200,200,200),-1)
        cv2.circle(img,P(z['cx'],z['cy']),int(z['r']*dpi),(0,0,0),2)
    return img
def pdf(path):
    c=canvas.Canvas(path,pagesize=letter); k=72
    Y=lambda y:(H-y)*k
    for mk in T['markers']:
        m=marker(mk['id']); s=mk['size']/7
        c.setFillColorRGB(0,0,0)
        for i in range(7):
            for j in range(7):
                if not m[i][j]: c.rect((mk['x']+j*s)*k,Y(mk['y']+(i+1)*s),s*k+0.3,s*k+0.3,stroke=0,fill=1)
    for z in sorted(T['zones'],key=lambda z:-z['r']):
        g=0.25 if z['score']==5 else (0.8 if z['score']==3 else 0.92)
        c.setFillColorRGB(g,g,g); c.setStrokeColorRGB(0,0,0); c.setLineWidth(1.5)
        c.circle(z['cx']*k,Y(z['cy']),z['r']*k,stroke=1,fill=1)
        c.setFillColorRGB(1 if g<0.5 else 0,1 if g<0.5 else 0,1 if g<0.5 else 0); c.setFont('Helvetica-Bold',14)
        c.drawCentredString(z['cx']*k,Y(z['cy']-z['r'])-16 if z['score']!=5 else Y(z['cy'])-5,str(z['score']))
    c.setFillColorRGB(0,0,0); c.setFont('Helvetica',9)
    c.drawCentredString(W/2*k,0.35*k,'Laser Drills test target "bullseye" - print at 100% (no scaling) on US Letter. Keep all 4 corner markers flat and visible.')
    c.drawCentredString(W/2*k,(H-0.3)*k,'Rings: 5 / 3 / 1 points. Marker IDs 1-4 (js-aruco 5x5).')
    c.showPage(); c.save()
pdf('targets/bullseye-letter.pdf'); cv2.imwrite('test/target.png',png())
for s in (192,512):
    ic=np.full((s,s,3),(30,30,30),np.uint8)
    for r,col in ((0.45,(255,255,255)),(0.32,(30,30,30)),(0.18,(255,255,255)),(0.06,(40,40,230))):
        cv2.circle(ic,(s//2,s//2),int(r*s),col,-1)
    cv2.imwrite(f'icon-{s}.png',ic)
