"""Read-only search for an ABI-compatible existing pointgroup extension."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
assert subprocess.check_output(['hostname'], universal_newlines=True, timeout=5).strip() == 'sysu311-MS-7C59'
roots = [
    Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d/framework/lib'),
    Path('/sdc1/songcl/Project/Cluster_project/Cluster/framework/lib'),
    Path('/sdc1/songcl/IPDN/lib'),
    Path('/sdc1/songcl/IPDN/ops'),
    Path('/sdc1/songcl/IPDN/model'),
    Path('/home/songcl/.conda/envs/3d-stmn/lib/python3.8/site-packages'),
]
records=[]
for root in roots:
    matches=[]
    if root.is_dir():
        for path in root.rglob('*'):
            if path.is_file() and ('pointgroup' in path.name or 'pointgroup' in str(path.parent)):
                if path.suffix in ('.so', '.py', '.cu', '.cpp') or path.name == 'setup.py':
                    matches.append({'path':str(path),'bytes':path.stat().st_size})
                if len(matches)>=100: break
    records.append({'root':str(root),'exists':root.exists(),'matches':matches})
import torch
commands={}
for name,cmd in {'nvcc':['nvcc','--version'],'gcc':['gcc','--version'],'disk':['df','-h','/sdc1/songcl/Project/Cluster_project']}.items():
    try:
        p=subprocess.run(cmd,universal_newlines=True,capture_output=True,timeout=10)
        commands[name]={'rc':p.returncode,'stdout':p.stdout[:2000],'stderr':p.stderr[:1000]}
    except OSError as exc:commands[name]={'error':str(exc)}
print('SERVER3_COMPATIBILITY_JSON='+json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),
    'python':sys.version,'torch':torch.__version__,'cuda_initialized':torch.cuda.is_initialized(),
    'roots':records,'commands':commands,'cuda_home':os.environ.get('CUDA_HOME')}))
