"""Local GET-only preview of existing runtime responses. No credentials leave EC2."""
import json, shlex, subprocess, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
REMOTE = '''import sys,urllib.request
sys.path.insert(0,"/opt/stockanalysis/app/src")
from stockanalysis.operations.env_file import load_env_file_values
values=load_env_file_values("/opt/stockanalysis/runtime/frontend-api.env")
path=sys.stdin.read().strip()
request=urllib.request.Request("http://127.0.0.1:8787"+path,headers={"Authorization":"Bearer "+values['STOCKANALYSIS_FRONTEND_API_READ_TOKEN']})
with urllib.request.urlopen(request,timeout=25) as response: print(response.read().decode())
'''
cache={}
lock=threading.Lock()
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if not self.path.startswith(('/api/','/__admin/')):
   self.send_error(404);return
  with lock: result=cache.get(self.path)
  if result is None:
   try:
    r=subprocess.run(['ssh','-S','/private/tmp/stocka-model-live-20260910.sock','-i','/Users/woody/Downloads/settle.pem','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=8','ec2-user@3.211.40.142','python3 -c '+shlex.quote(REMOTE)],input=self.path,text=True,capture_output=True,timeout=32)
    if r.returncode: raise RuntimeError('read failed')
    result=json.dumps(json.loads(r.stdout),ensure_ascii=False).encode()
    with lock: cache[self.path]=result
   except Exception:
    self.send_error(502,'Runtime read unavailable');return
  self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(result)
 def log_message(self,fmt,*args): print(fmt % args,flush=True)
ThreadingHTTPServer(('127.0.0.1',18780),Handler).serve_forever()
