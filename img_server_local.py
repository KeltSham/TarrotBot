from http.server import HTTPServer, BaseHTTPRequestHandler
import os, threading, urllib.request, time, json

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
os.makedirs(OUT, exist_ok=True)

BASE = 'https://www.sacred-texts.com/tarot/pkt/img/'
SUITS = ['wa', 'cu', 'sw', 'pe']

def all_cards():
    cards = [f'ar{str(i).zfill(2)}.jpg' for i in range(22)]
    for s in SUITS:
        cards.append(f'{s}ac.jpg')
        for n in range(2, 11):
            cards.append(f'{s}{str(n).zfill(2)}.jpg')
        cards.extend([f'{s}pa.jpg', f'{s}kn.jpg', f'{s}qu.jpg', f'{s}ki.jpg'])
    return cards

_state = {'done': 0, 'total': 0, 'errors': [], 'log': [], 'finished': False}

def download_all():
    cards = all_cards()
    already = set(f for f in os.listdir(OUT) if f.endswith('.jpg') and os.path.getsize(os.path.join(OUT, f)) > 1000)
    todo = [c for c in cards if c not in already]
    _state['total'] = len(todo)
    _state['log'].append(f'Need {len(todo)} cards, {len(already)} already done')
    for fname in todo:
        for attempt in range(1, 4):
            try:
                url = BASE + fname
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = r.read()
                with open(os.path.join(OUT, fname), 'wb') as f:
                    f.write(data)
                _state['done'] += 1
                _state['log'].append(f'OK [{_state["done"]}/{_state["total"]}] {fname} ({len(data)} bytes)')
                print(f'OK {fname}', flush=True)
                break
            except Exception as e:
                if attempt == 3:
                    _state['errors'].append(fname)
                    _state['log'].append(f'FAILED {fname}: {e}')
                    print(f'FAILED {fname}: {e}', flush=True)
                else:
                    time.sleep(attempt)
        time.sleep(0.3)
    _state['finished'] = True
    print(f'Done! {_state["done"]} saved, {len(_state["errors"])} errors', flush=True)

PAGE = b"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Tarot Downloader</title>
<meta http-equiv="refresh" content="3">
</head>
<body style="font-family:sans-serif;padding:20px;background:#111;color:#eee">
<h2 id="title" style="color:#7cf">Tarot Card Downloader</h2>
<div id="bar" style="background:#333;border-radius:6px;height:24px;margin:12px 0">
  <div id="fill" style="height:24px;border-radius:6px;background:#4cf;transition:width .5s"></div>
</div>
<p id="status">Loading...</p>
<div id="log" style="font-family:monospace;font-size:11px;height:450px;overflow-y:auto;border:1px solid #333;padding:8px;background:#000"></div>
<script>
fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('status').textContent =
    d.finished ? ('Done! Saved: ' + d.done + (d.errors.length ? ', errors: ' + d.errors.join(', ') : ''))
               : ('Downloading... ' + d.done + '/' + d.total);
  const pct = d.total > 0 ? Math.round(d.done/d.total*100) : 0;
  document.getElementById('fill').style.width = pct + '%';
  document.getElementById('fill').textContent = pct + '%';
  document.getElementById('log').innerHTML = d.log.slice(-60).map(l =>
    '<span style="color:' + (l.startsWith('OK') ? '#4f4' : l.startsWith('FAIL') ? '#f44' : '#aaa') + '">' + l + '</span>'
  ).join('<br>');
  document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight;
  if (d.finished) {
    document.querySelector('meta[http-equiv]').remove();
    document.getElementById('title').style.color = '#4f4';
  }
});
</script>
</body></html>"""

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            body = json.dumps(_state).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(PAGE)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(PAGE)
    def log_message(self, fmt, *args): pass

print(f'Output: {OUT}', flush=True)
print('Server on http://localhost:8765', flush=True)

# Start downloading in background thread
t = threading.Thread(target=download_all, daemon=True)
t.start()

server = HTTPServer(('127.0.0.1', 8765), H)
server.serve_forever()
