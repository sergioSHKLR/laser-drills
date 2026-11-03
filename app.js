const $=id=>document.getElementById(id);
const DEF={redMin:180,redDom:40,diffMin:60,minPixels:2,maxPixels:4000,refractoryMs:200,bgAlpha:0.15,shotgunSpread:1.5};
const RANGES={redMin:[50,255,1],redDom:[5,200,1],diffMin:[5,200,1],minPixels:[1,50,1],maxPixels:[50,20000,50],refractoryMs:[50,1000,10],bgAlpha:[0.01,0.5,0.01],shotgunSpread:[0,4,0.1]};
let settings=Object.assign({},DEF,JSON.parse(localStorage.getItem('ld-settings')||'{}'));
let DOC,DRILLS,video,vctx,view=$('view'),ctx=view.getContext('2d',{willReadFrequently:true});
let det=new AR.Detector(),laser=new Core.LaserDetector(settings),lock=null,lockAge=0,mask=null,lastDetect=0;
let W=640,H=480,state={mode:'idle',shots:[],beep:0,timer:null},marks=[],frames=0,fpsT=performance.now();
const ac=new (window.AudioContext||window.webkitAudioContext)();
function tone(f,ms){const o=ac.createOscillator(),g=ac.createGain();o.frequency.value=f;o.connect(g);g.connect(ac.destination);g.gain.value=0.4;o.start();o.stop(ac.currentTime+ms/1000);}
async function init(){[DOC,DRILLS]=await Promise.all([fetch('targets.json').then(r=>r.json()),fetch('drills.json').then(r=>r.json())]);
  DRILLS.forEach((d,i)=>$('drillSel').add(new Option(d.name,i)));showNotes();buildSliders();
  if('serviceWorker'in navigator)navigator.serviceWorker.register('sw.js');}
let course={idx:0,results:[]};
const sel=()=>DRILLS[$('drillSel').value];
const drill=()=>{const d=sel();return d.type==='course'?Object.assign({scoring:'idpa',maxPerShot:0},d.stages[Math.min(course.idx,d.stages.length-1)]):d;};
const target=()=>lock?lock.target:DOC.targets[drill().target==='any'?'bullseye':drill().target];
const spread=()=>($('shotgun').checked||drill().shotgun)?(target().spread||settings.shotgunSpread):0;
let ctrlT=0;
function showNotes(){const c=sel(),d=drill();let t=`${d.shots} shots · par ${d.parTime}s · random start ${d.startDelay[0]}–${d.startDelay[1]}s. ${d.notes||''}`;
  if(c.type==='course')t=`${c.notes}\nNOW: ${d.name} [target ${DOC.targets[d.target].code} ${DOC.targets[d.target].name}] ${d.brief} (${d.shots} shots, par ${d.parTime}s)`+(course.results.length?'\nDone: '+course.results.map(r=>`${r.name}: ${r.final.toFixed(2)}`).join(' | '):'');
  $('drillNotes').textContent=t;$('drillNotes').style.whiteSpace='pre-line';}
$('drillSel').onchange=()=>{course={idx:0,results:[]};showNotes();lock=null;};
function buildSliders(){const s=$('sliders');s.innerHTML='';for(const k in RANGES){const[a,b,st]=RANGES[k];
  const l=document.createElement('label');l.innerHTML=`${k}: <b>${settings[k]}</b><input type=range min=${a} max=${b} step=${st} value=${settings[k]}>`;
  l.querySelector('input').oninput=e=>{settings[k]=+e.target.value;l.querySelector('b').textContent=settings[k];Object.assign(laser.o,settings);localStorage.setItem('ld-settings',JSON.stringify(settings));};s.appendChild(l);}}
$('resetBtn').onclick=()=>{settings=Object.assign({},DEF);localStorage.removeItem('ld-settings');Object.assign(laser.o,settings);buildSliders();};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('on',x===b));
  ['drill','cal'].forEach(t=>$('tab-'+t).classList.toggle('hidden',t!==b.dataset.tab));});
$('camBtn').onclick=async()=>{ac.resume();try{
  const st=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720},frameRate:{ideal:60}}});
  video=document.createElement('video');video.playsInline=true;video.muted=true;video.srcObject=st;await video.play();
  const tr=st.getVideoTracks()[0],caps=tr.getCapabilities?tr.getCapabilities():{};
  // Lock exposure low if supported: laser pops more on a darker image.
  try{const adv={};if(caps.exposureMode&&caps.exposureMode.includes('manual'))adv.exposureMode='manual';
    if(caps.focusMode&&caps.focusMode.includes('continuous'))adv.focusMode='continuous';await tr.applyConstraints({advanced:[adv]});}catch(e){}
  H=Math.round(W*video.videoHeight/video.videoWidth);view.width=W;view.height=H;$('camBtn').disabled=true;loop();
 }catch(e){$('status').textContent='Camera error: '+e.message+' (needs HTTPS + permission)';}};
function buildMask(){mask=new Uint8Array(W*H);const f=DOC.template.field,p=[[f.x,f.y],[f.x+f.w,f.y],[f.x+f.w,f.y+f.h],[f.x,f.y+f.h]].map(q=>Core.apply(lock.tgtToImg,{x:q[0],y:q[1]}));
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){let inside=false;for(let i=0,j=3;i<4;j=i++){const a=p[i],b=p[j];
    if((a.y>y)!==(b.y>y)&&x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x)inside=!inside;}mask[y*W+x]=inside;}}
function loop(){const cb=(now)=>{tick(now);video.requestVideoFrameCallback?video.requestVideoFrameCallback(cb):requestAnimationFrame(cb);};
  video.requestVideoFrameCallback?video.requestVideoFrameCallback(cb):requestAnimationFrame(cb);}
function tick(now){ctx.drawImage(video,0,0,W,H);const img=ctx.getImageData(0,0,W,H);frames++;
  if(now-fpsT>1000){$('fps').textContent=frames;frames=0;fpsT=now;}
  if(now-lastDetect>(lock?1500:300)){lastDetect=now;const nl=Core.lockTarget(det.detect(img),DOC);
    if(nl){lock=nl;lockAge=now;buildMask();}else if(lock&&now-lockAge>4000){lock=null;mask=null;}}
  const hit=laser.process(img.data,W,H,now,$('maskTgt').checked&&mask?mask:null);
  $('cnt').textContent=laser.lastCount||0;
  if($('showMask').checked&&!$('tab-cal').classList.contains('hidden')&&laser.lastCount){const o=laser.o,d=img.data;
    for(let i=0;i<W*H;i++){const r=d[i*4],s=r-(d[i*4+1]+d[i*4+2])/2;if(r>=o.redMin&&s>=o.redDom){d[i*4]=255;d[i*4+1]=0;d[i*4+2]=255;}}ctx.putImageData(img,0,0);}
  if(hit)onHit(hit,now);draw();
  const d=drill();$('status').textContent=lock?(`Locked: ${lock.target.name} (${lock.target.code})`+(d.target!=='any'&&d.target!==lock.key?` ⚠ drill expects '${d.target}'`:'')):'Looking for 4 corner markers…';}
function onHit(h,now){const T=target(),d=drill();
  const exp=state.mode==='live'&&d.sequence?d.sequence[state.shots.length]:null;
  const p=lock?Core.apply(lock.imgToTgt,h):null,sc=p?Core.score(T,p,spread(),DOC.template,exp):{zone:null,score:0};
  if(sc.control){if(now-ctrlT<1200)return;ctrlT=now;tone(600,80);
    if(state.mode==='live'||state.mode==='free')finish();else if(state.mode!=='wait')$('goBtn').onclick();return;}
  marks.push({x:h.x,y:h.y,t:now});if(marks.length>30)marks.shift();
  if(state.mode==='free'||state.mode==='live'){state.shots.push({t:now,zone:sc.zone,score:sc.score,p,noshoot:sc.noshoot,ooo:sc.outOfOrder});tone(sc.noshoot?300:1600,sc.noshoot?200:40);render();
    if(state.mode==='live'&&state.shots.length>=d.shots)finish();}}
function poly(pts,col,dash){ctx.strokeStyle=col;ctx.setLineDash(dash||[]);ctx.beginPath();pts.forEach((q,i)=>{const r=Core.apply(lock.tgtToImg,q);i?ctx.lineTo(r.x,r.y):ctx.moveTo(r.x,r.y);});ctx.stroke();ctx.setLineDash([]);}
function draw(){if(lock){ctx.lineWidth=2;const tp=DOC.template,f=tp.field,c=tp.control,T=lock.target,g=spread();
   poly(Core.outline({shape:'rect',x:f.x,y:f.y,w:f.w,h:f.h}),'#29b6f6',[6,4]);
   poly(Core.outline({shape:'rect',x:c.x,y:c.y,w:c.w,h:c.h}),state.mode==='live'||state.mode==='free'?'#ff9800':'#00e676');
   for(const z of T.zones)if(z.kind!=='decor')poly(Core.outline(z,z.noGrow?0:g),z.kind==='noshoot'?'rgba(255,255,255,.9)':'rgba(255,235,59,.75)');}
  for(const m of marks){ctx.fillStyle='#00e676';ctx.beginPath();ctx.arc(m.x,m.y,5,0,7);ctx.fill();}}
function render(){const s=Core.drillSummary(drill(),state.beep,state.shots);
  $('shots').innerHTML=state.shots.map((x,i)=>`<tr><td>${i+1}</td><td>${s.times[i].toFixed(2)}</td><td>${s.splits[i].toFixed(2)}</td><td>${x.hardcover?'HARD COVER':x.noshoot?(drill().scoring==='idpa'?'NON-THREAT':'NO-SHOOT'):x.ooo?x.zone+' (order)':(x.zone||'miss')}</td><td>${drill().scoring==='idpa'?(x.noshoot?'+5s':'-'+x.pd):x.score}</td></tr>`).join('');
  if(state.mode==='done'&&drill().scoring==='idpa'){const r=Core.idpaSummary(drill(),state.shots,s.total);
    $('big').textContent=`${drill().name||'Stage'}: raw ${r.raw.toFixed(2)}s + PD ${r.pd} + PE ${r.pe}×3 + HNT ${r.hnt}×5 = ${r.final.toFixed(2)}`;}
  else if(state.mode==='done')$('big').textContent=`${s.score}/${s.maxScore} pts · ${s.total!=null?s.total.toFixed(2)+'s':'—'} ${s.underPar?'✅ under par':'❌ over par/incomplete'}`;}
function reset(){clearTimeout(state.timer);clearTimeout(state.par);state={mode:'idle',shots:[],beep:0};marks=[];$('shots').innerHTML='';$('big').textContent='';}
$('goBtn').onclick=()=>{ac.resume();reset();const d=drill();if(!lock){$('big').textContent='No target lock yet';return;}
  if(d.target!=='any'&&lock.key!==d.target){$('big').textContent=`Put up target ${DOC.targets[d.target].code} (${DOC.targets[d.target].name})`;return;}
  if(sel().type==='course'&&course.idx>=sel().stages.length){course={idx:0,results:[]};showNotes();}
  state.mode='wait';$('big').textContent='Stand by…';const delay=(d.startDelay[0]+Math.random()*(d.startDelay[1]-d.startDelay[0]))*1000;
  state.timer=setTimeout(()=>{state.mode='live';state.beep=performance.now();tone(2200,250);$('big').textContent='GO';
    state.par=setTimeout(()=>tone(900,300),d.parTime*1000);state.timer=setTimeout(finish,d.timeout*1000);},delay);};
$('freeBtn').onclick=()=>{ac.resume();reset();state.mode='free';state.beep=performance.now();$('big').textContent='Free fire';};
$('stopBtn').onclick=()=>{if(state.mode==='idle'&&sel().type==='course'){course={idx:0,results:[]};showNotes();}if(state.mode==='live'||state.mode==='free')finish();else reset();};
function finish(){clearTimeout(state.timer);clearTimeout(state.par);const was=state.mode;state.mode='done';render();
  const c=sel();if(c.type==='course'&&was==='live'){const d=drill(),s=Core.drillSummary(d,state.beep,state.shots),r=Core.idpaSummary(d,state.shots,s.total);
    course.results.push(Object.assign({name:d.name},r));course.idx++;
    if(course.idx>=c.stages.length){const tot=course.results.reduce((a,r)=>a+r.final,0);$('big').textContent+=` · COURSE TOTAL ${tot.toFixed(2)}s`;}
    else $('big').textContent+=` · Next: ${c.stages[course.idx].name}`;showNotes();}}
init();
