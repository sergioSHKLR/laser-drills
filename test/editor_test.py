# Headless UI test for editor.html: draw circle/rect/poly, move, handle-resize, rule panel, Delete, save, reset, share link -> app import.
import json,sys
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765/'
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1300,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(B+'editor.html?t=silhouette');pg.wait_for_timeout(1500)
    n0=pg.evaluate('zones.length');box=pg.locator('#cv').bounding_box()
    def at(x,y): return pg.evaluate(f'T({x},{y})')
    def drag(a,b2):
        pg.mouse.move(box['x']+a[0],box['y']+a[1]);pg.mouse.down();pg.mouse.move(box['x']+b2[0],box['y']+b2[1],steps=5);pg.mouse.up()
    pg.keyboard.press('r');drag(at(1,8.6),at(2,9.0))
    pg.keyboard.press('c');drag(at(7,3),at(7.4,3))
    pg.keyboard.press('p')
    for q in [(1,2.2),(2,2.2),(1.5,3)]: x,y=at(*q);pg.mouse.click(box['x']+x,box['y']+y)
    x,y=at(1.5,3);pg.mouse.dblclick(box['x']+x,box['y']+y)
    zs=pg.evaluate('zones');assert len(zs)>=n0+3,(len(zs),n0)
    new=zs[n0:];print('shapes',[z['shape'] for z in new])
    # move the circle and resize via its radius handle
    pg.evaluate(f'sel={n0+1};panel();redraw()');drag(at(7,3),at(7.5,3.5));c=pg.evaluate(f'zones[{n0+1}]');assert abs(c['cx']-7.5)<0.05,c
    drag(at(c['cx']+c['r'],c['cy']),at(c['cx']+1,c['cy']));c=pg.evaluate(f'zones[{n0+1}]');assert abs(c['r']-1)<0.05,c
    # rule via panel: rect = requires 3 shots
    pg.evaluate(f'sel={n0};panel()');pg.select_option('#fr','requires');pg.fill('#fnn','3');pg.dispatch_event('#fnn','change')
    r=pg.evaluate(f'zones[{n0}]');assert r['needs']==3 and r['kind']=='score',r
    # right-click circle -> No-hit
    x,y=at(7.5,3.5);pg.mouse.click(box['x']+x,box['y']+y,button='right');pg.click('#menu div[data-r=nohit]')
    assert pg.evaluate(f'zones[{n0+1}].kind')=='noshoot'
    # poly = sequence after the rect
    pg.evaluate(f'sel={n0+2};panel()');pg.select_option('#fr','sequence');pg.select_option('#faf',[r['name']])
    s=pg.evaluate(f'zones[{n0+2}]');assert s['after']==[r['name']],s
    pg.screenshot(path='/workspace/target-previews/editor-v14.png')
    # Delete key
    pg.evaluate(f'sel={n0+1};panel()');pg.locator('#cv').focus() if False else None;pg.mouse.move(box['x']+5,box['y']+5);pg.keyboard.press('Delete');assert pg.evaluate('zones.length')==len(zs)-1
    pg.click('#save');ov=json.loads(pg.evaluate("localStorage.getItem('ld-zones')"));assert 'silhouette' in ov
    pg.evaluate("navigator.clipboard.writeText=t=>{window._u=t;return Promise.resolve()}");pg.click('#share');pg.wait_for_timeout(200);u=pg.evaluate('window._u');
    pg.evaluate("localStorage.removeItem('ld-zones')")
    pg.on('dialog',lambda d:d.accept());pg.goto(u.replace('#','index.html#'));pg.wait_for_timeout(2500)
    ov2=json.loads(pg.evaluate("localStorage.getItem('ld-zones')")or'{}');assert len(ov2['silhouette']['zones'])==len(zs)-1
    pg.goto(B+'editor.html?t=silhouette');pg.wait_for_timeout(1000);pg.click('#reset');pg.wait_for_timeout(200)
    assert pg.evaluate('zones.length')==n0 and 'silhouette' not in json.loads(pg.evaluate("localStorage.getItem('ld-zones')"))
    assert not errs,errs;print('editor UI OK',len(u),'char link');b.close()
