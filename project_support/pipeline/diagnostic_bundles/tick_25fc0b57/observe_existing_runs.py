"""One current-owner read-only call reuses the frozen original-run reader; no new diagnostic package."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,subprocess,shlex
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/dual_original_run_observer'
def main():
 if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
 guard();base=u.read(HERE/'protected_assets_before.json');u.protect(base)
 assert sha(FROZEN/'constants.json')=='db6f2837f7010f1d1be09aa3b3d878257626f92570226aaea3a3543e2ee9af21'
 assert sha(FROZEN/'remote_readonly.py.txt')=='43a205c31e9b0997a877110131c2ad300e7da136d324d3bdf5fa10645f4ce9d1'
 k=u.read(FROZEN/'constants.json');w=k['WFC'];p=ROOT/'pipeline/diagnostic_bundles/tick_d94467a9/lft_original_process_binding.json'
 assert sha(p)=='cb92ec6d63ca6745ce1a517ee44c8735b99bb3b5b1b63f8eefd592545426ffdb'
 b=u.read(p);assert b['pid']==2685912 and str(b['start_ticks'])=='106767833'
 processes=[w,{'experiment_id':'M227-LFT','pid':b['pid'],'start_ticks':b['start_ticks'],'config':b['config'],'log':b['log'],'commit':b['code_commit'],'physical_gpu':1,'gpu_uuid':b['gpu_uuid'],'root':w['root'],'hashes':k['LFT_HASHES']}]
 for item in processes:
  e=u.read(ROOT/'pipeline/experiments'/(item['experiment_id']+'.json'))
  assert e['status']=='running' and e['pid']==item['pid'] and e['code_commit']==item['commit'] and e['config']==item['config'] and e['log']==item['log']
 program='payload='+repr({'owner':EXPECTED,'constants':k,'processes':processes})+'\n'+(FROZEN/'remote_readonly.py.txt').read_text('utf8')
 command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(program)]
 guard();run=subprocess.run(command,capture_output=True,text=True,encoding='utf8',timeout=80)
 result={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':command,'returncode':run.returncode,'stderr':run.stderr,'reader_program':u.ref(FROZEN/'remote_readonly.py.txt'),'constants':u.ref(FROZEN/'constants.json'),'scope':'Original runs/progress/native partial validation plus physical GPU precondition only; no new model entry, tests or training.'}
 if run.returncode==0:
  data=json.loads(run.stdout);sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
  for item in data['observations']:
   vals,best,noimp=mon.parse_native_lineage('\n'.join(item['metric_lines']),resumed=False)
   item['precise_native_validation']={'values':vals,'best':best if vals else None,'no_improve':noimp if vals else None,'scope':'Partial original native logger, no checkpoint body or efficacy claim.'}
  rows={int(x.split(',')[0]):[z.strip() for z in x.split(',')] for x in data['queries']['gpu']['stdout'].splitlines()}
  contexts={(x.split(',')[0].strip(),int(x.split(',')[1])) for x in data['queries']['compute']['stdout'].splitlines() if ',' in x}
  assert set(rows)=={0,1}
  for item in processes:assert rows[item['physical_gpu']][1]==item['gpu_uuid'] and (item['gpu_uuid'],item['pid']) in contexts
  idle=[g for g,row in rows.items() if int(row[3])<1024 and int(row[2])<10 and not any(uuid==row[1] for uuid,pid in contexts)]
  result.update(observation=data,resource_precondition={'server':'server-4','allowed_gpu_ids':[0,1],'idle_gpu_ids':idle,'busy_gpu_ids':[g for g in rows if g not in idle],'result':'blocked' if not idle else 'passed','scope':'Physical precondition, not candidate resource-profile pass.'})
 else:result['raw_stdout']=run.stdout
 u.protect(base);u.save(HERE/'existing_runs_and_resource_observation.json',result)
 assert run.returncode==0,run.stderr
 print(json.dumps({'evidence':u.ref(HERE/'existing_runs_and_resource_observation.json'),'resource_precondition':result['resource_precondition'],'runs':[{'id':x['experiment_id'],'samples':x['samples'],'train_growth':x['strict_native_train_growth'],'validation_growth':x['strict_native_validation_growth'],'native_validation':x['precise_native_validation']} for x in data['observations']]}))
if __name__=='__main__':main()
