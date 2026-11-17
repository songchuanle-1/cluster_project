"""Terminate only our identified read-only precheck; never an external process."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate as m

m.guard()
result = json.loads(m.remote(m.TARGET, """
import json,os,pathlib,signal,subprocess
pid=2591725;p=pathlib.Path('/proc')/str(pid)
args=(p/'cmdline').read_bytes().split(b'\\0')
assert args[:3]==[b'python3',b'-B',b'-']
fields=(p/'stat').read_text().split()
assert fields[21]=='154296422'
assert os.readlink(p/'fd/3')=='/tmp/cluster_project_gpu0_exclusive.lock'
assert os.readlink(p/'fd/4')=='/proc/3172/cmdline'
observed={'pid':pid,'state':fields[2],'start_ticks':fields[21],
          'wchan':(p/'wchan').read_text(),'blocked_fd4':os.readlink(p/'fd/4'),
          'gpu':subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=uuid,memory.used,memory.free','--format=csv,noheader,nounits'],text=True).strip()}
os.kill(pid,signal.SIGKILL)
observed['termination_signal_sent']='SIGKILL'
try:
    observed['state_after_signal']=(p/'stat').read_text().split()[2]
    observed['old_lease_released']=False
except FileNotFoundError:
    observed['state_after_signal']='absent';observed['old_lease_released']=True
observed['scope']='Verified current-turn read-only precheck orphaned after local timeout, not a training process. Its transmitted program only scans/asserts/hashes/prints; never launches or writes project data. Foreign PID3172 is untouched. Old lock not removed/replaced; use distinct migration training reservation and exact own PID markers instead of all-/proc scans.'
print(json.dumps(observed))
""", timeout=25))
m.record("precheck_recovery", result)
print(json.dumps(result))
