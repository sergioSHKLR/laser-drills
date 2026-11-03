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
MASKCOL={0:'#1F3A5F',-1:'#4F6F94',-3:'#9DB3C9',5:'#1F3A5F',4:'#34506E',3:'#6F8BA8',2:'#9DB3C9',1:'#C9D6E2'}
RULECOL={'hit':'#1F4E9A','nohit':'#FFFFFF','cover':'#000000','twohit':'#2E8B57','conditional':'#7B4FA0','headonly':'#00A3B4','penalty':'#8C8C8C'}
RULETXT=[('hit','Hit: scores (shade = value; labels show pts)'),('nohit','No-hit / no-shoot (hatched): penalty'),('cover','Hard cover: blocks, no hit'),('twohit','Two-hit: counts on 2nd hit'),('conditional','Conditional: only after required hits elsewhere'),('headonly','Head-only / e-vest: only this counts'),('penalty','Penalty / backstop (bystander)')]
HITSHADE={0:'#1F4E9A',5:'#1F4E9A',4:'#2D5FAE',-1:'#4F7BC0',3:'#4F7BC0',2:'#7FA0D3',-3:'#7FA0D3',1:'#AFC4E6'}
for _k,_v in list(RULECOL.items())+list(HITSHADE.items()):
    _r,_g,_b=[int(_v[i:i+2],16) for i in (1,3,5)]; assert _r-(_g+_b)/2<20, f'mask colour {_v} too red'
def rule_of(z):
    if z.get('rule'): return z['rule']
    k=z['kind']
    if k=='noshoot': return 'nohit'
    if k=='hardcover': return 'cover'
    if k=='bystander': return 'penalty'
    if z.get('headOnly'): return 'headonly'
    if z.get('after'): return 'conditional'
    if z.get('needs',1)>1: return 'twohit'
    return 'hit'
def draw_mask(d,t):
    """Scoring map only: zones filled by type/value, no images. Drawn back-to-front (first listed = on top)."""
    c=d.c; zs=t['zones']
    RK={'bystander':0,'score':1,'hardcover':2,'noshoot':3}
    for z in sorted(zs,key=lambda z:(RK.get(z['kind'],0),z.get('z',0),z.get('score',0))):
        k=z['kind']
        if k=='decor': continue
        c.setLineWidth(0.8); c.setStrokeColor(black)
        ru=rule_of(z); col=HITSHADE.get(z.get('score'),RULECOL['hit']) if ru=='hit' else RULECOL[ru]
        d.color(col); c.drawPath(d.path(z),stroke=1,fill=1)
        if k=='noshoot': d.hatch(z,PAL['noshootInk'],gap=0.1,width=0.8); c.drawPath(d.path(z),stroke=1,fill=0)
    seen=set(); placed=[]
    for z in zs:
        k=z['kind']
        if k=='decor': continue
        if k=='score': lab=f"{z['name']} {z['score']:+d}" if t.get('scoring')!='idpa' else z['name']
        elif k=='noshoot': lab=f"NO-SHOOT {z.get('penalty','')}".strip()+(' FRIENDLY' if z.get('friendly') else '')
        elif k=='hardcover': lab='HARD COVER'
        elif k=='bystander': lab='BYSTANDER'
        else: lab=z.get('name',k)
        cx,cy=z.get('label') or zone_center(z)
        if not z.get('label') and z['shape']=='circle' and z['r']>0.6: cy=cy-z['r']+0.15
        if (lab,round(cx,1),round(cy,1)) in seen: continue
        seen.add((lab,round(cx,1),round(cy,1)))
        if z['shape'] in('poly','rect') and not z.get('label') and z['kind']=='score' and z.get('score',9)<0:
            ys=[p[1] for p in z['pts']] if z['shape']=='poly' else [z['y']]; xs=[p[0] for p in z['pts'] if p[1]<min(ys)+0.6] if z['shape']=='poly' else [z['x'],z['x']+z['w']]
            cy=min(ys)+0.6 if z['score']==-1 else (min(ys)+1.0 if z['score']==-3 else cy); cx=sum(xs)/len(xs) if z['score']!=-3 else cx
        if z['shape']=='ellipse' and z.get('ry',0)>0.45 and not z.get('label'): cy=cy-z['ry']+0.14   # big ellipse: label at its top edge
        for _ in range(8):   # nudge away from labels already placed
            if any(abs(cx-px)<0.45 and abs(cy-py)<0.13 for px,py in placed): cy+=0.14
            else: break
        placed.append((cx,cy))
        dark=(k=='hardcover') or (rule_of(z)!='nohit' and lum(HITSHADE.get(z.get('score'),RULECOL[rule_of(z)]) if rule_of(z)=='hit' else RULECOL[rule_of(z)])<0.3)
        sz=6 if (z.get('rx',z.get('r',1))<0.35) else 7
        c.setFont('Helvetica-Bold',sz); tw=c.stringWidth(lab,'Helvetica-Bold',sz); x,y=d.P(cx,cy)
        if k=='noshoot': c.setFillColor(white); c.rect(x-tw/2-1,y-2.5,tw+2,sz+1.5,stroke=0,fill=1); dark=False
        c.setFillColor(white if dark else black); c.drawCentredString(x,y-2,lab)
def keepouts():   # marker + quiet zone rects (inches, y down)
    return [(x-Q,y-Q,x+MS+Q,y+MS+Q) for x,y in marker_pos()]
class Rec:
    """Wrap canvas text calls: record every text bbox (inches) so we can assert none hits a marker quiet zone."""
    def __init__(s,c): s.c=c; s.boxes=[]
    def _add(s,x,y,txt,align):
        f,sz=s.c._fontname,s.c._fontsize; w=s.c.stringWidth(txt,f,sz)
        x0={'l':x,'c':x-w/2,'r':x-w}[align]
        s.boxes.append(((x0/K),PH-(y+sz*0.8)/K,(x0+w)/K,PH-(y-sz*0.22)/K,txt))
    def install(s):
        c=s.c; o=(c.drawString,c.drawCentredString,c.drawRightString)
        c.drawString=lambda x,y,t,*a,**k:(s._add(x,y,t,'l'),o[0](x,y,t,*a,**k))
        c.drawCentredString=lambda x,y,t,*a,**k:(s._add(x,y,t,'c'),o[1](x,y,t,*a,**k))
        c.drawRightString=lambda x,y,t,*a,**k:(s._add(x,y,t,'r'),o[2](x,y,t,*a,**k))
def hit(a,b): return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
def fitfont(c,txt,font,size,maxw,minsize=4.8):
    """Shrink font (then ellipsize) so txt fits maxw inches."""
    while size>minsize and c.stringWidth(txt,font,size)>maxw*K: size-=0.2
    while c.stringWidth(txt,font,size)>maxw*K and len(txt)>4: txt=txt[:-2].rstrip()+'…'
    c.setFont(font,size); return txt
def draw_target(key,t,path,maskmode=False):
    global PW,PH
    TPL.clear(); TPL.update(BASE); TPL.update(t.get('layout',{})); PW,PH=TPL['page']['w'],TPL['page']['h']
    d=Pdf(path); c=d.c; c.setPageSize((PW*K,PH*K)); rec=Rec(c); rec.install(); artbox=[]
    # markers
    for (x,y),mid in zip(marker_pos(),t['markerIds']):
        bits=marker_bits(mid); s=MS/7; c.setFillColor(black)
        for i in range(7):
            for j in range(7):
                if not bits[i][j]:
                    px,py=d.P(x+j*s,y+(i+1)*s); c.rect(px,py,s*K+0.4,s*K+0.4,stroke=0,fill=1)
    # scan field edge
    f=TPL['field']
    if not t.get('art') or maskmode:
     c.setDash(3,3); d.color(PAL['fieldEdge'],True); c.setLineWidth(0.6)
     x,y=d.P(f['x'],f['y']+f['h']); c.rect(x,y,f['w']*K,f['h']*K,stroke=1,fill=0); c.setDash()
     c.setFont('Helvetica',5.5); c.setFillColor(HexColor('#777777'))
     c.drawString(*d.P(max(f['x']+0.05,M+MS+Q+0.03),f['y']-0.04),'SCAN FIELD - laser hits outside this line are ignored')
    # raster character art (GenerateImage illustrations, laser-safe recolored by tools_diehard.py)
    for a in ([] if maskmode else t.get('art',[])):
        from PIL import Image; from reportlab.lib.utils import ImageReader; import numpy as np
        im=Image.open(a['src']).convert('RGB')
        if a.get('crop'): im=im.crop(tuple(a['crop']))
        arr=np.asarray(im).astype(int); rd=(arr[...,0]-(arr[...,1]+arr[...,2])/2).max()
        assert rd<40 or a.get('warm'), f"{a['src']} too red for laser detection ({rd})"
        artbox.append((a['x'],a['y'],a['x']+a['w'],a['y']+a['h'],a['src'])); x,y=d.P(a['x'],a['y']+a['h']); c.drawImage(ImageReader(im),x,y,a['w']*K,a['h']*K)
    # zones
    if maskmode: draw_mask(d,t)
    for z in ([] if maskmode else t['zones']):
        if z.get('subtle'): continue   # art sheets: clean illustration, zones live in targets.json + the -mask sheet
        if z['kind'] in ('bystander',) or (z['kind'] in ('noshoot','score') and z.get('art')): continue   # unmarked on the art: shooter must discriminate
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
        if z['kind']=='hardcover' and z.get('art'):   # rendered cover object in the art: faint outline only
            continue
        if z['kind']=='hardcover':
            c.setFillColor(black); c.drawPath(d.path(z),stroke=0,fill=1)
            lx,ly=d.P(*(z.get('label') or zone_center(z))); c.setFillColor(white); c.setFont('Helvetica-Bold',9)
            c.drawCentredString(lx,ly+3,'HARD'); c.drawCentredString(lx,ly-8,'COVER'); continue
        d.color(PAL[z['tier']]); d.color(PAL[z.get('line','outline')],True)
        if z.get('dashed'):
            c.setDash(5,3); c.drawPath(d.path(z),stroke=1,fill=1); c.setDash()
        else: c.drawPath(d.path(z),stroke=1,fill=1)
    for tx in ([] if maskmode else t.get('texts',[])):
        c.setFont('Helvetica-Bold',tx['size']); tw=c.stringWidth(tx['text'],'Helvetica-Bold',tx['size']); x,y=d.P(tx['x'],tx['y'])
        c.setFillColor(white); c.rect(x-tw/2-2,y-2,tw+4,tx['size']+2,stroke=0,fill=1); c.setFillColor(black); c.drawCentredString(x,y,tx['text'])
    # zone labels (after fills so they stay on top)
    for z in ([] if maskmode else t['zones']):
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
    hx=M+MS+Q+0.03; hw=PW-2*hx; c.setFillColor(black)
    c.drawString(*d.P(hx,M+0.3),fitfont(c,t['name']+(' - SCORING MASK' if maskmode else ''),'Helvetica-Bold',17,hw-1.0))
    c.drawString(*d.P(hx,M+0.55),fitfont(c,f"{t['code']}  ·  key '{key}'  ·  markers {t['markerIds'][0]}-{t['markerIds'][-1]}",'Helvetica',8.5,hw))
    c.drawString(*d.P(hx,M+0.78),fitfont(c,f"Recommended distance: {t['distance']}",'Helvetica',8.5,hw))
    dn=[DRILLS[x]['name'] for x in t['drills'] if x in DRILLS]
    if dn: c.drawString(*d.P(hx,M+1.0),fitfont(c,'Pairs with: '+'; '.join(dn),'Helvetica',8.5,hw))
    c.setFont('Helvetica-Bold',7); c.drawRightString(*d.P(hx+hw-0.03,M+0.3),'LASER DRILLS')
    # footer band: instructions | legend
    fy=PH-M-MS; c.setFont('Helvetica-Bold',8); c.drawString(*d.P(hx,fy+0.12),'HOW TO')
    c.setFont('Helvetica',7.2)
    for i,line in enumerate(t['instructions'][:5]): c.drawString(*d.P(hx,fy+0.3+i*0.16),fitfont(c,f'{i+1}. {line}','Helvetica',7.2,2.65))
    vt='VOICE: "start"/"standby" · "stop" · "reset" · "next" · "repeat" · "score"  (or tap / BT media button)'; c.drawString(*d.P(hx,M+1.2),fitfont(c,vt,'Helvetica-Bold',7,hw))
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
    if maskmode: items=[(RULECOL[r],txt,'hatch' if r=='nohit' else None) for r,txt in RULETXT]
    c.setFont('Helvetica',6.6 if maskmode else 7.2)
    for i,(col,txt,kind) in enumerate(items[:7 if maskmode else 6]):
        yy=fy+0.2+i*(0.12 if maskmode else 0.14); x,y=d.P(lx,yy+0.1); c.setFillColor(HexColor(col)); c.setStrokeColor(black); c.setLineWidth(0.5)
        r=0.055*K; cx,cy=x+0.11*K,y+0.055*K
        if kind=='dash': c.setFillColor(white); c.circle(cx,cy,r,stroke=0,fill=1); c.setDash(1.5,1.5); c.setStrokeColor(HexColor(PAL['subtle'])); c.circle(cx,cy,r,stroke=1,fill=0); c.setDash()
        else: c.circle(cx,cy,r,stroke=1,fill=1)
        if kind=='hatch':
            c.saveState(); p=c.beginPath(); p.circle(cx,cy,r); c.clipPath(p,stroke=0,fill=0); c.setStrokeColor(black)
            for q in range(-2,4): c.line(cx-r+q*3,cy-r,cx-r+q*3+2*r,cy+r)
            c.restoreState(); c.circle(cx,cy,r,stroke=1,fill=0)
        c.setFillColor(black); c.drawString(x+0.3*K,y+1,fitfont(c,txt,'Helvetica',7.2,PW-M-MS-Q-0.05-(lx+0.3)))
    PAPER={(8.5,11):'US Letter portrait',(11,8.5):'US Letter LANDSCAPE',(17,11):'Tabloid 11x17 LANDSCAPE'}[(PW,PH)]
    c.setFillColor(HexColor('#555555'))
    ft=f'Print at 100% (Actual size), {PAPER}. Keep the white quiet zone around each corner marker clear. Know your target and what is beyond it. Dry fire only: verify unloaded.'
    c.drawCentredString(*d.P(PW/2,PH-M-0.02),fitfont(c,ft,'Helvetica',6,hw,4.0))
    bad=[(b[4],k) for b in rec.boxes+artbox for k in keepouts() if hit(b,k)]
    assert not bad, f'{key}: text/art overlaps marker quiet zone: {bad[:3]}'
    c.showPage(); c.save()
if __name__=='__main__':
    os.makedirs('targets',exist_ok=True)
    print('\n'.join(check_palette()))
    for key,t in DOC['targets'].items():
        p=f'targets/{key}-letter.pdf'; draw_target(key,t,p); print('wrote',p)
        draw_target(key,t,f'targets/{key}-mask.pdf',maskmode=True)
    li=lambda k,t:f"<li><a href='{k}-letter.pdf'><img src='{k}-letter.png' width=160><br>{t['code']} {t['name']}</a> — {t['distance']} · <a href='{k}-mask.pdf'>scoring mask</a> (<a href='{k}-mask.png'>png</a>)</li>"
    rows=''.join(li(k,t) for k,t in DOC['targets'].items() if t.get('set')!='diehard')
    dh=''.join(li(k,t) for k,t in DOC['targets'].items() if t.get('set')=='diehard')
    UL="<ul style='list-style:none;display:flex;flex-wrap:wrap;gap:16px;padding:0'>"
    open('targets/index.html','w').write(f"<!doctype html><meta name=viewport content='width=device-width'><title>Laser Drills targets</title><body style='font:15px system-ui;background:#111;color:#eee'><h1>Printable targets</h1><p>Print at 100% / Actual size. Paper is printed in each sheet footer (US Letter unless marked LANDSCAPE / Tabloid 11x17).</p><h2 id=training>Self-Defense Training</h2><p>Bullseye, IDPA, hostage, hard cover and shoot/don't-shoot sheets.</p>{UL}{rows}</ul><h2 id=fun>Fun</h2><h3 id=diehard>Die Hard (Set 1: Nakatomi Plaza)</h3><p>Full-colour illustrated characters with faint anatomy-based -0/-1/-3 outlines. Hatched = hostage; rendered desk/rail/pillar/cabinet = hard cover. Fan-made training targets; characters are drawn, not actor likenesses.</p>{UL}{dh}</ul><p><a href='../' style='color:#8ab4f8'>Back to app</a></p>".replace('<a ',"<a style='color:#8ab4f8' "))
    import subprocess
    for k in DOC['targets']: subprocess.run(['pdftoppm','-r','50','-png','-singlefile',f'targets/{k}-letter.pdf',f'targets/{k}-letter'],check=True); subprocess.run(['pdftoppm','-r','50','-png','-singlefile',f'targets/{k}-mask.pdf',f'targets/{k}-mask'],check=True)
    # blank mask template (letter portrait + tabloid landscape): markers, quiet zones, scan field, rule colour legend
    for suf,lay in (('letter',{}),('tabloid',{'page':{'w':17,'h':11},'field':{'x':0.4,'y':1.85,'w':16.2,'h':7.3}})):
        tt=dict(name='Blank template',code='LD-MT',markerIds=[200,201,202,203],distance='any',drills=[],zones=[],layout=lay,
                instructions=['Draw zones inside the dashed scan field only.','Fill each zone with its rule colour (legend).','Keep markers + white quiet zones clear.','Same colours as every -mask sheet and the Zone Editor.'])
        p=f'targets/mask-template-{suf}'; draw_target('mask-template',tt,p+'.pdf',maskmode=True)
        subprocess.run(['pdftoppm','-r','100','-png','-singlefile',p+'.pdf',p],check=True)
        subprocess.run(['pdftocairo','-svg',p+'.pdf',p+'.svg'],check=True)
    h=open('targets/index.html').read()
    h=h.replace("<h2 id=training>","<p><b>Blank scoring mask template</b> (rule-colour legend): Letter <a style='color:#8ab4f8' href='mask-template-letter.pdf'>PDF</a> · <a style='color:#8ab4f8' href='mask-template-letter.png'>PNG</a> · <a style='color:#8ab4f8' href='mask-template-letter.svg'>SVG</a> | Tabloid 11x17 landscape <a style='color:#8ab4f8' href='mask-template-tabloid.pdf'>PDF</a> · <a style='color:#8ab4f8' href='mask-template-tabloid.png'>PNG</a> · <a style='color:#8ab4f8' href='mask-template-tabloid.svg'>SVG</a></p><h2 id=training>",1)
    open('targets/index.html','w').write(h)
