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
      hits.push({p,...Core.score(lock.target,p,shotgun?lock.target.spread:0,DOC.template,seq?seq.sequence[n]:null)});}}
  if(!lock||lock.key!==key){console.log(key,'FAIL lock',lock&&lock.key);fail++;continue;}
  console.log(`[${key}] locked as ${lock.key}`);
  set.shots.forEach((e,i)=>{const h=hits[i];if(!h){console.log(' shot',i+1,'MISSING');fail++;return;}
    const err=Math.hypot(h.p.x-e[0],h.p.y-e[1]),got=h.control?'CTRL':(typeof e[2]==='string'?(h.zone||'MISS'):h.score),ok=err<0.25&&got===e[2];if(!ok)fail++;
    console.log(` shot ${i+1}: (${e[0]},${e[1]}) err ${err.toFixed(2)}in -> ${got}${h.noshoot?' (no-shoot)':''}${h.outOfOrder?' (out of order)':''} expected ${e[2]} ${ok?'ok':'FAIL'}`);});
  if(key==='idpa-multi'){const st=DR.find(d=>d.id==='idpa-course').stages[4],r=Core.idpaSummary(st,hits,4.0);
    const ok=r.pe===1&&r.pd===15&&r.final===4+15+3;if(!ok)fail++;console.log(' idpa summary',JSON.stringify(r),ok?'ok':'FAIL');}
  if(key==='idpa-nonthreat'){const r=Core.idpaSummary({shots:2},hits,2.0);const ok=r.hnt===1&&r.pd===5&&r.final===12;if(!ok)fail++;console.log(' idpa summary',JSON.stringify(r),ok?'ok':'FAIL');}
  if(hits.length!==set.shots.length){console.log(' extra/missing hits',hits.length);fail++;}}
console.log(fail?`FAIL (${fail})`:'PASS');process.exit(fail?1:0);
