"""FCB-only actual reviewed standards -> canonical admission -> waiting. Default no write."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,math,os,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from anchor import guard
import fcb_evidence as evidence
ROOT=Path('D:/project/cluster_project');HERE=evidence.TICK;CODE=ROOT/'Cluster'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');GIT='C:/Program Files (x86)/Git/cmd/git.exe'
EXP='M223-FCB';CID='hierarchy-fine-coarse-complete-bipartite-composition';COMMIT=evidence.COMMIT;BASE=evidence.BASE
CONFIG='configs/Quard/ctf_hcg_csort_fcb/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fcb.yaml';GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
AUTH={'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
RESOURCE_AUTH={'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
LIFECYCLE=HERE/'fcb_before_admission_lifecycle.json';LIFECYCLE_SHA=None
REVIEW=HERE/'fcb_actual_four_result_review.json';REVIEW_SHA=None
INDEPENDENT=None
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
 p=Path(p).resolve();assert p.is_relative_to(ROOT.resolve());return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(p,v):
 guard();data=encoded(v)
 with Path(p).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def replace(p,v):
 guard();data=encoded(v);tmp=p.with_name(p.name+'.fcb_admission.tmp')
 with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 guard();os.replace(tmp,p)
def git(*args):return subprocess.check_output([GIT,'--no-optional-locks','-C',str(CODE),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
def check_source():
 guard();assert git('rev-parse','HEAD').decode().strip()==COMMIT and git('show','-s','--format=%P',COMMIT).decode().strip()==BASE
 manifest=read(HERE/'fcb_execution/native_manifest.json');assert manifest['candidate_id']==CID and manifest['code_commit']==COMMIT and manifest['config']==CONFIG and manifest['physical_gpu']==0 and manifest['runtime_code_commit']==BASE
 paths={'framework/model/Quard_model/'+manifest['candidate_name']+'/'+n:h for n,h in manifest['candidate_source_hashes'].items()};paths[CONFIG]=manifest['candidate_config_sha256'];assert len(paths)==9
 assert set(git('diff-tree','--no-commit-id','--name-status','-r',COMMIT).decode().splitlines())=={'A\t'+x for x in paths}
 for name,h in paths.items():assert sha(CODE/name)==h and hashlib.sha256(git('show',COMMIT+':'+name)).hexdigest()==h
 b=read(HERE/'protected_assets_before.json');assert len(b['files'])==28 and git('status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and all(sha(CODE/x)==h for x,h in b['files'].items()) and not git('diff','--cached','--name-only','-z')
 return manifest,paths

def protected_others():
 assert sha(LIFECYCLE)==evidence.read(HERE/'fcb_summary_outputs.json')['lifecycle_baseline']['sha256'];b=read(LIFECYCLE);q=read(ROOT/'pipeline/queue.json');r=read(ROOT/'pipeline/running.json');w=read(ROOT/'pipeline/research_work.json')
 normalized=copy.deepcopy(q)
 for rows in normalized['gpu_queues'].values():rows[:]=[x for x in rows if x.get('id')!=EXP]
 assert normalized==b['queue'];assert [(s,str(g),eid) for s,gs in r.items() for g,eid in gs.items() if eid!=EXP]==[(s,str(g),eid) for s,gs in b['running'].items() for g,eid in gs.items()]
 for name,h in b['protected_ledgers'].items():
  if name not in ('queue.json','running.json'):assert sha(ROOT/'pipeline'/name)==h,name
 digest=lambda c:hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
 assert set(c['id'] for c in w['candidates'])==set(b['candidate_digests']) and all(digest(c)==b['candidate_digests'][c['id']] for c in w['candidates'] if c['id']!=CID)
 return b

def decision_path(stdout):
 value=stdout.strip().rsplit('-> ',1)[-1].strip()
 if re.match(r'^/[a-zA-Z]/',value):value=value[1].upper()+':/'+value[3:]
 p=Path(value).resolve();assert p.is_relative_to((ROOT/'pipeline/decisions').resolve()) and p.is_file();return p

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_ADMISSION_QUEUE_WRITE');return
 evidence.require_execution();evidence.reviewed()
 owner=guard();assert owner['token']=='68d6c0e3561947c69bfcbb6a4b514d74' and os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode
 assert not any((HERE/n).exists() for n in ['fcb_admission_intent.json','fcb_admission_queue_result.json']) and not (ROOT/'pipeline/admissions/M223-FCB.json').exists(),'Existing/partial admission requires read-only reconciliation, never replay'
 assert sha(REVIEW)==evidence.review_ref()['sha256'];local=read(REVIEW);assert local['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION' and local['observations']['native_semantics_and_pairing_checked'] is True and local['observations']['resource_protocol_checked'] is True and local['standard_PASS_receipt_queue_written'] is False
 identity={'id':EXP,'candidate_id':CID,'config':CONFIG,'code_commit':COMMIT,'goal_sha256':GOAL}
 assert all(local.get(k)==v for k,v in identity.items()) and local['observations']['existing_memory_condition_needs_separate_retention_decision'] is False
 reviews=[]
 for entry in [evidence.independent_ref()]:
  p=ROOT/entry['path'];assert sha(p)==entry['sha256'] and read(p)['material_concerns']==[];reviews.append(ref(p))
 assert local['independent_reviews']==reviews
 for item in local['evidence']:assert sha(ROOT/item['path'])==item['sha256']
 assert len(local['raw_results'])==4
 for item in local['raw_results']:
  p=ROOT/item['path'];assert sha(p)==item['sha256'];envelope=read(p);raw=envelope['result'];assert envelope['certainty']=='terminal' and envelope['returncode']==0 and raw['execution_completed'] is True and raw['candidate_id']==CID and raw['code_commit']==COMMIT and raw['goal_sha256']==GOAL
 standards={'smoke':HERE/'fcb_native_smoke.json','resources':HERE/'fcb_resource_comparison.json','constraints':HERE/'fcb_constraints_independence.json'};std={k:read(p) for k,p in standards.items()}
 for value in std.values():
  assert all(value.get(k)==v for k,v in identity.items())
  for item in value['evidence']:assert sha(ROOT/item['path'])==item['sha256']
 assert std['smoke']['steps']==2 and type(std['smoke']['steps']) is int and len(std['smoke']['losses'])==2 and all(type(x) in (int,float) and math.isfinite(x) for x in std['smoke']['losses'])
 assert all(std['smoke'][x] is True for x in ['native_data_loaded','backward_finite','intended_path_observed']) and std['smoke']['split']=='train'
 assert std['resources']['passed_existing_resource_requirements'] is True and std['constraints']['passed'] is True and std['resources']['observations']['candidate']['profile']['flops']<=10e9
 sys.path.insert(0,str(SKILL));import closure,pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();manifest,paths=check_source();protected_others();queue=monitor.load_queue(str(ROOT));work=read(ROOT/'pipeline/research_work.json');before_work=copy.deepcopy(work)
  assert not any(t.get('id')==EXP for ts in queue['gpu_queues'].values() for t in ts) and monitor.load_experiment(str(ROOT),EXP) is None
  c=next(x for x in work['candidates'] if x['id']==CID);assert c['stage']=='validation' and c['code_commit']==COMMIT and c['authorization']==AUTH and not c.get('revision_history') and not c.get('implementation_revision_sha256')
  assert not any(c.get(k) for k in ['human_hold','scope_hold','numerical_hold','dispatch_hold','hold','paused','requires_human','requires_confirmation','needs_confirmation'])
  now=datetime.now(timezone.utc).isoformat();task={'id':EXP,'label':'FCB fine-coarse complete-bipartite composition','config':CONFIG,'code_commit':COMMIT,'admission_receipt':'pipeline/admissions/M223-FCB.json','status':'waiting','gpu':'0','server':'server-4','profile':'experiment_first','added_at':now,'note':'Original seed1999/nativeYAML/50epochs/maxiters70 unchanged. Actual pairedTRAIN2/resources independently reviewed; technical admission is not efficacy. Preserve all actual canonical terminal archives, all prior terminal receipts and M206 user pause. No borrowed result or model revision; original FCB source graph unchanged.'}
  save(HERE/'fcb_admission_intent.json',{'owner':{k:owner[k] for k in ['token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256']},'recorded_at':now,'operation':'FCB-only actual experiment-first admission and FIFO waiting, no launch','before_work_sha256':sha(ROOT/'pipeline/research_work.json'),'fresh_lifecycle':ref(LIFECYCLE),'actual_review':ref(REVIEW),'standards':{k:ref(p) for k,p in standards.items()},'independent_reviews':reviews,'task':task,'partial_policy':'Never blindly replay or overwrite partial receipt/work/queue; reconcile exact existing attempt.'})
  logargs=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','queue_push','Admit exact compatible FCB after actual matched original TRAIN2 and resource pair?','Create actual experiment-first receipt and FIFO GPU0 waiting; this helper does not launch.','Actual2TRAIN finite backward/updates, whole two-map core aggregate weight gradient/update and actual pair-map plus middle-map/GELU calls/same q two marginals/third mean from fine delta to original middle parents/original IDs/threeLN-skips/HCG-inst path; individual map/pair/row/four-column/bias zero legal; original paired resources/handlers and full unsupported retained. Efficacy/novelty/pureTRAIN UNKNOWN; paired median/P90 retained descriptively without a new latency gate. Original canonical terminal states retained and M206 pause preserved.','; '.join(x['path']+' SHA'+x['sha256'] for x in [ref(p) for p in standards.values()]+reviews)]
  guard();run=subprocess.run(logargs,capture_output=True,text=True,encoding='utf8',timeout=30,env=os.environ.copy());assert run.returncode==0,run.stderr;decision=decision_path(run.stdout)
  receipt={**identity,'profile':'experiment_first','authorization':AUTH,'native_smoke':ref(standards['smoke']),'decision':ref(decision),'created_at':now,'promotion_owner':{k:owner[k] for k in ['token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256']},'current_resource_authorization':RESOURCE_AUTH,'independent_reviews':reviews,'gates':{name:{'passed':True,'evidence':[ref(standards[kind]),*reviews]} for name,kind in [('native_backward','smoke'),('resources','resources'),('independence','constraints'),('constraints','constraints')]},'efficacy':'UNKNOWN; technical admission is not successful training or accuracy gain.'}
  save(ROOT/'pipeline/admissions/M223-FCB.json',receipt);closure.admission(ROOT,task)
  prospective=copy.deepcopy(queue);prospective['gpu_queues']['server-4'].append(task);closure.validate_foreground_dispatch_budget(ROOT,prospective,task)
  c.setdefault('execution_preparation_history',[]).append({'recorded_at':now,'reason':'Preserve prior static preparation before actual four-arm admission','worker_preparation':copy.deepcopy(c.get('worker_preparation')),'execution_adapter':copy.deepcopy(c.get('execution_adapter')),'prior_native_status':c.get('native_status'),'prior_resource_status':c.get('resource_status'),'prior_native_execution':copy.deepcopy(c.get('native_execution'))})
  c.update(stage='deployment',training_status='waiting',experiment_first_admission=True,admission_receipt=ref(ROOT/'pipeline/admissions/M223-FCB.json'),native_status='ACTUAL_ORIGINAL_TRAIN2_BACKWARD_PATH_UPDATES_PASSED',resource_status='ACTUAL_ORIGINAL_PAIRED_RESOURCES_PASSED',native_execution=ref(REVIEW),native_execution_code_commit=COMMIT,native_smoke_status='ACTUAL_TRAIN2_PASSED',resource_profile_status='ACTUAL_PAIRED_RESOURCES_PASSED',admission_status='ADMITTED_WAITING',implementation_status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCE_PAIR_VERIFIED',source_status='TESTED_FCB_COMPATIBLE_PRESENT_MAIN',next_action='Canonical one-shot GPU0 dispatch must revalidate exact source/runtime/idle/assets/UUID/three locks/original deadline and real progress. Preserve original PES, current AOC and all earlier terminal archives/receipts and M206 user pause; no blind replay, GPU1 or sibling-source promotion.')
  for k in ['blocker_kind','blocker','blocked_at','retry_after','unblock_condition']:c.pop(k,None)
  c['worker_preparation'].update(status='ACTUAL_NATIVE_TRAIN2_AND_RESOURCES_COMPLETED_PASSED',native_backward_executed=True,resource_profile_executed=True,native_backward_passed=True,resources_passed=True,active_native_manifest_or_execution_lease_created=True)
  c['execution_adapter'].update(status='ACTUAL_FRESH_BINDING_FOUR_ARMS_TERMINAL_REVIEWED',native_execution_tested=True,native_execution_code_commit=COMMIT,remote_adapter_execution_tested=True,active_binding_manifest_lease_created=True,transport_executed=True,standard_summaries_created=True,active_binding=ref(HERE/'fcb_execution/execution_binding.json'),native_manifest=ref(HERE/'fcb_execution/native_manifest.json'),execution_lease=ref(HERE/'fcb_execution/execution_lease.json'),actual_four_result_review=ref(REVIEW),execution_results={m+'_'+t:ref(HERE/'fcb_execution'/(m+'_'+t+'_execution.json')) for m,t in [('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]})
  for item in [*[ref(p) for p in standards.values()],*reviews,ref(REVIEW),ref(ROOT/'pipeline/admissions/M223-FCB.json'),ref(decision)]:
   if item not in c['evidence']:c['evidence'].append(item)
  work['updated_at']=now;assert {x['id']:x for x in work['candidates'] if x['id']!=CID}=={x['id']:x for x in before_work['candidates'] if x['id']!=CID}
  guard();protected_others();check_source();replace(ROOT/'pipeline/research_work.json',work);guard();monitor.save_queue(str(ROOT),prospective)
  guard();monitor.save_experiment(str(ROOT),{**task,'history':[{'ts':now,'status':'waiting','action':'actual_experiment_first_admission_queued','receipt':ref(ROOT/'pipeline/admissions/M223-FCB.json')}]})
  protected_others();check_source();save(HERE/'fcb_admission_queue_result.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'id':EXP,'task':task,'receipt':ref(ROOT/'pipeline/admissions/M223-FCB.json'),'decision':ref(decision),'standard_artifacts':{k:ref(p) for k,p in standards.items()},'canonical_admission_validated':True,'canonical_tick_budget_validated':True,'protected_other_candidates_and_original_lifecycle_preserved':True,'training_launched':False,'source_sync_performed':False})
  print(json.dumps({'status':'ADMITTED_WAITING_NOT_LAUNCHED','id':EXP,'receipt':ref(ROOT/'pipeline/admissions/M223-FCB.json'),'result':ref(HERE/'fcb_admission_queue_result.json')}))
 finally:lock.close()
if __name__=='__main__':main()
