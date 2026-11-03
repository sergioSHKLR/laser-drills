// Shared logic (browser + node tests): homography, target lock, laser detection, scoring.
(function(root){
const Core={};
// Solve homography mapping src[i] -> dst[i] (4 points). Returns 3x3 array.
Core.homography=function(src,dst){
  const A=[],b=[];
  for(let i=0;i<4;i++){const {x,y}=src[i],u=dst[i].x,v=dst[i].y;
    A.push([x,y,1,0,0,0,-u*x,-u*y]);b.push(u);A.push([0,0,0,x,y,1,-v*x,-v*y]);b.push(v);}
  const n=8;for(let c=0;c<n;c++){let p=c;for(let r=c+1;r<n;r++)if(Math.abs(A[r][c])>Math.abs(A[p][c]))p=r;
    [A[c],A[p]]=[A[p],A[c]];[b[c],b[p]]=[b[p],b[c]];
    for(let r=0;r<n;r++)if(r!==c){const f=A[r][c]/A[c][c];for(let k=c;k<n;k++)A[r][k]-=f*A[c][k];b[r]-=f*b[c];}}
  const h=b.map((v,i)=>v/A[i][i]);return [[h[0],h[1],h[2]],[h[3],h[4],h[5]],[h[6],h[7],1]];
};
Core.apply=function(H,p){const w=H[2][0]*p.x+H[2][1]*p.y+H[2][2];
  return {x:(H[0][0]*p.x+H[0][1]*p.y+H[0][2])/w,y:(H[1][0]*p.x+H[1][1]*p.y+H[1][2])/w};};
// Template marker outer corners (inches) in TL,TR,BR,BL order.
Core.markerCorners=function(tpl){const m=tpl.margin,s=tpl.marker.size,W=tpl.page.w,H=tpl.page.h;
  return [{x:m,y:m},{x:W-m,y:m},{x:W-m,y:H-m},{x:m,y:H-m}];};
// markers: js-aruco list; doc: targets.json. Auto-identifies target by its marker IDs.
Core.tpl=function(doc,t){return t&&t.layout?Object.assign({},doc.template,t.layout):doc.template;};
Core.lockTarget=function(markers,doc){
  for(const key in doc.targets){const t=doc.targets[key],src=[],dst=Core.markerCorners(Core.tpl(doc,t));
    for(let c=0;c<4;c++){const f=markers.find(k=>k.id===t.markerIds[c]);if(!f)break;src.push(f.corners[c]);}
    if(src.length===4)return {key,target:t,imgToTgt:Core.homography(src,dst),tgtToImg:Core.homography(dst,src),imgPts:src};}
  return null;};
Core.inZone=function(z,p,g){g=g||0;
  switch(z.shape){
   case 'circle':return Math.hypot(p.x-z.cx,p.y-z.cy)<=z.r+g;
   case 'ellipse':{const dx=(p.x-z.cx)/(z.rx+g),dy=(p.y-z.cy)/(z.ry+g);return dx*dx+dy*dy<=1;}
   case 'rect':return p.x>=z.x-g&&p.x<=z.x+z.w+g&&p.y>=z.y-g&&p.y<=z.y+z.h+g;
   case 'poly':{let ins=false;const q=z.pts;for(let i=0,j=q.length-1;i<q.length;j=i++){
      if((q[i][1]>p.y)!==(q[j][1]>p.y)&&p.x<(q[j][0]-q[i][0])*(p.y-q[i][1])/(q[j][1]-q[i][1])+q[i][0])ins=!ins;}
     if(ins||!g)return ins;
     for(let i=0,j=q.length-1;i<q.length;j=i++){const ax=q[j][0],ay=q[j][1],bx=q[i][0],by=q[i][1],l=(bx-ax)**2+(by-ay)**2;
       const t=Math.max(0,Math.min(1,((p.x-ax)*(bx-ax)+(p.y-ay)*(by-ay))/l));if(Math.hypot(p.x-ax-t*(bx-ax),p.y-ay-t*(by-ay))<=g)return true;}
     return false;}}
  return false;};
Core.outline=function(z,g){g=g||0;const o=[];
  if(z.shape==='circle'||z.shape==='ellipse'){const rx=(z.r||z.rx)+g,ry=(z.r||z.ry)+g;for(let a=0;a<=48;a++)o.push({x:z.cx+rx*Math.cos(a/24*Math.PI),y:z.cy+ry*Math.sin(a/24*Math.PI)});}
  else if(z.shape==='rect')[[z.x-g,z.y-g],[z.x+z.w+g,z.y-g],[z.x+z.w+g,z.y+z.h+g],[z.x-g,z.y+z.h+g],[z.x-g,z.y-g]].forEach(q=>o.push({x:q[0],y:q[1]}));
  else {z.pts.forEach(q=>o.push({x:q[0],y:q[1]}));o.push({x:z.pts[0][0],y:z.pts[0][1]});}
  return o;};
// Classify a hit (target inches). expect: zone name (sequence) or group (IDPA order) to enforce.
// Returns {hardcover} | {noshoot,score(penalty)} | {zone,score,pd,group} | miss {zone:null,score:0,pd:5}
Core.score=function(target,pt,spread,tpl,expectName){spread=spread||0;
  if(tpl){const f=tpl.field;if(!Core.inZone({shape:'rect',x:f.x,y:f.y,w:f.w,h:f.h},pt,0))return {zone:null,score:0,pd:5,outside:true};}
  for(const z of target.zones)if(z.kind==='hardcover'&&Core.inZone(z,pt,0))return {zone:'HC',score:0,pd:5,hardcover:true};
  for(const z of target.zones)if(z.kind==='noshoot'&&Core.inZone(z,pt,spread))return {zone:z.name,score:z.penalty,pd:5,noshoot:true,ntSeconds:z.ntSeconds||5};
  let best=null;
  for(const z of target.zones){if(z.kind!=='score')continue;if(expectName&&!target.scoring&&z.name!==expectName)continue;
    if(Core.inZone(z,pt,z.noGrow?0:spread)&&(!best||z.score>best.score))best={zone:z.name,score:z.score,pd:z.pd!=null?z.pd:0,group:z.group,part:z.part};}
  if(best)return best;
  if(expectName&&!target.scoring){for(const z of target.zones)if(z.kind==='score'&&Core.inZone(z,pt,spread))return {zone:z.name,score:0,pd:5,outOfOrder:true};}
  return {zone:null,score:0,pd:5};};
// IDPA-style stage result: raw + PD*1s + PE*3s + HNT*5s. Each required hit missing (or on hard cover / non-threat) = 5 PD.
Core.idpaSummary=function(stage,shots,rawTime){
  const req=stage.shots,comp=stage.compliant||[],cnt=shots.slice(0,Math.max(req,shots.length)).map(s=>s.group&&comp.includes(s.group)?Object.assign({},s,{noshoot:true,compliantHit:true}):s);let pd=0,valid=0,hnt=0,pe=0;
  const win=stage.window||3,vt=(stage.verbalTimes||[]).filter(t=>t<=win),fc=Math.max(0,comp.length-vt.length),fcs=stage.failCommand||3;
  for(const s of cnt){if(s.noshoot)hnt++;if(s.zone&&!s.noshoot&&!s.hardcover){if(valid<req){pd+=s.pd;valid++;}}}
  pd+=5*Math.max(0,req-valid);
  if(stage.order){const got=cnt.filter(s=>s.group&&!s.noshoot);for(let i=0;i<got.length;i++)
    if(stage.order[i]&&(got[i].group!==stage.order[i]||(stage.parts&&stage.parts[i]&&got[i].part!==stage.parts[i]))){pe=1;break;}}
  const raw=rawTime==null?stage.timeout:rawTime;
  return {raw,pd,pe,hnt,fc,final:raw+pd+3*pe+5*hnt+fcs*fc};};
// Voice: app commands (only when NOT live) and verbal scenario commands (only during live scenario drills).
Core.VOICE={start:['start','standby','stand by','stand-by','begin','shooter ready'],stop:['stop','halt','cease'],reset:['reset','clear'],
  next:['next','next stage','skip'],repeat:['repeat','again','redo'],score:['score','result','results','how did i do']};
Core.VERBAL=['drop it','drop the gun','drop the weapon','drop the knife','show me your hands','hands up','let me see your hands','police','dont move','don t move','do not move','freeze','get down','on the ground','stay back','back up'];
Core.norm=t=>' '+String(t||'').toLowerCase().replace(/[^a-z ]+/g,' ').replace(/\s+/g,' ').trim()+' ';
Core.parseCommand=function(text){const t=Core.norm(text);let best=null,pos=-1;
  for(const cmd in Core.VOICE)for(const w of Core.VOICE[cmd]){const i=t.lastIndexOf(' '+w+' ');if(i>pos||(i===pos&&best&&w.length>best.len)){pos=i;best={cmd,len:w.length};}}
  return pos>=0?best.cmd:null;};
Core.isVerbal=function(text){const t=Core.norm(text);return Core.VERBAL.some(w=>t.includes(' '+w+' '));};
// Shoot/don't-shoot scenario: pick `count` targets, each THREAT (shoot) or COMPLIANT (verbal command, do not shoot).
Core.makeScenario=function(sc,rand){const pool=sc.pool.slice();for(let i=pool.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[pool[i],pool[j]]=[pool[j],pool[i]];}
  const pick=pool.slice(0,sc.count),st=pick.map(()=>rand()<sc.pCompliant?'compliant':'threat');
  if(!st.includes('threat')&&!sc.allowAllCompliant)st[0]='threat';if(sc.count>1&&!st.includes('compliant'))st[st.length-1]='compliant';
  const order=[],compliant=[],callList=[];pick.forEach((g,i)=>{callList.push({group:g,state:st[i]});if(st[i]==='threat')for(let k=0;k<sc.threatShots;k++)order.push(g);else compliant.push(g);});
  return {order,compliant,callList,shots:order.length,window:sc.window,failCommand:sc.failCommand,
    text:callList.map(k=>`${(sc.names&&sc.names[k.group])||k.group} ${k.state==='threat'?'GUN':'HANDS UP'}`).join(' · '),
    speech:callList.map(k=>`${(sc.names&&sc.names[k.group])||k.group.replace('T','Target ')}, ${k.state==='threat'?'gun':'hands up'}`).join('. ')};};
// Random call list: calls=[{group,label,shots|parts}] -> {order,parts,shots,text}
Core.makeCalls=function(calls,rand,shuffle){const c=calls.slice();if(shuffle!==false)for(let i=c.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[c[i],c[j]]=[c[j],c[i]];}
  const order=[],parts=[];for(const k of c){const p=k.parts||Array(k.shots).fill(null);for(const q of p){order.push(k.group);parts.push(q);}}
  return {order,parts,shots:order.length,callList:c,text:c.map(k=>`${k.group} ${k.label}${k.parts?' ('+k.parts.map(x=>x[0].toUpperCase()).join('-')+')':' x'+k.shots}`).join(' → ')};};
// Laser detector: frame differencing on a red-dominance score.
Core.LaserDetector=function(opts){
  this.o=Object.assign({redMin:180,redDom:40,diffMin:60,minPixels:2,maxPixels:4000,refractoryMs:200,bgAlpha:0.15},opts||{});
  this.bg=null;this.lastHit=-1e9;
};
Core.LaserDetector.prototype.process=function(rgba,w,h,tMs,mask){
  const o=this.o,n=w*h;if(!this.bg||this.bg.length!==n){this.bg=new Float32Array(n);
    for(let i=0;i<n;i++){const r=rgba[i*4],g=rgba[i*4+1],b=rgba[i*4+2];this.bg[i]=r-(g+b)/2;}return null;}
  let cnt=0,sx=0,sy=0,sw=0;const bg=this.bg,a=o.bgAlpha;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x,p=i*4,r=rgba[p],g=rgba[p+1],b=rgba[p+2];
    const s=r-(g+b)/2,d=s-bg[i];
    if(r>=o.redMin&&s>=o.redDom&&d>=o.diffMin&&(!mask||mask[i])){cnt++;sx+=x*d;sy+=y*d;sw+=d;}
    else bg[i]+=a*(s-bg[i]); // don't absorb the flash into the background
  }
  this.lastCount=cnt;
  if(cnt<o.minPixels||cnt>o.maxPixels)return null;
  if(tMs-this.lastHit<o.refractoryMs)return null;
  this.lastHit=tMs;return {x:sx/sw,y:sy/sw,pixels:cnt,t:tMs};
};
Core.drillSummary=function(drill,beepT,shots){
  const times=shots.map(s=>(s.t-beepT)/1000),splits=times.map((t,i)=>i?t-times[i-1]:t);
  const total=times.length?times[times.length-1]:null,score=shots.reduce((a,s)=>a+s.score,0);
  return {times,splits,total,score,maxScore:drill.shots*(drill.maxPerShot||5),par:drill.parTime,underPar:total!==null&&total<=drill.parTime&&shots.length===drill.shots};
};
if(typeof module!=='undefined')module.exports=Core;else root.Core=Core;
})(this);
