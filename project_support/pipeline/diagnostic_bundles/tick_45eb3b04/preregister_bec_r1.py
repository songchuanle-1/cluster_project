"""Preregister one bounded implementation repair; preserve failed native evidence."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 owner=guard();assert not (HERE/'bec_revision1_preregistration.json').exists()
 fail=HERE/'bec_execution/resources_candidate_execution.json';raw=json.loads(fail.read_text('utf8'))
 assert sha(fail)=='f8fac959a9b040838710d9a7199ea5a9e552bc364904e6d0b182feb77811c4f5'
 assert raw['certainty']=='terminal' and raw['returncode']==1 and not raw['result']['execution_completed'] and 'aten::index_fill' in raw['result']['error']
 checker=HERE/'bec_actual_four_result_review.json';assert json.loads(checker.read_text('utf8'))['review_status']=='REFUSED_MISSING_OR_INVALID_ACTUAL_EVIDENCE'
 sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as monitor;import closure
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();path=ROOT/'pipeline/research_work.json';work=json.loads(path.read_text('utf8'));c=next(x for x in work['candidates'] if x['id']=='hierarchy-cross-level-bipartite-edge-composition');old=copy.deepcopy(c)
  assert c['code_commit']=='9b6782f44ca7f2c8ac35baea01dfd070314b5701' and c['stage']=='validation' and c.get('revision_history',[])==[]
  now=datetime.now(timezone.utc).isoformat()
  revision={'revision':1,'failure_scope':'implementation','reason':'Original true two-step TRAIN smoke succeeded, but original fvcore/PyTorch JIT resource trace fails on bool scalar argument to aten::index_fill; no measured budget failure or mechanism falsification.',
   'change':'First reproduce exact bool index_fill tracer failure on same server CPU and compare bool mask eager outputs against integer-one scalar. Only if exact semantics match and tracer accepts it, change BEC bipartite_edges.py coarse support-mask index_fill scalar True to integer1; no graph routing, weights, masks, seed, data, YAML, profiler handlers or thresholds change. Save new isolated compatible source/version/tool copy; never patch frozen9b/2d/322c.',
   'prediction':'Matched CPU dtype/shape/mask outputs remain exactly equal while original tracer error disappears. Then on the new exact version rerun original fixed M95/BEC two TRAIN batches and original resource pair on an actually idle allowed GPU; require same original native/gradient/common/source/resource gates. If not reproduced or compatibility differs, mark inconclusive/failed; no resampling, threshold relaxation or automatic second revision.',
   'failure_evidence':[ref(fail),ref(checker)],'preregistered_at':now,'result':'pending','evidence':[]}
  c['revision_history']=[revision];c['implementation_revisions']=1;c['failure_scope']='implementation';c['native_status']='ACTUAL_TRAIN2_SUCCEEDED_RESOURCE_JIT_INDEX_FILL_FAILED_R1_PREREGISTERED'
  c['native_execution_code_commit']=c['code_commit'];c['native_smoke_status']='EXECUTED_TWO_STEPS_FINITE_PAIR_REVIEW_PENDING';c['resource_status']=c['resource_profile_status']='FAILED_PROFILER_IMPLEMENTATION_NOT_BUDGET_RESULT'
  c['next_action']='Advance preregistered BEC R1 CPU trace reproduction and exact bool-mask compatibility first; only then save new isolated source compatible with actual main, bind new tools and actually rerun original native/resource gates. Preserve original9b smoke and JIT failure; do not relabel raw or queue without complete passed results. This local hold does not block independent CTS.'
  for p in [fail,checker,HERE/'bec_execution/smoke_champion_execution.json',HERE/'bec_execution/smoke_candidate_execution.json',HERE/'bec_execution/resources_champion_execution.json']:
   item=ref(p)
   if item not in c['evidence']:c['evidence'].append(item)
  closure.validate_revisions(str(ROOT),c,old)
  record={'token':owner['token'],'candidate_id':c['id'],'original_code_commit':c['code_commit'],'preregistration':revision,'source_changed':False,'native_result_relabelled':False}
  with (HERE/'bec_revision1_preregistration.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  c['evidence'].append(ref(HERE/'bec_revision1_preregistration.json'));work['updated_at']=now;guard()
  temporary=path.with_name(path.name+'.'+owner['token']+'.r1.tmp')
  with temporary.open('x',encoding='utf8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(temporary,path)
  print(json.dumps({'revision':1,'result':'pending','preregistered_at':now,'evidence':ref(HERE/'bec_revision1_preregistration.json'),'source_changed':False}))
 finally:lock.close()
if __name__=='__main__':main()
