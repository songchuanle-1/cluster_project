"""Disabled root-only BEC R1 static catalog anchor; import has no side effects."""
import argparse,copy,hashlib,json,math,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/project/cluster_project');CODE=ROOT/'Cluster';HERE=Path(__file__).resolve().parent;TICK=HERE.parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
ENABLE_ROOT_EXECUTION=True
OWNER={'token': '3d001030cda04cddade0810e9d380a22', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-26T10:05:37.308291+00:00', 'deadline_at': '2026-10-26T11:05:37.308291+00:00', 'context_sha256': '58907261bcdd1c77799391926782c69573a4c401610de57381fa2571d5cae71d', 'pending_sha256': 'bf6fc5e11ef8e1138972f47cb9bc8275838689ee8165547f194d4b0729abab0e'}
CID='hierarchy-cross-level-bipartite-edge-composition';EXP='M215-BEC'
NEW='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563';PARENT='4e80006047d5cb3dcdfb9c1102e02c33f354a07d';OLD='9b6782f44ca7f2c8ac35baea01dfd070314b5701'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
AUTH={'path':'pipeline/authorizations/experiment_first_20261021.json','sha256':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'}
RESOURCE={'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
OP=ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_operational_prepare'
NATIVE=OP/'native';CHECKER=ROOT/'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_execution_review_prepare'
PCE={'path':'pipeline/diagnostic_bundles/tick_e2e3d058/bec_r1_operational_independent_review.json','sha256':'0e3572192e3a0d68e8d4f656cdf3d74d15a8e3f9b1b2b79f2fcf4671f5dcc627'}
OP_REF={'path':OP.relative_to(ROOT).as_posix()+'/preparation.json','sha256':'9a81c28ac80f2f9f00184f67f7bd47841124cb8a18e0a22c554eaceb10957d35'}
NATIVE_REF={'path':NATIVE.relative_to(ROOT).as_posix()+'/preparation.json','sha256':'edd2049e2f990e94ffed784800797f033a27ef3a7f69dd928630715bf8bee078'}
CHECKER_REF={'path':CHECKER.relative_to(ROOT).as_posix()+'/preparation.json','sha256':'57752ca3a597f59c18f3d70f431d298ad15a43dbec848d3de3ca2004cd45e25b'}
PEER={'path':'pipeline/diagnostic_bundles/tick_faccbed6/bec_r1_checker_peer_review.json','sha256':'98def9573c07d8df7ad7840ca7661169f015c34dac62a9a703ad9c610061b19c'}
TEMPLATE_REF={'path':OP.relative_to(ROOT).as_posix()+'/release_template.json','sha256':'ee75b2934373d22362400e4fe66fd92ba17ef66405c7e7bcdd9aaae74fc2c059'}
SOURCE_REF={'path':'pipeline/diagnostic_bundles/tick_45eb3b04/bec_r1_prepare/preparation.json','sha256':'2ef488c483bf1fb5234dc9615069f7ec2a9232370d186ec4f92cb2bfb3212731'}
VERSION_REF={'path':'pipeline/diagnostic_bundles/tick_45eb3b04/bec_r1_version_operation/isolated_source_version.json','sha256':'617203db75c05528e4d0a58b94309edb6b86888bcb91f3a73cf5fc18e1bc089e'}
REG_REF={'path':'pipeline/diagnostic_bundles/tick_45eb3b04/bec_revision1_preregistration.json','sha256':'3fa782b8970de909a219cc090e2188983e1afeab1ac99cac43df07b4f1e5b527'}
CPU_REF={'path':'pipeline/diagnostic_bundles/tick_45eb3b04/bec_r1_cpu_trace_evidence.json','sha256':'390ac50aef6ac17c121427a49956aebef4526b6e3b6ac8e3dd0eb4e21d16ac5f'}
IMPL_REF={'path':'pipeline/diagnostic_bundles/tick_45eb3b04/bec_r1_implementation_independent_review.json','sha256':'972c47f2bd2f9080db45c98d755ab5296a855207e9b94472cf410a27340c2dbe'}
PROTECTED_BASELINE={'path':'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json','sha256':'deb2f6e1093be710fbbae886b4008c187b2e6b63d63276bfb47706b36b4be142'}
CURRENT_BASELINE={'path': 'pipeline/diagnostic_bundles/tick_3d001030/protected_assets_before.json', 'sha256': '5656f1f205722cb9fcc67ed965de7e0b6eebde93b08bd8b9705365693627752b'}
ACTIVE_FIELDS=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
def need(v,m):
    if not v:raise RuntimeError(m)
def read(p):
    def reject(v):raise ValueError('Nonstandard JSON '+v)
    return json.loads(Path(p).read_text(encoding='utf-8'),parse_constant=reject)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ref(p):
    p=Path(p).resolve();need(p.is_relative_to(ROOT.resolve()),'Path outside cluster project')
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def check_ref(item):
    p=(ROOT/item['path']).resolve();need(p.is_relative_to(ROOT.resolve()) and sha(p)==item['sha256'],'Missing or changed reviewed reference '+item['path']);return p
def save(p,v):
    owner_guard()
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def owner_guard():
    o=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');mode=read(ROOT/'pipeline/execution_mode.json')
    need({k:o.get(k) for k in OWNER}==OWNER,'Original currentowner6 changed; no old owner replay/extension')
    need(mode.get('mode')=='foreground' and mode.get('target_thread_id')==OWNER['thread_id']==os.environ.get('CODEX_THREAD_ID'),'Actual thread/environment/foreground target mismatch')
    now=datetime.now(timezone.utc);need(datetime.fromisoformat(OWNER['generated_at'])<=now<datetime.fromisoformat(OWNER['deadline_at']),'Original currentdeadline expired/future')
    need(sha(ROOT/'pipeline/headless/.tick_context.json')==OWNER['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==OWNER['pending_sha256'],'Current context/pending changed')
    need(sha(ROOT/'pipeline/goal.json')==GOAL,'Goal changed')
    ctx=read(ROOT/'pipeline/headless/.tick_context.json');policy=read(ROOT/'pipeline/closure_policy.json')
    need(policy.get('enabled') is True and policy['experiment_first']['enabled'] is True and policy['experiment_first']['authorization']==ctx['experiment_first']['authorization']==AUTH,'Standing current experiment-first policy changed')
    check_ref(AUTH);check_ref(RESOURCE)
    need(sha(ROOT/'SERVERS.yaml')=='2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1','Current GPU0-only resource registry changed')
    import yaml
    server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    need(server['allowed_gpus']==[0] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True and server['host']=='192.168.1.115' and server['user']=='songcl' and server['expected_hostname']=='dl04-MS-7E06','Current resource identity/scope changed')
    snapshots=[s for s in ctx['queue']['servers'] if s['name']=='server-4'];need(len(snapshots)==1 and snapshots[0]['allowed_gpus']==[0] and snapshots[0]['max_tasks_per_gpu']==1,'Bound resource snapshot differs')
    return o
def validate_refs():
    for r in (OP_REF,NATIVE_REF,CHECKER_REF,PEER,TEMPLATE_REF,SOURCE_REF,VERSION_REF,REG_REF,CPU_REF,IMPL_REF,PCE):check_ref(r)
    review=read(ROOT/PCE['path']);need(review.get('status')=='STATIC_OPERATIONAL_BEC_R1_PACKET_REVIEWED_NOT_NATIVE_PASS' and review.get('material_concerns')==[] and review.get('metadata_blockers')==[] and review.get('bookkeeping_blockers')==[],'Actual PCE final has unresolved static concerns')
    need((review.get('candidate_id'),review.get('code_commit'),review.get('source_parent_commit'),review.get('runtime_expected_commit'))==(CID,NEW,PARENT,PARENT),'PCE final does not review exact R1 version')
    need(review['anchors']['preparation']==OP_REF and review['anchors']['native_preparation']==NATIVE_REF and review['anchors']['release_template']==TEMPLATE_REF,'PCE packet anchors differ')
    for base,item in ((OP,OP_REF),(NATIVE,NATIVE_REF),(CHECKER,CHECKER_REF)):
        data=read(ROOT/item['path'])
        for n,h in data['prepared_file_hashes'].items():
            p=(base/n).resolve();need(p.is_relative_to(base.resolve()) and sha(p)==h,'Frozen packet file changed: '+n)
    n=read(NATIVE/'preparation.json');m=read(NATIVE/'manifest_template.json')
    need(n['code_commit']==n['source_commit']==NEW and n['source_parent_commit']==n['runtime_expected_commit']==PARENT and n['draft_execution_disabled'] is False,'R1 native declaration differs')
    need(all(m[k] is None for k in ACTIVE_FIELDS),'An unexecuted template has active identity fields')
    need(not any((NATIVE/n).exists() for n in ('native_manifest.json','execution_lease.json','execution_binding.json')),'Unexpected active native material')
    source=read(ROOT/VERSION_REF['path']);prep=read(ROOT/SOURCE_REF['path'])
    need(source['code_commit']==NEW and source['parent_commit']==PARENT and source['single_parent'] is True and source['exact_additions_count']==9 and source['frozen_source_files']==source['committed_blob_sha256']==prep['source_files'],'Actual R1 source proof differs')
    return n,m
def git_bytes(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(CODE),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def protected_code():
    check_ref(PROTECTED_BASELINE);rows=read(ROOT/PROTECTED_BASELINE['path'])['protected_existing_worktree']
    need(len(rows)==28,'Wrong28 baseline')
    head=git_bytes('rev-parse','HEAD').decode().strip();need(head==PARENT,'Primary must remain actual testedCTS4e8; no checkout/ff by anchor')
    status=git_bytes('status','--porcelain=v1','-z','-uall');actual={(x[:2].decode(),x[3:].decode()) for x in status.split(b'\0') if x}
    need(actual=={(r['status'],r['path']) for r in rows} and all(sha(CODE/r['path'])==r['sha256'] for r in rows),'Original28 status/bytes changed')
    need(not git_bytes('diff','--cached','--name-only','-z'),'Index is not empty')
    ix=Path(git_bytes('rev-parse','--git-path','index').decode().strip());ix=ix if ix.is_absolute() else CODE/ix
    return {'head':head,'status_hex':status.hex(),'index_sha256':sha(ix),'rows':rows}
def registered_state():
    queue=read(ROOT/'pipeline/queue.json');running=read(ROOT/'pipeline/running.json')
    rows=[t for ts in queue['gpu_queues'].values() for t in ts if t.get('id')=='M214-CTS']
    need(len(rows)==1 and (rows[0].get('status'),str(rows[0].get('gpu')),rows[0].get('code_commit'),rows[0].get('pid'),rows[0].get('launch_verified'))==('running','0',PARENT,3505065,True),'Original registeredCTS identity differs; reconcile first')
    need(running.get('server-4',{}).get('0')=='M214-CTS','OriginalCTS running-map differs')
    paused=[t for ts in queue['gpu_queues'].values() for t in ts if t.get('id')=='M206-CGCA']
    need(len(paused)==1 and paused[0].get('dispatch_hold') and paused[0].get('resume_authorized') is False,'M206 user pause changed')
    baseline=read(check_ref(CURRENT_BASELINE))['protected_ledgers'];need(len(baseline)==12,'Expected current twelve-ledger baseline')
    hashes={n:sha(ROOT/'pipeline'/n) for n in baseline};need(hashes==baseline,'Current twelve protected ledgers changed; reconcile before anchor/guard')
    return {'hashes':hashes,'CTS':copy.deepcopy(rows[0]),'M206':copy.deepcopy(paused[0])}
def r1_pending(c):
    need(c['stage']=='validation' and c['code_commit']==OLD and c['native_execution_code_commit']==OLD,'Only existing pre-anchor9b BEC may be updated')
    need(not any(c.get(k) for k in ('human_hold','scope_hold','numerical_hold','dispatch_hold','hold','paused')),'BEC is held')
    hist=c['revision_history'];reg=read(ROOT/REG_REF['path'])['preregistration'];mutable={'result','evidence','result_evidence'}
    need(len(hist)==1 and hist[0].get('result')=='pending' and hist[0].get('revision')==1 and hist[0].get('failure_scope')=='implementation','Only the existing pendingR1 is eligible')
    need({k:v for k,v in hist[0].items() if k not in mutable}=={k:v for k,v in reg.items() if k not in mutable},'Immutable R1 registration changed')
def legacy_results(prior):
    base=ROOT/'pipeline/diagnostic_bundles/tick_45eb3b04/bec_execution';facts={}
    for mode,target in [('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]:
        p=base/(mode+'_'+target+'_execution.json');name=p.relative_to(ROOT).as_posix()
        declared=[item for item in prior.get('evidence',[]) if isinstance(item,dict) and item.get('path')==name]
        need(len(declared)==1,'Original9b raw must have exactly one existing declared reference: '+name)
        check_ref(declared[0]);e=read(p);r=e['result']
        need(e['certainty']=='terminal' and r.get('code_commit')==OLD and r.get('candidate_id')==CID,'Old9b result identity changed')
        if mode=='smoke':need(e['returncode']==0 and r['optimizer_steps']==2 and r['native_data_loaded'] is True and r['backward_finite'] is True and r['intended_path_observed'] is True and all(type(x) in (int,float) and math.isfinite(x) for x in r['losses']),'Historical two-smoke result differs')
        if (mode,target)==('resources','candidate'):need(sha(p)=='f8fac959a9b040838710d9a7199ea5a9e552bc364904e6d0b182feb77811c4f5' and e['returncode']==1 and r['execution_completed'] is False,'Original JIT failure must remain exact')
        facts[mode+'_'+target]={'artifact':ref(p),'returncode':e['returncode'],'execution_completed':r.get('execution_completed'),'optimizer_steps':r.get('optimizer_steps'),'losses':r.get('losses'),'native_code_commit':OLD,'scope':'Historical9b only, not R1 evidence'}
    return facts
def other_candidates(w):return {c['id']:digest(c) for c in w['candidates'] if c['id']!=CID}
def compose(w,legacy):
    out=copy.deepcopy(w);c=next(x for x in out['candidates'] if x['id']==CID);prior=copy.deepcopy(c);now=datetime.now(timezone.utc).isoformat()
    c.setdefault('execution_preparation_history',[]).append({'recorded_at':now,'reason':'Preserve complete9b declarations, actual two-smoke success and JIT resource failure before separate reviewed R1 static catalog. No historical source or native result is relabeled.','prior_candidate_record':prior,'old_source_commit':OLD,'old_native_execution_code_commit':prior['native_execution_code_commit'],'actual_9b_result_history':legacy,'old_worker_preparation':copy.deepcopy(prior['worker_preparation']),'old_execution_adapter':copy.deepcopy(prior['execution_adapter'])})
    c.setdefault('source_version_history',[]).append({'recorded_at':now,'reason':'Exact registered R1 source026c single-child currentCTS4e8; no public promotion or native inheritance.','prior_source_commit':OLD,'source_commit':NEW,'source_parent_commit':PARENT,'source_preparation':SOURCE_REF,'source_version':VERSION_REF})
    c.update(code_commit=NEW,source_commit=NEW,source_parent_commit=PARENT,runtime_expected_commit=PARENT,future_version_parent=PARENT,source_preparation=SOURCE_REF,source_version=VERSION_REF,isolated_worktree=read(ROOT/VERSION_REF['path'])['worktree'],resource_authorization=RESOURCE,native_execution_code_commit=None,
      source_status='EXACT_R1_026C_PRIVATE_VERSION_BOUND_NATIVE_NOT_RUN',version_packaging_status='R1_SOURCE_AND_OPERATIONAL_STATIC_CATALOG_REVIEWED',
      implementation_status='R1_PREPARED_REVIEWED_NEW_SOURCE_TOOLS_ONLY',native_status='NOT_RUN_ON_R1',native_smoke_status='NOT_RUN_ON_R1',resource_status='NOT_RUN_ON_R1',resource_profile_status='NOT_RUN_ON_R1',admission_status='NOT_ADMITTED_R1',
      operational_preparation_status='REVIEWED_STATIC_CATALOG_ANCHORED_R1_NATIVE_NOT_RUN',result_checker_status='R1_READONLY_CHECKER_PREPARED_REVIEWED_NOT_RUN',
      next_action='Preserve original CTS3505065 on soleGPU0. After canonical terminal release and actual idle/UUID/three-lock validation, use a fresh current-owner binding to execute all original M95/R1 TRAIN2 and resource arms. No GPU1, eviction, source sync, oldraw inheritance, lease replay, resampling or threshold changes.')
    c['staged_repository']=(ROOT/'pipeline/diagnostic_bundles/tick_45eb3b04/bec_r1_prepare/staged_repository').as_posix()
    c['version_compatibility']={'actual_parent':PARENT,'expected_current_main_runtime':PARENT,'relationship':'R1_SINGLE_CHILD_CTS4E8_NOT_PROMOTED_OR_NATIVE_TESTED','historical9b_sibling_scope':'Preserved unchanged in execution_preparation_history.prior_candidate_record; never relabeled.'}
    if prior.get('resource_wait') is not None:
        c.setdefault('resource_wait_history',[]).append({'recorded_at':now,'reason':'Preserve prior dual-card9b resource snapshot before current GPU0-only R1 metadata.','previous_resource_wait':copy.deepcopy(prior['resource_wait'])})
    c['resource_wait']={'allowed_server':'server-4','allowed_physical_gpus':[0],'observed_at':now,'code_commit':NEW,'registered_task':'M214-CTS','registered_PID':3505065,'scope':'Canonical registered occupancy only; no GPU hardware/process observation by static anchor. Fresh actual idle/UUID/three-lock validation remains required.','current_resource_authorization':RESOURCE}
    c['worker_preparation']={'status':'PREPARED_REVIEWED_R1_VERSION_BOUND_NATIVE_NOT_RUN','preparation':NATIVE_REF,'worker':ref(NATIVE/'worker.py'),'runtime':ref(NATIVE/'native_runtime.py'),'manifest_template':ref(NATIVE/'manifest_template.json'),'source_commit':NEW,'source_parent_commit':PARENT,'runtime_expected_commit':PARENT,'source_preparation':SOURCE_REF,'independent_review':PCE,'native_backward_executed':False,'resource_profile_executed':False,'native_backward_passed':False,'resources_passed':False,'active_native_manifest_or_execution_lease_created':False,'draft_execution_disabled':False}
    c['execution_adapter']={'status':'PREPARED_REVIEWED_R1_STATIC_CATALOG_ONLY_UNEXECUTED','preparation':OP_REF,'release':{'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':TEMPLATE_REF['sha256']},'adapter':ref(OP/'adapter.py'),'remote_ops':ref(OP/'remote_ops.py'),'README':ref(OP/'README.md'),'independent_review':PCE,'independent_tests':ref(OP/'static_validation_final.json'),'external_anchor_required':True,'source_commit':NEW,'source_parent_commit':PARENT,'runtime_expected_commit':PARENT,'native_execution_code_commit':None,'native_execution_tested':False,'remote_adapter_execution_tested':False,'active_binding_manifest_lease_created':False,'static_module_release_only':True,'standard_result_formatter_implemented':False,'prepared_readonly_result_checker':CHECKER_REF,'prepared_result_checker_independent_review':PEER,'actual_native_four_result_review_executed':False,'actual_current_local_guard':None}
    for r in (OP_REF,NATIVE_REF,CHECKER_REF,PEER,PCE,SOURCE_REF,VERSION_REF,REG_REF,CPU_REF,IMPL_REF,{'path':(OP/'adapter_release.json').relative_to(ROOT).as_posix(),'sha256':TEMPLATE_REF['sha256']}):
        if r not in c['evidence']:c['evidence'].append(r)
    need(c['revision_history']==prior['revision_history'],'R1 history must remain byte-equivalent data/pending')
    out['updated_at']=now
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-root',action='store_true');a=p.parse_args()
    if not a.execute_root:print('DRAFT_DISABLED: no static release or shared metadata operation');return
    need(ENABLE_ROOT_EXECUTION,'Root-reviewed sibling copy must be explicitly enabled')
    owner_guard();validate_refs()
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));need(lock is not None,'Canonical project lock busy')
    try:
        owner_guard();validate_refs();code_before=protected_code();state_before=registered_state()
        intent=TICK/'bec_r1_anchor_intent.json';result_path=TICK/'bec_r1_static_anchor_result.json'
        need(not intent.exists() and not result_path.exists(),'Existing anchor phase requires read-only reconciliation; no replay')
        release=OP/'adapter_release.json';need(not release.exists(),'Existing production release is an unknown prior phase; reconcile, do not overwrite/adopt')
        work_path=ROOT/'pipeline/research_work.json';work=read(work_path);before_work_sha=sha(work_path)
        need(len(work['candidates'])==141 and len({c['id'] for c in work['candidates']})==141,'Candidate inventory changed')
        matches=[c for c in work['candidates'] if c['id']==CID];need(len(matches)==1,'Missing/ambiguous BEC')
        r1_pending(matches[0]);others_before=other_candidates(work);legacy=legacy_results(matches[0])
        need(not (ROOT/'pipeline/experiments/M215-BEC.json').exists() and not (ROOT/'pipeline/admissions/M215-BEC.json').exists(),'BEC is already admitted/queued; reconcile')
        updated=compose(work,legacy)
        need(other_candidates(updated)==others_before and len(updated['candidates'])==141,'Other candidate changed')
        for k in set(work)|set(updated):
            if k not in ('candidates','updated_at'):need(work.get(k)==updated.get(k),'Noncandidate top-level state changed')
        serialized=json.dumps(updated,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        save(intent,{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':OWNER,'operation':'static_R1_release_and_existing_BEC_metadata_only','work_before_sha256':before_work_sha,'prepared_work_sha256':hashlib.sha256(serialized.encode()).hexdigest(),'target_before_digest':digest(matches[0]),'other140_digests':others_before,'protected_code':code_before,'protected_registry':state_before,'PCE_final':PCE,'R1_packet':OP_REF,'legacy_9b_results':legacy,'no_compute_or_source_promotion':True})
        save(TICK/'bec_r1_anchor_before.json',{'target_before':matches[0],'other140_digests':others_before,'work_sha256':before_work_sha,'protected_registry':state_before})
        owner_guard()
        with release.open('xb') as f:f.write((OP/'release_template.json').read_bytes());f.flush();os.fsync(f.fileno())
        need(sha(release)==TEMPLATE_REF['sha256'],'Static release copy differs')
        temp=work_path.with_name(work_path.name+'.'+OWNER['token']+'.bec_r1_anchor.tmp')
        with temp.open('x',encoding='utf-8') as f:f.write(serialized);f.flush();os.fsync(f.fileno())
        owner_guard();need(sha(work_path)==before_work_sha and protected_code()==code_before and registered_state()==state_before,'Concurrent protected state changed; leave once-intent and reconcile, no rollback')
        os.replace(temp,work_path)
        actual=read(work_path);need(actual==updated and other_candidates(actual)==others_before,'Metadata write mismatch')
        target=next(c for c in actual['candidates'] if c['id']==CID)
        need(target['native_execution_code_commit'] is None and target['revision_history']==matches[0]['revision_history'],'R1 native/historical revision falsely relabeled')
        need(target['execution_preparation_history'][-1]['prior_candidate_record']==matches[0],'Full9b history not retained')
        need(protected_code()==code_before and registered_state()==state_before,'Protected source/CTS/M206/queue/receipts changed')
        validate_refs();owner_guard()
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':OWNER,'candidate_id':CID,'code_commit':NEW,'source_parent_commit':PARENT,'runtime_expected_commit':PARENT,'static_release':ref(release),'work_before_sha256':before_work_sha,'work_after_sha256':sha(work_path),'candidate_count':141,'other140_candidates_unchanged':True,'only_existing_BEC_and_work_updated_at_changed':True,'legacy9b_native_code_preserved_in_history':True,'R1_native_execution_code_commit':None,'R1_native':'NOT_RUN','R1_resources':'NOT_RUN','R1_revision_result':'pending','manifest10_execution_fields_all_null':True,'protected_source_index28_and_registry_unchanged':True,'CTS_registered_PID':3505065,'PCE_final':PCE,'checker':CHECKER_REF,'checker_peer':PEER,'GPU_Torch_SSH_remote_lease_queue_dispatch_or_source_promotion':False,'Git_used_readonly':True,'material_concerns':[]}
        save(result_path,result);print(json.dumps({'status':'STATIC_R1_CATALOG_ANCHORED_NATIVE_NOT_RUN','result':ref(result_path)},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
