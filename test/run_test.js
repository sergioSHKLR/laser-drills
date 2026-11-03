const fs=require('fs'),vm=require('vm'),path=require('path');
const ctx={};vm.createContext(ctx);
for(const f of['cv.js','aruco.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../vendor',f),'utf8'),ctx);
const Core=require('../core.js'),T=require('../targets.json').bullseye,meta=require('./frames.json');
vm.runInContext('this.CV=CV;this.AR=AR;',ctx);
const det=new ctx.AR.Detector(),laser=new Core.LaserDetector();
let lock=null,hits=[],t=0,fail=0;
for(const name of meta.frames){const data=new Uint8ClampedArray(fs.readFileSync(path.join(__dirname,name+'.rgba')));
  const img={width:meta.w,height:meta.h,data};
  if(!lock){const m=det.detect(img);console.log('markers',m.map(k=>k.id));lock=Core.lockTarget(m,T);}
  const h=laser.process(data,meta.w,meta.h,t+=100);
  if(h&&lock){const p=Core.apply(lock.imgToTgt,h);hits.push({...p,...Core.score(T,p,0),sg:Core.score(T,p,1.5).score});}
}
if(!lock){console.log('FAIL no lock');process.exit(1);}
hits.forEach((h,i)=>{const e=meta.shots[i],err=Math.hypot(h.x-e[0],h.y-e[1]);if(err>0.25)fail++;
  console.log(`shot ${i+1}: expected (${e}) got (${h.x.toFixed(2)},${h.y.toFixed(2)}) err ${err.toFixed(2)}in zone ${h.zone} score ${h.score} shotgun ${h.sg}`);});
if(hits.length!==meta.shots.length)fail++;
console.log(fail?'FAIL':'PASS',hits.length,'hits');process.exit(fail?1:0);
