"""Bind the human's scoped exploratory authorization to the tested CPA bundle."""
from ops import *
import closure
import pipeline_monitor as monitor

guard()
package=tick.load(PREVIOUS/'independent_package.json')
code=ROOT/'Cluster'
files={}
for name,digest in package['source_hashes'].items():
    path=Path(package['source_path'])/name
    assert tick.digest(path)==digest,name
    files[path.relative_to(code).as_posix()]=digest
config=package['candidate_config']['path'].removeprefix('Cluster/')
assert tick.digest(code/config)==package['candidate_config']['sha256']
files[config]=tick.digest(code/config)
work=tick.load(ROOT/'pipeline/research_work.json')
candidate=next(c for c in work['candidates'] if c['id']==CID)
assert candidate['gates']['diagnosis']['passed'] is False
assert candidate['gates']['controls']['passed'] is False
assert candidate['revision_history'][-1]['result']=='inconclusive'
for gate in ('native_backward','resources','independence'):
    assert candidate['gates'][gate]['passed'] is True
    for item in candidate['gates'][gate]['evidence']:closure.artifact(ROOT,item)
live=ssh('''import json,subprocess,fcntl
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [x.strip() for x in row.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
    h=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
    try:fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available'
    except BlockingIOError:locks[kind]='busy'
    finally:h.close()
root='/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b'
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()
dirty=subprocess.check_output(['git','-C',root,'status','--short','--untracked-files=no'],text=True).splitlines()
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),gpu=row,contexts=contexts,locks=locks,remote_head=head,remote_tracked_changes=dirty)))
''')
save('initial_environment.json',live)
auth={
 'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'project':'cluster_project',
 'thread_id':THREAD,'candidate_id':CID,'experiment_id':'M204-CPA','kind':'single_manual_exploratory_training',
 'human_reply_verbatim':'授权',
 'reply_to':'是否授权 CPA-R1 先做一次探索性训练，保留未通过标记，使用 server4 GPU0、seed 1999、batch 2、50 epochs，不调参？',
 'provenance':'Unambiguous human reply in the owning chat after the explicit scoped question;not a heartbeat or agent-generated consent.',
 'authorized':True,'maximum_training_launches':1,'automatic_retry_or_restart':False,
 'operations':['scoped local commit of the nine tested files','safe fast-forward synchronization to server-4 only','one guarded native training launch and progress verification'],
 'server':'server-4','physical_gpu':0,'hostname':'dl04-MS-7E06','gpu_uuid':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',
 'config':config,'files':files,'goal_sha256':GOAL,'base_code_commit':closure.git(code,'rev-parse','HEAD'),
 'seed':1999,'batch_size':2,'workers':4,'epochs':50,'max_iters':70,'pretrain_only':'original sp_unet_backbone.pth','resume':None,
 'scientific_admission':False,'diagnosis_passed':False,'semantic_controls_passed':False,
 'implementation_revision_result':'inconclusive','revision_history_unchanged':True,
 'exception':'One-candidate operational permission to train despite unresolved pre-training diagnosis/semantic-control and passed-revision prerequisites. This is NOT a scientific PASS or a general pipeline-policy change.',
 'preserved_constraints':'All other goal constraints, bans, lightweight limits, fixed data/validation boundaries, GPU permissions and scheduler settings stay unchanged.',
 'prior_evidence':evidence(ROOT/'pipeline/diagnostic_bundles/tick_4419252f/launch_request_review.json')}
auth_path=ROOT/'pipeline/authorizations/cpa_exploratory_20261019_72695a5d.json'
guard();auth_path.parent.mkdir(parents=True,exist_ok=True)
assert not auth_path.exists()
tick.save(auth_path,auth)
save('authorization_binding.json',{'authorization':evidence(auth_path),'files':files,'remote_probe':evidence(OUT/'initial_environment.json')})
advance([auth_path,OUT/'authorization_binding.json',OUT/'initial_environment.json'],
 exploratory_training_authorization=evidence(auth_path),
 next_action='Execute the human-authorized single CPA-R1 exploratory run on server4GPU0;scientific gates/revision stay unresolved,verify native steps before training disposition')
decision=monitor.log_decision(str(ROOT),'manual','用户明确回复授权，是否执行CPA-R1单次探索性训练？',
 '仅为M204-CPA在server4GPU0执行限定提交、安全同步与一次原生训练；保留diagnosis/semantic controls未通过与revision1 inconclusive。',
 '人工明确授权覆盖此候选训练前科学准入限制，不影响其他候选或资源、seed1999/batch2/workers4/epochs50/max_iters70、禁调参等约束。',
 str(auth_path))
advance([Path(decision)])
print(json.dumps({'authorization':str(auth_path),'file_count':len(files),'environment':live,'decision':decision},ensure_ascii=False,indent=2))
