from pathlib import Path
import hashlib,json
from run_next_bec_arm import guard
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_01d2f548'
def main():
 guard()
 with (HERE/'anchor_bfc_packet.py').open('x',encoding='utf8') as f:f.write('from run_next_bec_arm import guard\n')
 n='verify_protected_assets.py';b=(OLD/n).read_bytes()
 with (HERE/n).open('xb') as f:f.write(b)
 with (HERE/'protection_helper_provenance.json').open('x',encoding='utf8') as f:json.dump({'new_root_guard_import':'run_next_bec_arm.guard current6','readonly_snapshot_sha256':hashlib.sha256(b).hexdigest(),'old_source_byte_exact':True},f,indent=2)
 print('CURRENT_PROTECTION_HELPERS_READY')
if __name__=='__main__':main()
