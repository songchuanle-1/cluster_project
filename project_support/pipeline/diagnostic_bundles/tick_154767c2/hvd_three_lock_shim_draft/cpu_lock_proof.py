"""Pinned-host foreground CPU proof; no model/GPU/background guardian."""
import argparse,hashlib,json,os,shlex,socket,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--shim',required=True);p.add_argument('--sha256',required=True);p.add_argument('--root',required=True);a=p.parse_args()
assert socket.gethostname()=='dl04-MS-7E06'
shim=Path(a.shim).resolve();assert hashlib.sha256(shim.read_bytes()).hexdigest()==a.sha256
probe="""import os,sys,json,fcntl
paths=['/tmp/cluster_project_gpu0_'+k+'.lock' for k in ['training','diagnostic','exclusive']]
assert os.getpid()==int(os.environ['HVD_CPU_EXPECTED_PID'])
expected=['--cpu-probe','a b','*','$literal','']
assert sys.argv[1:]==expected
fds={}
for item in os.listdir('/proc/self/fd'):
 try:
  path=os.readlink('/proc/self/fd/'+item)
  if path in paths:fds[path]=int(item)
 except OSError:pass
assert set(fds)==set(paths)
for path,fd in fds.items():
 assert not (fcntl.fcntl(fd,fcntl.F_GETFD)&fcntl.FD_CLOEXEC)
 with open(path,'a+b') as other:
  try:fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:pass
  else:raise AssertionError('Inherited lock was not held')
print(json.dumps({'passed':True,'foreground_exec_PID_preserved':True,'argv_exact':True,'three_inherited_FDs':True,'three_locks_contended':True,'GPU_or_model_execution':False}))
"""
# Directly exercise the exact unchanged production helper with a CPU-only target.
# The source/routing match must be reviewed against canonical training argv separately.
script='source '+shlex.quote(str(shim))+' && conda activate project_cluster && cd '+shlex.quote(a.root)+' && export HVD_CPU_EXPECTED_PID=$BASHPID && _hvd_gpu0_locked_exec "$CONDA_PREFIX/bin/python" -B -c '+shlex.quote(probe)+' '+shlex.join(['--cpu-probe','a b','*','$literal',''])
r=subprocess.run(['/bin/bash','-c',script],capture_output=True,text=True,timeout=20)
print(json.dumps({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'shim_sha256':a.sha256,'GPU_or_model_execution':False}))
raise SystemExit(r.returncode)
