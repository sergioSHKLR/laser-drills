// Laser Drills UI shell: tabs/router, gallery, drill picker, results history. Uses globals from app.js.
const UI={view:'home',tf:null,dc:'training',chips:new Set(),cat:[],gS:{},rr:1};
const esc=s=>String(s==null?'':s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const VIEWS=['home','drills','courses','shoot','results','settings','calibrate'];
UI.go=v=>{if(location.hash!=='#'+v)location.hash=v;else UI.route();};
UI.route=()=>{let v=location.hash.slice(1);if(!VIEWS.includes(v))v='home';UI.view=v;
  VIEWS.forEach(x=>$('v-'+x).classList.toggle('hidden',x!==v));
  document.querySelectorAll('#nav [data-v]').forEach(b=>b.classList.toggle('on',b.dataset.v===(v==='calibrate'?'settings':v==='courses'?'drills':v)));
  $('tab-cal').classList.toggle('hidden',v!=='calibrate');
  const st=$('stage');if(v==='calibrate')$('calStage').appendChild(st);else if(st.parentNode.id==='calStage')$('v-shoot').children[1].prepend(st);
  if(v==='drills')UI.drawDrills();if(v==='courses')UI.drawCourses();if(v==='results')UI.drawResults();$('v-'+v).scrollTop=0;};
window.addEventListener('hashchange',UI.route);
document.querySelectorAll('#nav [data-v]').forEach(b=>b.onclick=()=>UI.go(b.dataset.v));
$('v-shoot').classList.add('wide');
UI.cam=on=>{const p=$('homeCam');p.innerHTML=I(on?'camera':'camera-off')+(on?' Camera on':' Camera off');p.className='pill '+(on?'ok':'warn');};
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
  <div class=row><a class="btn" style="display:flex;align-items:center;justify-content:center;background:var(--s2);border:1px solid var(--bd);text-decoration:none;color:var(--tx)" href="targets/${esc(k)}-letter.pdf"><svg class=ic><use href="#i-file-down"/></svg> Target PDF</a><a class="btn" style="display:flex;align-items:center;justify-content:center;background:var(--s2);border:1px solid var(--bd);text-decoration:none;color:var(--tx)" href="targets/${esc(k)}-mask.pdf"><svg class=ic><use href="#i-file-down"/></svg> Mask PDF</a></div>
  <div class=muted style="text-align:center;margin:8px 0"><a href="targets/${esc(k)}-mask.png">Mask PNG</a></div>
  <button class="btn go" style="width:100%" id="shTgt" ${n?'':'disabled'}>${I('crosshair')} ${n?`Shoot a drill on this target (${n})`:'No drills for this target yet'}</button>`);
  $('shTgt').onclick=()=>{UI.close();UI.tf=k;const f=drillsFor(k)[0];if(f){UI.dc=f[0].type==='course'?'course':(f[0].category||'training');}UI.go('drills');};};
// ---- drills
const thumb=d=>{const k=d.target&&d.target!=='any'?d.target:(d.targets||[])[0]||((d.stages||[])[0]||{}).target||'bullseye';return k;};
const dcat=d=>d.type==='course'?'course':(d.category||'training');
UI.drawDrills=()=>{if(!DRILLS)return;document.querySelectorAll('#dseg button').forEach(b=>b.classList.toggle('on',b.dataset.c===UI.dc));
  const ch=[];if(UI.tf)ch.push(['tf','Target: '+((UI.cat.find(c=>c.k===UI.tf)||{}).name||UI.tf),true,'x']);if(lock)ch.push(['lock','Matches locked target',UI.chips.has('lock')]);
  ch.push(['letter','Letter',UI.chips.has('letter')],['tabloid','Tabloid',UI.chips.has('tabloid')],['shotgun','Shotgun',UI.chips.has('shotgun')]);
  $('dchips').innerHTML=ch.map(([k,t,on,ic])=>`<button class="chip${on?' on':''}" data-k="${k}">${esc(t)}${ic?' '+I(ic):''}</button>`).join('');
  $('dchips').querySelectorAll('button').forEach(b=>b.onclick=()=>{const k=b.dataset.k;if(k==='tf')UI.tf=null;else UI.chips.has(k)?UI.chips.delete(k):UI.chips.add(k);UI.drawDrills();});
  const q=$('dq').value.trim().toLowerCase(),cur=+$('drillSel').value;
  const L=DRILLS.map((d,i)=>[d,i]).filter(([d])=>{const t=thumb(d),tab=/tabloid/.test(t)||/tabloid/i.test(d.name);
    if(d.hidden||dcat(d)!==UI.dc)return false;if(q&&!(d.name+' '+(d.notes||'')).toLowerCase().includes(q))return false;
    if(UI.tf&&!drillsFor(UI.tf).some(([,j])=>j===DRILLS.indexOf(d)))return false;
    if(UI.chips.has('lock')&&lock&&!drillsFor(lock.key).some(([x])=>x===d)&&d.target!=='any')return false;
    if(UI.chips.has('letter')&&tab)return false;if(UI.chips.has('tabloid')&&!tab)return false;if(UI.chips.has('shotgun')&&!d.shotgun)return false;return true;});
  $('dlist').innerHTML=L.length?L.map(([d,i])=>{const b=Core.scoreAtEnd(d.type==='course'?{category:'training'}:d,SAE);const s=d.type==='course'?`${d.stages.length} stages`:`${d.shots||'?'} shots · par ${d.parTime}s`;
    return `<button class="drow${i===cur?' sel':''}" data-i="${i}"><img loading=lazy src="targets/${esc(thumb(d))}-letter.png" alt="" onerror="this.style.visibility='hidden'"><div class=t><b>${esc(d.name)}</b><span>${esc(s)}</span></div><span class="badge${b?'':' live'}">${b?'Score at end':'Live'}</span></button>`;}).join(''):'<p class=muted>No drills match.</p>';
  $('dlist').querySelectorAll('.drow').forEach(b=>b.onclick=()=>{$('drillSel').value=b.dataset.i;$('drillSel').onchange();UI.drawDrills();});
  $('dShoot').innerHTML=I('crosshair')+' Shoot “'+esc(sel().name)+'”';};
document.querySelectorAll('#dseg button').forEach(b=>b.onclick=()=>{UI.dc=b.dataset.c;UI.drawDrills();});$('dq').oninput=UI.drawDrills;
UI.onDrill=()=>{if(!DRILLS)return;const c=sel(),d=drill();$('dName').textContent=c.type==='course'?`${c.name} · ${d.name}`:c.name;const b=blind();$('saeBadge').textContent=b?'Score at end':'Live';$('saeBadge').className='badge'+(b?'':' live');
  $('shootH').textContent='Shoot';if(UI.view==='drills')UI.drawDrills();};
// ---- shoot state (START/STOP swap, lock pill)
setInterval(()=>{const busy=['wait','live','free','fr'].includes(state.mode);$('goBtn').classList.toggle('hidden',busy);$('freeBtn').classList.toggle('hidden',busy);$('stopBtn').classList.toggle('hidden',!busy);
  const l=lock?`Locked ${lock.target.code}`:'No target locked';if($('drLock').textContent.trim()!==l){$('drLock').innerHTML=(lock?I('lock')+' ':'')+l;$('drLock').className='pill'+(lock?' ok':'');}
  $('status').className='pill'+(lock?' ok':'');},200);
// ---- results history
const HK='ld.history',FK='ld.firearms',AK='ld.fw';
const saveHist=h=>localStorage.setItem(HK,JSON.stringify(h));
const hist=()=>{try{return JSON.parse(localStorage.getItem(HK)||'[]');}catch(e){return[];}};
// one-time migration: give every run an id and assign legacy runs to 'Unassigned'
(()=>{const h=hist();if(h.some(r=>!r.id||!r.fw))saveHist(Core.histMigrate(h));})();
const fws=()=>{try{return JSON.parse(localStorage.getItem(FK)||'[]');}catch(e){return[];}};const saveFws=f=>localStorage.setItem(FK,JSON.stringify(f));
const activeFw=()=>{const a=localStorage.getItem(AK);return fws().some(f=>f.id===a)?a:Core.UNASSIGNED;};
const fwName=id=>id===Core.UNASSIGNED||!id?'Unassigned':((fws().find(f=>f.id===id)||{}).name||'Deleted firearm');
const dl=(txt,type,name)=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([txt],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
UI.setFw=id=>{localStorage.setItem(AK,id);const f=fws().find(x=>x.id===id);if(f&&$('shotgun').checked!==(f.type==='shotgun')){$('shotgun').checked=f.type==='shotgun';$('shotgun').dispatchEvent(new Event('change'));}UI.drawFwPick();};
UI.drawFwPick=()=>{const a=activeFw(),L=[{id:Core.UNASSIGNED,name:'Unassigned'}].concat(fws());
  $('fwPick').innerHTML='<b>Firearm</b>'+L.map(f=>`<button class="chip${f.id===a?' on':''}" data-fw="${esc(f.id)}">${f.id===Core.UNASSIGNED?'—':I('target')+' '}${esc(f.name)}${f.suppressor?' · S':''}</button>`).join('')+'<button class="chip" data-fw="+" aria-label="Add firearm">'+I('plus')+'</button>';
  $('fwPick').querySelectorAll('[data-fw]').forEach(b=>b.onclick=()=>{if(b.dataset.fw==='+')UI.editFw(null);else UI.setFw(b.dataset.fw);});};
UI.drawFwList=()=>{const L=fws(),h=hist();$('fwList').innerHTML=L.length?L.map(f=>`<button class="drow" data-ed="${esc(f.id)}" style="min-height:60px"><div class=t><b>${esc(f.name)}</b><span>${esc([f.type,f.caliber,f.optic,f.suppressor&&('suppressor: '+f.suppressor)].filter(Boolean).join(' · '))} · ${h.filter(r=>r.fw===f.id).length} runs</span></div>${I('chevron-right')}</button>`).join(''):'<div class="muted" style="padding:6px 4px">No firearms yet. Runs are saved as “Unassigned”.</div>';
  $('fwList').querySelectorAll('[data-ed]').forEach(b=>b.onclick=()=>UI.editFw(b.dataset.ed));};
UI.editFw=id=>{const f=fws().find(x=>x.id===id)||{type:'pistol'};UI.fwEd=id;$('fwDlgH').textContent=id?'Edit firearm':'Add firearm';
  [['fwName','name'],['fwType','type'],['fwCal','caliber'],['fwOptic','optic'],['fwSup','suppressor'],['fwNotes','notes']].forEach(([e,k])=>$(e).value=f[k]||(k==='type'?'pistol':''));
  $('fwErr').textContent='';$('fwDel').classList.toggle('hidden',!id);$('fwDlg').showModal();};
$('fwAdd').onclick=()=>UI.editFw(null);$('fwNo').onclick=()=>$('fwDlg').close();
$('fwSave').onclick=()=>{const n=$('fwName').value.trim();if(!n){$('fwErr').textContent='Name is required.';return;}
  const L=fws(),rec={id:UI.fwEd||('fw'+Date.now().toString(36)),name:n,type:$('fwType').value,caliber:$('fwCal').value.trim(),optic:$('fwOptic').value.trim(),suppressor:$('fwSup').value.trim(),notes:$('fwNotes').value.trim()};
  const i=L.findIndex(x=>x.id===rec.id);if(i>=0)L[i]=rec;else L.push(rec);saveFws(L);if(!UI.fwEd)localStorage.setItem(AK,rec.id);$('fwDlg').close();UI.drawFwList();UI.drawFwPick();};
$('fwDel').onclick=()=>{const id=UI.fwEd,n=hist().filter(r=>r.fw===id).length;if(!confirm(`Delete this firearm? Its ${n} run(s) are kept and moved to Unassigned.`))return;
  saveFws(fws().filter(f=>f.id!==id));saveHist(hist().map(r=>r.fw===id?Object.assign(r,{fw:Core.UNASSIGNED}):r));if(localStorage.getItem(AK)===id)localStorage.removeItem(AK);$('fwDlg').close();UI.drawFwList();UI.drawFwPick();};
UI.record=()=>{try{const c=sel(),d=drill(),s=Core.drillSummary(d,state.beep,state.shots),r={ts:Date.now(),drill:c.type==='course'?`${c.name} · ${d.name}`:c.courseId?`${(COURSES.find(x=>x.id===c.courseId)||{}).name} · ${c.name}`:c.name,cat:dcat(c),shots:state.shots.length,
    time:s.total!=null?+s.total.toFixed(2):null,score:s.score,max:s.maxScore,blind:blind(),fw:activeFw()};r.id='r'+r.ts.toString(36)+Math.random().toString(36).slice(2,6);
  if(d.scoring==='idpa'){const x=Core.idpaSummary(d,state.shots,s.total);Object.assign(r,{final:+x.final.toFixed(2),raw:+x.raw.toFixed(2),pd:x.pd,pe:x.pe,hnt:x.hnt,fail:x.fail});}
  if(d.game&&state.game)r.game=state.game.summary||'';
  if(state.fr&&state.fr.res){const f=state.fr.res;r.fr=f.fail?'FAIL':f.comply!=null?'OK':'NC';r.frLate=f.late;r.frComply=f.comply;if(r.final!=null)r.final=+(r.final+f.penalty).toFixed(2);else r.frPen=f.penalty;if(f.fail)r.fail=true;}
  if(c.courseId){const C=COURSES.find(x=>x.id===c.courseId),S=C&&C.stages[c.stage];r.course=c.courseId;r.stage=c.stage;
    r.pass=Core.stagePass(S&&S.pass,r,(d.calls||d.crowd||d.scenario)?0:d.shots);UI.lastStage={pass:r.pass,c:C,i:c.stage};
    setTimeout(()=>{$('big').textContent+=r.pass?' · STAGE PASSED':' · stage not passed ('+Core.passText(S.pass)+')';},60);
    setTimeout(()=>{try{say(r.pass?'Stage passed':'Stage not passed');}catch(e){}},2600);}
  const h=hist();h.push(r);while(h.length>5000)h.shift();saveHist(h);}catch(e){console.warn(e);}};
const val=r=>r.final!=null?r.final:r.time;const fmt=r=>r.final!=null?r.final.toFixed(2)+' s':r.game!=null?(r.score+' pts'):r.time!=null?`${r.score!=null?r.score+'/'+r.max+' · ':''}${r.time.toFixed(2)}s`:`${r.score}/${r.max}`;
UI.drawResults=()=>{document.querySelectorAll('#rseg button').forEach(b=>b.classList.toggle('on',+b.dataset.r===UI.rr));
  const now=Date.now(),day=new Date();day.setHours(0,0,0,0);const from=UI.rr===1?day.getTime():UI.rr?now-UI.rr*864e5:0;
  const all=hist(),used=new Set(all.map(r=>r.fw)),FL=[{id:Core.UNASSIGNED,name:'Unassigned'}].concat(fws()).filter(f=>used.has(f.id)||f.id!==Core.UNASSIGNED);
  if(UI.rf&&UI.rf!=='all'&&!FL.some(f=>f.id===UI.rf))UI.rf='all';const rf=UI.rf||'all',H=rf==='all'?all:all.filter(r=>r.fw===rf);
  $('rfw').innerHTML='<b>Firearm</b>'+[{id:'all',name:'All'}].concat(FL).map(f=>`<button class="chip${f.id===rf?' on':''}" data-rf="${esc(f.id)}">${esc(f.name)}</button>`).join('');
  $('rfw').querySelectorAll('[data-rf]').forEach(b=>b.onclick=()=>{UI.rf=b.dataset.rf;UI.drawResults();});
  const L=H.filter(r=>r.ts>=from).reverse();if(!L.length){$('rbody').innerHTML='<div class=card><div class=muted>No runs yet in this range. Finished drill strings are saved here automatically (on this device).</div></div>';return;}
  const name=L[0].drill,same=H.filter(r=>r.drill===name&&val(r)!=null&&!r.game),best=same.length?same.reduce((a,r)=>val(r)<val(a)?r:a):null;
  let svg='';const pts=same.slice(-20).map(val);if(pts.length>1){const mx=Math.max(...pts),mn=Math.min(...pts),w=340,hh=70;svg=`<svg viewBox="0 0 ${w} ${hh+10}" style="width:100%;height:80px"><polyline fill=none stroke="#8ab4f8" stroke-width=3 points="${pts.map((v,i)=>`${(i/(pts.length-1)*w).toFixed(1)},${(5+(mx===mn?hh/2:(v-mn)/(mx-mn)*hh)).toFixed(1)}`).join(' ')}"/></svg><div class=muted>Last ${pts.length} runs · higher on chart = faster</div>`;}
  const st=Core.fwStats(H.filter(r=>r.drill===name)),fwCard=rf==='all'?'':`<div class=card><div class=muted>${I('target')} ${esc(fwName(rf))} · ${esc(name)}</div><div class=statg><div><b>${st.runs}</b>runs</div><div><b>${st.best?esc(fmt(st.best)):'—'}</b>best</div><div><b>${st.avg!=null?st.avg.toFixed(2)+'s':'—'}</b>avg</div><div><b>${st.trend==null?'—':(st.trend<=0?I('trending-down')+' ':I('trending-up')+' ')+Math.abs(st.trend).toFixed(2)+'s'}</b>trend</div></div><div class=muted style="margin-top:6px">${st.fails} fail(s) · trend = recent half vs earlier half (down = faster)</div></div>`;
  $('rbody').innerHTML=fwCard+`<div class=card><div class=muted>${esc(name)} · ${same.length} timed run${same.length===1?'':'s'}</div><div class=big2>${best?'Best '+esc(fmt(best)):'—'}</div>${svg}</div>`+
   L.map(r=>`<div class=drow style="min-height:64px"><div class=t><b>${esc(r.drill)}</b><span>${new Date(r.ts).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}${r.pd!=null?` · PD ${r.pd} · PE ${r.pe} · HNT ${r.hnt}`:''}${r.fr?` · ${I('siren')} FR ${r.fr==='OK'?'comply '+r.frComply.toFixed(2)+'s':r.fr==='FAIL'?r.frLate+' late shot(s)':'no comply'}`:''}${r.fail?' · FAIL':''}${r.game?' · '+esc(r.game):''}${rf==='all'?' · '+I('target')+' '+esc(fwName(r.fw)):''}</span></div><b style="font-size:17px;flex:none">${esc(fmt(r))}</b></div>`).join('');};
document.querySelectorAll('#rseg button').forEach(b=>b.onclick=()=>{UI.rr=+b.dataset.r;UI.drawResults();});
$('csvBtn').onclick=()=>{const h=hist(),K=['ts','drill','cat','shots','time','score','max','final','raw','pd','pe','hnt','fail','game','blind','fr','frLate','frComply','frPen','course','stage','pass','fw','firearm','id'];
  const q=v=>v==null?'':/[",\n]/.test(String(v))?'"'+String(v).replace(/"/g,'""')+'"':String(v);
  const csv=[['date',...K.slice(1)].join(',')].concat(h.map(r=>[new Date(r.ts).toISOString(),...K.slice(1).map(k=>q(k==='firearm'?fwName(r.fw):r[k]))].join(','))).join('\n');
  dl(csv,'text/csv','laser-drills-history.csv');};
$('jsonBtn').onclick=()=>dl(JSON.stringify(Core.histExport(hist(),fws()),null,1),'application/json',`laser-drills-history-${new Date().toISOString().slice(0,10)}.json`);
$('impBtn').onclick=()=>{$('impMsg').innerHTML='';$('impFile').value='';$('impDlg').showModal();};$('impNo').onclick=()=>$('impDlg').close();
$('impYes').onclick=async()=>{const f=$('impFile').files[0],m=$('impMsg');if(!f){m.innerHTML='<div class=err>Choose a .json file first.</div>';return;}
  try{const txt=await f.text(),mode=$('impMode').value;if(mode==='replace'&&!confirm('Replace ALL current runs and firearms with this file?'))return;
    const r=Core.histImport(hist(),fws(),txt,mode);saveHist(r.runs);saveFws(r.firearms);
    m.innerHTML=`<div class=okm>Imported ${r.added} run(s)${r.skipped?`, skipped ${r.skipped} duplicate(s)`:''} · ${r.firearms.length} firearm(s).</div>`;UI.drawResults();UI.drawFwList();UI.drawFwPick();}
  catch(e){m.innerHTML=`<div class=err>Import failed: ${esc(e.message)}</div>`;}};
$('clrHist').onclick=()=>{const h=hist(),opts=[['all',`All runs (${h.length})`]].concat([{id:Core.UNASSIGNED,name:'Unassigned'}].concat(fws()).map(f=>[f.id,`Only ${f.name} (${h.filter(r=>r.fw===f.id).length})`]));
  $('resetScope').innerHTML=opts.map(([v,t])=>`<option value="${esc(v)}">${esc(t)}</option>`).join('');if(UI.rf&&UI.rf!=='all')$('resetScope').value=UI.rf;$('resetInfo').textContent='';$('resetDlg').showModal();};
$('resetNo').onclick=()=>$('resetDlg').close();
$('resetYes').onclick=()=>{const s=$('resetScope').value,h=hist();saveHist(s==='all'?[]:h.filter(r=>r.fw!==s));$('resetDlg').close();UI.drawResults();UI.drawFwList();};
UI.drawFwPick();UI.drawFwList();
// ---- courses (courses.json; progress derived from history runs tagged course/stage/pass, per firearm)
let COURSES=[];UI.copen=UI.copen||{};
const CG=[['qual','Qualification ranks (NRA-style ladder)'],['fund','Fundamentals'],['def','Defensive'],['la','Reaction · Hunt · Eyes'],['bm','Benchmarks']];
UI.runStage=(cid,i)=>{const C=COURSES.find(x=>x.id===cid);if(!C)return;const d=Core.stageDrill(DRILLS,cid,i,C.stages[i]);if(!d){alert('Stage drill missing');return;}
  let k=DRILLS.findIndex(x=>x.id==='__cs');if(k<0){k=DRILLS.length;DRILLS.push(d);const o=new Option('Course stage',k);o.hidden=true;$('drillSel').appendChild(o);}else DRILLS[k]=d;
  $('drillSel').value=k;$('drillSel').onchange();UI.go('shoot');};
UI.drawCourses=()=>{const fw=activeFw(),P=Core.courseProgress(COURSES,hist(),fw);$('cFw').innerHTML=I('target')+' '+esc(fwName(fw));
  const E=COURSES.filter(c=>P[c.id].done);
  $('cBadges').innerHTML=`<div class=card><div class=muted>Badges · ${esc(fwName(fw))} · ${E.length}/${COURSES.length}</div><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px">${COURSES.map(c=>`<span class="tag" title="${esc(c.name)}" style="${P[c.id].done?'':'opacity:.35;filter:grayscale(1)'}">${I(c.icon)} ${esc(c.badge)}</span>`).join('')}</div><div class=muted style="margin-top:6px">Switch firearm in Shoot › Firearm to see its own progress.</div></div>`;
  $('cList').innerHTML=CG.map(([g,l])=>`<div class=sec-h>${esc(l)}</div>`+COURSES.filter(c=>c.group===g).map(c=>{const p=P[c.id],op=UI.copen[c.id];
    return `<div class=card style="padding:10px"><button class="drow" data-co="${esc(c.id)}" style="min-height:56px;width:100%"><div class=t><b>${I(c.icon)} ${esc(c.name)}</b><span>${p.locked?I('lock')+' Pass '+esc((COURSES.find(x=>x.id===c.requires)||{}).badge)+' first · ':''}${p.passed}/${p.total} stages${p.done?' · '+I('circle-check')+' '+new Date(p.earned).toLocaleDateString():''}</span></div>${I(op?'chevron-down':'chevron-right')}</button>
    ${op?`<div class=muted style="margin:6px 2px">${esc(c.notes)}</div>`+c.stages.map((s,i)=>{const q=p.stages[i];return `<div class=drow style="min-height:56px"><div class=t><b>${I(q.passed?'circle-check':'circle')} ${i+1}. ${esc(s.name)}</b><span>${esc(s.dist)} · pass ${esc(Core.passText(s.pass))}${q.runs?` · ${q.runs} run(s)${q.best!=null?' · best '+q.best.toFixed(2)+'s':''}`:''}</span></div><button class="chip" data-rs="${esc(c.id)}" data-i="${i}" ${p.locked?'disabled':''}>${I('play')} Shoot</button></div>`;}).join(''):''}</div>`;}).join('')).join('');
  $('cList').querySelectorAll('[data-co]').forEach(b=>b.onclick=()=>{UI.copen[b.dataset.co]=!UI.copen[b.dataset.co];UI.drawCourses();});
  $('cList').querySelectorAll('[data-rs]').forEach(b=>b.onclick=()=>UI.runStage(b.dataset.rs,+b.dataset.i));};
fetch('courses.json').then(r=>r.json()).then(c=>{COURSES=c;if(UI.view==='courses')UI.drawCourses();}).catch(()=>{});
// ---- boot (wait for app.js init to load DRILLS)
fetch('targets/catalog.json').then(r=>r.json()).then(c=>{UI.cat=c;UI.drawGallery();}).catch(()=>{$('gN').textContent='offline';});
(function wait(){if(typeof DRILLS!=='undefined'&&DRILLS&&$('drillSel').options.length){UI.onDrill();UI.route();}else setTimeout(wait,50);})();
if(!/zones=/.test(location.hash))UI.route();
