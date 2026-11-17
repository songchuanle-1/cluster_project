"""One remote fixed pair of fresh CPU import processes; no Torch import here."""
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import os,sys,json,hashlib,subprocess,base64
from pathlib import Path
from datetime import datetime,timezone
assert sys.executable=='/home/songcl/.conda/envs/project_cluster/bin/python'
assert datetime.now(timezone.utc)<datetime.fromisoformat(BOUND_OWNER['deadline_at'])
ROOT='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
BASE=Path('/data/songcl/Project/Cluster_project/pipeline/import_order_01b53a4e')
assert BASE.parent.resolve()==Path('/data/songcl/Project/Cluster_project/pipeline').resolve() and not BASE.exists()
BASE.mkdir(mode=0o700)
source=base64.b64decode(CHILD_SOURCE_BASE64).decode('utf-8')
assert hashlib.sha256(source.encode()).hexdigest()==CHILD_SOURCE_SHA256
report={'owner':BOUND_OWNER,'experiment':'Fixed original pccm/gorilla/torch CPU import-order pair','started_at':datetime.now(timezone.utc).isoformat(),'private_base':str(BASE),'child_source_sha256':CHILD_SOURCE_SHA256,'conditions':[],'native_PASS':False,'global_environment_or_sitepackages_modified':False}
for condition in ['PCCM_FIRST','GORILLA_FIRST']:
    assert (datetime.fromisoformat(BOUND_OWNER['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>125
    private=BASE/condition;private.mkdir(mode=0o700)
    for leaf in ['tmp','mpl','cache','config']:(private/leaf).mkdir(mode=0o700)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='1999',
        TMPDIR=str(private/'tmp'),MPLCONFIGDIR=str(private/'mpl'),XDG_CACHE_HOME=str(private/'cache'),XDG_CONFIG_HOME=str(private/'config'),IMPORT_ORDER_PRIVATE=str(private),
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
    command=[sys.executable,'-B','-',condition]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,env=env,text=True,encoding='utf-8')
    entry={'condition':condition,'pid':proc.pid,'command':command,'private_directory':str(private)}
    report['conditions'].append(entry)
    try:stdout,stderr=proc.communicate(source,timeout=120)
    except subprocess.TimeoutExpired:
        entry['status']='CPU_CHILD_TIMEOUT_UNCERTAIN_NO_REPLAY';entry['signals_sent']=False
        report['status']='CPU_IMPORT_ORDER_PAIR_INCOMPLETE_UNCERTAIN';break
    entry.update(returncode=proc.returncode,stdout=stdout,stderr=stderr,stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
    lines=[]
    for line in stdout.splitlines():
        if line.startswith('IMPORT_ORDER_RESULT='):lines.append(line[len('IMPORT_ORDER_RESULT='):])
    entry['observation']=json.loads(lines[0]) if len(lines)==1 else None
    entry['status']='CPU_CONDITION_REPORTED' if entry['observation'] is not None else 'CPU_CONDITION_FAILED_NO_STRUCTURED_RESULT'
else:report['status']='FIXED_TWO_CPU_IMPORT_ORDER_CONDITIONS_COMPLETED_NOT_NATIVE_PASS'
report['finished_at']=datetime.now(timezone.utc).isoformat()
print('IMPORT_ORDER_PAIR='+json.dumps(report,ensure_ascii=False,allow_nan=False),flush=True)
