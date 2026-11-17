"""Create one scoped, falsifiable primary-axis diagnosis under this tick lease."""
from datetime import datetime,timezone
import json,hashlib,os,sys
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
root=Path('D:/project/cluster_project');out=Path(__file__).resolve().parent
token='28fc3749e22e4c968fcadf9b6a2907a6';cid='m95-scale-specific-boundary-responsibility'
owner=tick.load(root/'pipeline/headless/.foreground.lockdir/owner.json')
assert owner['token']==token and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
assert datetime.fromisoformat(owner['deadline_at'])>datetime.now(timezone.utc)
assert tick.digest(root/'pipeline/goal.json')=='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
work=tick.load(root/'pipeline/research_work.json')
assert not any(c['id']==cid for c in work['candidates']),'Reuse the existing ID instead of creating duplicates'
def evidence(path):return {'path':path.relative_to(root).as_posix(),'sha256':tick.digest(path)}
candidate={'id':cid,'stage':'diagnosis','kind':'primary_point_feature_scale_responsibility_diagnosis','created_at':datetime.now(timezone.utc).isoformat(),'hypothesis_id':'native-fine-versus-coarse-boundary-marginal-effect','hypothesis':'In the existing trained M95 point-feature update, fine-scale contextual readback carries a larger unique marginal mask contribution on receivers inside fine cells containing both native positive and negative target superpoints than on interior receivers,relative to coarse readback. The paired difference-of-differences should be positive. This is a task-specific scale-responsibility diagnosis,NOT a new claim from pooled rank/mean blindness or an already rejected mechanism.','matched_control':'Original fixed trained M95,frozen TRAIN scenes and native supervision/matching;identity reconstruction control plus separate deletion of ONLY one existing fine/middle/coarse message before original fusion. Hold original query features,all model weights,other scale messages and mask readout fixed in paired replay. Define mixed-cell membership from original native target/fine assignment before interventions. No new projection,gating,residual,routing,normalization,loss,seed or tuning.','next_action':'Run the cheapest native source/CPU graph and target-index contract,then bind the existing frozen TRAIN scene/asset manifest before paired actual-mask replay. Verify live authorized identity/idleness/lease before CUDA;preserve the running M204. No new training admission from this diagnosis.','failure_scope':'inconclusive','gate_result':'Pending source/CPU/native tests;no task-deficit or efficacy conclusion yet','gates':{'diagnosis':{'passed':False,'reason':'Preregistered task-scale interaction has not been measured'},'controls':{'passed':False,'reason':'Native matched identity/query/target indexing controls pending'},'native_backward':{'passed':False,'reason':'No new mechanism or candidate backward claimed'},'resources':{'passed':False,'reason':'No resource result for a new mechanism'},'independence':{'passed':False,'reason':'Diagnostic only,not an admitted model package'},'constraints':{'passed':False,'reason':'No scientific admission or new training requested'}},'evidence':[evidence(out/'scale_responsibility_prereg.md'),evidence(Path(__file__))]}
work['candidates'].append(candidate)
tick.save(root/'pipeline/research_work.json',work)
print(json.dumps({'created_candidate_id':cid,'stage':'diagnosis','new_candidates':1,'training_launches':0,'scientific_gates_passed':0},ensure_ascii=True))
