"""Root-only final records. Default reads nothing and writes nothing; no launch API."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, hashlib, json, os, sys

TICK = Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_2b832a02')
sys.path.insert(0, str(TICK))
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
DRAFT_EXECUTION_DISABLED = True
SOURCE = '6282263d805c1741234f97afc981a05aca2ad6e3'
HERE = TICK / 'final_hpc_tick_prepare'

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf8')

def exclusive(path, data):
    guard()
    with Path(path).open('xb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())

def atomic(path, data):
    guard(); path=Path(path); tmp=path.with_name(path.name+'.2b832a02.final.tmp')
    exclusive(tmp, data); guard(); os.replace(tmp, path)

def protect(b):
    guard(); repo=ROOT/'Cluster'
    assert u.git(repo,'rev-parse','HEAD').decode().strip()==b['head']==SOURCE
    assert u.git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex']
    assert not u.git(repo,'diff','--cached','--name-only','-z')
    assert all(sha(repo/n)==h for n,h in b['files'].items())
    assert all(sha(repo/n)==h for n,h in b['exact_tested_nine_source_paths'].items())
    index=Path(u.git(repo,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute(): index=repo/index
    assert sha(index)==b['index_sha256']
    assert len(b['protected_ledgers'])==20
    assert all(sha(ROOT/'pipeline'/n)==h for n,h in b['protected_ledgers'].items())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--execute-root',action='store_true'); args=ap.parse_args()
    if not args.execute_root:
        print('DEFAULT_READ_ONLY; actual records not written'); return
    assert not DRAFT_EXECUTION_DISABLED, 'Root must review and explicitly enable a separate copy'
    os.environ['GIT_OPTIONAL_LOCKS']='0'; guard()
    bound=u.read(HERE/'actual_bindings.json'); u.check_refs(list(bound.values()))
    loaded={k:u.read(ROOT/v['path']) for k,v in bound.items()}
    b=loaded['post']; assert b['owner']==EXPECTED and b['new_ADMITTED_HPC_original_pid']==187081
    ds=loaded['dispatch']; assert ds['canonical_dispatch_invoked_once'] is True and ds['verified_native_progress'] is True
    task=ds['task_after']; assert task['status']=='running' and task['pid']==187081 and task['launch_verified'] is True
    assert task['launch_verification']=='training_progress' and task['code_commit']==SOURCE and ds['physical_gpu']==0
    assert ds['signals_sent'] is False and ds['blind_relaunch_performed'] is False
    receipt=loaded['receipt']; assert receipt['id']=='M218-HPC' and receipt['code_commit']==SOURCE
    review=loaded['review']; assert review['review_status']=='RAW_SEMANTICS_VALIDATED_NOT_ADMISSION'
    assert review['code_commit']==SOURCE and review['observations']['native_semantics_and_pairing_checked'] is True
    assert review['observations']['resource_protocol_checked'] is True
    for key in ('native_peer','launch_peer'):
        assert loaded[key]['material_concerns']==[] and loaded[key]['code_commit']==SOURCE
    live=loaded['growth']; assert live['owner']==EXPECTED and live['returncode']==0
    ob=live['observation']; assert ob['runtime_commit']==SOURCE and ob['identity_before']==ob['identity_after']
    identity=ob['identity_after']; assert identity['pid']==187081 and str(identity['start_ticks'])=='80008729'
    samples=ob['samples']; assert len(samples)==2 and samples[-1]['max_native_step']>samples[0]['max_native_step']
    assert all(s.get('tail_exception_seen') is False for s in samples)
    assert 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in str(ob) and '187081' in str(ob['GPU0_contexts'])
    assert all(v is None for k,v in live['precise_native_validation'].items() if k in ('values','best','no_improve'))
    assert loaded['cre_archive']['archive_id']=='0177c22e3480465bac304836253de8aa'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard(); protect(b)
        intent=HERE/'hpc_final_records_intent.json'; result=HERE/'hpc_final_records_result.json'
        notes_path=TICK/'report_notes.json'; decision=ROOT/'pipeline/decisions/20261028_2b832a02_hpc_final.md'
        for p in (intent,result,notes_path,decision): assert not p.exists(), str(p)
        work=u.read(ROOT/'pipeline/research_work.json'); original=copy.deepcopy(work)
        assert len(work['candidates'])==145 and {c['id'] for c in work['candidates']}==set(b['candidate_digests'])
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'])
        now=datetime.now(timezone.utc).isoformat(); by={c['id']:c for c in work['candidates']}
        h=by[u.HPC]; a=by[u.APF]; assert h['stage']=='training' and h['code_commit']==SOURCE
        assert by[u.CRE]['stage']=='complete' and a['code_commit']=='bf6c3fafe0f690e16e838e7c0192f09e789389f9'
        h.setdefault('native_check_history',[]).append({'recorded_at':now,'prior_current_native_check':copy.deepcopy(h.get('current_native_check'))})
        h['current_native_check']={'recorded_at':now,'result':'passed','code_commit':SOURCE,'optimizer_steps':2,
            'evidence':[bound[k] for k in ('smoke','review','native_peer')],
            'scope':'Four actual current-source arms reviewed; original two TRAIN losses/backward/optimizer and intended two-solve/three-FFN path passed. Old 0f import failure remains historical; root cause not established.'}
        h.setdefault('observation_history',[]).append({'recorded_at':now,'prior_latest_native_training_progress':copy.deepcopy(h.get('latest_native_training_progress'))})
        epoch,step=samples[-1]['max_native_step']
        h['latest_native_training_progress']={'recorded_at':ob['observed_at'],'pid':187081,'start_ticks':'80008729',
            'epoch':epoch,'step':step,'steps_per_epoch':4686,'observed_steps':samples,
            'precise_native_validation':live['precise_native_validation'],'evidence':bound['growth'],
            'scope':'Root read-only original PID/source8/YAML/runtime6282/physicalGPU0 identity and native TRAIN growth; peer separately binds initial launch samples. Validation remains unknown.'}
        h.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_current_resource_check':copy.deepcopy(h.get('current_resource_check'))})
        h['current_resource_check']={'recorded_at':ob['observed_at'],'result':'running_original_verified_training','physical_gpu':0,
            'evidence':[bound[k] for k in ('resources','receipt','dispatch','growth','launch_peer')],
            'scope':'Actual paired resource pass and one canonical admitted HPC launch; no additional native run or idle permission.'}
        if isinstance(h.get('execution_adapter'),dict):
            h.setdefault('execution_metadata_history',[]).append({'recorded_at':now,'execution_adapter':copy.deepcopy(h['execution_adapter'])})
            h['execution_adapter']['transport_executed']=True
        a.setdefault('compatibility_history',[]).append({'recorded_at':now,'prior_next_action':a.get('next_action'),'prior_current_resource_check':copy.deepcopy(a.get('current_resource_check'))})
        a['current_resource_check']={'recorded_at':now,'result':'compatible_packaging_required','physical_gpu':0,'current_runtime':SOURCE,
            'evidence':bound['growth'],'scope':'Existing APF bf6 parentd585/static tools preserved. Current main/runtime6282 requires separately saved compatible source and version-bound tooling before future fresh-idle GPU0 native checks; no model revision or old-raw relabel.'}
        a['requires_current_runtime_compatible_copy']=True
        a['next_action']='Preserve bf6/parentd585 and frozen source/native/op history. Package unchanged nine source files on actual current compatible6282 parent, bind fresh static tools, then await genuinely idle GPU0 for original paired TRAIN2/resources. Native/results remain NOT_RUN.'
        for c,keys in ((h,('review','native_peer','smoke','resources','receipt','dispatch','growth','launch_peer')),(a,('growth',))):
            for k in keys:
                if bound[k] not in c.setdefault('evidence',[]): c['evidence'].append(bound[k])
        if work.get('tick_attempt'): work.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
        smoke=loaded['smoke']
        work['tick_attempt']={'tick_started_at':EXPECTED['generated_at'],'candidate_id':u.HPC,'kind':'native_smoke','result':'passed',
            'command':smoke['command'],'observation':'Current6282 actual original TRAIN2/native path and paired resources passed; one canonical formal GPU0 launch now shows original PID187081 growth. Validation metrics unknown. No old import failure root-cause repair claimed.',
            'evidence':[bound[k] for k in ('smoke','review','native_peer','resources','dispatch','growth','launch_peer')]}
        work['updated_at']=now; work['last_event_tick']=EXPECTED['generated_at']
        work['next_action']='Continue original admitted HPC187081 on GPU0 under unchanged patience; prepare existing APF unchanged-source compatible packaging for runtime6282. No GPU1, replay, new candidate or model revision.'
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id'] not in {u.HPC,u.APF})
        first, last=samples[0]['max_native_step'][1],step
        notes={'actions':[
            'CRE原PID不存在的初始观察已由原日志正常earlystop30/50及exact best .4961479902267456解释；canonical archive0177与research/aux对齐已完成，未重启或改旧负证据。',
            'HPC6282真实四臂两原TRAIN/common全named配对/两S三FFN路径及原资源门通过。双方9.762532428G/157484090参数；median35.7843→35.1946ms/P9037.7583→36.6085ms。unsupported完整保留，不宣称resolver零成本或纯TRAIN峰值已测。',
            f'HPC exact9A合法ff d585→6282、receipt41e648及一次canonical GPU0派发成功。原PID187081/start80008729，根实际{ob["observed_at"]} TRAIN{epoch}/50 {first}→{last}/4686；validation/best/noimprove均UNKNOWN。',
            '保留旧2f7 import control失败与APF bf6/父d585所有冻结材料；本轮最终只HPC/APF元数据、memory/notes/decision，其他143候选/20账/28用户文件和post-ff index保持。APF需当前6282兼容包装。'],
            'decisions':['0新候选/0新模型修订；本轮实际4个native worker臂和1次HPC正式训练启动；目标.5100、champion.5020保持。仅GPU0，M206暂停及旧额度边界不变。',
            '继续HPC原patience10，不据早期TRAIN推断收益；APF先兼容包装再等合法空GPU0，禁止跨兄弟ff、借旧PASS、盲重放或宣称历史导入根因已修复。']}
        memory=f'''# Codex Research Memory

## Goal And Phase
- 当前2b832a02；generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值。Phase1原层级pointfeature→inst_feats→masks；目标.5100，M95 champion.5020，gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583；只server4 physicalGPU0/max1，GPU1禁用；M206用户pause/resumeFalse保持。
- seed1999/epochs50/patience10/原YAML/data/pretrain/loss/optimizer/precision与资源≤10G口径不变。禁调参/gate/语言routing/大QKV/N²attention/重复inst/旧拒绝改名。

## Champion And Baseline
- M95仍.5020；未有本轮新champion。BEC.5001/24、AEF.495597243309021/23均历史正常早停。
- CRE本轮正常earlystop30/50，exactbest.4961479902267456/noimprove10，archive0177c22e3480465bac304836253de8aa。原PID118189无/proc的初始错误是终态观察，不是新crash/恢复依据。

## Active Hypotheses
- M218-HPC hierarchy-tree-resolvent-nonlinear-composition：真fine→middle→coarse森林A=I+L，两次S=A^-1包原3FFN，原LN/rawskip/HCG/CSORT/单inst保留，无新参数。
- 原c94f NULL/reference56、旧2f7父56和0f控制导入失败完整保留；当前兼容source6282263d805c1741234f97afc981a05aca2ad6e3单父d585，实际原始两TRAIN/common全named配对/两solver三FFN/原loss backward和optimizer2步通过。
- 实际资源双方9.762532428G/157484090参数/allocated936763392/reserved1191182336；median35.7843→35.1946ms，P9037.7583→36.6085ms；unsupported保持，resolver完整FLOPs和pureTRAIN峰值未知。
- receipt41e648d669684de525270f69b696af7540b21dfb5ceec186f0132e8682b17b8c；一次canonical launch GPU0 PID187081/start80008729，launch_verified training_progress。当前source/runtime6282。
- 根{ob['observed_at']}真实TRAIN{epoch}/50 {first}→{last}/4686；validation.values/best/no_improve均UNKNOWN，不可置0或当最终效果。
- M219-APF ancestry路径joint3C→3C/GELU拆u/v/w，fine直接u、middle/coarse按真fine路径私有equalmean，原LN/rawskip/HCG/单inst保留。source bf6c3fafe0f690e16e838e7c0192f09e789389f9/父d585及04993/61185/旧工具冻结；实际native/resources仍NOT_RUN。
- APF下一步仅把同9源显式兼容到实际current6282并重绑静态工具后等待空GPU0；不假定bf6可跨兄弟ff，不改原NULL，不算模型修订。

## Closed Or Failed Directions
- CRE complete/auxdone，canonical archive/原receipt/原日志不再改；旧0f CRE/HPC依赖导入失败根因仍UNKNOWN，本次HPC四臂通过不证明环境根因修复。
- CTS stopped_unknown14/.4890不自动恢复；BFC DataLoader overlap crash20/3832根因UNKNOWN，epoch19旧ckpt不含完整RNG/sampler/失败输入；需专属恢复计划及许可。
- M206 pause+dispatch_hold+resumeFalse；PCE2+extra1、RSTR2已尽，禁R4/R3/M201自动恢复；HAP恢复授权已消费。旧10本轮due小字段digest未变，仅5bc9私有边界证明，不读旧855/grant/checkpoint正文。

## Running And Queue
- 唯一正式训练M218-HPC server4 physicalGPU0 PID187081/runtime6282；原日志hpc_20261028_183226.log。不要因dispatch_phase旧progress_pending重放。
- CRE已complete，APF是已有静态储备非已准入队列；M206暂停不可派发。145 IDs未增，creation_budget0，本轮无新候选/模型修订。
- SSH key/strict hostkey pinned dl04-MS-7E06，仅GPU0 UUID958e741a；禁GPU1/信号/删锁/盲重启。28用户文件/status/空暂存与合法ff后index保持；20生命周期账本不由最终记录器改写。

## Open Questions And Risks
- HPC效果/泛化/新颖性未知，非线性SFS不据S性质宣称均值守恒；无新FP32/Jacobian数值门。
- APF未来真实自然batch/全参数训练性与资源未知；逐call/row零合法，整体factor原loss聚合训练性依原协议，不重抽样追覆盖。

## Last Tick
- 本轮CRE正常归档与对齐、HPC真实四臂/独审/三标准/ff/receipt/一次派发及原PID增长均已完成；0新candidate/0模型revision，1既有HPC正式launch。
- 最终记录器只更新HPC/APF，其他143（含CRE）保持；总体仅CRE/HPC/APF三条变化，其余142/原28及postdispatch20账保护。未预签canonical postflight/report/finish。
'''
        assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        decision_text=f'# 本轮既有实验执行记录\n\n{now}\n\n'+'\n\n'.join(notes['actions']+notes['decisions'])+'\n'
        payloads=[(ROOT/'pipeline/research_work.json',encoded(work)),(ROOT/'pipeline/codex_memory.md',memory.encode('utf8')),
            (notes_path,encoded(notes)),(decision,decision_text.encode('utf8'))]
        # Serialize every payload and check destinations before the first durable intent/shared write.
        for p,data in payloads: assert isinstance(data,bytes) and not p.with_name(p.name+'.2b832a02.final.tmp').exists()
        guard(); protect(b)
        exclusive(intent,encoded({'owner':EXPECTED,'recorded_at':now,'research_work_before':sha(ROOT/'pipeline/research_work.json'),
            'memory_before':sha(ROOT/'pipeline/codex_memory.md'),'bindings':bound,'partial_replay_forbidden':True}))
        for p,data in payloads:
            if p in (notes_path,decision): exclusive(p,data)
            else: atomic(p,data)
        protect(b); after=u.read(ROOT/'pipeline/research_work.json')
        assert len(after['candidates'])==145
        assert all(u.digest(c)==b['candidate_digests'][c['id']] for c in after['candidates'] if c['id'] not in {u.HPC,u.APF})
        exclusive(result,encoded({'owner':EXPECTED,'recorded_at':now,'changed_candidates':[u.HPC,u.APF],
            'other_143_candidates_unchanged':True,'protected_20_ledgers_and_28_files_index_unchanged':True,
            'memory_lines':len(memory.splitlines()),'notes':u.ref(notes_path),'decision':u.ref(decision),
            'final_records_only':True,'canonical_postflight_or_finish_performed':False}))
        print(json.dumps({'status':'RECORDED','result':u.ref(result)},ensure_ascii=False))
    finally: lock.release()

if __name__=='__main__': main()
