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
   case 'ellipse':{let ex=p.x-z.cx,ey=p.y-z.cy;if(z.rot){const t=z.rot*Math.PI/180,c=Math.cos(t),s=Math.sin(t);[ex,ey]=[ex*c-ey*s,ex*s+ey*c];}const dx=ex/(z.rx+g),dy=ey/(z.ry+g);return dx*dx+dy*dy<=1;}
   case 'rect':return p.x>=z.x-g&&p.x<=z.x+z.w+g&&p.y>=z.y-g&&p.y<=z.y+z.h+g;
   case 'poly':{let ins=false;const q=z.pts;for(let i=0,j=q.length-1;i<q.length;j=i++){
      if((q[i][1]>p.y)!==(q[j][1]>p.y)&&p.x<(q[j][0]-q[i][0])*(p.y-q[i][1])/(q[j][1]-q[i][1])+q[i][0])ins=!ins;}
     if(ins||!g)return ins;
     for(let i=0,j=q.length-1;i<q.length;j=i++){const ax=q[j][0],ay=q[j][1],bx=q[i][0],by=q[i][1],l=(bx-ax)**2+(by-ay)**2;
       const t=Math.max(0,Math.min(1,((p.x-ax)*(bx-ax)+(p.y-ay)*(by-ay))/l));if(Math.hypot(p.x-ax-t*(bx-ax),p.y-ay-t*(by-ay))<=g)return true;}
     return false;}}
  return false;};
Core.outline=function(z,g){g=g||0;const o=[];
  if(z.shape==='circle'||z.shape==='ellipse'){const rx=(z.r||z.rx)+g,ry=(z.r||z.ry)+g;for(let a=0;a<=48;a++){const t=-(z.rot||0)*Math.PI/180,u=rx*Math.cos(a/24*Math.PI),v=ry*Math.sin(a/24*Math.PI);o.push({x:z.cx+u*Math.cos(t)-v*Math.sin(t),y:z.cy+u*Math.sin(t)+v*Math.cos(t)});}}
  else if(z.shape==='rect')[[z.x-g,z.y-g],[z.x+z.w+g,z.y-g],[z.x+z.w+g,z.y+z.h+g],[z.x-g,z.y+z.h+g],[z.x-g,z.y-g]].forEach(q=>o.push({x:q[0],y:q[1]}));
  else {z.pts.forEach(q=>o.push({x:q[0],y:q[1]}));o.push({x:z.pts[0][0],y:z.pts[0][1]});}
  return o;};
// Classify a hit (target inches). expect: zone name (sequence) or group (IDPA order) to enforce.
// Returns {hardcover} | {noshoot,score(penalty)} | {zone,score,pd,group} | miss {zone:null,score:0,pd:5}
Core.score=function(target,pt,spread,tpl,expectName){spread=spread||0;
  if(tpl){const f=tpl.field;if(!Core.inZone({shape:'rect',x:f.x,y:f.y,w:f.w,h:f.h},pt,0))return {zone:null,score:0,pd:5,outside:true};}
  for(const z of target.zones)if(z.kind==='hardcover'&&Core.inZone(z,pt,0))return {zone:'HC',score:0,pd:5,hardcover:true};
  let best=null,topZ=null;
  // overlapping people: the front one (highest z among silhouettes containing the point; no-shoot/friendly people included) owns the hit
  for(const z of target.zones)if((z.kind==='score'&&z.sil||z.kind==='noshoot')&&z.z!=null&&Core.inZone(z,pt,0)&&(topZ===null||z.z>topZ))topZ=z.z;
  for(const z of target.zones)if(z.kind==='noshoot'&&!(topZ!==null&&z.z!=null&&z.z!==topZ)&&Core.inZone(z,pt,z.z!=null?0:spread))return {zone:z.name,score:z.penalty,pd:5,noshoot:true,friendly:!!z.friendly,ntSeconds:z.ntSeconds||5};
  for(const z of target.zones){if(z.kind!=='score')continue;if(topZ!==null&&z.z!=null&&z.z!==topZ)continue;if(expectName&&!target.scoring&&z.name!==expectName)continue;
    if(Core.inZone(z,pt,z.noGrow?0:spread)&&(!best||z.score>best.score))best={zone:z.name,score:z.score,pd:z.pd!=null?z.pd:0,group:z.group,part:z.part};}
  if(best){const bz=target.zones.find(q=>q.name===best.zone&&q.kind==='score');
    // e-vest / head-only: a person with a headOnly zone only counts head hits; any other hit on them = vest strike (+5 s, no score)
    if(best.group&&!(bz&&bz.headOnly)&&target.zones.some(q=>q.headOnly&&q.group===best.group))return {zone:best.zone,score:0,pd:5,noshoot:true,vestStrike:true,ntSeconds:5,group:best.group};
    return best;}
  // backstop: bystanders sit BEHIND threats, so only shots that miss every scoring zone land on them
  for(const z of target.zones)if(z.kind==='bystander'&&Core.inZone(z,pt,0))return {zone:z.name,score:z.penalty||-10,pd:5,bystander:true,backstop:true};
  if(expectName&&!target.scoring){for(const z of target.zones)if(z.kind==='score'&&Core.inZone(z,pt,spread))return {zone:z.name,score:0,pd:5,outOfOrder:true};}
  return {zone:null,score:0,pd:5};};
// Custom zone rules (Zone Editor): z.needs=N -> a zone hit counts only on its Nth hit (earlier ones 'pending', score 0);
// z.after=[names], z.afterN=N -> counts only after N hits in those zones (else out of order). history = earlier results.
Core.applyRules=function(target,res,history){if(!res||!res.zone)return res;const z=target.zones.find(q=>q.name===res.zone&&q.kind==='score');if(!z)return res;history=history||[];
  if(z.after&&z.after.length){const n=history.filter(h=>z.after.includes(h.zone)&&!h.pending&&!h.outOfOrder).length;if(n<(z.afterN||1))return Object.assign({},res,{score:0,pd:5,outOfOrder:true,rule:`needs ${z.afterN||1} in ${z.after.join('/')} first`});}
  if(z.needs>1){const n=history.filter(h=>h.zone===res.zone).length+1;if(n<z.needs)return Object.assign({},res,{score:0,pd:0,pending:true,rule:`hit ${n}/${z.needs}`});}
  return res;};
// Zone overrides from the Zone Editor (localStorage 'ld-zones') applied over targets.json
Core.applyOverrides=function(doc,ov){for(const k in ov||{})if(doc.targets[k]&&ov[k]&&ov[k].zones)doc.targets[k].zones=ov[k].zones;return doc;};
// IDPA-style stage result: raw + PD*1s + PE*3s + HNT*5s. Each required hit missing (or on hard cover / non-threat) = 5 PD.
Core.scoreAtEnd=function(d,pref){const c=(d&&d.category)||'training';return pref&&pref[c]!=null?!!pref[c]:c==='training';};
Core.idpaSummary=function(stage,shots,rawTime){
  const req=stage.shots,comp=stage.compliant||[],cnt=shots.slice(0,Math.max(req,shots.length)).map(s=>s.group&&comp.includes(s.group)?Object.assign({},s,{noshoot:true,compliantHit:true}):s);let pd=0,valid=0,hnt=0,pe=0,bys=0,ff=0;
  const win=stage.window||3,vt=(stage.verbalTimes||[]).filter(t=>t<=win),fc=Math.max(0,comp.length-vt.length),fcs=stage.failCommand||3;
  for(const s of cnt){if(s.bystander){bys++;continue;}if(s.noshoot&&s.friendly&&!s.compliantHit)ff++;else if(s.noshoot)hnt++;if(s.zone&&!s.noshoot&&!s.hardcover){if(valid<req){pd+=s.pd;valid++;}}}
  pd+=5*Math.max(0,req-valid);
  if(stage.order){const got=cnt.filter(s=>s.group&&!s.noshoot);for(let i=0;i<got.length;i++)
    if(stage.order[i]&&(got[i].group!==stage.order[i]||(stage.parts&&stage.parts[i]&&got[i].part!==stage.parts[i]))){pe=1;break;}}
  let wp=0;if(stage.crowd&&stage.order){const got=cnt.filter(s=>s.group&&!s.noshoot);for(let i=0;i<got.length;i++)if(stage.order[i]&&got[i].group!==stage.order[i])wp++;pe=0;}
  const raw=rawTime==null?stage.timeout:rawTime;
  return {raw,pd,pe,hnt,ff,fc,bys,wp,backstop:bys>0,fail:!!((stage.failOnNoShoot&&hnt>0)||(stage.failOnFriendly&&ff>0)),final:raw+pd+3*pe+5*hnt+10*ff+fcs*fc+10*bys+(stage.wrongPenalty||5)*wp};};
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

// Crowd Hunt: BOLO-style descriptions that resolve to exactly ONE person (target.people[]).
Core.crowdAtoms=function(p){const a=[];
  a.push({k:'shirt',t:`${p.shirt} shirt`,f:q=>q.shirt===p.shirt});
  a.push(p.jacket?{k:'jacket',t:`${p.jacket} jacket`,f:q=>q.jacket===p.jacket}:{k:'jacket',t:'no jacket',f:q=>!q.jacket});
  a.push(p.hat?{k:'hat',t:p.hat,f:q=>q.hat===p.hat}:{k:'hat',t:'no hat',f:q=>!q.hat});
  a.push(p.backpack?{k:'bag',t:`${p.backpack} backpack`,f:q=>q.backpack===p.backpack}:{k:'bag',t:'no backpack',f:q=>!q.backpack});
  a.push(p.glasses?{k:'glasses',t:'glasses',f:q=>q.glasses}:{k:'glasses',t:'no glasses',f:q=>!q.glasses});
  a.push({k:'held',t:p.held==='gun'?'holding a gun':`holding ${/^[aeiou]/.test(p.held)?'an':'a'} ${p.held}`,f:q=>q.held===p.held});
  a.push({k:'skin',t:`${p.skin}-skinned`,f:q=>q.skin===p.skin,skin:true});
  a.push({k:'sex',t:p.sex,f:q=>q.sex===p.sex,sex:true});return a;};
Core.crowdPhrase=function(p,atoms){const sk=atoms.find(a=>a.skin),sx=atoms.find(a=>a.sex),rest=atoms.filter(a=>!a.skin&&!a.sex&&!a.rel),rel=atoms.find(a=>a.rel);
  const head=[sk&&sk.t,sx?sx.t:'person'].filter(Boolean).join(' ');return [head[0].toUpperCase()+head.slice(1)].concat(rest.map(a=>a.t)).join(', ')+(rel?', '+rel.t:'');};
Core.crowdDescribe=function(people,p,level,rand){const n=(xs,f)=>xs.filter(f).length,one=f=>n(people,f)===1;
  const A=Core.crowdAtoms(p),plain=A.filter(a=>!a.skin&&!a.sex),shuf=x=>{x=x.slice();for(let i=x.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;};
  const all=(as)=>q=>as.every(a=>a.f(q));
  if(level===1){for(const a of shuf(plain))if(one(a.f))return [a];return null;}
  if(level===2){let pool=shuf(A.filter(a=>!a.sex));if(rand()<0.6)pool=pool.sort((a,b)=>(b.skin?1:0)-(a.skin?1:0));  // skin allowed, only combined with clothing/gear
    for(let i=0;i<pool.length;i++)for(let j=i+1;j<pool.length;j++){const c=[pool[i],pool[j]];if(c.every(a=>a.skin)||c.filter(a=>!a.skin).length===0)continue;
      if(one(all(c))&&!c.some(a=>one(a.f)))return rand()<0.5?c.concat([A.find(a=>a.sex)]):c;}
    return null;}
  // level 3: three atoms (none/no pair unique alone) or two atoms + relative position to a uniquely described anchor
  let pool=shuf(A.filter(a=>!a.sex));if(rand()<0.6)pool=pool.sort((a,b)=>(b.skin?1:0)-(a.skin?1:0));
  if(rand()<0.5){for(let i=0;i<pool.length;i++)for(let j=i+1;j<pool.length;j++)for(let k=j+1;k<pool.length;k++){const c=[pool[i],pool[j],pool[k]];
    if(c.filter(a=>!a.skin).length<2)continue;if(one(all(c))&&![[0,1],[0,2],[1,2]].some(([x,y])=>one(all([c[x],c[y]]))))return c;}}
  for(const anc of shuf(people.filter(q=>q!==p))){const ua=shuf(Core.crowdAtoms(anc).filter(a=>!a.skin&&!a.sex)).find(a=>one(a.f));if(!ua)continue;
    const side=p.x<anc.x?'left':'right',rf=q=>side==='left'?q.x<anc.x:q.x>anc.x;
    for(let i=0;i<pool.length;i++)for(let j=i+1;j<pool.length;j++){const c=[pool[i],pool[j]];if(c.every(a=>a.skin))continue;const f=all(c);
      if(n(people,f)>1&&n(people,q=>f(q)&&rf(q))===1)return c.concat([{rel:true,t:`${side} of the person ${/^(holding|no )/.test(ua.t)?(ua.t.startsWith('no ')?'with '+ua.t:ua.t):(ua.t==='glasses'?'with glasses':'in the '+ua.t)}`}]);}}
  return null;};
Core.crowdCalls=function(target,cfg,rand){const people=target.people,calls=[],used=new Set();let guard=0;
  while(calls.length<(cfg.rounds||3)&&guard++<200){const p=people[Math.floor(rand()*people.length)];if(used.has(p.group))continue;
    const d=Core.crowdDescribe(people,p,cfg.level||1,rand);if(!d)continue;used.add(p.group);const say=Core.crowdPhrase(p,d);
    calls.push({group:p.group,label:say,say,shots:cfg.shots||2});}
  const r=Core.makeCalls(calls,rand,false);r.wrongPenalty=cfg.wrongPenalty||5;r.text=calls.map((c,i)=>`${i+1}) ${c.say}`).join('  ');return r;};
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
// ---- Games (drill.game): callouts, battleship, poker. gameStart -> state; gameShot(state,target,res) -> {pts,msg,say}
Core.shuffle=(a,rand)=>{a=a.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
Core.zoneTags=function(T,name){const z=name&&T.zones.find(q=>q.name===name);return z?[z.name,z.group].concat(z.tags||[]).filter(Boolean):[];};
Core.placeFleet=function(rows,cols,ships,rand){const used=new Set(),fleet=[];
  for(const sh of ships){for(let k=0;k<500;k++){const h=rand()<0.5,r=Math.floor(rand()*(h?rows:rows-sh.len+1)),c=Math.floor(rand()*(h?cols-sh.len+1:cols));
      const cells=[];for(let i=0;i<sh.len;i++)cells.push(String.fromCharCode(65+(h?r:r+i))+((h?c+i:c)+1));
      if(cells.some(x=>used.has(x)))continue;cells.forEach(x=>used.add(x));fleet.push({name:sh.name,cells,hit:[]});break;}}
  return fleet;};
const RK='23456789TJQKA';
Core.cardParse=c=>{c=String(c).toUpperCase().replace('10','T');return {r:RK.indexOf(c[0])+2,s:c[1]};};
Core.HANDS=['High card','One pair','Two pair','Three of a kind','Straight','Flush','Full house','Four of a kind','Straight flush','Royal flush'];
Core.pokerRank=function(cards){const p=cards.map(Core.cardParse),rs=p.map(x=>x.r).sort((a,b)=>b-a),cnt={};rs.forEach(r=>cnt[r]=(cnt[r]||0)+1);
  const c=Object.values(cnt).sort((a,b)=>b-a),fl=p.length===5&&p.every(x=>x.s===p[0].s),u=[...new Set(rs)];
  let st=u.length===5&&(u[0]-u[4]===4||(u[0]===14&&u[1]===5));
  let r=st&&fl?(rs[0]===14&&rs[4]===10?9:8):c[0]===4?7:c[0]===3&&c[1]===2?6:fl?5:st?4:c[0]===3?3:c[0]===2&&c[1]===2?2:c[0]===2?1:0;
  return {rank:r,name:Core.HANDS[r]};};
Core.gameStart=function(g,T,rand){const s={g,score:0,shots:0,done:false,log:[]};
  if(g.type==='battle'){s.fleet=Core.placeFleet(g.rows,g.cols,g.ships,rand);s.shot=new Set();s.say=`${g.ships.length} ships hidden. Fire at will.`;}
  else if(g.type==='poker'){s.cards=[];s.say='Shoot five cards.';}
  else {let q=Core.shuffle(g.calls,rand);if(g.rounds)while(q.length<g.rounds)q=q.concat(Core.shuffle(g.calls,rand));s.queue=q.slice(0,g.rounds||q.length);s.i=0;s.need=s.queue[0].n||1;s.say=s.queue[0].say;}
  s.text=s.say;return s;};
Core.gameShot=function(s,T,res){if(s.done)return {pts:0,msg:'game over',say:''};s.shots++;const g=s.g,tags=Core.zoneTags(T,res&&res.zone);let pts=0,msg,say;
  if(g.type==='battle'){const cell=tags.find(t=>/^[A-Z]\d+$/.test(t));
    if(!cell){msg='off grid';say='Off grid';}
    else if(s.shot.has(cell)){msg=cell+' again';say='Already fired at '+cell;}
    else{s.shot.add(cell);const sh=s.fleet.find(f=>f.cells.includes(cell));
      if(!sh){msg=cell+' miss';say='Miss';}
      else{sh.hit.push(cell);if(sh.hit.length===sh.cells.length){msg=cell+' SUNK '+sh.name;say='Hit. You sunk my '+sh.name;}else{msg=cell+' HIT';say='Hit';}
        if(s.fleet.every(f=>f.hit.length===f.cells.length)){s.done=true;say+=`. Fleet destroyed in ${s.shots} shots`;}}}
    s.score=-s.shots;pts=0;s.summary=s.done?`Fleet sunk in ${s.shots} shots`:`${s.fleet.filter(f=>f.hit.length===f.cells.length).length} of ${s.fleet.length} ships sunk, ${s.shots} shots`;}
  else if(g.type==='poker'){const card=tags.find(t=>/^(10|[2-9TJQKA])[SHDC]$/.test(t));
    if(!card){msg='miss';say='Miss';}else if(s.cards.includes(card)){msg=card+' again';say='Already have it';}
    else{s.cards.push(card);msg=card;say=card;if(s.cards.length===5){const r=Core.pokerRank(s.cards);s.done=true;pts=r.rank*10;s.hand=r;say=r.name;msg+=' → '+r.name;}}
    s.score=s.hand?s.hand.rank*10:0;s.summary=s.hand?`${s.hand.name}: ${s.cards.join(' ')}`:`${s.cards.length} cards: ${s.cards.join(' ')}`;}
  else{const cur=s.queue[s.i],base=r=>r>0?r:({0:5,'-1':3,'-3':1}[r]||1);
    if(res&&res.vestStrike){pts=g.vest||-5;msg='VEST STRIKE';say='Vest strike';}
    else if(res&&(res.noshoot||res.bystander)){pts=g.noShoot||-10;msg='NO-SHOOT';say='No shoot!';}
    else if(cur.forbid&&tags.some(t=>cur.forbid.includes(t))){pts=g.fratricide||-25;msg='FRIENDLY FIRE';say='Friendly fire!';}
    else if(tags.some(t=>cur.tags.includes(t))){pts=base(res.score);msg='HIT '+(res.zone||'');s.need--;say='Hit';}
    else if(res&&res.zone){pts=g.wrong||-2;msg='WRONG '+res.zone;say='Wrong target';}
    else{msg='miss';say='Miss';}
    if(s.need<=0){s.i++;if(s.i>=s.queue.length){s.done=true;say+='. Done';}else{s.need=s.queue[s.i].n||1;say+='. Next: '+s.queue[s.i].say;}}
    s.score+=pts;s.summary=`${s.score} points, ${s.i} of ${s.queue.length} calls in ${s.shots} shots`;}
  s.text=s.done?s.summary:(g.type==='battle'||g.type==='poker'?s.summary:'CALL: '+s.queue[s.i].say);
  return {pts,msg,say};};
if(typeof module!=='undefined')module.exports=Core;else root.Core=Core;
})(this);
