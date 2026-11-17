"""Default NOP. Explicit root-only read-only original-process observation."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,argparse,subprocess,shlex,hashlib
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent))
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
CONSTANTS_SHA256='db6f2837f7010f1d1be09aa3b3d878257626f92570226aaea3a3543e2ee9af21'
REMOTE_SHA256='43a205c31e9b0997a877110131c2ad300e7da136d324d3bdf5fa10645f4ce9d1'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--target',choices=['wfc','lft','both'],default='wfc');ap.add_argument('--lft-binding-file');ap.add_argument('--lft-binding-sha256');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_NOP_NO_REMOTE_NO_GIT_NO_MODEL');return
 guard();assert sha(HERE/'constants.json')==CONSTANTS_SHA256 and sha(HERE/'remote_readonly.py.txt')==REMOTE_SHA256
 k=u.read(HERE/'constants.json');processes=[]
 if args.target in ('wfc','both'):
  e=u.read(ROOT/'pipeline/experiments/M226-WFC.json');p=k['WFC'];assert e['pid']==p['pid'] and e['code_commit']==p['commit'] and e['status']=='running';processes.append(p)
 if args.target in ('lft','both'):
  assert args.lft_binding_file and args.lft_binding_sha256
  bp=Path(args.lft_binding_file).resolve();assert bp.is_relative_to(HERE.parent) and sha(bp)==args.lft_binding_sha256
  b=u.read(bp);assert b['owner']==EXPECTED and b['experiment_id']=='M227-LFT' and b['code_commit']==k['LFT_COMMIT'] and b['physical_gpu']==1 and b['gpu_uuid']==k['LFT_UUID']
  assert type(b['pid']) is int and b['pid']>0 and str(b['start_ticks']).isdigit()
  config=next(n for n in k['LFT_HASHES'] if n.endswith('.yaml'));assert b['config']==config
  assert b['log'].startswith(k['WFC']['root']+'/logs/train_'+Path(config).stem+'_') and b['log'].endswith('.log')
  e=u.read(ROOT/'pipeline/experiments/M227-LFT.json');assert e['pid']==b['pid'] and e['code_commit']==b['code_commit'] and e['status']=='running'
  processes.append({'experiment_id':'M227-LFT','pid':b['pid'],'start_ticks':str(b['start_ticks']),'config':config,'log':b['log'],'commit':b['code_commit'],'physical_gpu':1,'gpu_uuid':b['gpu_uuid'],'root':k['WFC']['root'],'hashes':k['LFT_HASHES']})
 payload={'owner':EXPECTED,'constants':k,'processes':processes};program='payload='+repr(payload)+'\n'+(HERE/'remote_readonly.py.txt').read_text('utf8')
 guard();argv=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(program)]
 result=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=80);record={'owner':EXPECTED,'actual_root_thread_required':True,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':argv,'returncode':result.returncode,'stderr':result.stderr,'target':args.target}
 if result.returncode==0:
  record['observation']=json.loads(result.stdout);sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
  for obs in record['observation']['observations']:
   vals,best,noimp=mon.parse_native_lineage('\n'.join(obs['metric_lines']),resumed=False);obs['precise_native_validation']={'values':vals,'best':best if vals else None,'no_improve':noimp if vals else None,'scope':'Original native logger partial validation only; no checkpoint, final completion or efficacy claim.'}
 else:record['stdout']=result.stdout
 guard();u.save(HERE/('original_'+args.target+'_phase_observation.json'),record);assert result.returncode==0,result.stderr
 print(json.dumps({'evidence':u.ref(HERE/('original_'+args.target+'_phase_observation.json')),'observations':[{'experiment_id':o['experiment_id'],'samples':o['samples'],'train_growth':o['strict_native_train_growth'],'validation_growth':o['strict_native_validation_growth'],'precise_native_validation':o['precise_native_validation']} for o in record['observation']['observations']]}))
if __name__=='__main__':main()
