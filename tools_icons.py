# Builds an inline Lucide SVG sprite (ISC) into index.html between <!--LUCIDE--> markers and vendor/lucide/.
import re,os,shutil,sys
SRC=sys.argv[1] if len(sys.argv)>1 else '/tmp/package'
NAMES="house list crosshair chart-column settings camera camera-off mic mic-off play square rotate-ccw skip-forward volume-2 download upload trash-2 circle circle-check circle-x circle-dot lock chevron-right chevron-down chevron-left x triangle-alert siren hand medal award trophy crown shield eye star zap users timer puzzle target trending-down trending-up check plus file-down".split()
os.makedirs('vendor/lucide',exist_ok=True);shutil.copy(SRC+'/LICENSE','vendor/lucide/LICENSE')
sym=[]
for n in NAMES:
    s=open(f'{SRC}/icons/{n}.svg').read();body=re.search(r'>\s*(.*)</svg>',s,re.S).group(1)
    body=re.sub(r'\s+',' ',body).strip();sym.append(f'<symbol id="i-{n}" viewBox="0 0 24 24">{body}</symbol>')
sp='<svg xmlns="http://www.w3.org/2000/svg" style="display:none"><!-- Lucide icons v1.67.0, ISC License, https://lucide.dev --><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+''.join(sym)+'</g></svg>'
open('vendor/lucide/sprite.svg','w').write(sp)
h=open('index.html').read()
h=re.sub(r'<!--LUCIDE-->.*?<!--/LUCIDE-->','',h,flags=re.S).replace('<body>','<body><!--LUCIDE-->'+sp+'<!--/LUCIDE-->',1)
open('index.html','w').write(h);print(len(NAMES),'icons')
