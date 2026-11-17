"""Bounded producer-key/disabled-template source checks; never imports a helper."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_5f3e6c7b/aoc_promotion_prepare'
PRODUCER=ROOT/'pipeline/diagnostic_bundles/tick_89d05b33/fcb_native_prepare/worker.py'
SOURCES=['fcb_evidence.py','summarize_fcb_actual.py','fast_forward_tested_fcb.py','admit_fcb_queue.py','dispatch_fcb_once.py']
KEYS=['shapes','names','excluded_name_prefixes','FCB_fine_coarse_bipartite_observations','actual_true_pairs','actual_true_fine_paths','actual_pair_map_calls','actual_middle_map_calls','actual_map_calls','actual_GELU_calls','actual_private_mean_calls','actual_three_LN_calls','actual_original_builder_calls','plans','actual_same_q_two_marginals','actual_middle_context_from_original_fine_parent_mean','final_deltas_from_actual_captures_exact','unsupported_padding_deltas_zero','all_observed_internal_gradients_finite','whole_fine_coarse_bipartite_weight_gradient','whole_fine_coarse_bipartite_weight_updated','whole_fine_coarse_bipartite_module_updated']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text('utf8'))
def validate():
 checks=[]
 def check(label,ok):assert ok,label;checks.append(label)
 for name in SOURCES:compile((HERE/name).read_text('utf8'),str(HERE/name),'exec');check('compile_without_import:'+name,True)
 producer=ast.parse(PRODUCER.read_text('utf8'))
 keys={n.value for n in ast.walk(producer) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
 keys.update(n.arg for n in ast.walk(producer) if isinstance(n,ast.keyword))
 consumer=(HERE/'fcb_evidence.py').read_text('utf8');tree=ast.parse(consumer)
 check('producer_has_every_FCB_specific_consumer_key',all(k in keys for k in KEYS))
 check('actual_shapes_key_preserved',"['shapes']" in consumer and 'shaaoc' not in consumer and 'shafcb' not in consumer)
 check('DRAFT_true',next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='DRAFT_EXECUTION_DISABLED' for x in n.targets)) is True)
 check('actual_references_null',all(read(HERE/'evidence_bindings.json')[k] is None for k in ['independent_review','actual_four_result_review','actual_raw_results']))
 b=read(HERE/'source_bindings.json')
 check('real_source_parent_native',b['code_commit']=='d4d062ef075abfe7cde93d4b4347ce146572762f' and b['parent_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33' and b['native_preparation']['sha256']=='cc9dcf1245a273d9eed569d10afd26f0d3a04c8cec37fff54314f065c195bba3')
 check('source_refs_real_hashes',all(sha(ROOT/e['path'])==e['sha256'] for e in b.values() if isinstance(e,dict)))
 check('no_AOC_PES_specific_controls',not any(s in consumer for s in ['AOC_ancestral','PES_','actual_cell_calls','actual_cell_rows','actual_shared_cell_two_stage','contrast_from_actual_second','whole_ancestral','4E']))
 check('whole_core_only_trainability',all(s in consumer for s in KEYS[-3:]) and not any(s in consumer for s in ['column_weight_gradient','pair_map_weight_updated','middle_map_weight_updated']))
 check('calls1_1_GELU2_mean3',"['actual_pair_map_calls']==observed['actual_middle_map_calls']==1" in consumer and "['actual_private_mean_calls']==3" in consumer)
 check('current_owner_token','9169196d4bde408385418bf246bd8364' in (HERE/'admit_fcb_queue.py').read_text('utf8'))
 check('four_CLI_default_noop',all('if not args.execute_root' in (HERE/n).read_text('utf8') for n in SOURCES[1:]))
 check('ordinary_FIFO_no_exclusivity_field',all('requires_exclusive_ownership' not in (HERE/n).read_text('utf8') for n in SOURCES))
 old=(ORIGIN/'aoc_evidence.py').read_text('utf8').split(" for raw in [results['resources_champion']",1)[1]
 new=consumer.split(" for raw in [results['resources_champion']",1)[1]
 check('resource_validator_namespace_only',new==old.replace('aoc','fcb'))
 return {'status':'STATIC_PRODUCER_CONTRACT_AND_COMPILE_CHECKS_PASSED_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),'checks_count':len(checks),'checks':checks,'producer':ref(PRODUCER),'required_keys':KEYS,'checker':ref(Path(__file__).resolve()),'native':'NOT_RUN','resources':'NOT_RUN','root_or_API_entry_calls':0,'synthetic_native_results_generated':0}
if __name__=='__main__':
 result=validate()
 print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
