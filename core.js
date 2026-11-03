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
// markers: js-aruco Marker list; target: targets.json entry. Returns {imgToTgt, tgtToImg} or null.
Core.lockTarget=function(markers,target){
  const src=[],dst=[];
  for(const m of target.markers){const f=markers.find(k=>k.id===m.id);if(!f)return null;
    src.push(f.corners[m.corner]);
    const c=m.corner;dst.push({x:m.x+((c===1||c===2)?m.size:0),y:m.y+((c===2||c===3)?m.size:0)});}
  return {imgToTgt:Core.homography(src,dst),tgtToImg:Core.homography(dst,src),imgPts:src};
};
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
// Scoring; spread (inches) enlarges zones for shotgun mode.
Core.score=function(target,pt,spread){spread=spread||0;let best={zone:null,score:0};
  for(const z of target.zones){const d=Math.hypot(pt.x-z.cx,pt.y-z.cy);
    if(d<=z.r+spread&&z.score>best.score)best={zone:z.name,score:z.score,dist:d};}
  return best;};
Core.drillSummary=function(drill,beepT,shots){
  const times=shots.map(s=>(s.t-beepT)/1000),splits=times.map((t,i)=>i?t-times[i-1]:t);
  const total=times.length?times[times.length-1]:null,score=shots.reduce((a,s)=>a+s.score,0);
  return {times,splits,total,score,maxScore:drill.shots*5,par:drill.parTime,underPar:total!==null&&total<=drill.parTime&&shots.length===drill.shots};
};
if(typeof module!=='undefined')module.exports=Core;else root.Core=Core;
})(this);
