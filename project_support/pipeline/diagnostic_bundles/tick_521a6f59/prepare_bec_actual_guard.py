"""Prepare the same no-transport busy-guard check for the new BEC catalog."""
from pathlib import Path
import hashlib,json
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();source=HERE/'check_cts_actual_guard.py';data=source.read_text('utf8')
    old="PACKET=HERE.parent/'tick_6bdbcf77/cts_operational_prepare'"
    assert data.count(old)==1
    data=data.replace(old,"PACKET=HERE/'bec_operational_prepare'")
    data=data.replace('CTS4e8','BEC9b678').replace('CTS','BEC').replace('cts_','bec_')
    target=HERE/'check_bec_actual_guard.py'
    with target.open('x',encoding='utf8') as f:f.write(data)
    with (HERE/'bec_guard_check_provenance.json').open('x',encoding='utf8') as f:
        json.dump({'source_sha256':sha(source),'current_sha256':sha(target),'changes':'Only packet location, names and source-version labels. Same actual guard, NoTransport, process/socket fence,2registeredbusy/14invalid/originaldeadline/5hash/noactive assertions.','actual_check':'NOT_RUN_REQUIRES_EXTERNAL_STATIC_ANCHOR_FIRST'},f,indent=2);f.write('\n')
    print(json.dumps({'prepared':target.name,'actual_check':'NOT_RUN','sha256':sha(target)}))
if __name__=='__main__':main()
