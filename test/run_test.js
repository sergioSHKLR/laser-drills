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
 const pt={T1:[2.4,3.87],T2:[6.6,3.87],T3:[10.2,3.4],T4:[14.1,2.567],T5b:[2.4,7.52],T5h:[2.4,6.217],T7:[9.9,7.52],T8:[13.49,7.52]};
 const shots=c.order.map((g,i)=>sc(g==='T5'?(c.parts[i]==='head'?{x:pt.T5h[0],y:pt.T5h[1]}:{x:pt.T5b[0],y:pt.T5b[1]}):{x:pt[g][0],y:pt[g][1]}));
 const r1=Core.idpaSummary(Object.assign({},st,c),shots,10);
 const bad=shots.slice();const i5=c.order.indexOf('T5');[bad[i5],bad[i5+2]]=[bad[i5+2],bad[i5]];// head first
 const r2=Core.idpaSummary(Object.assign({},st,c),bad,10);
 const ok=ok1&&r1.pe===0&&r2.pe===1&&r2.final===r1.final+3;if(!ok)fail++;
 console.log('[calls] order',c.order.join(','),'clean',JSON.stringify(r1),'mozambique-swapped',JSON.stringify(r2),ok?'ok':'FAIL');}
console.log(fail?`FAIL (${fail})`:'PASS');process.exit(fail?1:0);
