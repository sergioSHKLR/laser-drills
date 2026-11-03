# Generates favicon set, maskable icons, apple-touch-icon and the 1200x630 Open Graph image.
from PIL import Image,ImageDraw,ImageFont
BG=(15,17,21);AC=(138,180,248)
def mark(sz,pad=0.0,bg=BG):
    im=Image.new('RGB',(sz,sz),bg);d=ImageDraw.Draw(im);c=sz/2;R=sz/2*(1-pad)
    for f,col in [(0.92,(240,240,240)),(0.70,BG),(0.48,(240,240,240)),(0.26,BG)]:
        r=R*f;d.ellipse([c-r,c-r,c+r,c+r],fill=col)
    r=R*0.11;d.ellipse([c-r,c-r,c+r,c+r],fill=(46,204,113))  # green laser dot (laser-safe palette)
    return im
for s in (192,512): mark(s,0.22).save(f'icons/maskable-{s}.png')
mark(180,0.12).save('icons/apple-touch-icon.png')
for s in (16,32,48): mark(s,0.0).save(f'icons/favicon-{s}.png')
mark(48).save('favicon.ico',sizes=[(16,16),(32,32),(48,48)])
W,H=1200,630;og=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(og)
og.paste(mark(380,0.02),(90,125))
F=lambda s,b=True:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if b else ''),s)
d.text((540,150),'Laser Drills',font=F(84),fill=(232,234,237))
d.text((544,265),'Free laser dry-fire trainer',font=F(40,False),fill=AC)
y=340
for t in ['Printable ArUco targets + scoring masks','Drills, courses, qualification badges','Voice start · score-at-end · works offline']:
    d.ellipse([548,y+14,562,y+28],fill=(46,204,113));d.text((580,y),t,font=F(30,False),fill=(196,199,204));y+=56
d.text((544,560),'sergioshklr.github.io/laser-drills',font=F(26,False),fill=(154,160,166))
og.save('og-image.png')
