"""Fresh-owner readonly observer and expanded protection snapshot, no old edits."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
EXPECTED={'token':'60d21b3324c94445b26d2ecb24a3ba65','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T16:09:41.027895+00:00','deadline_at':'2026-10-26T17:09:41.027895+00:00','context_sha256':'062a6fc0ddeba051336890fe88f3d2d0382d2036f7afc139f368da2568334c23','pending_sha256':'c3ef64975c4c76f8c4febbcdc09867e2c133dbd465aab18a834238cafcf98cb4'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,b):
 ast.parse(b)
 with (HERE/n).open('xb') as f:f.write(b)
def main():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in EXPECTED}==EXPECTED and os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 source=HERE.parent/'tick_150c2902/anchor_bfc_packet.py';b=source.read_bytes()
 old={'token':'150c29025cb0435c8ec6ddc7a971e921','generated_at':'2026-10-26T12:12:56.290224+00:00','deadline_at':'2026-10-26T13:12:56.290224+00:00','context_sha256':'01f3df6d6a18559bac7117bcbbd0a44afe84ade67baa9b7fe88c5ffd562a9b46','pending_sha256':'f64805308a5636fb444345b65935a9ca2138857c2d516f65ee7a4ec2d10348d4'}
 for k,v in old.items():assert b.count(v.encode())==1;b=b.replace(v.encode(),EXPECTED[k].encode())
 write('anchor_bfc_packet.py',b);items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(source),'new_sha256':sha(HERE/'anchor_bfc_packet.py'),'changes':'Only fresh owner5 constants; return owner dict intact.'}]
 source=HERE.parent/'tick_94f8ddb8/observe_bec_training_progress_r2.py';b=source.read_bytes()
 old=b'from run_next_bec_arm import guard as _base_guard';assert b.count(old)==1;b=b.replace(old,b'from anchor_bfc_packet import guard as _base_guard')
 old=b"HERE/'bec_r1_execution/native_manifest.json'";assert b.count(old)==1;b=b.replace(old,b"HERE.parent/'tick_94f8ddb8/bec_r1_execution/native_manifest.json'")
 write('observe_bec_training_progress.py',b);items.append({'file':'observe_bec_training_progress.py','source_sha256':sha(source),'new_sha256':sha(HERE/'observe_bec_training_progress.py'),'changes':'Current rootguard import + historical original026c manifest for source8 only; same readonly remote observer/logic.'})
 source=HERE.parent/'tick_01d2f548/verify_protected_assets.py';b=source.read_bytes()
 old=b"head=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'";assert b.count(old)==1;b=b.replace(old,b"head=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'")
 old=b"'admissions/M214-CTS.json']";assert b.count(old)==1;b=b.replace(old,b"'admissions/M214-CTS.json','experiments/M215-BEC.json','admissions/M215-BEC.json']")
 write('verify_protected_assets.py',b);items.append({'file':'verify_protected_assets.py','source_sha256':sha(source),'new_sha256':sha(HERE/'verify_protected_assets.py'),'changes':'Expected actualprimary026c; add active BEC experiment/receipt to protected14, no weaker existing protection.'})
 with (HERE/'current_helpers_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 from anchor_bfc_packet import guard
 guard();print('FRESH_GUARD_OBSERVER_AND_PROTECTED14_READY')
if __name__=='__main__':main()
