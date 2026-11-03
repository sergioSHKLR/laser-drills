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
  [['training','Self-Defense Training'],['fun','Fun']].forEach(([c,l])=>{const g=document.createElement('optgroup');g.label=l;DRILLS.forEach((d,i)=>{if((d.category||'training')===c)g.appendChild(new Option(d.name,i));});if(g.children.length)$('drillSel').appendChild(g);});showNotes();buildSliders();
  if('serviceWorker'in navigator)navigator.serviceWorker.register('sw.js');}
let course={idx:0,results:[]};
const sel=()=>DRILLS[$('drillSel').value];
const drill=()=>{const d=sel(),b=d.type==='course'?Object.assign({scoring:'idpa',maxPerShot:0},d.stages[Math.min(course.idx,d.stages.length-1)]):d;
  if(b.scenario)return Object.assign({},b,state.calls||{shots:b.scenario.count*b.scenario.threatShots},{verbalTimes:state.verbal||[]});
  if(b.crowd)return Object.assign({},b,state.calls||{shots:(b.crowd.rounds||3)*(b.crowd.shots||2)});
  return b.calls?Object.assign({},b,state.calls||{shots:b.calls.reduce((a,k)=>a+(k.parts?k.parts.length:k.shots),0)}):b;};
const TPL=()=>Core.tpl(DOC,lock?lock.target:null);
const target=()=>lock?lock.target:DOC.targets[drill().target==='any'?'bullseye':drill().target];
const spread=()=>($('shotgun').checked||drill().shotgun)?(target().spread||settings.shotgunSpread):0;
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
  W=Math.min(video.videoWidth||640,1280);H=Math.round(W*video.videoHeight/video.videoWidth);view.width=W;view.height=H;$('camBtn').disabled=true;loop();
 }catch(e){$('status').textContent='Camera error: '+e.message+' (needs HTTPS + permission)';}};
function buildMask(){mask=new Uint8Array(W*H);const f=TPL().field,p=[[f.x,f.y],[f.x+f.w,f.y],[f.x+f.w,f.y+f.h],[f.x,f.y+f.h]].map(q=>Core.apply(lock.tgtToImg,{x:q[0],y:q[1]}));
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
  const d=drill();$('status').textContent=lock?(`Locked: ${lock.target.name} (${lock.target.code})`+(d.target!=='any'&&d.target!==lock.key&&!(d.targets||[]).includes(lock.key)?` ⚠ drill expects '${d.target}'`:'')):'Looking for 4 corner markers…';}
function onHit(h,now){const T=target(),d=drill();
  const exp=state.mode==='live'&&d.sequence?d.sequence[state.shots.length]:null;
  const p=lock?Core.apply(lock.imgToTgt,h):null,sc=p?Core.score(T,p,spread(),TPL(),exp):{zone:null,score:0};
  marks.push({x:h.x,y:h.y,t:now});if(marks.length>30)marks.shift();
  if(state.mode==='free'||state.mode==='live'){state.shots.push(Object.assign({},sc,{t:now,p,ooo:sc.outOfOrder}));tone(sc.noshoot||sc.bystander?300:1600,sc.noshoot||sc.bystander?200:40);render();
    if(state.mode==='live'&&state.shots.length>=d.shots&&(!d.compliant||(state.verbal||[]).length>=d.compliant.length))finish();}}
function poly(pts,col,dash){ctx.strokeStyle=col;ctx.setLineDash(dash||[]);ctx.beginPath();pts.forEach((q,i)=>{const r=Core.apply(lock.tgtToImg,q);i?ctx.lineTo(r.x,r.y):ctx.moveTo(r.x,r.y);});ctx.stroke();ctx.setLineDash([]);}
function draw(){if(lock){ctx.lineWidth=2;const tp=TPL(),f=tp.field,T=lock.target,g=spread();
   poly(Core.outline({shape:'rect',x:f.x,y:f.y,w:f.w,h:f.h}),'#29b6f6',[6,4]);
   for(const z of T.zones)if(z.kind!=='decor')poly(Core.outline(z,z.noGrow?0:g),z.kind==='noshoot'||z.kind==='bystander'?'rgba(255,255,255,.9)':'rgba(255,235,59,.75)');}
  for(const m of marks){ctx.fillStyle='#00e676';ctx.beginPath();ctx.arc(m.x,m.y,5,0,7);ctx.fill();}}
function render(){const s=Core.drillSummary(drill(),state.beep,state.shots);
  $('shots').innerHTML=state.shots.map((x,i)=>`<tr><td>${i+1}</td><td>${s.times[i].toFixed(2)}</td><td>${s.splits[i].toFixed(2)}</td><td>${x.bystander?'BYSTANDER +10s':x.hardcover?'HARD COVER':x.noshoot?(drill().scoring==='idpa'?'NON-THREAT':'NO-SHOOT'):x.ooo?x.zone+' (order)':(x.zone||'miss')}</td><td>${drill().scoring==='idpa'?(x.noshoot?'+5s':'-'+x.pd):x.score}</td></tr>`).join('');
  if(state.mode==='done'&&drill().scoring==='idpa'){const r=Core.idpaSummary(drill(),state.shots,s.total);
    $('big').textContent=`${drill().name||'Stage'}: raw ${r.raw.toFixed(2)}s + PD ${r.pd} + PE ${r.pe}×3 + HNT ${r.hnt}×5${r.fc!=null&&drill().scenario?` + no-command ${r.fc}×${drill().failCommand}`:''} = ${r.final.toFixed(2)}${r.wp?` + WRONG PERSON ${r.wp}×${drill().crowd.wrongPenalty||5}`:''}${r.ff?` + FRIENDLY FIRE ${r.ff}×10`:''}${r.bys?` + BYSTANDER ${r.bys}×10 · BACKSTOP FAILURE`:''}${r.fail?(r.ff?' · FAIL: friendly fire':' · FAIL: hostage hit'):''}`+(drill().scenario?` · calls: ${drill().text} · verbal at ${(state.verbal||[]).map(x=>x.toFixed(1)+'s').join(', ')||'none'}`:'');}
  else if(state.mode==='done')$('big').textContent=`${s.score}/${s.maxScore} pts · ${s.total!=null?s.total.toFixed(2)+'s':'—'} ${s.underPar?'✅ under par':'❌ over par/incomplete'}`;}
function reset(){clearTimeout(state.timer);clearTimeout(state.par);state={mode:'idle',shots:[],beep:0};if(typeof Voice!=='undefined')Voice.resume();marks=[];$('shots').innerHTML='';$('big').textContent='';}
$('goBtn').onclick=()=>{ac.resume();reset();const d=drill();if(!lock){$('big').textContent='No target lock yet';return;}
  if(d.target!=='any'&&lock.key!==d.target&&!(d.targets||[]).includes(lock.key)){$('big').textContent=`Put up target ${DOC.targets[d.target].code} (${DOC.targets[d.target].name})`;return;}
  if(sel().type==='course'&&course.idx>=sel().stages.length){course={idx:0,results:[]};showNotes();}
  state.mode='wait';$('big').textContent='Stand by…';
  if(d.scenario){state.calls=Core.makeScenario(d.scenario,Math.random);state.verbal=[];$('big').textContent='Stand by…';}
  if(d.crowd){state.calls=Core.crowdCalls(lock.target,d.crowd,Math.random);$('big').textContent='BOLO: '+state.calls.text;
    say(state.calls.callList.map((k,i)=>'Call '+(i+1)+'. '+k.say).join('. '),true);}
  if(d.calls){state.calls=Core.makeCalls(d.calls,Math.random,d.randomize);$('big').textContent='CALLS: '+state.calls.text;
    try{speechSynthesis.speak(new SpeechSynthesisUtterance(state.calls.callList.map(k=>k.say||(k.group.replace('T','Target ')+(k.parts?' Mozambique':''))).join(', ')));}catch(e){}}const delay=(d.startDelay[0]+Math.random()*(d.startDelay[1]-d.startDelay[0]))*1000;
  state.timer=setTimeout(()=>{if(d.scenario)Voice.verbalMode();else Voice.pause();state.mode='live';state.beep=performance.now();tone(2200,250);
    if(d.scenario){$('big').textContent='GO · '+state.calls.text;setTimeout(()=>say(state.calls.speech,true),250);}$('big').textContent='GO'+(state.calls?' · '+state.calls.text:'');
    state.par=setTimeout(()=>tone(900,300),d.parTime*1000);state.timer=setTimeout(finish,d.timeout*1000);},delay);};
$('freeBtn').onclick=()=>{ac.resume();reset();state.mode='free';state.beep=performance.now();$('big').textContent='Free fire';};
$('stopBtn').onclick=()=>{Voice.resume();if(state.mode==='idle'&&sel().type==='course'){course={idx:0,results:[]};showNotes();}if(state.mode==='live'||state.mode==='free')finish();else reset();};
function onVerbal(txt,now){if(state.mode!=='live'||!drill().scenario)return;const t=(now-state.beep)/1000;state.verbal.push(t);tone(1200,60);
  $('heard').textContent=`verbal @${t.toFixed(2)}s: "${txt.trim()}"`;state.shots.push({t:now,zone:'VERBAL',verbal:true});render();state.shots.pop();
  const d=drill();if(state.shots.length>=d.shots&&state.verbal.length>=d.compliant.length)finish();}
function finish(){clearTimeout(state.timer);clearTimeout(state.par);const was=state.mode;state.mode='done';render();
  lastSay=spokenResult();if(was==='live'||was==='free')setTimeout(()=>{say(lastSay);Voice.resume();},400);else Voice.resume();
  const c=sel();if(c.type==='course'&&was==='live'){const d=drill(),s=Core.drillSummary(d,state.beep,state.shots),r=Core.idpaSummary(d,state.shots,s.total);
    course.results.push(Object.assign({name:d.name},r));course.idx++;
    if(course.idx>=c.stages.length){const tot=course.results.reduce((a,r)=>a+r.final,0);$('big').textContent+=` · COURSE TOTAL ${tot.toFixed(2)}s`;}
    else $('big').textContent+=` · Next: ${c.stages[course.idx].name}`;showNotes();
    if(course.idx>=c.stages.length)lastSay+=`. Course total ${course.results.reduce((a,r)=>a+r.final,0).toFixed(2)} seconds.`;}}
// ---- results by voice
let lastSay='No result yet.';
function say(t,keepListening){try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.rate=1.05;if(!keepListening)Voice.mute(true);u.onend=u.onerror=()=>setTimeout(()=>Voice.mute(false),500);speechSynthesis.speak(u);}catch(e){}}
function spokenResult(){const d=drill(),s=Core.drillSummary(d,state.beep,state.shots);
  if(d.scoring==='idpa'){const r=Core.idpaSummary(d,state.shots,s.total);return `Final ${r.final.toFixed(2)} seconds. Raw ${r.raw.toFixed(2)}, ${r.pd} down`+(r.pe?`, ${r.pe} procedural`:'')+(r.hnt?`, ${r.hnt} non-threat hits`:'')+(d.scenario&&r.fc?`, ${r.fc} missed commands`:'')+(r.wp?`. ${r.wp} wrong person hit${r.wp>1?'s':''}`:'')+(r.ff?`. Friendly fire, ${r.ff} hit${r.ff>1?'s':''} on the officer, plus ${10*r.ff} seconds`:'')+(r.bys?`. Backstop failure, ${r.bys} bystander hit${r.bys>1?'s':''}, plus ${10*r.bys} seconds`:'')+(r.fail?'. Fail, hostage hit':'')+'.';}
  return `${s.score} of ${s.maxScore} points`+(s.total!=null?`, ${s.total.toFixed(2)} seconds`:'')+(s.underPar?', under par.':'.');}
// ---- commands (voice, big buttons, media keys)
const CMD={start:()=>{if(state.mode==='wait'||state.mode==='live')return;$('goBtn').onclick();},
  stop:()=>{$('stopBtn').onclick();},
  reset:()=>{reset();if(sel().type==='course'){course={idx:0,results:[]};showNotes();}$('big').textContent='Reset';say('Reset');},
  next:()=>{reset();const c=sel();if(c.type==='course'&&course.idx<c.stages.length-1){course.idx++;showNotes();say('Next: '+drill().name);}else say('No next stage');},
  repeat:()=>{const c=sel();if(state.mode==='wait'||state.mode==='live')return;if(c.type==='course'&&course.results.length&&course.idx>0){course.idx--;course.results.pop();showNotes();}$('goBtn').onclick();},
  score:()=>say(lastSay)};
function command(cmd,src){if(!CMD[cmd])return;$('heard').textContent=`${src}: ${cmd}`;CMD[cmd]();}
document.querySelectorAll('[data-cmd]').forEach(b=>b.onclick=()=>{ac.resume();command(b.dataset.cmd,'tap');});
document.addEventListener('keydown',e=>{if(e.target&&/INPUT|SELECT/.test(e.target.tagName))return;
  const k=e.key,m={MediaPlayPause:'toggle',MediaPlay:'start',MediaStop:'stop',MediaPause:'stop',MediaTrackNext:'next',MediaTrackPrevious:'repeat',Enter:'toggle',' ':'toggle'};
  if(!m[k])return;e.preventDefault();ac.resume();const c=m[k]==='toggle'?((state.mode==='live'||state.mode==='wait'||state.mode==='free')?'stop':'start'):m[k];command(c,'key '+k);});
try{if('mediaSession'in navigator){navigator.mediaSession.setActionHandler('play',()=>command('start','media'));navigator.mediaSession.setActionHandler('pause',()=>command('stop','media'));
  navigator.mediaSession.setActionHandler('nexttrack',()=>command('next','media'));navigator.mediaSession.setActionHandler('previoustrack',()=>command('repeat','media'));}}catch(e){}
// Continuous, wake-word-free listening with auto-restart. While a drill is LIVE app commands are ignored
// (normal drills: recognition is stopped; scenario drills: only verbal de-escalation phrases are accepted).
const Voice={on:false,paused:false,verbal:false,muted:false,rec:null,
  init(){const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR){$('micBtn').disabled=true;$('micBtn').textContent='🎤 n/a';return;}
    const r=this.rec=new SR();r.continuous=true;r.interimResults=true;r.lang=navigator.language||'en-US';r.maxAlternatives=3;
    r.onresult=e=>{if(this.paused||this.muted)return;const now=performance.now();
      for(let i=e.resultIndex;i<e.results.length;i++){const res=e.results[i];
        if(state.mode==='live'){if(!this.verbal||res.verbalDone)continue;for(const alt of res)if(Core.isVerbal(alt.transcript)){res.verbalDone=true;onVerbal(alt.transcript,now);break;}continue;}
        if(!res.isFinal)continue;
        for(const alt of res){const c=Core.parseCommand(alt.transcript);if(c){command(c,'voice "'+alt.transcript.trim()+'"');return;}}
        $('heard').textContent='heard: '+res[0].transcript;}};
    r.onerror=e=>{if(e.error==='not-allowed'||e.error==='service-not-allowed'){this.on=false;this.ui();$('heard').textContent='Mic blocked: allow microphone for this site';}
      else if(e.error==='network')$('heard').textContent='Speech recognition needs network on this device (retrying)';};
    r.onend=()=>{if(this.on&&!this.paused)setTimeout(()=>{try{this.rec.start();}catch(e){}},300);};},
  toggle(){if(!this.rec)return;this.on=!this.on;this.ui();if(this.on){this.paused=false;try{this.rec.start();}catch(e){}}else try{this.rec.abort();}catch(e){}},
  pause(){this.paused=true;this.verbal=false;if(this.rec&&this.on)try{this.rec.abort();}catch(e){}this.ui();},
  verbalMode(){this.verbal=true;this.paused=false;this.ui();},
  resume(){this.verbal=false;if(!this.paused){this.ui();return;}this.paused=false;if(this.rec&&this.on)try{this.rec.start();}catch(e){}this.ui();},
  mute(v){this.muted=v;},
  ui(){const b=$('micBtn');if(!b)return;b.classList.toggle('on',this.on);b.textContent=!this.on?'🎤 Voice off':this.paused?'🎤 paused (live)':this.verbal?'🎤 verbal only':'🎤 listening';}};
Voice.init();$('micBtn').onclick=()=>{ac.resume();Voice.toggle();};
init();

// Viewfinder display settings (display only; detection always uses the full-res canvas buffer).
const VF={get(){try{return Object.assign({h:45,hide:false,min:false},JSON.parse(localStorage.getItem('ld.vf')||'{}'))}catch(e){return{h:45,hide:false,min:false}}},
 set(p){const v=Object.assign(VF.get(),p);localStorage.setItem('ld.vf',JSON.stringify(v));VF.apply();},
 apply(){const v=VF.get();document.documentElement.style.setProperty('--vf',v.h);$('vfRange').value=v.h;$('vfVal').textContent=v.h;$('vfHide').checked=v.hide;$('vfMin').checked=v.min;
  document.body.classList.toggle('vfmin',v.min||(v.hide&&state.mode==='live'));}};
$('vfBtn').onclick=()=>$('vfset').classList.toggle('hidden');
$('vfRange').oninput=e=>VF.set({h:+e.target.value});
document.querySelectorAll('[data-vf]').forEach(b=>b.onclick=()=>VF.set({h:+b.dataset.vf}));
$('vfHide').onchange=e=>VF.set({hide:e.target.checked});$('vfMin').onchange=e=>VF.set({min:e.target.checked});
{let lm;setInterval(()=>{if(state.mode!==lm){lm=state.mode;VF.apply();}},150);}
VF.apply();
