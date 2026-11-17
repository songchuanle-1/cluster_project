"""Read and preserve exact original APF log; no lifecycle mutation or signals."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,re,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
def save(path,data):
    guard()
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def main():
    guard();exp=json.loads((ROOT/'pipeline/experiments/M219-APF.json').read_text('utf8'))
    assert exp['pid']==793277 and exp['code_commit']=='d0e2f95712ed16446907706fbf6a65d34996a9ad' and exp['status']=='running'
    old=ast.parse((ROOT/'pipeline/diagnostic_bundles/tick_2b832a02/archive_cre_normal_terminal.py').read_text('utf8'))
    node=next(n for n in old.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROGRAM' for t in n.targets))
    program=ast.literal_eval(node.value).replace('118189','793277').replace('CRE_EXACT_ARCHIVE_META','APF_EXACT_ARCHIVE_META')
    dest=HERE/'apf_exact_terminal_archive';assert not dest.exists();dest.mkdir()
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
    r=subprocess.run(command,input=('LOG='+repr(exp['log'])+'\nCONFIG='+repr(exp['config'])+'\n'+program).encode(),capture_output=True,timeout=60)
    assert r.returncode==0,r.stderr.decode('utf8',errors='replace')[-1500:]
    lines=[x.removeprefix('APF_EXACT_ARCHIVE_META=') for x in r.stderr.decode('utf8',errors='replace').splitlines() if x.startswith('APF_EXACT_ARCHIVE_META=')]
    assert len(lines)==1;meta=json.loads(lines[0]);assert meta['bytes']==len(r.stdout) and meta['sha256']==hashlib.sha256(r.stdout).hexdigest()
    assert meta['log']==exp['log'] and meta['original_pid_absent_before_after'] is True and meta['same_config_processes']==[]
    path=dest/Path(exp['log']).name;save(path,r.stdout)
    ref={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}
    evidence={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'remote':meta,'local':ref,
        'scope':'Exact complete original APF log only. Original PID absent before/after read; no same-config own process, no signals/checkpoint body/GPU1 query. No lifecycle state inferred by this copy.'}
    save(dest/'exact_log_evidence.json',(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n').encode())
    tail=r.stdout[-16000:].decode('utf8',errors='replace').replace('\r','\n')
    fatal=[line[-1200:] for line in tail.splitlines() if re.search(r'Traceback|RuntimeError:|CUDA out of memory|Segmentation fault|Fatal Python|Killed|Aborted|Early stopping|training complete|finished training',line)]
    summary={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'exact_full_log':ref,
        'end_markers_in_last16KB':fatal,'last_nonempty_lines':[line[-800:] for line in tail.splitlines() if line.strip()][-4:],
        'terminal_classification':'UNKNOWN_PENDING_EXPLICIT_CANONICAL_RECONCILIATION'}
    save(dest/'local_terminal_semantics.json',(json.dumps(summary,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps({'bytes':meta['bytes'],'full_log_sha256':meta['sha256'],'same_config_processes':meta['same_config_processes'],
        'terminal_markers':fatal,'last_line_classes':[re.sub(r'\s+',' ',line)[:180] for line in summary['last_nonempty_lines']]},ensure_ascii=False))
if __name__=='__main__':main()
