"""Make only one enable-flag change in a reviewed private execution sibling."""
from pathlib import Path
import ast,hashlib,json
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 guard();src=HERE/'aef_version_prepare';dst=HERE/'aef_version_execute'
 assert sha(src/'preparation.json')=='4780754c81a3125cdcb5dae6809744ff5594a97faede92c42f82f4905794645b'
 p=json.loads((src/'preparation.json').read_text('utf8'))
 for n,h in p['prepared_file_hashes'].items():assert sha(src/n)==h
 peer=HERE/'aef_version_helper_independent_review.json';review=json.loads(peer.read_text('utf8'))
 assert review['material_concerns']==[]
 assert '93e243babed08dc7d6650b53d629e3416d972b6901f55f707fd7df377a4e46e5' in peer.read_text('utf8')
 assert not dst.exists();dst.mkdir()
 n='prepare_isolated_aef_version.py';before=(src/n).read_bytes();assert before.count(b'DRAFT_EXECUTION_ENABLED = False')==1
 after=before.replace(b'DRAFT_EXECUTION_ENABLED = False',b'DRAFT_EXECUTION_ENABLED = True')
 assert after.replace(b'DRAFT_EXECUTION_ENABLED = True',b'DRAFT_EXECUTION_ENABLED = False')==before;ast.parse(after)
 with (dst/n).open('xb') as f:f.write(after)
 with (dst/'materialization.json').open('x',encoding='utf8') as f:json.dump({'owner_token':'60d21b3324c94445b26d2ecb24a3ba65','prepared_sha256':sha(src/n),'execution_sha256':sha(dst/n),'only_single_enable_flag_changed':True,'peer_sha256':sha(peer),'source_mutation_invoked':False},f,indent=2)
 print(json.dumps({'status':'REVIEWED_SINGLE_FLAG_AEF_COPY_READY','directory':str(dst)}))
if __name__=='__main__':main()
