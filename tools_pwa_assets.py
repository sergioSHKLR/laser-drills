# Generates favicon set, maskable icons, apple-touch-icon and the 1200x630 Open Graph image.
from PIL import Image,ImageDraw,ImageFont
BG=(15,17,21);AC=(138,180,248)
def mark(sz,pad=0.0,bg=BG):   # LASER DRILLS bullseye mark (brand/mark.svg): black/white rings, red centre (red only here, never on printed sheets)
    S=sz*4; im=Image.new('RGB',(S,S),bg);d=ImageDraw.Draw(im);c=S/2;R=S/2*(1-pad)
    for f,col in [(1.0,(255,255,255)),(0.88,(17,17,17)),(0.686,(255,255,255)),(0.51,(17,17,17)),(0.334,(255,255,255)),(0.176,(224,27,36))]:
        r=R*f;d.ellipse([c-r,c-r,c+r,c+r],fill=col)
    return im.resize((sz,sz),Image.LANCZOS)
GR=(138,141,145)
def wordmark(d,x,y,s,F):   # gray bold LASER (bullseye) DRILLS, as brand/wordmark.svg
    f=F(s); d.text((x,y),'LASER',font=f,fill=GR); w=d.textlength('LASER',font=f); return x+w,f
for s in (192,512): mark(s,0.22).save(f'icons/maskable-{s}.png'); mark(s,0.04).save(f'icon-{s}.png')
mark(180,0.12).save('icons/apple-touch-icon.png')
for s in (16,32,48): mark(s,0.0).save(f'icons/favicon-{s}.png')
mark(48).save('favicon.ico',sizes=[(16,16),(32,32),(48,48)])
W,H=1200,630;og=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(og)
og.paste(mark(380,0.02),(90,125))  # brand mark
F=lambda s,b=True:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if b else ''),s)
x,f=wordmark(d,540,150,70,F); og.paste(mark(76),(int(x+12),158)); d.text((x+100,150),'DRILLS',font=f,fill=GR)
d.text((544,265),'Free laser dry-fire trainer',font=F(40,False),fill=AC)
y=340
for t in ['Printable ArUco targets + scoring masks','Drills, courses, qualification badges','Voice start · score-at-end · works offline']:
    d.ellipse([548,y+14,562,y+28],fill=(46,204,113));d.text((580,y),t,font=F(30,False),fill=(196,199,204));y+=56
d.text((544,560),'sergioshklr.github.io/laser-drills',font=F(26,False),fill=(154,160,166))
og.save('og-image.png')
