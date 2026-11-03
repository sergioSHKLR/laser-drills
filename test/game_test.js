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
console.log('GAME PASS');
