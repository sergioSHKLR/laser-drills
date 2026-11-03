"""Generate printable targets (PDF + PNG previews) from targets.json + drills.json.
One spec per target drives both the PDF artwork and the app's scoring zones."""
import json, math, os, sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
DOC=json.load(open('targets.json')); TPL=DOC['template']; PAL=TPL['palette']
DRILLS={d['id']:d for d in json.load(open('drills.json'))}; DRILLS['free']={'name':'Free fire'}
PW,PH=TPL['page']['w'],TPL['page']['h']; M=TPL['margin']; MS=TPL['marker']['size']; Q=TPL['marker']['quiet']
K=72
WORDS=[[1,0,0,0,0],[1,0,1,1,1],[0,1,0,0,1],[0,1,1,1,0]]
def marker_bits(mid):
    b=[[0]*7 for _ in range(7)]
    for i in range(5):
        w=WORDS[(mid>>(2*(4-i)))&3]
        for j in range(5): b[i+1][j+1]=w[j]
    return b
def marker_pos():  # TL,TR,BR,BL top-left corners (inches, y down)
    return [(M,M),(PW-M-MS,M),(PW-M-MS,PH-M-MS),(M,PH-M-MS)]
def lum(h):
    c=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    c=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def check_palette():
    rep=[]
    for k,v in PAL.items():
        r,g,b=[int(v[i:i+2],16) for i in (1,3,5)]
        reddom=r-(g+b)/2
        assert reddom<20, f'{k} too red for laser detection ({reddom})'
        rep.append(f'{k:12s} {v} L={lum(v):.2f} red-dominance={reddom:+.0f}')
    tiers=sorted([lum(PAL[t]) for t in ('tier5','tier3','tier2','tier1')])
    assert all(b-a>=0.12 for a,b in zip(tiers,tiers[1:])), 'tier luminance steps too small for grayscale'
    return rep
class Pdf:
    def __init__(s,path): s.c=canvas.Canvas(path,pagesize=letter)
    def P(s,x,y): return x*K,(PH-y)*K
    def color(s,h,stroke=False):
        (s.c.setStrokeColor if stroke else s.c.setFillColor)(HexColor(h) if isinstance(h,str) else h)
    def path(s,z,grow=0):
        p=s.c.beginPath(); sh=z['shape']
        if sh=='circle': p.circle(*s.P(z['cx'],z['cy']),(z['r']+grow)*K)
        elif sh=='ellipse':
            x,y=s.P(z['cx']-z['rx'],z['cy']+z['ry']); p.ellipse(x,y,2*z['rx']*K,2*z['ry']*K)
        elif sh=='rect':
            x,y=s.P(z['x'],z['y']+z['h']); p.rect(x,y,z['w']*K,z['h']*K)
        elif sh=='poly':
            pts=z['pts']; p.moveTo(*s.P(*pts[0]))
            for q in pts[1:]: p.lineTo(*s.P(*q))
            p.close()
        return p
    def hatch(s,z,ink,gap=0.12,width=1.2):
        c=s.c; c.saveState(); c.clipPath(s.path(z),stroke=0,fill=0)
        c.setStrokeColor(HexColor(ink)); c.setLineWidth(width)
        for i in range(-120,120):
            x0=i*gap; c.line(*s.P(x0,0),*s.P(x0+PH,PH))
        c.restoreState()
def zone_center(z):
    if 'cx' in z: return z['cx'],z['cy']
    if z['shape']=='rect': return z['x']+z['w']/2,z['y']+z['h']/2
    xs=[p[0] for p in z['pts']]; ys=[p[1] for p in z['pts']]; return sum(xs)/len(xs),sum(ys)/len(ys)
BASE=dict(TPL)
def draw_target(key,t,path):
    global PW,PH
    TPL.clear(); TPL.update(BASE); TPL.update(t.get('layout',{})); PW,PH=TPL['page']['w'],TPL['page']['h']
    d=Pdf(path); c=d.c; c.setPageSize((PW*K,PH*K))
    # markers
    for (x,y),mid in zip(marker_pos(),t['markerIds']):
        bits=marker_bits(mid); s=MS/7; c.setFillColor(black)
        for i in range(7):
            for j in range(7):
                if not bits[i][j]:
                    px,py=d.P(x+j*s,y+(i+1)*s); c.rect(px,py,s*K+0.4,s*K+0.4,stroke=0,fill=1)
        c.setFont('Helvetica',5.5); c.setFillColor(HexColor('#777777'))
        lx,ly=d.P(x,y+MS+0.12) if y<PH/2 else d.P(x,y-0.05); c.drawString(lx,ly,f'ID {mid}')
    # scan field edge
    f=TPL['field']; c.setDash(3,3); d.color(PAL['fieldEdge'],True); c.setLineWidth(0.6)
    x,y=d.P(f['x'],f['y']+f['h']); c.rect(x,y,f['w']*K,f['h']*K,stroke=1,fill=0); c.setDash()
    c.setFont('Helvetica',5.5); c.setFillColor(HexColor('#777777'))
    c.drawString(*d.P(f['x']+0.05,f['y']-0.04),'SCAN FIELD - laser hits outside this line are ignored')
    # raster character art (GenerateImage illustrations, laser-safe recolored by tools_diehard.py)
    for a in t.get('art',[]):
        from PIL import Image; from reportlab.lib.utils import ImageReader; import numpy as np
        im=Image.open(a['src']).convert('RGB')
        if a.get('crop'): im=im.crop(tuple(a['crop']))
        arr=np.asarray(im).astype(int); rd=(arr[...,0]-(arr[...,1]+arr[...,2])/2).max()
        assert rd<20, f"{a['src']} too red for laser detection ({rd})"
        x,y=d.P(a['x'],a['y']+a['h']); c.drawImage(ImageReader(im),x,y,a['w']*K,a['h']*K)
    # zones
    for z in t['zones']:
        if z.get('subtle'):
            c.setDash(2,2); c.setLineWidth(0.6); d.color(PAL['subtle'],True); c.drawPath(d.path(z),stroke=1,fill=0); c.setDash(); continue
        if z['kind']=='noshoot' and z.get('art'):
            d.hatch(z,PAL['hatchArt'],gap=0.14,width=0.7); c.setLineJoin(1); c.setLineWidth(1.6); d.color(PAL['noshootInk'],True); c.drawPath(d.path(z),stroke=1,fill=0)
            cx,cy=zone_center(z); bx,by=d.P(cx,cy); txt='HOSTAGE +5s'; c.setFont('Helvetica-Bold',9); tw=c.stringWidth(txt,'Helvetica-Bold',9)+8
            c.setFillColor(white); c.rect(bx-tw/2,by-5,tw,15,stroke=0,fill=1); c.setFillColor(black); c.drawCentredString(bx,by,txt); continue
        c.setLineWidth(1.4); d.color(PAL['outline'],True)
        if z['kind']=='decor' and z.get('line'):
            zl=t['zones']; i0=next(i for i,q in enumerate(zl) if q is z)
            if i0>0 and zl[i0-1]['kind']=='decor' and zl[i0-1].get('line'): continue
            outl=[]
            for q in zl[i0:]:
                if q['kind']=='decor' and q.get('line'): outl.append(q)
                else: break
            c.setLineJoin(1); c.setLineWidth(3.2); d.color(PAL[z['line']],True)
            for q in outl: c.drawPath(d.path(q),stroke=1,fill=0)
            for q in outl: d.color(PAL[q['fill']]); c.drawPath(d.path(q),stroke=0,fill=1)
            continue
        if z['kind']=='decor':
            d.color(PAL[z['fill']]); c.drawPath(d.path(z),stroke=0,fill=1); continue
        if z['kind']=='noshoot' and z.get('plain'):
            d.color(PAL[z['tier']]); d.color(PAL[z.get('line','outline')],True); c.drawPath(d.path(z),stroke=1,fill=1); continue
        if z['kind']=='noshoot':
            d.color(PAL['noshoot']); c.drawPath(d.path(z),stroke=0,fill=1)
            d.hatch(z,PAL['noshootInk']); d.color(PAL['noshootInk'],True); c.setLineWidth(2); c.drawPath(d.path(z),stroke=1,fill=0)
            cx,cy=z.get('label') or zone_center(z); c.setFont('Helvetica-Bold',9); bx,by=d.P(cx,cy)
            txt=('NON-THREAT +5s' if t.get('scoring')=='idpa' else f"{z['name'].replace('NS','NO SHOOT')} {z['penalty']}")
            tw=c.stringWidth(txt,'Helvetica-Bold',9)+8
            c.setFillColor(white); c.rect(bx-tw/2,by-5,tw,15,stroke=0,fill=1); c.setFillColor(black)
            c.drawCentredString(bx,by,txt)
            continue
        if z['kind']=='hardcover':
            c.setFillColor(black); c.drawPath(d.path(z),stroke=0,fill=1)
            lx,ly=d.P(*(z.get('label') or zone_center(z))); c.setFillColor(white); c.setFont('Helvetica-Bold',9)
            c.drawCentredString(lx,ly+3,'HARD'); c.drawCentredString(lx,ly-8,'COVER'); continue
        d.color(PAL[z['tier']]); d.color(PAL[z.get('line','outline')],True)
        if z.get('dashed'):
            c.setDash(5,3); c.drawPath(d.path(z),stroke=1,fill=1); c.setDash()
        else: c.drawPath(d.path(z),stroke=1,fill=1)
    for tx in t.get('texts',[]):
        c.setFont('Helvetica-Bold',tx['size']); tw=c.stringWidth(tx['text'],'Helvetica-Bold',tx['size']); x,y=d.P(tx['x'],tx['y'])
        c.setFillColor(white); c.rect(x-tw/2-2,y-2,tw+4,tx['size']+2,stroke=0,fill=1); c.setFillColor(black); c.drawCentredString(x,y,tx['text'])
    # zone labels (after fills so they stay on top)
    for z in t['zones']:
        if (z['kind']!='score' and not z.get('plain')) or z.get('subtle'): continue
        cx,cy=zone_center(z); dark=lum(PAL[z['tier']])<0.3
        if t.get('scoring')=='idpa':
            if 'label' in z: cx,cy=z['label']
            c.setFillColor(white if dark else black); c.setFont('Helvetica-Bold',t.get('labelSize',8 if key=='idpa-multi' else (9 if key=='idpa-nt-pair' else 10)))
            x,y=d.P(cx,cy); c.drawCentredString(x,y-3,z['name'].split(' ')[-1]); continue
        c.setFillColor(white if dark else black); c.setFont('Helvetica-Bold',9)
        if z['shape']=='circle' and not z.get('dashed') and z['r']>1.0: cy=cy-z['r']+0.22
        if z.get('dashed'): cy=cy+z['r']-0.2
        if 'label' in z: cx,cy=z['label']
        elif key in('silhouette','hostage') and z['shape']=='poly': cy=cy+ (1.9 if z['name']=='D' else 1.2)
        lab=z['name'] if key=='five-dot' else f"{z['name']} {z['score']}"
        if key=='five-dot': c.setFont('Helvetica-Bold',22)
        x,y=d.P(cx,cy); c.drawCentredString(x,y-3,lab)
    # header band
    hx=M+MS+Q; hw=PW-2*hx; c.setFillColor(black)
    c.setFont('Helvetica-Bold',17); c.drawString(*d.P(hx,M+0.3),t['name'])
    c.setFont('Helvetica',8.5)
    c.drawString(*d.P(hx,M+0.55),f"{t['code']}  ·  key '{key}'  ·  markers {t['markerIds'][0]}-{t['markerIds'][-1]}")
    c.drawString(*d.P(hx,M+0.78),f"Recommended distance: {t['distance']}")
    dn=[DRILLS[x]['name'] for x in t['drills'] if x in DRILLS]
    c.drawString(*d.P(hx,M+1.0),'Pairs with: '+'; '.join(dn)[:(95 if PW>9 else 70)])
    c.setFont('Helvetica-Bold',7); c.drawRightString(*d.P(hx+hw,M+0.3),'LASER DRILLS')
    # footer band: instructions | legend
    fy=PH-M-MS; c.setFont('Helvetica-Bold',8); c.drawString(*d.P(hx,fy+0.12),'HOW TO')
    c.setFont('Helvetica',7.2)
    for i,line in enumerate(t['instructions'][:5]): c.drawString(*d.P(hx,fy+0.3+i*0.16),f'{i+1}. {line}')
    c.setFont('Helvetica-Bold',7); c.drawString(*d.P(hx,M+1.2),'VOICE: "start"/"standby" · "stop" · "reset" · "next" · "repeat" · "score"  (or tap / BT media button)')
    lx=hx+2.75; c.setFont('Helvetica-Bold',8); c.drawString(*d.P(lx,fy+0.12),'SCORING MAP')
    items=[];seen=set()
    for z in sorted([z for z in t['zones'] if z['kind']=='score'],key=lambda z:-z['score']):
        k=(z['tier'],z['score'])
        if k in seen: continue
        seen.add(k); items.append((PAL[z['tier']],f"{'Dot' if key=='five-dot' else 'Zone'} {z['name'] if key!='clays' else ('clay' if z['score']==5 else 'pattern')}: {z['score']:+d} pts" if key!='five-dot' else f"Dots 1-5 in order: +5 each",None))
    if t.get('scoring')=='idpa':
        tz={z['name'].split(' ')[-1]:z['tier'] for z in t['zones'] if z['kind'] in('score','noshoot') and 'tier' in z}
        items=[]
        if any(z['kind']=='score' for z in t['zones']):
            items=[(PAL[tz['-0']],'Zone -0 (circles): 0 points down',None),(PAL[tz['-1']],'Zone -1 (head box, band): +1 s',None),(PAL[tz['-3']],'Zone -3 (outer): +3 s',None)]
        if any(z['kind']=='hardcover' for z in t['zones']): items.append(('#000000','Hard cover: no hit (miss = 5 PD)',None))
        if any(z['kind']=='noshoot' for z in t['zones']): items.append((PAL['kraft'],'Non-threat (open hands): +5 s per hit',None))
        if not any(z['kind']=='score' for z in t['zones']): items.append(('#FFFFFF','Do not shoot - any hit is a penalty',None))
    elif any(z['kind']=='noshoot' for z in t['zones']):
        p=[z for z in t['zones'] if z['kind']=='noshoot'][0]['penalty']; items.append((PAL['noshoot'],f'No-shoot (hatched): {p} pts','hatch'))
    items.append(('#FFFFFF','Outside zones: miss, 0 pts',None))
    if t.get('legend'): items=[(PAL.get(col,col),txt,'hatch' if col=='noshoot' else ('dash' if col=='tier1' else None)) for col,txt in t['legend']]
    c.setFont('Helvetica',7.2)
    for i,(col,txt,kind) in enumerate(items[:6]):
        yy=fy+0.2+i*0.14; x,y=d.P(lx,yy+0.1); c.setFillColor(HexColor(col)); c.setStrokeColor(black); c.setLineWidth(0.5)
        c.rect(x,y,0.22*K,0.11*K,stroke=1,fill=1)
        if kind=='dash': c.setFillColor(white); c.rect(x,y,0.22*K,0.11*K,stroke=0,fill=1); c.setDash(2,2); c.setStrokeColor(HexColor(PAL['subtle'])); c.rect(x,y,0.22*K,0.11*K,stroke=1,fill=0); c.setDash()
        if kind=='hatch':
            c.setStrokeColor(black)
            for q in range(3): c.line(x+q*5,y,x+q*5+4,y+0.11*K)
        c.setFillColor(black); c.drawString(x+0.3*K,y+1,txt)
    PAPER={(8.5,11):'US Letter portrait',(11,8.5):'US Letter LANDSCAPE',(17,11):'Tabloid 11x17 LANDSCAPE'}[(PW,PH)]
    c.setFont('Helvetica',6); c.setFillColor(HexColor('#555555'))
    c.drawCentredString(*d.P(PW/2,PH-M-0.02),f'Print at 100% (Actual size), {PAPER}. Keep the white quiet zone around each corner marker clear. Dry fire only: verify the firearm is unloaded.')
    c.showPage(); c.save()
if __name__=='__main__':
    os.makedirs('targets',exist_ok=True)
    print('\n'.join(check_palette()))
    for key,t in DOC['targets'].items():
        p=f'targets/{key}-letter.pdf'; draw_target(key,t,p); print('wrote',p)
    li=lambda k,t:f"<li><a href='{k}-letter.pdf'><img src='{k}-letter.png' width=160><br>{t['code']} {t['name']}</a> — {t['distance']}</li>"
    rows=''.join(li(k,t) for k,t in DOC['targets'].items() if t.get('set')!='diehard')
    dh=''.join(li(k,t) for k,t in DOC['targets'].items() if t.get('set')=='diehard')
    UL="<ul style='list-style:none;display:flex;flex-wrap:wrap;gap:16px;padding:0'>"
    open('targets/index.html','w').write(f"<!doctype html><meta name=viewport content='width=device-width'><title>Laser Drills targets</title><body style='font:15px system-ui;background:#111;color:#eee'><h2>Printable targets</h2><p>Print at 100% / Actual size. Paper is printed in each sheet footer (US Letter unless marked LANDSCAPE / Tabloid 11x17).</p>{UL}{rows}</ul><h2 id=diehard>Die Hard (Set 1: Nakatomi Plaza)</h2><p>Illustrated characters with faint anatomy-based -0/-1/-3 outlines. Hatched white = hostage, black = hard cover. Fan-made training targets; characters are drawn, not actor likenesses.</p>{UL}{dh}</ul><p><a href='../' style='color:#8ab4f8'>Back to app</a></p>".replace('<a ',"<a style='color:#8ab4f8' "))
    import subprocess
    for k in DOC['targets']: subprocess.run(['pdftoppm','-r','50','-png','-singlefile',f'targets/{k}-letter.pdf',f'targets/{k}-letter'],check=True)
