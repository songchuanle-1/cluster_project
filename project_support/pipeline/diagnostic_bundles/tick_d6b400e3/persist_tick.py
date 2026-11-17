"""Record same-candidate external tool preparation, never admission or launch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = 'd6b400e39d1445bfbf165ca916876e5c'
CID = 'hierarchy-parent-spectral-nonlinear-token-coupling'
BASE = '74fcd21df0af9a971792038ffe251af1ffea2604'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def save(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + TOKEN + '.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preparation', required=True)
    parser.add_argument('--review', required=True)
    parser.add_argument('--source-version', required=True)
    parser.add_argument('--source-review', required=True)
    args = parser.parse_args()
    prep_path, review_path = Path(args.preparation), Path(args.review)
    prep, review = read(prep_path), read(review_path)
    version_path, version_review_path = Path(args.source_version), Path(args.source_review)
    version, version_review = read(version_path), read(version_review_path)
    assert version['status'] == 'ISOLATED_SOURCE_COMMIT_ONLY_NATIVE_UNEXECUTED'
    assert version['code_commit'] == '43dce016c1a1713c2a5dab7061810dc2efde8954'
    assert version_review.get('material_concerns') == []
    assert prep['candidate_id'] == CID and prep['experiment_id'] == 'M210-PSNC'
    assert prep['code_commit'] is None
    for name, expected in prep['prepared_file_hashes'].items():
        file = (prep_path.parent / name).resolve()
        assert file.is_relative_to(prep_path.parent.resolve()) and sha(file) == expected, name
    assert review.get('material_concerns') == []
    owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == os.environ['CODEX_THREAD_ID'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    observation = read(HERE/'hrc_training_progress_observation.json')
    assert observation['exact_original_process_and_native_progress_increasing'] is True
    a, b = [row['data'] for row in observation['observations']]
    assert a['pid'] == b['pid'] == 2780804 and a['starttime'] == b['starttime'] == '29604100'
    assert a['progress'] == [8,50,3233,4686] and b['progress'] == [8,50,3244,4686]
    assert b['gpu0_contexts'] == '2780804, 19728' and b['errors'] == []
    boundary = read(HERE/'continuation_boundary_check.json')
    holds = read(HERE/'held_boundary_check.json')
    assert boundary['material_concerns'] == holds['material_concerns'] == []
    assert subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'rev-parse','HEAD'],text=True).strip() == BASE
    assert not subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'diff','--cached','--name-only'],text=True).strip()
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        protected_names = ['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json',
            'experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
        protected = {name:sha(ROOT/'pipeline'/name) for name in protected_names}
        work = read(ROOT/'pipeline/research_work.json')
        by_id = {c['id']:c for c in work['candidates']}
        candidate = by_id[CID]
        assert candidate['code_commit'] is None and candidate['source_status'] == 'PREPARED_EXTERNAL_UNVERSIONED'
        assert candidate['source_version_boundary']['new_source_commit'] is None
        assert not (ROOT/'pipeline/admissions/M210-PSNC.json').exists()
        tasks = {t['id']:t for t in monitor.load_queue(str(ROOT))['gpu_queues']['server-4']}
        assert tasks['M208-HRC']['status'] == 'running' and tasks['M208-HRC']['pid'] == 2780804
        assert tasks['M209-PSBR']['status'] == 'waiting' and tasks['M209-PSBR']['code_commit'] == BASE
        assert not tasks['M209-PSBR'].get('dispatch_hold') and not tasks['M209-PSBR'].get('pid')
        assert tasks['M206-CGCA']['resume_authorized'] is False
        now = datetime.now(timezone.utc)
        candidate['native_worker_adapter'] = 'EXTERNAL_DRAFT_EXECUTION_DISABLED_STATIC_ONLY'
        candidate['source_version_history'] = [{'recorded_at':now.isoformat(),'code_commit':None,
            'source_status':candidate['source_status'],'source_version_boundary':candidate['source_version_boundary'],
            'reason':'Original unversioned preparation retained. Independent worktree now stores exact frozen9 without advancing dispatch HEAD.'}]
        candidate['code_commit'] = version['code_commit']
        candidate['source_status'] = 'ISOLATED_COMMIT_PREPARED_NATIVE_NOT_RUN'
        candidate['source_version_binding'] = ref(version_path)
        candidate['source_version_independent_review'] = ref(version_review_path)
        candidate['prepared_repository_root'] = Path(version['worktree']).relative_to(ROOT).as_posix()
        candidate['config_status'] = 'Native YAML exists at exact isolated source commit; primary Cluster and remote active checkout unchanged. Native not run.'
        candidate['native_execution_code_commit'] = None
        candidate['native_status'] = 'NOT_RUN_waiting_idle_authorized_GPU0_and_operational_exact_version_binding'
        candidate['resource_status'] = 'NOT_RUN_waiting_idle_authorized_GPU0_and_operational_exact_version_binding'
        candidate['source_version_boundary'] = {'current_base_commit':BASE,'new_source_commit':version['code_commit'],
            'primary_Cluster_HEAD':BASE,'isolated_worktree':version['worktree'],'protect_existing_admitted_task':'M209-PSBR',
            'current_Cluster_modified':False,'Git_commit':True,'Git_sync':False,'future_exact_tested_version_required':True,
            'reason':'Isolated version storage is now evidenced safe; primary HEAD advancement still waits for PSBR verifiedlaunch/safe reconciliation. Never sync an active checkout.'}
        candidate['native_tool_preparation'] = ref(prep_path)
        candidate['native_tool_independent_review'] = ref(review_path)
        candidate['blocker'] = 'Only authorized physicalGPU0 occupied by exact original HRC2780804/start29604100/native8/50 increasing3233->3244 at2026-10-23 02:10:49 Shanghai; existing PSBR74f FIFO dispatch binding also protected. New external worker/adapter is a disabled draft, not runnable native evidence.'
        candidate['blocked_at'] = now.isoformat()
        candidate['retry_after'] = (now + timedelta(hours=1)).isoformat()
        candidate['unblock_condition'] = 'The frozen9 already have an isolated real source version43dce0, with primaryHEAD74f unchanged. First preserve PSBR verifiedlaunch or reconcile all pending74f launch bindings before primary ff; never sync active remote checkout. Complete and review disabled native transport/binding draft, then fresh exact-source/current-owner/assets/onlyGPU0 idleness/exclusive locks checks and actual original-YAML TRAIN2/resources are required.'
        candidate['next_action'] = 'Retain PSBR74f FIFO/current HRC and recoverable isolatedPSNC43dce0. When PSBR dispatch is safe, advance primary HEAD only by safe ff to the frozen9 source version; never mutate active remote checkout. Complete/review disabled transport draft and bind a fresh actual version/owner/assets/allowedGPU0 idle/exclusive lease before real M95/candidate TRAIN2 and original-resource pair. Native execution remains unbound/unrun. No GPU1/M206 restart or oldhold reopening.'
        evidence = [ref(HERE/'hrc_training_progress_observation.json'), ref(prep_path), ref(review_path), ref(HERE/'continuation_boundary_check.json'), ref(version_path), ref(version_review_path), ref(HERE/'isolated_version_feasibility.json')]
        for item in evidence:
            if item not in candidate['evidence']:
                candidate['evidence'].append(item)
        for item in [ref(HERE/'hrc_training_progress_observation.json')]:
            by_id['hierarchy-bottom-up-refined-token-composition']['evidence'].append(item)
        by_id['hierarchy-parent-segmented-bidirectional-token-state']['evidence'].append(ref(HERE/'continuation_boundary_check.json'))
        work['historical_hold_boundary_review'] = ref(HERE/'held_boundary_check.json')
        work['tick_attempt'] = {'tick_started_at':owner['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked',
            'command':'python -B pipeline/diagnostic_bundles/tick_d6b400e3/observe_hrc_training.py',
            'observation':'Exact current HRC8/50/native3233->3244 on only authorizedGPU0; no native slot. Same PSNC disabled native-check draft advanced with17actual static/refusal checks and independent review. Frozen9 saved in isolated actual commit43dce0 with blob hashes matching, primaryHEAD74f/index/28bytes and existing ledgers unchanged. No runnable binding, actual native/TRAIN/resources, new candidate/receipt/queue/launch/sync.',
            'evidence': evidence}
        work['updated_at'] = now.isoformat()
        work['next_action'] = candidate['next_action']
        decision_command = ['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','other',
            'Prepare PSNC native-check draft','Prepare disabled draft; protect PSBR74f FIFO',
            'HRC唯一GPU0原生8/50递增，PSBR已准入排队；同一PSNC补外置禁执行检查草案、17离线检查及独审。实际确认隔离worktree可不推进主HEAD，故已仅提交冻结9文件至43dce0并核blob；主74f/index/28字节和队列不变。此安全隔离版本存储修正此前需等待才能保存版本的保守决策，原绑定历史保留；真实原生/资源/执行binding仍无，无同步/新队列/启动/GPU1/M206操作。',
            '; '.join(x['path']+' SHA'+x['sha256'] for x in evidence)]
        run = subprocess.run(decision_command,capture_output=True,text=True,encoding='utf-8',env=os.environ.copy(),timeout=30)
        assert run.returncode == 0, run.stderr
        decision_path = Path(run.stdout.strip().split('-> ',1)[1].strip())
        decision = ref(decision_path)
        candidate['evidence'].append(decision)
        save(HERE/'canonical_preparation_decision.json', {'command':decision_command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'decision':decision})
        save(ROOT/'pipeline/research_work.json', work)
        assert {name:sha(ROOT/'pipeline'/name) for name in protected_names} == protected
        memory = (ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0]
        lines = memory.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('- 当前foreground'):
                lines[i] = '- 当前foreground'+TOKEN+'；actual owner与target01a159c5-29ab-7a22-ba7f-e79174757253一致，generated18:09:34.835902UTC/原deadline19:09:34.835902不延长。前轮e274已FINALIZED/released(2026-10-23 00:28:37上海)且无ownedlock/pending才begin；本轮随后真实report/finish确认收尾，不预写PASS。'
            elif line.startswith('- 本轮2026-10-23 00:05:39'):
                lines[i] = '- 当前2026-10-23 02:10:49上海真实同HRC PID2780804/start29604100/原argv/cwd/remoteHEAD74f/UUID，native8/50两次3233→3244/4686、logfresh.158s、仅HRC19728MiB context，GPU0整卡19781MiB。proof SHA58e73f3224afd3ad414e8ac231ff677a6dca071659f305bf28fbc955379480c9；GPU1未查未用，无signal/新GPU计算。'
            elif line.startswith('- PSNC外置包'):
                lines[i] = line.replace('code_commit=null/base74f，未装入Cluster/commit/sync/worker/native/resources/receipt/queue','旧包code_commit=null/base74f不改；当前冻结9文件已独立worktree提交43dce016c1a1713c2a5dab7061810dc2efde8954，主HEAD74f不动；未sync/native/resources/receipt/queue，本轮native工具为disabled草案')
            elif line.startswith('- PSNC当前blocked/'):
                lines[i] = '- PSNC当前blocked/exclusive_gpu_slot/resumeimplementation：唯一GPU0忙，已有PSBR74f新派发必须保留primaryHEAD74f。本轮独审证实独立detached worktree可安全保存版本，已仅冻9文件成43dce0，staged/final9blob逐字节匹配；旧null准备/原等待决策完整留存。以后PSBR verifiedlaunch/74f待派发安全处理后才主ff，不改活跃远端checkout；真实新版本YAML/TRAIN2与资源准入仍待空GPU0。'
            elif line.startswith('- 前轮dfb诊断stage'):
                lines[i] = line.replace('PSNC没有native worker/binding/lease','PSNC新外置native worker/adapter只是disabled草案，没有可执行binding/lease')
        memory = '\n'.join(lines)+'\n'
        memory += '\n## Last Tick\n'
        memory += '- 本轮d6b400e3 begin一次monitor/已有派发/goal，预算1、1running/0claiming/1readyPSBRwaiting，M206另为人工hold；无新终态/运行失败。HRC原进程8/50递增，当前无原生空槽；未重复monitor或诊断旧训练。\n'
        memory += '- 同一M210-PSNC推进外置native检查工具disabled草案，17项离线/实际拒绝入口检查及独审见'+ref(prep_path)['path']+' SHA'+sha(prep_path)+' / '+ref(review_path)['path']+' SHA'+sha(review_path)+'。draft code_commit=null表示未绑定执行，native/资源/真实模型梯度/效果未知。\n'
        memory += '- 独立worktree保存真实source版43dce016c1a1713c2a5dab7061810dc2efde8954，单亲74f且只新增冻结9文件，staged/final blob逐字节同原；主HEAD74f/index原字节/28status+bytes/既有三账与收据保持，远端0操作。source版独审见'+ref(version_review_path)['path']+' SHA'+sha(version_review_path)+'；原source null包和原决策保留，native执行仍未绑定。\n'
        memory += '- PSBR原receipt/标准hash和readonly admission通过、HEAD74f/index空/28保护文件字节保持；continuation审SHA207cff33d387e9b2bcb218b250354d007bd84a9ef3409bba9c8e8f06a54668e5。8due旧hold元数据/引用签名/授权边界同基准，SHA3f411b203855c929a55d748c09b99551d8826dc1ea773d926c7e5f492086504e，655正文/hash/exists-mtime复查0；旧修订上限不动。\n'
        memory += '- 当前tick_attempt是真resource_check blocked并同归PSNC证据；本轮1个仅本地隔离sourcecommit，新候选/原生计算/资源profile/收据/queue/launch/sync均0。PSBR1+PSNC准备1足够，不为统计继续造新候选。\n'
        memory += '- 七段memory/六段report按原token真实finish/receipt FINALIZED released及headless lock+pending消失才确认收尾；释放后不回写。GPU1留给别人/M206暂停，旧human hold没有新问题不重复问，调度/资源/目标/失败不改。\n'
        assert memory.count('\n## ') == 7 and len(memory.splitlines()) < 120
        save(ROOT/'pipeline/codex_memory.md',memory)
        notes = {'actions':[
            '归属actual/target一致，latest授权/目标/禁用项/onlyserver4GPU0/WindowsDisabled保持；前轮e274已确认FINALIZED released，新begin原generated18:09:34.835902/原deadline19:09:34.835902UTC不改。',
            'begin先monitor/派发已有合格队列/goal各一次，无新终态或operationalissue。额外精确只读HRC原PID/start/argv/cwd/74f/UUID核，上海02:10:49第8/50轮3233→3244/4686，GPU0仅HRC19728MiB context；不是新native计算、不是PID单独充当启动核验。',
            'PSBR原74f/c85ae4fe receipt与3标准artifacts、独立readonly admission通过；HRC唯一GPU0运行/M206原人工paused任务/HAP自然earlystop归档保持。local74f/index空/28protected status和小字节hash保持，不改变活跃远端checkout。',
            '八旧hold仅元数据/引用签名/13授权清单与3相关grant有界复核无变化；未读/hash/exists-mtime检查655历史证据，未重开scope、PCE/RSTR或新申请重复权限。',
            '准备目标已有PSBR1+PSNC模型1，不新增变体。同一PSNC外置native-check worker/adapter禁执行草案17离线检查/实际入口拒绝及独审通过，复用原YAML/TRAIN2/资源协议；draft commit null/transport未实现，不产生可执行lease/binding或native PASS。',
            '实际隔离版本可行性核查发现可保持主HEAD74f，故已在独立detached worktree仅冻9文件普通提交43dce0；每命令autocrlf=false保混合换行，staged/final9blob均同冻hash，单亲74f/只新增9文件/主index原字节与28status+bytes保持，独审无问题。原null包和此前等待决策不改，当前source版真实但native执行未绑定，远端0操作。',
            '原23static/17数学是上轮模型准备结果，不算本轮native；actual dtype DCT/模型/loader/inventory/梯度更新/资源/效果仍未执行或未知。当前resource_check blocked证据同归PSNC；本轮1本地隔离sourcecommit，0新候选/native/profile/receipt/queue/launch/sync，既有三账与收据hash保持。',
            '后续先保护PSBR74f正常派发，再允许主HEAD安全ff至已存43dce0；不得同步修改活跃checkout。补齐并review运行编排、真正空闲授权GPU0/fresh owner/assets/locks后，真实新版本原YAML M95/candidate TRAIN2及原资源通过才准入；GPU1/M206/调度不动。真实finish/receipt released才确认本轮完成，释放后不回写。'
        ],'decisions':['canonical other决策已记录：同一PSNC禁执行检查草案及独立source版本准备；隔离commit经实证可不影响主74f派发，故修正此前保守等待保存版本的实施决策。旧准备/决策/失败不改，不造新变体，实际native未知。']}
        save(HERE/'tick_notes.json',notes)
        result = {'recorded_at':now.isoformat(),'token':TOKEN,'candidate_id':CID,'preparation':ref(prep_path),'review':ref(review_path),
            'decision':decision,'code_commit':version['code_commit'],'native_execution_code_commit':None,'native':'NOT_RUN','resources':'NOT_RUN',
            'isolated_local_source_commits':1,'new_candidate_receipt_queue_launch_sync':False,
            'protected_records_unchanged':{name:sha(ROOT/'pipeline'/name)==expected for name,expected in protected.items()},'memory_lines':len(memory.splitlines())}
        save(HERE/'persistence_result.json',result)
        print(json.dumps(result,ensure_ascii=False))
    finally:
        lock.close()

if __name__ == '__main__':
    main()
