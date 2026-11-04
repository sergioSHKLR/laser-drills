#!/usr/bin/env python3
"""Stamp version.json for the Settings > About block.
Usage: python3 tools_version.py [X.Y.Z]   (default: keep current semver, start 1.0.0)
Fields: version (semver), build (now, America/Sao_Paulo), commit (short HEAD hash = source commit
being released), cache (service-worker cache name read from sw.js)."""
import json,re,subprocess,sys,datetime,os
from zoneinfo import ZoneInfo
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try: cur=json.load(open('version.json'))['version']
except Exception: cur='1.0.0'
ver=sys.argv[1] if len(sys.argv)>1 else cur
assert re.fullmatch(r'\d+\.\d+\.\d+',ver),'semver X.Y.Z'
commit=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip() or 'unknown'
cache=re.search(r"const C='([^']+)'",open('sw.js').read()).group(1)
build=datetime.datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%Y-%m-%d %H:%M')
v=dict(version=ver,build=build,commit=commit,cache=cache)
json.dump(v,open('version.json','w'),indent=1); open('version.json','a').write('\n'); print(v)
