"""Observer-only return-schema repair; no model, lifecycle, or old source changes."""
from pathlib import Path
import ast,hashlib,json
from run_next_bec_arm import guard
HERE=Path(__file__).resolve().parent
def main():
 guard();src=HERE/'observe_bec_training_progress.py';b=src.read_bytes();before=hashlib.sha256(b).hexdigest()
 old=b'from anchor_bfc_packet import guard\n';new=b"from run_next_bec_arm import guard as _base_guard\n\ndef guard():\n _base_guard()\n return json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))\n"
 assert b.count(old)==1;b=b.replace(old,new)
 assert b.count(b'original_CTS_launch_preserved')==1;b=b.replace(b'original_CTS_launch_preserved',b'original_BEC_launch_preserved')
 ast.parse(b);target=HERE/'observe_bec_training_progress_r2.py'
 with target.open('xb') as f:f.write(b)
 with (HERE/'bec_observer_return_binding_repair.json').open('x',encoding='utf8') as f:json.dump({'source_sha256':before,'new_sha256':hashlib.sha256(b).hexdigest(),'reason':'Root minimal guard validated owner but returned None; observer output constructor expected owner dict. Both prior remote observations succeeded but output JSON was not created. New copy adapts guard return and BEC output key only. No model revision or native failure.','remote_observation_program_unchanged':True,'original_failed_helper_preserved':True,'scope':'Observer bookkeeping only'},f,indent=2)
 print('OBSERVER_RETURN_BINDING_REPAIRED_IN_NEW_COPY')
if __name__=='__main__':main()
