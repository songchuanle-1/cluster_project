'Create actual NEC summaries only after four raw results and real independent review.'
import argparse,csv,hashlib,io,json,sys
from datetime import datetime,timezone
from pathlib import Path
import nec_evidence as e
ROOT=e.ROOT;HERE=e.TICK

def save(p,o):
 e.guard()
 with p.open('x',encoding='utf8') as f:json.dump(o,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');args=ap.parse_args()
 if not args.execute_root:print('DRAFT_READ_ONLY_NO_SUMMARIES');return
 e.require_execution();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon
 lock=mon.acquire_lock(str(ROOT));assert lock is not None
 try:
  m,raw,refs=e.reviewed();sc=raw['smoke_champion'];s=raw['smoke_candidate'];rc=raw['resources_champion'];r=raw['resources_candidate']
  assert not any((HERE/n).exists() for n in ['nec_summary_intent.json','nec_actual_four_result_review.json','nec_native_smoke.json','nec_resource_comparison.json','nec_constraints_independence.json','nec_before_admission_lifecycle.json','nec_summary_outputs.json']),'Existing/partial summaries require readonly reconciliation'
  b=e.read(HERE/'protected_assets_before.json');q=e.read(ROOT/'pipeline/queue.json');w=e.read(ROOT/'pipeline/research_work.json')
  assert not any(t.get('id')==e.EXP for ts in q['gpu_queues'].values() for t in ts)
  baseline={'recorded_at':datetime.now(timezone.utc).isoformat(),'queue':q,'running':e.read(ROOT/'pipeline/running.json'),'csv_rows':list(csv.DictReader(io.StringIO((ROOT/'pipeline/experiments.csv').read_text('utf-8-sig')))),'protected_ledgers':{n:e.sha(ROOT/'pipeline'/n) for n in b['protected_ledgers']},'candidate_digests':{c['id']:hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest() for c in w['candidates']}}
  save(HERE/'nec_summary_intent.json',{'owner':e.EXPECTED,'operation':'Four actual NEC results to review and standards only','independent_review':e.independent_ref(),'raw_results':refs[:4]})
  save(HERE/'nec_before_admission_lifecycle.json',baseline)
  identity={'id':e.EXP,'candidate_id':e.CID,'config':e.CONFIG,'code_commit':e.COMMIT,'goal_sha256':e.GOAL};now=datetime.now(timezone.utc).isoformat()
  needs=r['peak_allocated_bytes']>rc['peak_allocated_bytes']*1.15
  observed={t:{k:x[k] for k in ['parameters','median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes','profile']} for t,x in [('champion',rc),('candidate',r)]}
  limitations={'efficacy':'UNKNOWN','novelty':'UNKNOWN','pure_TRAIN_memory':'UNKNOWN; smoke has observers, resource process no optimizer','optional_boundaries':'Only actual natural coverage; absent cases NOT_EXERCISED','timing':'Actual slower/faster measurements are descriptive, no new latency gate','initial_import_failure':'Only actual current compatible NEC source requests count. Earlier other-candidate import failures remain separate; no inherited success or root-cause repair claim'}
  obs={'native_semantics_and_pairing_checked':True,'resource_protocol_checked':True,'losses':s['losses'],'paired_batches':s['batches'],'common_initialized_parameter_observations':{k:v for k,v in s['common_initialized_parameters'].items() if k!='names'},'resource_observations':observed,'existing_memory_condition_needs_separate_retention_decision':needs,'relative_candidate_delta':{k:r[k]/rc[k]-1 for k in ['median_ms','p90_ms','peak_allocated_bytes','peak_reserved_bytes']}}
  review={**identity,'recorded_at':now,'review_status':'RAW_SEMANTICS_VALIDATED_NOT_ADMISSION','observations':obs,'raw_results':refs[:4],'independent_reviews':[e.independent_ref()],'evidence':refs,'limitations':limitations,'standard_PASS_receipt_queue_written':False}
  save(HERE/'nec_actual_four_result_review.json',review);refs.append(e.ref(HERE/'nec_actual_four_result_review.json'))
  smoke={**identity,'recorded_at':now,'steps':2,'losses':s['losses'],'native_data_loaded':True,'backward_finite':True,'intended_path_observed':True,'split':'train','command':s['actual_train_command'],'data_source':s['data_source']['train'],'paired_TRAIN_batches':s['batches'],'evidence':refs,'limitations':limitations}
  resource={**identity,'recorded_at':now,'passed_existing_resource_requirements':not needs,'protocol':{'batch_size':1,'lang_num_max':1,'warmup':20,'repeat':100,'counted_flops_limit':10e9},'observations':observed,'evidence':refs,'limitations':limitations}
  paths={'framework/model/Quard_model/'+m['candidate_name']+'/'+n:h for n,h in m['candidate_source_hashes'].items()};paths[e.CONFIG]=m['candidate_config_sha256'];assert len(paths)==9
  constraints={**identity,'recorded_at':now,'passed':True,'source_hashes':paths,'checks':{'actual_native_semantics_and_pairing_reviewed':True,'original_trueforest_persistent_node_edge_OLDendpoint_NEWincident_actual_Drounds_3scatter_LN_skips_HCG_inst_path':True,'source_and_native_YAML_identity':True,'same_seed1999_data_pretrain_optimizer_precision_50_maxiters70':True,'GPU0_only_and_current_goal_scope':True},'evidence':refs,'limitations':limitations}
  for n,o in [('nec_native_smoke.json',smoke),('nec_resource_comparison.json',resource),('nec_constraints_independence.json',constraints)]:save(HERE/n,o)
  save(HERE/'nec_summary_outputs.json',{'review':e.ref(HERE/'nec_actual_four_result_review.json'),'smoke':e.ref(HERE/'nec_native_smoke.json'),'resources':e.ref(HERE/'nec_resource_comparison.json'),'constraints':e.ref(HERE/'nec_constraints_independence.json'),'lifecycle_baseline':e.ref(HERE/'nec_before_admission_lifecycle.json'),'independent_review':e.independent_ref(),'admission_written':False})
  print(json.dumps(e.read(HERE/'nec_summary_outputs.json')))
 finally:lock.close()
if __name__=='__main__':main()
