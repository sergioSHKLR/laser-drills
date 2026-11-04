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
HITSHADE={10:'#1F4E9A',9:'#2D5FAE',8:'#4F7BC0',0:'#1F4E9A',5:'#1F4E9A',4:'#2D5FAE',-1:'#4F7BC0',3:'#4F7BC0',2:'#7FA0D3',-3:'#7FA0D3',1:'#AFC4E6'}
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
        ru=rule_of(z); col=z.get('shade') or (HITSHADE.get(z.get('score'),RULECOL['hit']) if ru=='hit' else RULECOL[ru])
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
        dark=(k=='hardcover') or (rule_of(z)!='nohit' and lum(z.get('shade') or (HITSHADE.get(z.get('score'),RULECOL[rule_of(z)]) if rule_of(z)=='hit' else RULECOL[rule_of(z)]))<0.3)
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
    if not (t.get('art') or t.get('lineart')) or maskmode:
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
    # vector line art (clean qualification silhouettes): black strokes only, no fills
    for a in ([] if maskmode else t.get('lineart',[])):
        c.setLineWidth(a.get('lw',1.1)); c.setStrokeColor(black); c.setLineJoin(1)
        if a['shape']=='poly' and a.get('open'):
            p=c.beginPath(); p.moveTo(*d.P(*a['pts'][0]))
            for q in a['pts'][1:]: p.lineTo(*d.P(*q))
            c.drawPath(p,stroke=1,fill=0)
        elif a.get('fill'): c.setFillColor(HexColor(a['fill'])); c.drawPath(d.path(a),stroke=1,fill=1)
        else: c.drawPath(d.path(a),stroke=1,fill=0)
        xs=[q[0] for q in a['pts']] if 'pts' in a else [a.get('cx',a.get('x',0))-a.get('rx',a.get('r',0)),a.get('cx',a.get('x',0))+a.get('rx',a.get('r',a.get('w',0)))]
        ys=[q[1] for q in a['pts']] if 'pts' in a else [a.get('cy',a.get('y',0))-a.get('ry',a.get('r',0)),a.get('cy',a.get('y',0))+a.get('ry',a.get('r',a.get('h',0)))]
        artbox.append((min(xs),min(ys),max(xs),max(ys),'lineart'))
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
            items=[(PAL[tz[k]],l,None) for k,l in (('-0','Zone -0 (circles): 0 points down'),('-1','Zone -1 (head box, band): +1 s'),('-3','Zone -3 (outer): +3 s')) if k in tz]
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
def target_meta(k,t):
    zs=t.get('zones',[]); kinds={z['kind'] for z in zs}; names=' '.join((z.get('name','')+' '+str(z.get('group',''))).lower() for z in zs)
    cat={'diehard':'themed','games':'fun'}.get(t.get('set'),'tactical')
    paper='tabloid' if t.get('layout',{}).get('page',{}).get('w',8.5)>=17 else 'letter'
    groups={z.get('group') for z in zs if z.get('group') and z['kind'] in('score','noshoot')}
    nopeople={'bullseye','five-dot','clays','carnival','battle','cards'}
    people='none' if k in nopeople or t.get('set')=='games' else ('multi' if len(groups)>1 or k in('crowd','crowd-tabloid','idpa-nt-pair','idpa-multi','idpa-all-tabloid','idpa-all-letter','hostage','dh-finale','dh-party','dh-lobby','dh-nakatomi') else 'single')
    f=set()
    if 'noshoot' in kinds: f.add('no-shoot')
    if 'hostage' in names or 'holly' in names or k=='hostage': f.add('hostage')
    if 'hardcover' in kinds: f.add('hard cover')
    if 'bystander' in kinds: f.add('backstop')
    if any(z.get('needs',1)>1 for z in zs): f.add('two-hit')
    if any(z.get('after') for z in zs): f.add('conditional')
    if any(z.get('headOnly') for z in zs): f.add('head-only')
    m=dict(category=cat,paper=paper,people=people,features=sorted(f),weapon='shotgun' if t.get('spread') or 'shotgun' in t.get('name','').lower() else 'pistol')
    m.update(t.get('metaOverride',{})); return m
def write_gallery(DOC):
    import json,html
    cards=[]
    for k,t in DOC['targets'].items():
        m=target_meta(k,t); t['meta']=m
        cards.append(dict(k=k,code=t['code'],name=t['name'],dist=t.get('distance',''),**m,text=' '.join([k,t['code'],t['name'],t.get('distance','')]+t.get('instructions',[])).lower()))
    json.dump({**DOC,'template':BASE},open('targets.json','w'),indent=1)   # TPL (=DOC['template']) is mutated per target
    data=json.dumps(cards)
    page=r"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Laser Drills targets</title>
<style>
body{font:15px system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:12px}a{color:#8ab4f8}h1{margin:.2em 0;font-size:1.4em}
.bar{background:#111;padding:6px 0 8px;z-index:2;border-bottom:1px solid #333}
#q{position:sticky;top:0;z-index:3;width:100%;box-sizing:border-box;padding:10px;font-size:16px;border-radius:8px;border:1px solid #444;background:#1c1c1c;color:#eee}
.row::-webkit-scrollbar{display:none}
.row{scrollbar-width:none;display:flex;gap:6px;overflow-x:auto;padding:6px 0;-webkit-overflow-scrolling:touch;align-items:center}.row b{font-size:12px;color:#999;min-width:64px}
.chip{flex:none;border:1px solid #555;background:#1c1c1c;color:#ddd;border-radius:16px;padding:7px 12px;font-size:14px;min-height:36px;cursor:pointer}
.chip.on{background:#1F4E9A;border-color:#8ab4f8;color:#fff}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-top:12px}
.card{background:#1b1b1b;border:1px solid #333;border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:8.5/11;object-fit:contain;background:#fff}.card .t{padding:8px;font-size:13px;flex:1}.card .t b{display:block;font-size:14px}
.tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}.tags span{font-size:11px;background:#2a2a2a;border-radius:8px;padding:2px 6px;color:#bbb}
.lk{display:flex;border-top:1px solid #333}.lk a{flex:1;text-align:center;padding:10px 0;text-decoration:none;font-size:13px;border-right:1px solid #333}.lk a:last-child{border:0}
.tpl{font-size:13px;color:#bbb}#n{color:#999;font-size:13px}
</style><body>
<h1>Printable targets</h1><p class=tpl>Print at 100% / Actual size (paper is in each sheet footer). Blank scoring mask template: Letter <a href='mask-template-letter.pdf'>PDF</a> · <a href='mask-template-letter.png'>PNG</a> · <a href='mask-template-letter.svg'>SVG</a> | Tabloid 17x11 <a href='mask-template-tabloid.pdf'>PDF</a> · <a href='mask-template-tabloid.png'>PNG</a> · <a href='mask-template-tabloid.svg'>SVG</a> · <a href='../'>Back to app</a></p>
<div class=bar><input id=q type=search placeholder='Search targets (name, code, character...)'><div id=f></div><div id=n></div></div>
<div id=grid></div>
<script>
const C=__DATA__;
const F=[['category','Category',[['themed','Themed (Die Hard)'],['tactical','Tactical (IDPA, hostage, crowd)'],['fun','Fun']]],
 ['paper','Paper',[['letter','Letter'],['tabloid','Tabloid 17x11']]],
 ['people','People',[['single','Single'],['multi','Multi'],['none','No people']]],
 ['features','Features',[['hostage','Hostage'],['no-shoot','No-shoot'],['hard cover','Hard cover'],['backstop','Backstop'],['two-hit','Two-hit'],['conditional','Conditional'],['head-only','Head-only']]],
 ['weapon','Weapon',[['pistol','Pistol'],['shotgun','Shotgun']]]];
const S={};F.forEach(([k])=>S[k]=new Set());
const fd=document.getElementById('f');
F.forEach(([k,l,o])=>{const r=document.createElement('div');r.className='row';r.innerHTML='<b>'+l+'</b>';o.forEach(([v,t])=>{const b=document.createElement('button');b.className='chip';b.textContent=t;b.onclick=()=>{S[k].has(v)?S[k].delete(v):S[k].add(v);b.classList.toggle('on');draw()};r.appendChild(b)});fd.appendChild(r)});
const esc=s=>s.replace(/[&<>']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;'}[c]));
function ok(c){const q=document.getElementById('q').value.trim().toLowerCase();if(q&&!q.split(/\s+/).every(w=>c.text.includes(w)))return false;
 for(const[k]of F){const s=S[k];if(!s.size)continue;if(k=='features'){if(![...s].every(v=>c.features.includes(v)))return false}else if(!s.has(c[k]))return false}return true}
function draw(){const L=C.filter(ok);document.getElementById('n').textContent=L.length+' of '+C.length+' targets';
 document.getElementById('grid').innerHTML=L.map(c=>`<div class=card><a href='${c.k}-letter.pdf'><img loading=lazy src='${c.k}-letter.png' alt=''></a><div class=t><b>${esc(c.name)}</b>${esc(c.code)} · ${esc(c.dist)}<div class=tags><span>${c.category}</span><span>${c.paper}</span><span>${c.people=="none"?"no people":c.people}</span><span>${c.weapon}</span>${c.features.map(f=>'<span>'+f+'</span>').join('')}</div></div><div class=lk><a href='${c.k}-letter.pdf'>Target PDF</a><a href='${c.k}-mask.pdf'>Mask PDF</a><a href='${c.k}-mask.png'>Mask PNG</a></div></div>`).join('')}
document.getElementById('q').oninput=draw;draw();
</script>"""
    open('targets/catalog.json','w').write(data)
    # Gallery moved into the app (Home tab); keep old URL working. PDFs/PNGs stay in targets/.
    open('targets/index.html','w').write("<!doctype html><meta charset=utf-8><title>Laser Drills targets</title><meta http-equiv=refresh content='0;url=../#home'><script>location.replace('../#home'+(location.search?'':''))</script><p>Moved: <a href='../#home'>target gallery in the app</a></p>")
if __name__=='__main__':
    os.makedirs('targets',exist_ok=True)
    print('\n'.join(check_palette()))
    for key,t in DOC['targets'].items():
        p=f'targets/{key}-letter.pdf'; draw_target(key,t,p); print('wrote',p)
        draw_target(key,t,f'targets/{key}-mask.pdf',maskmode=True)
    write_gallery(DOC)
    import subprocess
    for k in DOC['targets']: subprocess.run(['pdftoppm','-r','50','-png','-singlefile',f'targets/{k}-letter.pdf',f'targets/{k}-letter'],check=True); subprocess.run(['pdftoppm','-r','50','-png','-singlefile',f'targets/{k}-mask.pdf',f'targets/{k}-mask'],check=True)
    # blank mask template (letter portrait + tabloid landscape): markers, quiet zones, scan field, rule colour legend
    for suf,lay in (('letter',{}),('tabloid',{'page':{'w':17,'h':11},'field':{'x':0.4,'y':1.85,'w':16.2,'h':7.3}})):
        tt=dict(name='Blank template',code='LD-MT',markerIds=[200,201,202,203],distance='any',drills=[],zones=[],layout=lay,
                instructions=['Draw zones inside the dashed scan field only.','Fill each zone with its rule colour (legend).','Keep markers + white quiet zones clear.','Same colours as every -mask sheet and the Zone Editor.'])
        p=f'targets/mask-template-{suf}'; draw_target('mask-template',tt,p+'.pdf',maskmode=True)
        subprocess.run(['pdftoppm','-r','100','-png','-singlefile',p+'.pdf',p],check=True)
        subprocess.run(['pdftocairo','-svg',p+'.pdf',p+'.svg'],check=True)
