"""Root-only exact reviewed preparation -> single-flag execution sibling."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 owner=guard();src=HERE/'bec_r1_anchor_prepare';dest=HERE/'bec_r1_anchor_execute'
 prep=src/'preparation.json';assert sha(prep)=='6d7e79700b1accd8eb7a2b0747d71ae7a7a243be40c6e6b73b768cf88fe24c75'
 p=json.loads(prep.read_text('utf8'))
 for n,h in p['prepared_file_hashes'].items():assert sha(src/n)==h
 peer=HERE/'bec_r1_anchor_helpers_independent_review.json';r=json.loads(peer.read_text('utf8'))
 assert r['material_concerns']==[] and r['metadata_blockers']==[]
 # Independent current review must bind the exact new preparation bytes.
 assert p['source_hashes']['anchor_bec_r1_static.py']=='b968c63e70dfbfbf6243e98e44a64acd94488f912f025c9caa93d6076f747273'
 assert '6d7e79700b1accd8eb7a2b0747d71ae7a7a243be40c6e6b73b768cf88fe24c75' in peer.read_text('utf8')
 assert not dest.exists();dest.mkdir()
 items=[]
 for n in ['anchor_bec_r1_static.py','check_bec_r1_current_guard.py']:
  before=(src/n).read_bytes();after=before
  if n=='anchor_bec_r1_static.py':
   assert before.count(b'ENABLE_ROOT_EXECUTION=False')==1
   after=before.replace(b'ENABLE_ROOT_EXECUTION=False',b'ENABLE_ROOT_EXECUTION=True')
   assert after.replace(b'ENABLE_ROOT_EXECUTION=True',b'ENABLE_ROOT_EXECUTION=False')==before
  ast.parse(after)
  with (dest/n).open('xb') as f:f.write(after)
  items.append({'name':n,'source_sha256':sha(src/n),'execution_sha256':sha(dest/n),'difference':'Only ENABLE_ROOT_EXECUTION=False to True' if before!=after else 'Byte-exact copy'})
 guard()
 with (dest/'materialization.json').open('x',encoding='utf8') as f:
  json.dump({'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':owner['token'],'preparation':{'path':prep.relative_to(ROOT).as_posix(),'sha256':sha(prep)},'independent_review':{'path':peer.relative_to(ROOT).as_posix(),'sha256':sha(peer)},'files':items,'no_helper_executed_by_materialization':True},f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'execution_copy':str(dest),'only_one_flag_changed':True,'sources_preserved':True}))
if __name__=='__main__':main()
