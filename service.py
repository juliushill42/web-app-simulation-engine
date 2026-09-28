import argparse,copy,random,sys
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from shared.common import *
DEFAULT={'name':'counter-demo','initial':{'route':'/','state':{'count':0,'logged_in':False}},'actions':{'login':{'set':{'logged_in':True}},'increment':{'add':{'count':1}},'decrement':{'add':{'count':-1}},'settings':{'route':'/settings'}},'assertions':[{'path':'state.count','gte':0}]}
def dig(o,p):
 for x in p.split('.'):o=o[x]
 return o
class Engine:
 def run(self,spec,flow,seed=1,drop_rate=0):
  rng=random.Random(seed);ctx=copy.deepcopy(spec.get('initial',{}));events=[]
  for i,step in enumerate(flow):
   a=step['action'];cfg=spec.get('actions',{}).get(a)
   if cfg is None:return {'ok':False,'error':'unknown action '+a,'events':events,'context':ctx}
   dropped=rng.random()<float(drop_rate);ev={'seq':i+1,'action':a,'dropped':dropped,'before':copy.deepcopy(ctx)}
   if not dropped:
    for k,v in cfg.get('set',{}).items():ctx['state'][k]=v
    for k,v in cfg.get('add',{}).items():ctx['state'][k]=ctx['state'].get(k,0)+v
    if 'route' in cfg:ctx['route']=cfg['route']
   ev['after']=copy.deepcopy(ctx);ev['event_hash']=sha(ev);events.append(ev)
  checks=[];ok=True
  for a in spec.get('assertions',[]):
   v=dig(ctx,a['path']);passed=(v>=a['gte'] if 'gte' in a else True) and (v<=a['lte'] if 'lte' in a else True) and (v==a['eq'] if 'eq' in a else True);checks.append({'assertion':a,'value':v,'passed':passed});ok=ok and passed
  return {'ok':ok,'context':ctx,'events':events,'assertions':checks,'replay_hash':sha({'spec':spec,'flow':flow,'seed':seed,'events':events}),'watermark':WATERMARK}
ENG=Engine()
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  p,_=pq(self)
  if p=='/health':return send(self,200,{'ok':True,'service':'web-app-sim-engine','watermark':WATERMARK})
  if p=='/api/example':return send(self,200,DEFAULT)
  if p=='/':return send(self,200,HTML,'text/html; charset=utf-8')
  return send(self,404,{'error':'not_found'})
 def do_POST(self):
  try:
   p,_=pq(self);b=readj(self)
   if p=='/api/run':return send(self,200,ENG.run(b.get('spec',DEFAULT),b.get('flow',[]),int(b.get('seed',1)),b.get('drop_rate',0)))
   return send(self,404,{'error':'not_found'})
  except Exception as e:return send(self,400,{'error':str(e)})
HTML='''<!doctype html><meta charset=utf-8><title>Web App Simulation</title><style>body{font-family:system-ui;background:#080a0f;color:#eef;padding:24px}textarea,button{font:inherit;padding:9px;background:#111827;color:#fff;border:1px solid #34405a;border-radius:9px}textarea{width:90%}pre{white-space:pre-wrap}</style><h2>Web-App Simulation Engine :</h2><textarea id=f rows=5>[{"action":"login"},{"action":"increment"},{"action":"increment"},{"action":"settings"}]</textarea><br><button onclick=run()>RUN + REPLAY</button><pre id=o></pre><script>async function run(){let s=await fetch('/api/example').then(r=>r.json());o.textContent=JSON.stringify(await fetch('/api/run',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({spec:s,flow:JSON.parse(f.value),seed:7})}).then(r=>r.json()),null,2)}</script>'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8813);a=ap.parse_args();ThreadingHTTPServer(('127.0.0.1',a.port),H).serve_forever()
if __name__=='__main__':main()
