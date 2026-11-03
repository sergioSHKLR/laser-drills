// Laser Drills UI shell: tabs/router, gallery, drill picker, results history. Uses globals from app.js.
const UI={view:'home',tf:null,dc:'training',chips:new Set(),cat:[],gS:{},rr:1};
const esc=s=>String(s==null?'':s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const VIEWS=['home','drills','shoot','results','settings','calibrate'];
UI.go=v=>{if(location.hash!=='#'+v)location.hash=v;else UI.route();};
UI.route=()=>{let v=location.hash.slice(1);if(!VIEWS.includes(v))v='home';UI.view=v;
  VIEWS.forEach(x=>$('v-'+x).classList.toggle('hidden',x!==v));
  document.querySelectorAll('#nav [data-v]').forEach(b=>b.classList.toggle('on',b.dataset.v===(v==='calibrate'?'settings':v)));
  $('tab-cal').classList.toggle('hidden',v!=='calibrate');
  const st=$('stage');if(v==='calibrate')$('calStage').appendChild(st);else if(st.parentNode.id==='calStage')$('v-shoot').children[1].prepend(st);
  if(v==='drills')UI.drawDrills();if(v==='results')UI.drawResults();$('v-'+v).scrollTop=0;};
window.addEventListener('hashchange',UI.route);
document.querySelectorAll('#nav [data-v]').forEach(b=>b.onclick=()=>UI.go(b.dataset.v));
$('v-shoot').classList.add('wide');
UI.cam=on=>{const p=$('homeCam');p.textContent=on?'● Camera on':'● Camera off';p.className='pill '+(on?'ok':'warn');};
// ---- sheet
UI.sheet=html=>{$('sheet').innerHTML='<div class=grab></div>'+html;$('sheet').classList.remove('hidden');$('scrim').classList.remove('hidden');};
UI.close=()=>{$('sheet').classList.add('hidden');$('scrim').classList.add('hidden');};$('scrim').onclick=UI.close;
// ---- gallery (data from targets/catalog.json, built by gen_assets.py)
const GF=[['category','Category',[['themed','Themed'],['tactical','Tactical'],['fun','Fun'],['self-defense','Self-Defense']]],['paper','Paper',[['letter','Letter'],['tabloid','Tabloid 17x11']]],
 ['people','People',[['single','Single'],['multi','Multi'],['none','No people']]],
 ['features','Features',[['hostage','Hostage'],['no-shoot','No-shoot'],['hard cover','Hard cover'],['backstop','Backstop'],['two-hit','Two-hit'],['conditional','Conditional'],['head-only','Head-only']]],
 ['weapon','Weapon',[['pistol','Pistol'],['shotgun','Shotgun']]]];
GF.forEach(([k,l,o])=>{UI.gS[k]=new Set();const r=document.createElement('div');r.className='chips';r.innerHTML='<b>'+l+'</b>';
  o.forEach(([v,t])=>{const b=document.createElement('button');b.className='chip';b.textContent=t;b.onclick=()=>{const s=UI.gS[k];s.has(v)?s.delete(v):s.add(v);b.classList.toggle('on');UI.drawGallery();};r.appendChild(b);});$('gf').appendChild(r);});
function gOk(c){const q=$('gq').value.trim().toLowerCase();if(q&&!q.split(/\s+/).every(w=>c.text.includes(w)))return false;
  for(const[k]of GF){const s=UI.gS[k];if(!s.size)continue;if(k==='features'){if(![...s].every(v=>c.features.includes(v)))return false;}else if(!s.has(c[k]))return false;}return true;}
UI.drawGallery=()=>{const L=UI.cat.filter(gOk);$('gN').textContent=L.length+' of '+UI.cat.length;
  $('grid').innerHTML=L.map(c=>`<button class=tcard data-k="${esc(c.k)}"><img loading=lazy src="targets/${esc(c.k)}-letter.png" alt=""><div class=b><div class=n>${esc(c.name)}</div><div class=c>${esc(c.code)} · ${esc(c.dist)}</div><span class=tag>${esc(c.category)}</span><span class=tag>${esc(c.paper)}</span>${c.features.slice(0,2).map(f=>'<span class=tag>'+esc(f)+'</span>').join('')}</div></button>`).join('');
  $('grid').querySelectorAll('.tcard').forEach(b=>b.onclick=()=>UI.target(b.dataset.k));};
$('gq').oninput=UI.drawGallery;
const drillsFor=k=>DRILLS.map((d,i)=>[d,i]).filter(([d])=>d.target===k||(d.targets||[]).includes(k)||(d.stages||[]).some(s=>s.target===k));
UI.target=k=>{const c=UI.cat.find(x=>x.k===k);if(!c)return;const n=drillsFor(k).length;
  UI.sheet(`<div style="display:flex;gap:14px;align-items:flex-start"><img src="targets/${esc(k)}-letter.png" style="width:46%;border-radius:12px;background:#fff"><div><h2 style="font-size:19px;margin:0 0 4px">${esc(c.name)}</h2><div class=muted>${esc(c.code)} · ${esc(c.paper)}<br>${esc(c.dist)}</div>${[c.category,c.people,c.weapon,...c.features].map(t=>'<span class=tag>'+esc(t)+'</span>').join('')}</div></div>
  <p class=muted>${esc(c.text.split(' ').slice(0,0).join(''))}</p>
  <div class=row><a class="btn" style="display:flex;align-items:center;justify-content:center;background:var(--s2);border:1px solid var(--bd);text-decoration:none;color:var(--tx)" href="targets/${esc(k)}-letter.pdf">⤓ Target PDF</a><a class="btn" style="display:flex;align-items:center;justify-content:center;background:var(--s2);border:1px solid var(--bd);text-decoration:none;color:var(--tx)" href="targets/${esc(k)}-mask.pdf">⤓ Mask PDF</a></div>
  <div class=muted style="text-align:center;margin:8px 0"><a href="targets/${esc(k)}-mask.png">Mask PNG</a></div>
  <button class="btn go" style="width:100%" id="shTgt" ${n?'':'disabled'}>◎ ${n?`Shoot a drill on this target (${n})`:'No drills for this target yet'}</button>`);
  $('shTgt').onclick=()=>{UI.close();UI.tf=k;const f=drillsFor(k)[0];if(f){UI.dc=f[0].type==='course'?'course':(f[0].category||'training');}UI.go('drills');};};
// ---- drills
const thumb=d=>{const k=d.target&&d.target!=='any'?d.target:(d.targets||[])[0]||((d.stages||[])[0]||{}).target||'bullseye';return k;};
const dcat=d=>d.type==='course'?'course':(d.category||'training');
UI.drawDrills=()=>{if(!DRILLS)return;document.querySelectorAll('#dseg button').forEach(b=>b.classList.toggle('on',b.dataset.c===UI.dc));
  const ch=[];if(UI.tf)ch.push(['tf','Target: '+((UI.cat.find(c=>c.k===UI.tf)||{}).name||UI.tf)+' ✕',true]);if(lock)ch.push(['lock','Matches locked target',UI.chips.has('lock')]);
  ch.push(['letter','Letter',UI.chips.has('letter')],['tabloid','Tabloid',UI.chips.has('tabloid')],['shotgun','Shotgun',UI.chips.has('shotgun')]);
  $('dchips').innerHTML=ch.map(([k,t,on])=>`<button class="chip${on?' on':''}" data-k="${k}">${esc(t)}</button>`).join('');
  $('dchips').querySelectorAll('button').forEach(b=>b.onclick=()=>{const k=b.dataset.k;if(k==='tf')UI.tf=null;else UI.chips.has(k)?UI.chips.delete(k):UI.chips.add(k);UI.drawDrills();});
  const q=$('dq').value.trim().toLowerCase(),cur=+$('drillSel').value;
  const L=DRILLS.map((d,i)=>[d,i]).filter(([d])=>{const t=thumb(d),tab=/tabloid/.test(t)||/tabloid/i.test(d.name);
    if(dcat(d)!==UI.dc)return false;if(q&&!(d.name+' '+(d.notes||'')).toLowerCase().includes(q))return false;
    if(UI.tf&&!drillsFor(UI.tf).some(([,j])=>j===DRILLS.indexOf(d)))return false;
    if(UI.chips.has('lock')&&lock&&!drillsFor(lock.key).some(([x])=>x===d)&&d.target!=='any')return false;
    if(UI.chips.has('letter')&&tab)return false;if(UI.chips.has('tabloid')&&!tab)return false;if(UI.chips.has('shotgun')&&!d.shotgun)return false;return true;});
  $('dlist').innerHTML=L.length?L.map(([d,i])=>{const b=Core.scoreAtEnd(d.type==='course'?{category:'training'}:d,SAE);const s=d.type==='course'?`${d.stages.length} stages`:`${d.shots||'?'} shots · par ${d.parTime}s`;
    return `<button class="drow${i===cur?' sel':''}" data-i="${i}"><img loading=lazy src="targets/${esc(thumb(d))}-letter.png" alt="" onerror="this.style.visibility='hidden'"><div class=t><b>${esc(d.name)}</b><span>${esc(s)}</span></div><span class="badge${b?'':' live'}">${b?'Score at end':'Live'}</span></button>`;}).join(''):'<p class=muted>No drills match.</p>';
  $('dlist').querySelectorAll('.drow').forEach(b=>b.onclick=()=>{$('drillSel').value=b.dataset.i;$('drillSel').onchange();UI.drawDrills();});
  $('dShoot').textContent='◎ Shoot “'+sel().name+'”';};
document.querySelectorAll('#dseg button').forEach(b=>b.onclick=()=>{UI.dc=b.dataset.c;UI.drawDrills();});$('dq').oninput=UI.drawDrills;
UI.onDrill=()=>{if(!DRILLS)return;const c=sel(),d=drill();$('dName').textContent=c.type==='course'?`${c.name} · ${d.name}`:c.name;const b=blind();$('saeBadge').textContent=b?'Score at end':'Live';$('saeBadge').className='badge'+(b?'':' live');
  $('shootH').textContent='Shoot';if(UI.view==='drills')UI.drawDrills();};
// ---- shoot state (START/STOP swap, lock pill)
setInterval(()=>{const busy=['wait','live','free'].includes(state.mode);$('goBtn').classList.toggle('hidden',busy);$('freeBtn').classList.toggle('hidden',busy);$('stopBtn').classList.toggle('hidden',!busy);
  const l=lock?`● Locked ${lock.target.code}`:'No target locked';if($('drLock').textContent!==l){$('drLock').textContent=l;$('drLock').className='pill'+(lock?' ok':'');}
  $('status').className='pill'+(lock?' ok':'');},200);
// ---- results history
const HK='ld.history';const hist=()=>{try{return JSON.parse(localStorage.getItem(HK)||'[]');}catch(e){return[];}};
UI.record=()=>{try{const c=sel(),d=drill(),s=Core.drillSummary(d,state.beep,state.shots),r={ts:Date.now(),drill:c.type==='course'?`${c.name} · ${d.name}`:c.name,cat:dcat(c),shots:state.shots.length,
    time:s.total!=null?+s.total.toFixed(2):null,score:s.score,max:s.maxScore,blind:blind()};
  if(d.scoring==='idpa'){const x=Core.idpaSummary(d,state.shots,s.total);Object.assign(r,{final:+x.final.toFixed(2),raw:+x.raw.toFixed(2),pd:x.pd,pe:x.pe,hnt:x.hnt,fail:x.fail});}
  if(d.game&&state.game)r.game=state.game.summary||'';
  const h=hist();h.push(r);while(h.length>1000)h.shift();localStorage.setItem(HK,JSON.stringify(h));}catch(e){console.warn(e);}};
const val=r=>r.final!=null?r.final:r.time;const fmt=r=>r.final!=null?r.final.toFixed(2)+' s':r.game!=null?(r.score+' pts'):r.time!=null?`${r.score}/${r.max} · ${r.time.toFixed(2)}s`:`${r.score}/${r.max}`;
UI.drawResults=()=>{document.querySelectorAll('#rseg button').forEach(b=>b.classList.toggle('on',+b.dataset.r===UI.rr));
  const now=Date.now(),day=new Date();day.setHours(0,0,0,0);const from=UI.rr===1?day.getTime():UI.rr?now-UI.rr*864e5:0;
  const L=hist().filter(r=>r.ts>=from).reverse();if(!L.length){$('rbody').innerHTML='<div class=card><div class=muted>No runs yet in this range. Finished drill strings are saved here automatically (on this device).</div></div>';return;}
  const name=L[0].drill,same=hist().filter(r=>r.drill===name&&val(r)!=null&&!r.game),best=same.length?same.reduce((a,r)=>val(r)<val(a)?r:a):null;
  let svg='';const pts=same.slice(-20).map(val);if(pts.length>1){const mx=Math.max(...pts),mn=Math.min(...pts),w=340,hh=70;svg=`<svg viewBox="0 0 ${w} ${hh+10}" style="width:100%;height:80px"><polyline fill=none stroke="#8ab4f8" stroke-width=3 points="${pts.map((v,i)=>`${(i/(pts.length-1)*w).toFixed(1)},${(5+(mx===mn?hh/2:(v-mn)/(mx-mn)*hh)).toFixed(1)}`).join(' ')}"/></svg><div class=muted>Last ${pts.length} runs · lower is better (higher on chart = slower)</div>`;}
  $('rbody').innerHTML=`<div class=card><div class=muted>${esc(name)} · ${same.length} timed run${same.length===1?'':'s'}</div><div class=big2>${best?'Best '+esc(fmt(best)):'—'}</div>${svg}</div>`+
   L.map(r=>`<div class=drow style="min-height:64px"><div class=t><b>${esc(r.drill)}</b><span>${new Date(r.ts).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}${r.pd!=null?` · PD ${r.pd} · PE ${r.pe} · HNT ${r.hnt}`:''}${r.fail?' · FAIL':''}${r.game?' · '+esc(r.game):''}</span></div><b style="font-size:17px;flex:none">${esc(fmt(r))}</b></div>`).join('');};
document.querySelectorAll('#rseg button').forEach(b=>b.onclick=()=>{UI.rr=+b.dataset.r;UI.drawResults();});
$('csvBtn').onclick=()=>{const h=hist(),K=['ts','drill','cat','shots','time','score','max','final','raw','pd','pe','hnt','fail','game','blind'];
  const q=v=>v==null?'':/[",\n]/.test(String(v))?'"'+String(v).replace(/"/g,'""')+'"':String(v);
  const csv=[['date',...K.slice(1)].join(',')].concat(h.map(r=>[new Date(r.ts).toISOString(),...K.slice(1).map(k=>q(r[k]))].join(','))).join('\n');
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='laser-drills-history.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('clrHist').onclick=()=>{if(confirm('Clear all run history on this device?')){localStorage.removeItem(HK);UI.drawResults();}};
// ---- boot (wait for app.js init to load DRILLS)
fetch('targets/catalog.json').then(r=>r.json()).then(c=>{UI.cat=c;UI.drawGallery();}).catch(()=>{$('gN').textContent='offline';});
(function wait(){if(typeof DRILLS!=='undefined'&&DRILLS&&$('drillSel').options.length){UI.onDrill();UI.route();}else setTimeout(wait,50);})();
if(!/zones=/.test(location.hash))UI.route();
