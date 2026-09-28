import hashlib,json,time
from urllib.parse import urlparse,parse_qs
WATERMARK=":"
def now_ms(): return int(time.time()*1000)
def jb(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def sha(x): return hashlib.sha256(x if isinstance(x,bytes) else jb(x)).hexdigest()
def readj(h):
 n=int(h.headers.get('Content-Length','0') or 0); return json.loads(h.rfile.read(n).decode() or '{}')
def send(h,code,obj,ctype='application/json'):
 b=jb(obj) if ctype=='application/json' else obj.encode(); h.send_response(code); h.send_header('Content-Type',ctype);h.send_header('Content-Length',str(len(b)));h.send_header('Cache-Control','no-store');h.send_header('X-Content-Type-Options','nosniff');h.send_header('X-Frame-Options','DENY');h.end_headers();h.wfile.write(b)
def pq(h):
 u=urlparse(h.path);return u.path,parse_qs(u.query)
