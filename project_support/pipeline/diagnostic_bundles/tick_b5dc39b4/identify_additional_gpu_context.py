"""Readonly NVML and minimal /proc metadata for a newly observed extra context."""
from pathlib import Path
import hashlib,json,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PROGRAM=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,os,pwd,json,subprocess,datetime
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
contexts=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True).strip()
records=[]
for pid in [1565126]:
    p=pathlib.Path('/proc')/str(pid)
    try:
        fields=(p/'stat').read_text().rsplit(')',1)[1].split()
        uid=p.stat().st_uid
        args=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v]
        cwd=os.readlink(p/'cwd')
        script=pathlib.PurePosixPath(args[1]).name if len(args)>1 and args[1].endswith('.py') else None
        mode='module' if len(args)>1 and args[1]=='-m' else 'inline' if len(args)>1 and args[1]=='-c' else 'script' if script else 'other'
        records.append({'pid':pid,'observed':True,'start_ticks':fields[19],'state':fields[0],
            'uid':uid,'owning_user':pwd.getpwuid(uid).pw_name,'executable_basename':pathlib.PurePosixPath(args[0]).name if args else None,
            'script_basename':script,'mode':mode,'argc':len(args),
            'cwd_within_cluster_project':cwd==root or cwd.startswith('/data/songcl/Project/Cluster_project/'),
            'cwd_within_current_runtime':cwd==root or cwd.startswith(root+'/'),
            'current_runtime_argv_reference':any(root in v for v in args),
            'raw_foreign_argv_or_environment_or_files_read':False})
    except (OSError,ProcessLookupError) as e:
        records.append({'pid':pid,'observed':False,'error_type':type(e).__name__})
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),
    'gpu_inventory':inventory,'compute_contexts':contexts,'extra_process_metadata':records,
    'signals_sent':False,'remote_file_writes':False,'scope':'NVML and minimal process owner/start/executable/script basename/project-scope booleans only. No foreign environment, source, logs or checkpoints read; argv values are not exported.'}))
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    owner=guard();q=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'))
    matches=[{'id':t.get('id'),'status':t.get('status'),'server':server} for server,tasks in q['gpu_queues'].items() for t in tasks if t.get('pid')==1565126]
    run=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'songcl@192.168.1.115','/usr/bin/python3 -B -'],input=PROGRAM,capture_output=True,text=True,encoding='utf8',timeout=35)
    assert run.returncode==0,run.stderr[-1600:]
    out=json.loads(run.stdout);guard()
    out.update(owner_token=owner['token'],current_project_queue_pid_matches=matches,reason='Prior actual observation shows additional PID1565126 on both authorized GPUs; protect it and identify minimal ownership only.',native_execution='NOT_RUN',new_gpu_compute='NOT_RUN')
    p=HERE/'additional_gpu_context_probe.json'
    with p.open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(p),'sha256':sha(p),'gpu_inventory':out['gpu_inventory'],'contexts':out['compute_contexts'],'extra_process_metadata':out['extra_process_metadata'],'current_project_queue_pid_matches':matches},ensure_ascii=False))
if __name__=='__main__':main()
