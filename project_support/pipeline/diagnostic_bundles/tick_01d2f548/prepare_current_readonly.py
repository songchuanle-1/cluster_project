"""Fresh-owner readonly helpers and NoTransport copy; original files stay frozen."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_150c2902'
EXPECTED={'token':'01d2f5482cb54841a4ca285805401771','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T14:05:55.958593+00:00','deadline_at':'2026-10-26T15:05:55.958593+00:00','context_sha256':'b1bac59eecb8a096a1aed1e3de83918efc646da544aec282ae1da7864c42155b','pending_sha256':'63b233bae64addd4b5527d144c41c1e0a33047cd16b3dd344f32f0cc8096eb74'}
BEFORE={'token':'150c29025cb0435c8ec6ddc7a971e921','generated_at':'2026-10-26T12:12:56.290224+00:00','deadline_at':'2026-10-26T13:12:56.290224+00:00','context_sha256':'01f3df6d6a18559bac7117bcbbd0a44afe84ade67baa9b7fe88c5ffd562a9b46','pending_sha256':'f64805308a5636fb444345b65935a9ca2138857c2d516f65ee7a4ec2d10348d4'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
 assert {k:o.get(k) for k in EXPECTED}==EXPECTED and EXPECTED['thread_id']==os.environ.get('CODEX_THREAD_ID')
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 items=[]
 for n in ['anchor_bfc_packet.py','observe_cts_native_progress.py','verify_protected_assets.py','check_bec_r1_current_no_transport.py']:
  data=(OLD/n).read_bytes();before=data
  if n=='check_bec_r1_current_no_transport.py':assert sha(OLD/n)=='6dac0a7411fd52ca2404dd1f6f69731ce8ce6a99ae827c78b7027e80957e5bb4'
  if n in ('anchor_bfc_packet.py','check_bec_r1_current_no_transport.py'):
   for k,v in BEFORE.items():
    assert data.count(v.encode())==1;data=data.replace(v.encode(),EXPECTED[k].encode())
   back=data
   for k,v in BEFORE.items():back=back.replace(EXPECTED[k].encode(),v.encode())
   assert back==before
  ast.parse(data)
  with (HERE/n).open('xb') as f:f.write(data)
  items.append({'file':n,'source_sha256':sha(OLD/n),'new_sha256':sha(HERE/n),'changes':'Only fresh owner5 constants; default-disabled flag and all functions unchanged' if before!=data else 'Byte-exact readonly copy'})
 with (HERE/'readonly_helpers_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 from anchor_bfc_packet import guard
 guard();print(json.dumps({'fresh_owner_bound':True,'helpers':len(items),'old_artifacts_unchanged':True,'NoTransport_not_executed':True}))
if __name__=='__main__':main()
