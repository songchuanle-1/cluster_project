"""Reuse unchanged readonly helpers; retain exact source and transform proofs."""
from pathlib import Path
import hashlib,json
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent;PREV=HERE.parent/'tick_6bdbcf77'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();items=[]
    for old,new in [('observe_active_runs.py','observe_active_runs.py'),('verify_protected_assets_v2.py','verify_protected_assets_v2.py'),('check_cts_actual_guard.py','check_cts_actual_guard.py')]:
        p=PREV/old;data=p.read_bytes()
        if new=='check_cts_actual_guard.py':
            assert data.count(b"PACKET=HERE/'cts_operational_prepare'")==1
            data=data.replace(b"PACKET=HERE/'cts_operational_prepare'",b"PACKET=HERE.parent/'tick_6bdbcf77/cts_operational_prepare'")
        with (HERE/new).open('xb') as f:f.write(data)
        items.append({'source':str(p),'source_sha256':sha(p),'current':new,'current_sha256':sha(HERE/new),
                      'change':'Only frozen CTS catalog lookup to prior6bdb; current guard/current output dir' if new.startswith('check_cts') else 'Exact byte copy; current readonly owner guard is separate'})
    with (HERE/'readonly_helper_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
    print(json.dumps({'prepared_readonly_helpers':len(items),'native':'NOT_RUN'}))
if __name__=='__main__':main()
