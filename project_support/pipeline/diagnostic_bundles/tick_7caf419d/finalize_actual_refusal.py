"""Honest closure of the consumed pre-Torch attempt; no native replay or admission."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import pipeline_monitor as monitor

def read(path): return json.loads(path.read_text(encoding='utf8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path))
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

owner=read(HERE/'current_owner_binding.json')
raw=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert {k:raw[k] for k in owner}==owner and owner['thread_id']==os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
for filename,key in (('.tick_context.json','context_sha256'),('.tick_context_state.next.json','pending_sha256')):
    assert sha(ROOT/'pipeline/headless'/filename)==owner[key]
actual_path=HERE/'cso_native_execution/run_smoke_candidate_actual.json'
actual=read(actual_path);observation=actual['observation'];result=observation['result']
assert actual['owner']==owner and actual['certainty']=='terminal' and actual['returncode']==0 and observation['returncode']==1
assert result['execution_completed'] is False and all(result[key]==0 for key in ('optimizer_steps','native_loss_forwards','native_criterion_backwards','native_predict_calls'))
assert result['error']=='Actual free GPU0 memory below 20000 MiB; external tasks remain untouched'
assert 'owner' not in result and 'code_commit' not in result
budget_path=HERE/'gpu0_overlay_budget_after_refusal.actual.json';budget=read(budget_path)
assert budget['observation']['memory_free_mib']==19494 and not budget['memory_budget_satisfied'] and budget['project_cap1_available']
reviews=[HERE/'peer_review'/name for name in ('cso_native_bound_independent_review.json','cso_native_refusal_independent_review.json','cso_native_refusal_supplement_independent_review.json','cso_integration_independent_review.json')]
for path in reviews:
    review=read(path);assert review['owner']==owner and review['passed'] is True and review['material_concerns']==[]
proof_path=HERE/'cso_integration_commit/commit_proof.json';proof=read(proof_path)
integrated=ROOT/'pipeline/isolated_versions/m236_cso_integrated_7caf419d'
commit='5413102c57b526035f3920b5e7a81f3b58ad764d'
assert subprocess.check_output(['git','--no-optional-locks','-C',str(integrated),'rev-parse','HEAD'],text=True).strip()==commit
assert subprocess.check_output(['git','--no-optional-locks','-C',str(integrated),'rev-list','--parents','-n','1','HEAD'],text=True).strip()==commit+' b1e639b3ceb14bb5c65d9f81a084d41c834b951c'
assert not subprocess.check_output(['git','--no-optional-locks','-C',str(integrated),'status','--porcelain=v1','--untracked-files=all'])
draft_path=HERE/'cso_ops_source_draft/SOURCE_MANIFEST.NOT_APPROVED.json'
refusal=dict(owner=owner,recorded_at=datetime.now(timezone.utc).isoformat(),kind='ACTUAL_KNOWN_TERMINAL_PRE_TORCH_MEMORY_REFUSAL',raw_actual=ref(actual_path),original_remote_result_sha256=observation['result_sha256'],original_missing_owner_and_code_commit_preserved=True,provenance_bound_by='Current outer wrapper, exact request/intent/lease/manifest and independent actual review; no edits to raw result.',native_model_executed=False,optimizer_steps=0,native_loss_forwards=0,native_criterion_backwards=0,native_predict_calls=0,actual_native_gate='NOT_RUN',actual_resource_gate='NOT_RUN',reason=result['error'],initial_direct_free_mib=21836,readiness_direct_free_mib=21830,post_refusal_direct_free_mib=19494,original_minimum_free_mib=20000,allow_external_overlay=True,remote_stage='/data/songcl/Project/Cluster_project/pipeline/cso_7caf419d_gpu0',execution_lease_created=True,remote_stage_created=True,attempt_consumed_no_replay=True,source_commit='af45707d7b6089f764843337c5f88af285383f88',runtime_commit='b1e639b3ceb14bb5c65d9f81a084d41c834b951c',retained_integration_commit=commit,integration_is_source_retention_only=True,new_admissions=0,new_training=0,resources_observation=ref(budget_path),reviews=[ref(path) for path in reviews],future_direct_free_guard_draft=ref(draft_path),guard_draft_status='SOURCE_ONLY_NOT_APPROVED_NOT_ADOPTED_NO_ACTUAL_QUERY',frozen_executed_packet_unchanged=True,efficacy='UNKNOWN',novelty='UNKNOWN')
save(HERE/'native_refusal_disposition.actual.json',refusal)
command=['python','-B','-X','utf8',str(HERE/'cso_native_bound/run_native_once.py'),'--execute-root','--experiment-id','M236-CSO','--mode','smoke','--target','candidate','--source-version',str(HERE/'cso_native_bound/source_version.json'),'--source-version-sha256','c3b2c05f7b91c1b04fb3176feed3eddde7ab993be65b4b43d469b5aa722fb4cc','--review',str(reviews[0]),'--review-sha256','fec59eeecb765740c0bd02e68d8202eaa39c33eca38c121b6f83b1e1a09faf23']
lock=monitor.acquire_lock(str(ROOT));assert lock is not None
try:
    work=read(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']=='fine-leaf-full-covariance-shape-composition')
    assert candidate['stage']=='blocked' and candidate['native']=='NOT_RUN' and candidate['resources']=='NOT_RUN'
    assert candidate['scientific_admission'] is False and candidate['queued'] is False
    candidate['retained_integration_version_proof']['independent_review']=ref(reviews[3])
    candidate['latest_execution_preparation']['after_refusal_review']=ref(reviews[2])
    candidate['latest_memory_readiness']['superseded_by_pre_torch_resource_refusal']=True
    candidate['native_refusal_disposition']=ref(HERE/'native_refusal_disposition.actual.json')
    candidate['future_memory_guard_draft']={'status':'SOURCE_ONLY_NOT_APPROVED_NOT_ADOPTED','evidence':ref(draft_path),'actual_query_executed':False,'next_action':'Next owner must independently review the minimal direct memory.free operational guard and bind a new stage; unchanged worker/model/YAML/TRAIN2/resources protocol is reused. No current consumed intent replay.'}
    candidate['next_action']='保留7caf已消费stage/lease/intent及原始pre-Torch显存拒绝，不重放、不补签NULL。待实际memory.free>=20000且cap1/三锁满足后，新owner另存绑定并先独审memory.free读取守卫；复用af457原源码/协议和5413102整合字节证明，真实两自然TRAIN/common841/九core更新与资源及独审通过后才准入入队。'
    paths=[HERE/'native_refusal_disposition.actual.json',reviews[2],reviews[3],draft_path,HERE/'cso_native_execution/source_binding.json',HERE/'cso_native_execution/native_manifest.json',HERE/'cso_native_execution/execution_lease.json',HERE/'cso_native_execution/run_smoke_candidate_request.json',HERE/'cso_native_execution/run_smoke_candidate_intent.json']
    for path in paths:
        entry=ref(path)
        if entry not in candidate['evidence']:candidate['evidence'].append(entry)
    work['tick_attempt']['command']=subprocess.list2cmdline(command)
    work['next_action']=candidate['next_action']
    decision_path=Path(monitor.log_decision(str(ROOT),'other','M236启动前显存变化导致原生验证拒绝，是否重试同一意图或把源码整合算作准入？','保留已消费阶段和真实零步拒绝；当前显存19494<20000，不重放、不准入。整合5413102仅保留版本，原生/资源仍NOT_RUN。','真实首次free21836/就绪21830不代表稍后仍可用；worker在Torch前因原预算拒绝，全部原生计数0；现存与外部任务、三锁、GPU范围及调度保持。','pipeline/diagnostic_bundles/tick_7caf419d/native_refusal_disposition.actual.json'))
    entry=ref(decision_path)
    if entry not in candidate['evidence']:candidate['evidence'].append(entry)
    save(ROOT/'pipeline/research_work.json',work)
finally:lock.close()
memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf8')
memory=memory.replace('原准备包cafab8dd及91c85c42绑定包649d4aaa/独审98cbe260复用；本轮不重建native包。新stage未创建/actuallease未创建，不表示远端producer实测通过；未来新owner另存绑定。','原source/protocol/worker复用；7caf当前绑定3d326e81及独审fec59eee通过，实际stage/lease已创建并因pre-Torch预算拒绝而消费，禁止重放；原结果缺owner/code字段保持。')
memory=memory.replace('GPU0本轮实际free18710MiB<原20000','GPU0本轮先free21836/就绪21830，启动前预算拒绝；后续直接free19494MiB<原20000')
memory=memory.split('## Last Tick')[0]+'''## Last Tick
- 7caf419d：先canonical核无训练/新终态，初次memory.free21836>=20000；严格SSH/运行rootb1/18项资产及环境哈希就绪核验通过，当时free21830。
- 最近M236仅owner/stage最小绑定；原生smoke尝试一次，acquire显存守卫在Torch前拒绝，SSH0/worker1，loss/backward/predict/optimizer计数全0，native/resources仍NOT_RUN，非机制失败。
- cso_7caf419d_gpu0及新lease/intent已消费并保存，不续写/重放/补签原NULL。后续直接free19494<20000；资源拒绝与补充独审a109b8af/0118e1a0通过，无准入/入队/训练。
- 已保留整合commit5413102(parentb1)与真实native sourceaf457完全相同CSO9，仅新增九文件；独审04608ef8通过。原主HEAD0747/index/dirty37和旧工作树保持，未sync远端。
- 操作层守卫草稿以实际memory.free替代total-used推算，供未来native/production新绑定采用；仅源码/语法/NOP，NOT_APPROVED，未独审或实测/采用，不改当前已执行冻结包或原20000预算。
- 当前需真实原预算槽位后新owner独审守卫并另存执行绑定，再真实TRAIN2/common841/九core更新/同口径资源；不为额度新增变体、恢复M235或M206/M227。证据tick_7caf419d。
'''
assert memory.count('\n## ')==7 and len(memory.splitlines())<120
(ROOT/'pipeline/codex_memory.md').write_text(memory,encoding='utf8')
notes=dict(actions=['先观察canonical原生/终态：无项目训练和新终态，M235原crashed与完整epoch1/partialepoch2证据保持，人工暂停项不动。','原显存检查free21836/就绪21830满足预算；本轮绑定及source/runtime/root/UUID/18项资产/producer核验后，实际执行M236原生smoke一次。worker在导入Torch前因显存不足原20000预算拒绝，全部原生计数0；后续直接free19494。','源代码与协议冻结复用；本地保留5413102整合版本，CSO9逐字节/原blob与af457一致、仅九文件新增，主HEAD/index/dirty37及旧工作树保持。源码/拒绝/后续资源/整合关联分别独审。','只保留未批准的直接memory.free操作守卫草稿供未来新绑定，未运行实际查询或更改当前冻结包。无原生/资源门槛PASS，无准入、入队、同步或训练。'],decisions=['初次预算满足不能替代实际启动前核验；本次守卫安全拒绝属于资源阻塞，不能当作候选机制失败或实际两步TRAIN成功。','当前free19494<20000，不重试同一已消费stage/intent，不续写旧lease、不补签原始缺失owner/code字段；允许外部共享，不要求空卡/零context/低利用率。','原生TRAIN2/common-init/九core更新及资源仍NOT_RUN；新owner需重核真实资源并另存/独审新执行绑定，未来guard直接读取memory.free，原预算/三锁/并发/GPU范围/暂停/调度不变。'])
save(HERE/'report_notes.json',notes)
before=read(HERE/'research_work.json.before');after=read(ROOT/'pipeline/research_work.json');old={c['id']:c for c in before['candidates']};new={c['id']:c for c in after['candidates']};assert {cid for cid in old if old[cid]!=new[cid]}=={'fine-leaf-full-covariance-shape-composition'}
baseline=read(HERE/'integrity_before.json');repo=ROOT/'Cluster'
assert sha(ROOT/'pipeline/goal.json')==baseline['goal_sha256'] and sha(ROOT/'SERVERS.yaml')==baseline['servers_sha256']
assert subprocess.check_output(['git','--no-optional-locks','-C',str(repo),'rev-parse','HEAD'],text=True).strip()==baseline['local_main_HEAD']
assert sha(repo/'.git/index')==baseline['index_sha256'] and all(sha(repo/name)==digest for name,digest in baseline['dirty_sha256'].items())
assert read(ROOT/'pipeline/queue.json')==read(HERE/'queue.json.before')
assert sha(ROOT/'pipeline/experiments/M235-SINC.json')=='8f8bc6c3791823ec4166a3097e6e9a5617820b9a2d97ce4809171f7d127c9c62'
save(HERE/'completion_audit.actual.json',dict(owner=owner,other161_candidates_unchanged=True,queue_and_manual_pauses_unchanged=True,M235_archive_unchanged=True,protected37_index_goal_SERVERS_unchanged=True,integration_commit=commit,integration_source_only=True,remote_sync=False,native_model_executed=False,optimizer_steps=0,native='NOT_RUN',resources='NOT_RUN',new_candidates=0,new_admissions=0,new_training=0,consumed_attempt_preserved=True,original_missing_fields_preserved=True,decision=ref(decision_path),refusal_disposition=ref(HERE/'native_refusal_disposition.actual.json')))
print(json.dumps(dict(status='PRE_TORCH_BLOCK_AND_SOURCE_RETENTION_CLOSED_HONESTLY',native='NOT_RUN',resources='NOT_RUN',steps=0,new_admissions=0,other161_unchanged=True,protected37_unchanged=True,notes=str(HERE/'report_notes.json'))))
