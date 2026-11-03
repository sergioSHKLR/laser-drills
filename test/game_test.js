const C=require('../core.js'),assert=require('assert');let seed=1;const R=()=>(seed=(seed*16807)%2147483647)/2147483647;
assert.equal(C.pokerRank(['AS','KS','QS','JS','TS']).name,'Royal flush');assert.equal(C.pokerRank(['2H','2D','2C','KS','KH']).name,'Full house');
assert.equal(C.pokerRank(['AH','2D','3C','4S','5H']).name,'Straight');assert.equal(C.pokerRank(['9H','9D','4C','4S','KH']).name,'Two pair');assert.equal(C.pokerRank(['2H','7D','9C','JS','KH']).name,'High card');
const f=C.placeFleet(8,8,[{name:'carrier',len:4},{name:'cruiser',len:3},{name:'sub',len:2}],R),all=f.flatMap(x=>x.cells);assert.equal(new Set(all).size,9);
// battle: shoot every cell
const T={zones:[]};for(let r=0;r<8;r++)for(let c=0;c<8;c++)T.zones.push({name:String.fromCharCode(65+r)+(c+1),kind:'score'});
const g=C.gameStart({type:'battle',rows:8,cols:8,ships:[{name:'carrier',len:4},{name:'sub',len:2}]},T,R);for(const z of T.zones){if(g.done)break;C.gameShot(g,T,{zone:z.name,score:1});}assert(g.done);
// callouts w/ forbid
const T2={zones:[{name:'P1',kind:'score',group:'P1',tags:['white']},{name:'P2',kind:'score',group:'P2',tags:['blue']}]};
const s=C.gameStart({type:'calls',calls:[{say:'engage white',tags:['white'],forbid:['blue']}]},T2,R);let r=C.gameShot(s,T2,{zone:'P2',score:0});assert.equal(r.msg,'FRIENDLY FIRE');r=C.gameShot(s,T2,{zone:'P1',score:0});assert(s.done&&s.score===-20);
// headOnly vest
const T3={zones:[{name:'V head',kind:'score',shape:'circle',cx:1,cy:1,r:0.3,score:0,group:'V',headOnly:true},{name:'V body',kind:'score',shape:'rect',x:0,y:1.5,w:2,h:3,score:-3,group:'V'}]};
assert(C.score(T3,{x:1,y:3}).vestStrike);assert.equal(C.score(T3,{x:1,y:1}).zone,'V head');
// First Responders
{const p=C.frPlan(()=>0.5);assert(p.cmds.length>=2&&p.cmds[0].at>=1&&p.end>p.cmds.at(-1).at);
 let r=C.frScore({first:2,shots:[1.5],comply:3.2});assert.equal(r.late,0);assert.equal(r.comply,1.2);assert.equal(r.penalty,0);assert(!r.fail);
 r=C.frScore({first:2,shots:[2.5,4],comply:null});assert.equal(r.late,2);assert.equal(r.penalty,45);assert(r.fail);
 assert(C.FR_COMPLY.test("okay don't shoot"));assert(!C.FR_COMPLY.test('drop the weapon'));}
// history / firearms
{const old=[{ts:1,drill:'A',time:3},{ts:2,drill:'A',time:2.5,fw:'g1'}];const m=C.histMigrate(old);assert.equal(m[0].fw,'unassigned');assert(m[0].id&&m[1].id!==m[0].id);
 const ex=C.histExport(old,[{id:'g1',name:'LCP II'}]);const rt=C.histImport([],[],JSON.stringify(ex),'replace');assert.equal(rt.runs.length,2);assert.equal(rt.firearms[0].name,'LCP II');
 const mg=C.histImport(m,[{id:'g1',name:'LCP II'}],ex,'merge');assert.equal(mg.added,0);assert.equal(mg.skipped,2);assert.equal(mg.firearms.length,1);
 const mg2=C.histImport(m,[],{runs:[{ts:5,drill:'B',time:4}]},'merge');assert.equal(mg2.added,1);assert.equal(mg2.runs.length,3);
 assert.throws(()=>C.histImport([],[],'{oops','merge'),/Not valid JSON/);assert.throws(()=>C.histImport([],[],{foo:1},'merge'),/missing "runs"/);
 assert.throws(()=>C.histImport([],[],{runs:[{ts:'x'}]},'merge'),/rejected/);
 const st=C.fwStats([{time:4},{time:3.5},{time:3},{time:2.5,fail:true},{game:'x',score:5}]);assert.equal(st.best.time,2.5);assert.equal(st.timed,4);assert(st.trend<0);assert.equal(st.fails,1);}
console.log('GAME PASS');
