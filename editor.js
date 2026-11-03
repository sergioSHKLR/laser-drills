// Desktop mouse-driven zone editor. Zones are in target inches (same as targets.json); saved to localStorage 'ld-zones'.
const $=id=>document.getElementById(id),cv=$('cv'),cx=cv.getContext('2d');
let DOC,ORIG,key,zones=[],img=new Image(),page,sel=-1,tool='sel',view={s:60,ox:20,oy:20},drag=null,polyPts=null,mouse={x:0,y:0};
const OV=()=>JSON.parse(localStorage.getItem('ld-zones')||'{}');
const RULES={hit:'Hit (points / -0 -1 -3)',nohit:'No-hit / no-shoot (penalty)',requires:'Requires N shots',sequence:'Sequence (after N hits elsewhere)',cover:'Hard cover',bystander:'Bystander (backstop)'};
const ruleOf=z=>z.rule||(z.kind==='noshoot'?'nohit':z.kind==='hardcover'?'cover':z.kind==='bystander'?'bystander':z.after?'sequence':z.needs>1?'requires':'hit');
function setRule(z,r){z.rule=r;z.kind={nohit:'noshoot',cover:'hardcover',bystander:'bystander'}[r]||'score';
  if(z.kind==='score'){if(z.score==null)z.score=5;if(z.pd==null)z.pd=0;}else{delete z.sil;}
  if(r==='nohit'&&z.penalty==null)z.penalty=-10;if(r==='requires'&&!(z.needs>1))z.needs=2;if(r!=='requires')delete z.needs;
  if(r==='sequence'){z.after=z.after||[];z.afterN=z.afterN||2;}else{delete z.after;delete z.afterN;}}
fetch('targets.json').then(r=>r.json()).then(d=>{ORIG=JSON.parse(JSON.stringify(d));DOC=d;
  for(const k in d.targets)$('tsel').add(new Option(`${d.targets[k].code||''} ${d.targets[k].name}`,k));
  const h=new URLSearchParams(location.search).get('t');if(h&&d.targets[h])$('tsel').value=h;load();});
$('tsel').onchange=load;
function load(){key=$('tsel').value;const t=DOC.targets[key],o=OV()[key];zones=JSON.parse(JSON.stringify(o?o.zones:t.zones));sel=-1;
  page=(t.layout&&t.layout.page)||DOC.template.page;img=new Image();img.onload=fit;img.src=`targets/${key}-letter.png`;msg(o?'custom zones loaded':'default zones');}
function fit(){size();view.s=Math.min((cv.width-40)/page.w,(cv.height-40)/page.h);view.ox=20;view.oy=20;redraw();}
function size(){cv.width=$('wrap').clientWidth;cv.height=$('wrap').clientHeight;}addEventListener('resize',()=>{size();redraw();});
const T=(x,y)=>[view.ox+x*view.s,view.oy+y*view.s],I=(px,py)=>({x:(px-view.ox)/view.s,y:(py-view.oy)/view.s});
const msg=t=>$('msg').textContent=t;
function color(z){return {score:'#ffd600',noshoot:'#ff40ff',hardcover:'#888',bystander:'#ff9800',decor:'#555'}[z.kind]||'#fff';}
function handles(z){if(z.shape==='circle')return[{x:z.cx,y:z.cy,h:'c'},{x:z.cx+z.r,y:z.cy,h:'r'}];
  if(z.shape==='ellipse')return[{x:z.cx,y:z.cy,h:'c'},{x:z.cx+z.rx,y:z.cy,h:'rx'},{x:z.cx,y:z.cy+z.ry,h:'ry'}];
  if(z.shape==='rect')return[[0,0],[1,0],[1,1],[0,1]].map(([a,b],i)=>({x:z.x+a*z.w,y:z.y+b*z.h,h:'k'+i}));
  return z.pts.map((p,i)=>({x:p[0],y:p[1],h:'p'+i}));}
function redraw(){cx.fillStyle='#1e1f22';cx.fillRect(0,0,cv.width,cv.height);if(!page)return;const[a,b]=T(0,0);
  cx.drawImage(img,a,b,page.w*view.s,page.h*view.s);
  zones.forEach((z,i)=>{if(z.kind==='decor'||(!$('showAll').checked&&z.kind==='bystander'))return;const o=Core.outline(z,0);cx.beginPath();o.forEach((p,j)=>{const[q,r]=T(p.x,p.y);j?cx.lineTo(q,r):cx.moveTo(q,r);});
    cx.strokeStyle=color(z);cx.lineWidth=i===sel?3:1.5;cx.setLineDash(z.kind==='hardcover'?[6,4]:[]);cx.stroke();cx.setLineDash([]);
    if(i===sel){cx.fillStyle=color(z)+'33';cx.fill();cx.fillStyle='#fff';handles(z).forEach(h=>{const[q,r]=T(h.x,h.y);cx.fillRect(q-4,r-4,8,8);});}});
  if(polyPts){cx.strokeStyle='#0f0';cx.beginPath();[...polyPts,[mouse.x,mouse.y]].forEach((p,j)=>{const[q,r]=T(p[0],p[1]);j?cx.lineTo(q,r):cx.moveTo(q,r);});cx.stroke();}
  if(drag&&drag.draw){const z=drag.z,o=Core.outline(z,0);cx.strokeStyle='#0f0';cx.beginPath();o.forEach((p,j)=>{const[q,r]=T(p.x,p.y);j?cx.lineTo(q,r):cx.moveTo(q,r);});cx.stroke();}
  list();}
function hitTest(p){for(let i=zones.length-1;i>=0;i--){const z=zones[i];if(z.kind==='decor'||(!$('showAll').checked&&z.kind==='bystander'))continue;if(Core.inZone(z,p,0))return i;}return -1;}
function handleAt(px,py){if(sel<0)return null;for(const h of handles(zones[sel])){const[q,r]=T(h.x,h.y);if(Math.abs(q-px)<7&&Math.abs(r-py)<7)return h.h;}return null;}
document.querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>setTool(b.dataset.t));
function setTool(t){tool=t;polyPts=null;document.querySelectorAll('[data-t]').forEach(b=>b.classList.toggle('on',b.dataset.t===t));cv.style.cursor=t==='sel'?'default':'crosshair';redraw();}
cv.onwheel=e=>{e.preventDefault();const p=I(e.offsetX,e.offsetY),f=e.deltaY<0?1.15:1/1.15;view.s*=f;view.ox=e.offsetX-p.x*view.s;view.oy=e.offsetY-p.y*view.s;redraw();};
cv.oncontextmenu=e=>{e.preventDefault();const i=hitTest(I(e.offsetX,e.offsetY));if(i<0)return;sel=i;redraw();panel();const m=$('menu');
  m.innerHTML=Object.entries(RULES).map(([k,v])=>`<div data-r="${k}">${ruleOf(zones[i])===k?'✓ ':''}${v}</div>`).join('')+'<div data-r="del">Delete zone</div>';
  m.style.left=e.clientX+'px';m.style.top=e.clientY+'px';m.style.display='block';
  m.querySelectorAll('div').forEach(d=>d.onclick=()=>{m.style.display='none';if(d.dataset.r==='del')del();else{setRule(zones[sel],d.dataset.r);panel();redraw();}});};
addEventListener('mousedown',e=>{if(!$('menu').contains(e.target))$('menu').style.display='none';});
const snap=v=>Math.round(v*100)/100;
cv.onmousedown=e=>{if(e.button===2)return;const p=I(e.offsetX,e.offsetY);
  if(e.button===1||(tool==='sel'&&!handleAt(e.offsetX,e.offsetY)&&hitTest(p)<0&&!e.shiftKey)){if(tool==='sel'&&e.button===0){sel=-1;panel();}drag={pan:1,sx:e.offsetX,sy:e.offsetY,ox:view.ox,oy:view.oy};return;}
  if(tool==='sel'){const h=handleAt(e.offsetX,e.offsetY);if(h){drag={h,z:zones[sel]};return;}sel=hitTest(p);panel();if(sel>=0)drag={move:1,last:p,z:zones[sel]};redraw();return;}
  if(tool==='poly'){if(!polyPts)polyPts=[];polyPts.push([snap(p.x),snap(p.y)]);redraw();return;}
  const z=tool==='circle'?{shape:'circle',cx:snap(p.x),cy:snap(p.y),r:0.05}:{shape:'rect',x:snap(p.x),y:snap(p.y),w:0.05,h:0.05};drag={draw:1,z,p0:p};};
cv.ondblclick=()=>{if(tool==='poly')closePoly();};
function closePoly(){if(polyPts&&polyPts.length>=3)add({shape:'poly',pts:polyPts});polyPts=null;redraw();}
function add(z){z.name=`Z${zones.length+1}`;setRule(z,'hit');zones.push(z);sel=zones.length-1;panel();setTool('sel');}
cv.onmousemove=e=>{const p=I(e.offsetX,e.offsetY);mouse={x:p.x,y:p.y};
  if(!drag){if(polyPts)redraw();return;}
  if(drag.pan){view.ox=drag.ox+e.offsetX-drag.sx;view.oy=drag.oy+e.offsetY-drag.sy;}
  else if(drag.draw){const z=drag.z,q=drag.p0;if(z.shape==='circle')z.r=snap(Math.max(0.05,Math.hypot(p.x-q.x,p.y-q.y)));else{z.x=snap(Math.min(p.x,q.x));z.y=snap(Math.min(p.y,q.y));z.w=snap(Math.abs(p.x-q.x));z.h=snap(Math.abs(p.y-q.y));}}
  else if(drag.move){const dx=p.x-drag.last.x,dy=p.y-drag.last.y,z=drag.z;drag.last=p;
    if(z.cx!=null){z.cx+=dx;z.cy+=dy;}else if(z.shape==='rect'){z.x+=dx;z.y+=dy;}else z.pts=z.pts.map(q=>[q[0]+dx,q[1]+dy]);}
  else if(drag.h){const z=drag.z,h=drag.h;
    if(h==='c'){z.cx=p.x;z.cy=p.y;}else if(h==='r')z.r=Math.max(0.05,Math.hypot(p.x-z.cx,p.y-z.cy));else if(h==='rx')z.rx=Math.max(0.05,Math.abs(p.x-z.cx));else if(h==='ry')z.ry=Math.max(0.05,Math.abs(p.y-z.cy));
    else if(h[0]==='p')z.pts[+h.slice(1)]=[p.x,p.y];
    else{const i=+h.slice(1),x2=z.x+z.w,y2=z.y+z.h;let[x1,y1,x3,y3]=[z.x,z.y,x2,y2];if(i===0||i===3)x1=p.x;else x3=p.x;if(i<2)y1=p.y;else y3=p.y;z.x=Math.min(x1,x3);z.y=Math.min(y1,y3);z.w=Math.abs(x3-x1);z.h=Math.abs(y3-y1);}}
  redraw();};
cv.onmouseup=()=>{if(drag&&drag.draw&&(drag.z.r>0.1||drag.z.w>0.1))add(drag.z);drag=null;round();redraw();};
function round(){if(sel<0)return;const z=zones[sel];for(const k of['cx','cy','r','rx','ry','x','y','w','h'])if(z[k]!=null)z[k]=snap(z[k]);if(z.pts)z.pts=z.pts.map(q=>[snap(q[0]),snap(q[1])]);}
addEventListener('keydown',e=>{if(/INPUT|SELECT/.test(document.activeElement.tagName))return;
  if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();del();}else if(e.key==='Enter')closePoly();else if(e.key==='Escape'){polyPts=null;sel=-1;panel();redraw();}
  else{const t={v:'sel',c:'circle',r:'rect',p:'poly'}[e.key.toLowerCase()];if(t)setTool(t);}});
function del(){if(sel<0)return;const n=zones[sel].name;zones.splice(sel,1);zones.forEach(z=>{if(z.after)z.after=z.after.filter(a=>a!==n);});sel=-1;panel();redraw();}
function panel(){const P=$('zp');if(sel<0){P.textContent='none (click a zone, or draw one)';return;}const z=zones[sel],r=ruleOf(z);
  const names=[...new Set(zones.filter((q,i)=>i!==sel&&q.kind==='score').map(q=>q.name))].filter(n=>n!==z.name);
  P.innerHTML=`<label>Name <input id="fn" value="${z.name}"></label><label>Rule <select id="fr">${Object.entries(RULES).map(([k,v])=>`<option value="${k}" ${k===r?'selected':''}>${v}</option>`).join('')}</select></label>`+
   (z.kind==='score'?`<label>Points <input type=number id="fs" value="${z.score}"></label><label>IDPA <select id="fpd">${[0,1,3].map(v=>`<option value=${v} ${z.pd===v?'selected':''}>-${v}</option>`).join('')}</select></label>`:'')+
   (r==='nohit'?`<label>Penalty points <input type=number id="fp" value="${z.penalty}"></label><label>Seconds added <input type=number id="fsec" value="${z.ntSeconds||5}"></label>`:'')+
   (r==='requires'?`<label>Shots required <input type=number min=2 id="fnn" value="${z.needs}"></label>`:'')+
   (r==='sequence'?`<label>Counts after <input type=number min=1 id="fan" value="${z.afterN}"> hits in:</label><select id="faf" multiple size=5 style="width:100%">${names.map(n=>`<option ${z.after.includes(n)?'selected':''}>${n}</option>`).join('')}</select>`:'')+
   `<div class="row"><button onclick="del()">Delete</button><button onclick="dup()">Duplicate</button></div>`;
  const on=(id,f)=>{const el=$(id);if(el)el.onchange=()=>{f(el);panel();redraw();};};
  on('fn',el=>{const old=z.name;z.name=el.value.trim()||old;zones.forEach(q=>{if(q.after)q.after=q.after.map(a=>a===old?z.name:a);});});
  on('fr',el=>setRule(z,el.value));on('fs',el=>z.score=+el.value);on('fpd',el=>z.pd=+el.value);on('fp',el=>z.penalty=+el.value);on('fsec',el=>z.ntSeconds=+el.value);
  on('fnn',el=>z.needs=Math.max(2,+el.value));on('fan',el=>z.afterN=Math.max(1,+el.value));on('faf',el=>z.after=[...el.selectedOptions].map(o=>o.value));}
function dup(){const z=JSON.parse(JSON.stringify(zones[sel]));z.name+="'";if(z.cx!=null){z.cx+=.3;z.cy+=.3;}else if(z.x!=null){z.x+=.3;z.y+=.3;}else z.pts=z.pts.map(q=>[q[0]+.3,q[1]+.3]);zones.push(z);sel=zones.length-1;panel();redraw();}
function list(){$('list').innerHTML='<h3>Zones</h3>'+zones.map((z,i)=>z.kind==='decor'?'':`<div style="cursor:pointer;${i===sel?'color:#fff;font-weight:bold':''}" onclick="sel=${i};panel();redraw()">${z.name} · ${RULES[ruleOf(z)].split(' (')[0]}${z.kind==='score'?' · '+z.score:''}</div>`).join('');}
$('showAll').onchange=redraw;
$('save').onclick=()=>{const o=OV();o[key]={zones};localStorage.setItem('ld-zones',JSON.stringify(o));msg('saved for '+key+' (used by the app in this browser)');};
$('reset').onclick=()=>{if(!confirm('Discard custom zones for this target?'))return;const o=OV();delete o[key];localStorage.setItem('ld-zones',JSON.stringify(o));zones=JSON.parse(JSON.stringify(ORIG.targets[key].zones));sel=-1;panel();redraw();msg('reset to default');};
$('exp').onclick=()=>{const b=new Blob([JSON.stringify({[key]:{zones}},null,1)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=`zones-${key}.json`;a.click();};
$('imp').onclick=()=>$('file').click();
$('file').onchange=async e=>{try{const o=JSON.parse(await e.target.files[0].text()),cur=OV();for(const k in o)if(DOC.targets[k]&&o[k].zones)cur[k]=o[k];localStorage.setItem('ld-zones',JSON.stringify(cur));load();msg('imported: '+Object.keys(o).join(', '));}catch(x){msg('bad JSON file');}e.target.value='';};
$('share').onclick=()=>{const s=btoa(unescape(encodeURIComponent(JSON.stringify({[key]:{zones}})))),u=location.href.replace(/editor\.html.*$/,'')+'#zones='+encodeURIComponent(s);
  navigator.clipboard.writeText(u).then(()=>msg(`link copied (${u.length} chars): open it on the phone`),()=>prompt('Copy this link',u));};
