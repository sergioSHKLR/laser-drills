const fs=require('fs'),vm=require('vm'),path=require('path');
const ctx={};vm.createContext(ctx);
for(const f of['cv.js','aruco.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../vendor',f),'utf8'),ctx);
vm.runInContext('this.AR=AR',ctx);
const Core=require('../core.js'),DOC=require('../targets.json'),DR=require('../drills.json'),meta=require('./frames.json');
let fail=0;
for(const key in meta.sets){const set=meta.sets[key],det=new ctx.AR.Detector(),laser=new Core.LaserDetector();
  const seq=DR.find(d=>d.target===key&&d.sequence),shotgun=DR.find(d=>d.target===key&&d.shotgun);
  let lock=null,t=0,hits=[];
  for(const name of set.frames){const data=new Uint8ClampedArray(fs.readFileSync(path.join(__dirname,name+'.rgba')));
    if(!lock)lock=Core.lockTarget(det.detect({width:meta.w,height:meta.h,data}),DOC);
    const h=laser.process(data,meta.w,meta.h,t+=100);
    if(h&&lock){const p=Core.apply(lock.imgToTgt,h),n=hits.filter(x=>!x.control).length;
      hits.push({p,...Core.score(lock.target,p,shotgun?lock.target.spread:0,Core.tpl(DOC,lock.target),seq?seq.sequence[n]:null)});}}
  if(!lock||lock.key!==key){console.log(key,'FAIL lock',lock&&lock.key);fail++;continue;}
  console.log(`[${key}] locked as ${lock.key}`);
  set.shots.forEach((e,i)=>{const h=hits[i];if(!h){console.log(' shot',i+1,'MISSING');fail++;return;}
    const err=Math.hypot(h.p.x-e[0],h.p.y-e[1]),got=h.control?'CTRL':(typeof e[2]==='string'?(h.zone||'MISS'):h.score),ok=err<0.25&&got===e[2];if(!ok)fail++;
    console.log(` shot ${i+1}: (${e[0]},${e[1]}) err ${err.toFixed(2)}in -> ${got}${h.noshoot?' (no-shoot)':''}${h.outOfOrder?' (out of order)':''} expected ${e[2]} ${ok?'ok':'FAIL'}`);});
  if(key==='idpa-multi'){const st=DR.find(d=>d.id==='idpa-course').stages.find(s=>s.target==='idpa-multi'),r=Core.idpaSummary(st,hits,4.0);
    const ok=r.pe===1&&r.pd===15&&r.final===4+15+3;if(!ok)fail++;console.log(' idpa summary',JSON.stringify(r),ok?'ok':'FAIL');}
  if(key==='idpa-nonthreat'){const r=Core.idpaSummary({shots:2},hits,2.0);const ok=r.hnt===1&&r.pd===10&&r.final===17;if(!ok)fail++;console.log(' idpa summary',JSON.stringify(r),ok?'ok':'FAIL');}
  if(hits.length!==set.shots.length){console.log(' extra/missing hits',hits.length);fail++;}}
{const t=DOC.targets['idpa-all-tabloid'],st=DR.find(d=>d.id==='idpa-all-calls'),c=Core.makeCalls(st.calls,()=>0.5);
 const sc=q=>Core.score(t,q,0,Core.tpl(DOC,t));const m=c.callList.findIndex(k=>k.group==='T5');
 const ok1=c.shots===14&&new Set(c.order).size===7&&c.order.filter(g=>g==='T5').length===3;
 // shoot every call correctly at T-centre points; Mozambique body,body,head
 const pt={T1:[2.5,3.87],T2:[6.25,3.87],T3:[10.0,3.4],T4:[13.75,2.567],T5b:[2.5,7.52],T5h:[2.5,6.217],T7:[10.0,7.52],T8:[13.15,7.52]};
 const shots=c.order.map((g,i)=>sc(g==='T5'?(c.parts[i]==='head'?{x:pt.T5h[0],y:pt.T5h[1]}:{x:pt.T5b[0],y:pt.T5b[1]}):{x:pt[g][0],y:pt[g][1]}));
 const r1=Core.idpaSummary(Object.assign({},st,c),shots,10);
 const bad=shots.slice();const i5=c.order.indexOf('T5');[bad[i5],bad[i5+2]]=[bad[i5+2],bad[i5]];// head first
 const r2=Core.idpaSummary(Object.assign({},st,c),bad,10);
 const ok=ok1&&r1.pe===0&&r2.pe===1&&r2.final===r1.final+3;if(!ok)fail++;
 console.log('[calls] order',c.order.join(','),'clean',JSON.stringify(r1),'mozambique-swapped',JSON.stringify(r2),ok?'ok':'FAIL');}
{const P=Core.parseCommand,ex=[['start',"start"],['stand by please','start'],['Standby','start'],['okay stop','stop'],['reset','reset'],['next stage','next'],['repeat that','repeat'],['what is my score','score'],['restart the car',null],['bang',null]];
 for(const[t,e]of ex){const g=P(t);if(g!==e){fail++;console.log(' voice FAIL',t,g,e);}}
 const vb=[["Drop it!",true],["show me your hands",true],["Police, don't move!",true],["start",false],["pop pop",false]];
 for(const[t,e]of vb)if(Core.isVerbal(t)!==e){fail++;console.log(' verbal FAIL',t);}
 const st=DR.find(d=>d.id==='shoot-dont-shoot'),t=DOC.targets[st.target];let seed=7;const rnd=()=>((seed=seed*16807%2147483647)/2147483647);
 const c=Core.makeScenario(st.scenario,rnd);const ok1=c.compliant.length>=1&&c.order.length>=2&&c.shots===c.order.length;
 const pt={T1:[2.5,3.87],T2:[6.25,3.87],T3:[10.0,4.0],T4:[13.75,2.567],T5:[2.5,7.52],T7:[10.0,7.52],T8:[13.15,7.52]};
 const hit=g=>Core.score(t,{x:pt[g][0],y:pt[g][1]},0,Core.tpl(DOC,t));
 const good=c.order.map(hit),stg=Object.assign({},st,c);
 const r1=Core.idpaSummary(Object.assign({},stg,{verbalTimes:c.compliant.map(()=>1.2)}),good,6);
 const r2=Core.idpaSummary(Object.assign({},stg,{verbalTimes:[]}),good.concat([hit(c.compliant[0])]),6);
 const ok=ok1&&r1.fc===0&&r1.hnt===0&&r2.fc===c.compliant.length&&r2.hnt===1&&r2.final===r1.final+5+3*c.compliant.length;
 if(!ok)fail++;console.log('[voice+scenario] calls',c.text,'| clean',JSON.stringify(r1),'| shot compliant + no commands',JSON.stringify(r2),ok?'ok':'FAIL');}
{const r=Core.idpaSummary({shots:2},[{zone:'T1 -0',pd:0,group:'T1'},{zone:'BYSTANDER 1',bystander:true,pd:5}],3);
 console.log('[backstop]',JSON.stringify(r));if(!(r.bys===1&&r.backstop&&r.final===18)){console.log('FAIL backstop');fail++;}}
{const C=require('../core.js'),J=require('../targets.json').targets;let bad=0;
for(const k of ['crowd','crowd-tabloid'])for(const L of [1,2,3])for(let i=0;i<300;i++){const c=C.crowdCalls(J[k],{level:L,rounds:3,wrongPenalty:5},Math.random);
 if(c.callList.length!==3||c.shots!==6||c.callList.some(x=>!J[k].people.find(p=>p.group===x.group)))bad++;}
if(bad)throw new Error('crowd calls bad '+bad);console.log('[crowd] 1800 call sets OK');}
{// overlapping people: any point inside 2+ silhouettes must score for the front (highest z) person
 const C=require('../core.js'),J=require('../targets.json').targets;let n=0,bad=0;
 for(const k of ['crowd','crowd-tabloid','dh-nakatomi','idpa-multi']){const t=J[k],S=t.zones.filter(z=>z.sil);
  for(let x=0.4;x<16.6;x+=0.04)for(let y=1.8;y<9.3;y+=0.04){const ins=S.filter(z=>C.inZone(z,{x,y},0));if(ins.length<2)continue;n++;
   const top=ins.reduce((a,b)=>b.z>a.z?b:a),r=C.score(t,{x,y});if(r.group!==top.group)bad++;}}
 console.log(`[overlap] ${n} overlap points, ${bad} wrong owner`);if(bad||!n)fail++;}
{// friendly fire: Powell hit = +10 s and FAIL when failOnFriendly
 const t=DOC.targets['dh-lobby'],z=t.zones.find(z=>z.name==='POWELL FRIENDLY');const xs=z.pts.map(p=>p[0]),ys=z.pts.map(p=>p[1]);
 let q=null;for(let y=Math.min(...ys)+0.5;y<Math.max(...ys)&&!q;y+=0.1)for(let x=Math.min(...xs);x<Math.max(...xs);x+=0.1)if(Core.inZone(z,{x,y},0)){q={x,y};break;}
 const h=Core.score(t,q,0,Core.tpl(DOC,t)),st={shots:2,failOnFriendly:true};
 const c=Core.score(t,{x:DOC.targets['dh-lobby'].zones.find(z=>z.name==='T1 -0').cx,y:DOC.targets['dh-lobby'].zones.filter(z=>z.name==='T1 -0')[1].cy},0,Core.tpl(DOC,t));
 const r=Core.idpaSummary(Object.assign({},st,{failOnFriendly:true}),[c,c,h],3);const ok=h.friendly&&r.ff===1&&r.final>=13&&r.fail;
 if(!ok)fail++;console.log('[friendly]',JSON.stringify(h),JSON.stringify(r),ok?'ok':'FAIL');}
console.log(fail?`FAIL (${fail})`:'PASS');process.exit(fail?1:0);
