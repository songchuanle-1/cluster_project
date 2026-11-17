"""Read exact native lineage and matching flock ownership without broad process scans."""

import json
from pathlib import Path
from audit_terminal import BUNDLE, PROJECT, SSH, PYTHON, command, save, monitor

exp = monitor.load_experiment(str(PROJECT), "M201-BPS")
server = monitor.load_servers(str(PROJECT))["server-4"]
root = server["remote_code_root"]
folder = server["work_dir"] + "/" + Path(exp["config"]).stem + "/20261014_154431"
program = f"""
import datetime,hashlib,json,os,pathlib,re,subprocess
os.environ['CUDA_VISIBLE_DEVICES']=''
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
lock=pathlib.Path('/tmp/cluster_project_gpu0_m201_migration.lock')
stat=lock.stat();key=f"{{os.major(stat.st_dev):02x}}:{{os.minor(stat.st_dev):02x}}:{{stat.st_ino}}"
matching=[line for line in pathlib.Path('/proc/locks').read_text().splitlines() if key in line]
holders=[];candidate_pids=set()
for line in matching:
    cells=line.replace('->','').split()
    if len(cells)>4 and cells[4].isdigit() and int(cells[4])>0:candidate_pids.add(int(cells[4]))
for pid in sorted(candidate_pids):
    p=pathlib.Path('/proc')/str(pid)
    record={{'pid':pid,'exists':p.exists()}}
    if p.exists():
        record.update(state=(p/'stat').read_text().split()[2],
            cwd=os.readlink(p/'cwd'),
            args=[part.decode() for part in (p/'cmdline').read_bytes().split(b'\\0') if part],
            children=(p/'task'/str(pid)/'children').read_text().split())
    holders.append(record)
base=pathlib.Path({folder!r});logs=list(base.glob('*.log'));assert len(logs)==1
native_log=logs[0];text=native_log.read_text();values=re.findall(r'mIoU : ([0-9.eE+-]+)',text)
stdout=pathlib.Path({exp["log"]!r});stdout_values=re.findall(r'\\bmIOU: ([0-9]+\\.[0-9]+)',stdout.read_text())
best_saves=[line for line in text.splitlines() if 'save best pth' in line][-8:]
import torch
assert not torch.cuda.is_initialized()
metas={{}}
for name in ('best.pth','last.pth'):
    p=base/name;s=p.stat();saved=torch.load(p,map_location='cpu',weights_only=False,mmap=True)
    assert (s.st_size,s.st_mtime_ns)==(p.stat().st_size,p.stat().st_mtime_ns)
    metas[name]=saved['meta']
print(json.dumps({{'observed_at':datetime.datetime.now().astimezone().isoformat(),
    'matching_kernel_lock_lines':matching,'exact_lock_holders':holders,
    'native_log':str(native_log),'native_log_sha256':hashlib.sha256(native_log.read_bytes()).hexdigest(),
    'native_full_precision_values':[float(value) for value in values],
    'stdout_rounded_values':[float(value) for value in stdout_values],
    'best_save_events':best_saves,'checkpoint_metas':metas,
    'native_terminal_messages':[line for line in text.splitlines() if 'Early stopping' in line],
    'gpu':subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
    'compute':subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip(),
    'cuda_initialized':torch.cuda.is_initialized(),'actions':'Read-only; no signals, resets or foreign process scans'}},
    default=lambda value:value.item()))
"""
result = json.loads(command(SSH + [PYTHON, "-B", "-"], program, timeout=45))
save("resource_diagnosis", result)
native_name = Path(result["native_log"]).name
command(["scp", *SSH[1:-1], "server-4:" + result["native_log"], str(BUNDLE / native_name)], timeout=45)
print(json.dumps(result))
