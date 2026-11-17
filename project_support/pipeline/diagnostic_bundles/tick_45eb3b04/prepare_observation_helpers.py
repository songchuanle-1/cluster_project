"""Rebind readonly observation to the current owned foreground tick."""
from pathlib import Path
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_509e9191'
EXPECTED={'token':'45eb3b045c6243518d56eade38d5cd17','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
 'generated_at':'2026-10-26T04:52:30.746713+00:00','deadline_at':'2026-10-26T05:52:30.746713+00:00',
 'context_sha256':'4e63c8bb12f2e9573fd51d46fb0d585743728517ad3b506cbc97a36cdd0025c3',
 'pending_sha256':'b4cc5fc4dd9fd75f8396fc6a13965c537ee21a860bf2b8529e2077acc2067b2c'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
 assert {k:owner.get(k) for k in EXPECTED}==EXPECTED and os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 previous={'token':'509e919168b1426b8ebfab88075116e2','generated_at':'2026-10-26T04:11:37.612490+00:00','deadline_at':'2026-10-26T05:11:37.612490+00:00',
 'context_sha256':'44050aa4a1004dbe8124ae02fe45f7b6ce0d748696c62f42491cf00cdf25c8a7','pending_sha256':'813ed2630fe189a4d0a6e84d9aaacdd26b1a8896d724535e95ab7eaebc4dd4f8'}
 data=(OLD/'anchor_bfc_packet.py').read_bytes()
 for key,before in previous.items():
  assert data.count(before.encode())==1;data=data.replace(before.encode(),EXPECTED[key].encode())
 ast.parse(data)
 with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
 from anchor_bfc_packet import guard
 guard();items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(OLD/'anchor_bfc_packet.py'),'current_sha256':sha(HERE/'anchor_bfc_packet.py'),'change':'Only five current owner/snapshot constants; no permissions/protocol changes.'}]
 for name in ['observe_active_runs.py','verify_protected_assets_v3.py']:
  data=(OLD/name).read_bytes();ast.parse(data)
  with (HERE/name).open('xb') as f:f.write(data)
  items.append({'file':name,'source_sha256':sha(OLD/name),'current_sha256':sha(HERE/name),'change':'Exact byte copy, current guard/private output; readonly only.'})
 with (HERE/'readonly_helper_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 print(json.dumps({'current_owner_guard':True,'readonly_helpers':2,'native_resources':'NOT_RUN'}))
if __name__=='__main__':main()
