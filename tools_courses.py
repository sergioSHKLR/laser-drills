# Builds courses.json: original laser-adapted courses (not copies of any program's materials).
import json
B=lambda shots,par,to=None,sd=(2,4):{"shots":shots,"parTime":par,"timeout":to or max(10,int(par*3)),"startDelay":list(sd)}
def st(name,drill,brief,dist,set_=None,pas=None,**ov):
    s={"name":name,"drill":drill,"brief":brief,"dist":dist,"set":dict(set_ or {},**ov),"pass":pas or {}}
    return s
IDPA={"scoring":"idpa","maxPerShot":0}
C=[]
# --- Qualification ranks (NRA-style progression, original standards)
ranks=[("Pro-Marksman",60,1.25,"medal"),("Marksman",70,1.0,"award"),("Sharpshooter",78,0.85,"crosshair"),("Expert",85,0.72,"trophy"),("Distinguished Expert",92,0.6,"crown")]
prev=None
for i,(n,pct,k,ic) in enumerate(ranks):
    cid="qual-"+n.lower().replace(" ","-")
    C.append({"id":cid,"group":"qual","name":f"Qualification: {n}","badge":n,"icon":ic,"requires":prev,
     "notes":f"Rank {i+1} of 5 in a progressive marksmanship ladder (inspired by NRA-style qualification ranks; original laser standards). Pass every stage at {pct}% or better. Repeat stages as often as you like; your best run counts.",
     "stages":[
      st("Slow fire, bullseye","five-shot-par","5 shots, precision, no time pressure.","5 yd real / 2.5 yd laser",B(5,round(20*k,1),40),{"minPct":pct}),
      st("Timed fire, bullseye","five-shot-par","5 shots inside the par.","5 yd / 2.5 yd laser",B(5,round(10*k,1),25),{"minPct":pct-5,"maxTime":round(10*k,1)}),
      st("Rapid fire, silhouette","five-shot-par","5 shots to the body A zone.","7 yd / 3.5 yd laser",dict(B(5,round(6*k,1),20),target="silhouette"),{"minPct":pct-10,"maxTime":round(6*k,1)}),
      st("Dot sequence","dot-sequence","Dots 1→5 in order.","3 yd / 1.5 yd laser",B(5,round(12*k,1),30),{"minPct":pct,"maxTime":round(12*k,1)})]})
    prev=cid
# --- Basic Pistol-style fundamentals
C.append({"id":"fund-basic","group":"fund","name":"Pistol Fundamentals (Basic Pistol-style)","badge":"Fundamentals","icon":"target",
 "notes":"Grip, sight alignment, trigger press. Group shooting at four scaled distances (inspired by NRA Basic Pistol-style range work; original content). Laser distance = half the standard distance on the Letter bullseye. Slow and clean beats fast.",
 "stages":[st(f"Group at {d} yd","five-shot-par",f"5-shot group, slow fire. Stand at {lz}.",f"{d} yd / {lz} laser",B(5,30,60),{"minPct":p}) for d,lz,p in [(3,"1.5 yd",80),(5,"2.5 yd",75),(7,"3.5 yd",70),(15,"7.5 yd",60)]]
  +[st("Trigger control: dots","dot-sequence","Dots in order, no time pressure. Focus on a surprise break.","3 yd / 1.5 yd laser",B(5,20,40),{"minPct":80})]})
# --- Defensive Pistol-style
C.append({"id":"def-pistol","group":"def","name":"Defensive Pistol (Defensive-course-style)","badge":"Defender","icon":"shield",
 "notes":"Draw from concealment, ankle draw from a kneel, movement and decision. Score at end (IDPA-style: raw time + 1 s per point down). Inspired by defensive pistol course themes; original stages. Say “start” to begin each stage.",
 "stages":[
  st("Draw to first shot","single-draw","From concealment: draw, 1 shot to body.","7 yd / 3.5 yd laser",B(1,2.0,8),{"minPct":60,"maxTime":2.0}),
  st("Draw, 2 to body","single-draw","Draw, 2 shots to the -0.","7 yd / 3.5 yd laser",dict(B(2,3.0,10),target="idpa-threat",**IDPA),{"maxFinal":4.0}),
  st("Ankle draw, kneeling","ankle-standing","Ankle draw, drop to a kneel behind cover, 2 to the called threat.","kneel at 2–3 yd",{},{"maxFinal":6.0,"noFail":True}),
  st("Move off the X","single-draw","Step laterally 1–2 steps at the beep, then draw and fire 2.","5 yd / 2.5 yd laser",dict(B(2,3.5,10),target="idpa-threat",**IDPA),{"maxFinal":5.0}),
  st("Shoot / don't-shoot","shoot-dont-shoot-letter","Engage only the threats; verbal command for compliant.","Letter landscape at 3 yd",{},{"maxFinal":18.0,"noFail":True}),
  st("Multiple threats","idpa-course:idpa-multi","2 each, left to right.","3 yd laser",{},{"maxFinal":10.0})]})
# --- Laser Academy-style originals
C.append({"id":"la-style","group":"la","name":"Reaction · Hunt · Eyes (Laser-Academy-style)","badge":"Quick Eyes","icon":"eye",
 "notes":"Original drills in the spirit of popular laser-trainer apps: reaction to the beep, hunting the called target, and eyes/decision drills. Inspired by Mantis Laser Academy-style drill types; no copied content.",
 "stages":[
  st("Reaction: single shot","five-shot-par","Random beep, 1 shot to the center.","3 yd laser",B(1,1.2,5,(2,6)),{"minPct":60,"maxTime":1.2}),
  st("Reaction: double tap","single-draw","From ready: 2 shots to body A.","3 yd laser",dict(B(2,1.6,6),),{"minPct":70,"maxTime":1.6}),
  st("Hunt: one attribute","crowd-l1","Find the described person, 2 shots.","3 yd laser",{},{"maxFinal":20.0}),
  st("Hunt: two attributes","crowd-l2","Harder description.","3 yd laser",{},{"maxFinal":28.0}),
  st("Eyes: friend or foe","fof-tape","Shoot only foes in the window. Completion stage: score is tracked.","3 yd laser",{},{}),
  st("Eyes: decision","mar-decision","Smuggler or civilian? Decide fast. Completion stage: score is tracked.","3 yd laser",{},{})]})
# --- Benchmarks
C+= [
 {"id":"bm-fbi","group":"bm","name":"FBI-style Qualification (laser)","badge":"Qualified","icon":"star","notes":"Original laser adaptation of a law-enforcement-style qualification: close, fast strings then longer, slower strings. Pass ≥ 80% on every stage.",
  "stages":[st("3 yd: 3 rounds","five-shot-par","Draw, 3 shots, strong hand.","3 yd / 1.5 yd laser",dict(B(3,3.0,10),target="silhouette"),{"minPct":80,"maxTime":3.0}),
   st("5 yd: 4 rounds","five-shot-par","Draw, 4 shots.","5 yd / 2.5 yd laser",dict(B(4,4.0,12),target="silhouette"),{"minPct":80,"maxTime":4.0}),
   st("7 yd: 6 rounds","five-shot-par","Draw, 6 shots.","7 yd / 3.5 yd laser",dict(B(6,6.0,15),target="silhouette"),{"minPct":80,"maxTime":6.0}),
   st("15 yd: 5 rounds","five-shot-par","Draw, 5 shots, slower.","15 yd / 7.5 yd laser",dict(B(5,10.0,20),target="silhouette"),{"minPct":80,"maxTime":10.0})]},
 {"id":"bm-bill","group":"bm","name":"Bill Drill","badge":"Bill Drill","icon":"zap","notes":"6 shots to the body A zone from the draw as fast as you can keep them in. Benchmark par 2.5 s.",
  "stages":[st("Bill Drill","single-draw","Draw, 6 shots to body A.","7 yd / 3.5 yd laser",B(6,2.5,10),{"minPct":80,"maxTime":2.5})]},
 {"id":"bm-elprez","group":"bm","name":"El Presidente (laser)","badge":"El Presidente","icon":"users","notes":"Original laser adaptation: turn from facing uprange, 2 each on three threats, simulated reload (rack/reset), 2 each again. Uses the 3-threat sheet.",
  "stages":[st("El Prez","idpa-course:idpa-multi","Start facing away. Turn, draw, 2-2-2, reset, 2-2-2.","3 yd laser (≈27 yd sim)",dict(shots=12,parTime=10.0,timeout=25),{"maxFinal":16.0})]},
 {"id":"bm-dot","group":"bm","name":"Dot Torture (laser)","badge":"Dot Torture","icon":"circle-dot","notes":"Original precision drill on the 5-dot sheet: repeated slow and fast sequences. Every shot must hit its dot in order.",
  "stages":[st(n,"dot-sequence",b,"3 yd / 1.5 yd laser",B(5,p,40),{"minPct":100,"maxTime":p}) for n,b,p in [("Slow sequence","Dots 1→5, slow.",20),("Draw sequence","Draw, dots 1→5.",12),("Fast sequence","Dots 1→5 fast.",8),("Speed sequence","Dots 1→5 under pressure.",6)]]},
 {"id":"bm-3sec","group":"bm","name":"3-Seconds-or-Less (laser)","badge":"Under 3","icon":"timer","notes":"Original adaptation of the classic 'three seconds or less' idea: every string must finish in 3 s or less with hits.",
  "stages":[st("Draw, 1 shot","single-draw","Draw, 1 to body.","3 yd laser",B(1,3.0,8),{"minPct":60,"maxTime":3.0}),
   st("Draw, 2 shots","single-draw","Draw, 2 to body.","3 yd laser",B(2,3.0,8),{"minPct":60,"maxTime":3.0}),
   st("Ready, 3 shots","single-draw","From ready, 3 to body.","3 yd laser",B(3,3.0,8),{"minPct":60,"maxTime":3.0}),
   st("Head shot","single-draw","Draw, 1 to the head box.","3 yd laser",B(1,3.0,8),{"minPct":100,"maxTime":3.0}),
   st("Ankle draw, 1 shot","ankle-standing","Ankle draw to kneel, 2 shots.","kneel 2–3 yd",{"parTime":3.0},{"maxTime":3.0,"noFail":True})]},
 {"id":"bm-core","group":"bm","name":"Core Skills (laser)","badge":"Core Skills","icon":"puzzle","notes":"Original skills test in the spirit of instructor 'core skills' assessments: draw, accuracy, pairs, head shot, and a multi-threat string. Pass every stage.",
  "stages":[st("Draw, 1","single-draw","Draw, 1 to body A.","5 yd / 2.5 yd laser",B(1,1.8,6),{"minPct":80,"maxTime":1.8}),
   st("Pair","single-draw","Draw, 2 to body A.","5 yd / 2.5 yd laser",B(2,2.3,8),{"minPct":80,"maxTime":2.3}),
   st("Precision","five-shot-par","5 shots to the bullseye.","7 yd / 3.5 yd laser",B(5,8.0,20),{"minPct":80,"maxTime":8.0}),
   st("Head","hostage-head","2 head shots, hostage present.","5 yd / 2.5 yd laser",{},{"minPct":80,"maxTime":3.0}),
   st("Multi-threat","idpa-course:idpa-multi","2 each left to right.","3 yd laser",{},{"maxFinal":8.0})]},
 {"id":"bm-5x5","group":"bm","name":"5×5 (laser)","badge":"5×5","icon":"hand","notes":"Original take on the 5×5 idea: 5 shots, 5 seconds, one small circle. Use the center ring of the bullseye; anything not 5 pts is a miss.",
  "stages":[st("5×5","five-shot-par","5 shots in 5 s, center ring only.","5 yd / 2.5 yd laser",B(5,5.0,15),{"minPct":100,"maxTime":5.0})]},
]
json.dump(C,open("courses.json","w"),indent=1,ensure_ascii=False)
print(len(C),"courses",sum(len(c["stages"]) for c in C),"stages")
