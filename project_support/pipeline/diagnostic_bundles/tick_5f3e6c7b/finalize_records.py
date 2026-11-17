"""Persist this tick's actual terminal, admission and verified launch."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
SOURCE = '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_FINAL_RECORDS')
        return
    guard()
    baseline_path = HERE / 'post_aoc_launch_baseline.json'
    assert sha(baseline_path) == 'b7b45e1c7b14586512bb40c33cadf54c361ff2ded34fa2463f1733aa7eddedc7'
    b = u.read(baseline_path)
    repo = ROOT / 'Cluster'
    def protect():
        guard()
        assert u.git(repo, 'rev-parse', 'HEAD').decode().strip() == SOURCE == b['head']
        assert u.git(repo, 'status', '--porcelain=v1', '--untracked-files=all', '-z').hex() == b['status_hex']
        assert not u.git(repo, 'diff', '--cached', '--name-only', '-z')
        assert all(sha(repo / n) == h for n, h in b['files'].items())
        assert all(sha(repo / n) == h for n, h in b['current_candidate_source_paths'].items())
        index = Path(u.git(repo, 'rev-parse', '--git-path', 'index').decode().strip())
        index = index if index.is_absolute() else repo / index
        assert sha(index) == b['index_sha256']
        assert all(sha(ROOT / 'pipeline' / n) == h for n, h in b['protected_ledgers'].items())
    protect()
    assert sha(ROOT / 'pipeline/admissions/M222-AOC.json') == 'bf4426ca1b9251ed850de7d8a13f643a26de14ef59a1329c345140d4436a1778'
    assert sha(ROOT / 'pipeline/admissions/M221-PES.json') == '6fcee3f5bbfb865b9902ff04e0b019c464f8911c600906de07577608a930f2b1'
    assert u.read(HERE / 'pes_finalize_result.json')['archive_id'] == 'fab7b5b013ea4e858cf018f37233f6a2'
    progress = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    assert sha(progress) == '5106a25d114181f9271e25002de47e49805539ebed40bbfe65227d24a76a06ea'
    assert sha(HERE / 'aoc_launch_independent_review.json') == 'b905573a529b602e0682dba66f44ac9e739c05b544514351c36f73e5bf0d96cb'
    occupation = u.read(HERE / 'gpu0_occupation_closure_result.json')['result']['evidence']
    proof = u.read(ROOT / occupation['path'])
    assert sha(ROOT / occupation['path']) == occupation['sha256'] == '80cf279d79cb556b2cedc99cc2f4dd4e731de1aea035d97cd22abe08717ddec9'
    assert proof['token'] == EXPECTED['token'] and proof['snapshot_sha256'] == EXPECTED['context_sha256']
    assert 0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(proof['observed_at'])).total_seconds() < 240
    work = u.read(ROOT / 'pipeline/research_work.json')
    assert len(work['candidates']) == 149
    fcb = next(c for c in work['candidates'] if c.get('experiment_id') == 'M223-FCB')
    aoc = next(c for c in work['candidates'] if c.get('experiment_id') == 'M222-AOC')
    pes = next(c for c in work['candidates'] if c.get('experiment_id') == 'M221-PES')
    assert fcb['stage'] == 'blocked' and fcb['blocker_kind'] == 'exclusive_gpu_slot' and fcb['occupation_evidence'] == occupation
    assert aoc['stage'] == 'training' and aoc['code_commit'] == SOURCE
    assert pes['stage'] == 'complete' and pes['training_status'] == 'crashed' and pes['failure_scope'] == 'inconclusive'
    assert work['tick_attempt']['tick_started_at'] == EXPECTED['generated_at']
    assert work['tick_attempt']['kind'] == 'resource_check' and work['tick_attempt']['result'] == 'blocked'
    original = u.read(HERE / 'protected_assets_before.json')
    excluded = {'M221-PES', 'M222-AOC', 'M223-FCB'}
    assert all(u.digest(c) == original['candidate_digests'][c['id']] for c in work['candidates'] if c.get('experiment_id') not in excluded)
    memory = f'''# Codex Research Memory

## Goal And Phase
- 当前5f3e6c7b generated{EXPECTED['generated_at']}/deadline{EXPECTED['deadline_at']}原值，实际thread01a159c5-29ab-7a22-ba7f-e79174757253匹配foreground；Phase1 pointfeature→inst_feats→masks，目标.5100/冠军M95 .5020/gap.0080，Phase2人工。
- goal0441/standing2e892/GPU0auth94075/SERVERS2583/closure2993不动；仅server4物理GPU0/max1，GPU1禁用，后台Pipeline-cluster_project禁用不改。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50-maxiters70-patience10/10G及bans保持。

## Champion And Baseline
- 最佳仍M95 .5020，baseline .4894；新正式AOC首轮尚无val/best/noimprove，均None非0。PES只有4次已完成验证[.2965591251850128,.3763071894645691,.41243723034858704,.4211066663265228]，partialbest.4211066663265228，训练崩溃未完成，非最终效果或机制否定。
- 历史DCE正常earlystop27/50/noimprove10/best.4971300959587097已在14fea canonical归档a5a9；BEC.5001/24、AEF.495597243309021/23、CRE.4961479902267456/30保持，不重启或重复归档。

## Active Hypotheses
- 当前唯一正式M222-AOC，source/primary/runtime0314b932a92a8cc7f67804068ecb1c1f7a5f2e33，单父9c。共享binaryT的两祖先次序diamond差q；fine q与两层沿原truefinepath直接mean同q，原3LN3rawskip/HCG/CSORT/单inst保持；novelty/efficacy UNKNOWN。
- 原f7 NULL/ref5c/proof83d/c11/native9cf/op e45/release630/协议a041均不改。本轮actualmanifest77c0d273/leaseb0134a9a，fresh prepare-stage24540b18及四arm都terminal0。两自然TRAIN配对common动态835/155907386、names/shapes/count/hash一致；candidate losses9.172385215759277/13.90751838684082。
- 每实际forward2048真finepaths，两sharedcell/GELU各4096行、两sameq directmeans、真实wholecell原loss梯度和weight/module每步更新、原skip/HCG/inst-mask均经actualpeer e42c9041；逐call/branch/row/列/bias零合法，无新FP32/Jacobian门，optional未观测不补采样。
- AOC原同口径resources9.724783692G vs M95 9.762532428G；median35.558438452426344 vs34.864016459323466ms（+1.9918%），P9037.69716832321137 vs36.14520003320649ms（+4.2937%），alloc930981888 vs936763392（−.61718%）。fullunsupported/bs1lang1/warm20repeat100保留，15%条件false；不称更快/纯TRAIN峰值或最终有效。
- 本轮disabledpromotion a1c707保留DRAFTTrue/null（来自38ab shapes修正）；真实peer e42c绑定新active4f7ac1，再summary048c/smoke449685/resourcesa90bcc/constraints23932，exact9A localff9c→0314与safe remote sync、receiptbf4426ca准入1、canonicaldispatch76bfdfae一次/15pinnedcalls中唯一Popen，strictgrowth5106a25d核真启动。原d3接口错误/拒签d66a/38ab修正保留，不是模型修订。
- M223-FCB原型44c63/manifest95ae9872/协议3809eecd/源审c91f7不改，原code/source/actualparentNULL/ref9c不回填；真scene-local fine×coarse共享q双marginal+middle原fineparent组合，原3LN3skip/HCG单inst不动，效力/新颖性未知。
- FCB实际isolated d4d062ef075abfe7cde93d4b4347ce146572762f单父0314/proof0a792/peer408dae，精确9A/9blob不改。原conditionalnativecc9/op5fcdc/peer1c1db10activeNULL，无FCB native/resources/receipt/exp/queue；本轮实际父0314与AOC技术receipt已满足，localguardbf6a071d真实passes/transport0，不代表GPU0空闲。

## Closed Or Failed Directions
- 原PES2265073在TRAIN5/50 529/4686异常退出，ownlog5731527B/358d479d完整保留，无原PID或sameconfig进程；4val best.4211066663265228/noimprove0，无早停。精确trace native clip_grad_norm_(model.parameters())→named_parameters/_named_members→ValueError: too many values to unpack(expected0)，rootcause UNKNOWN/failure_scope inconclusive，不宣称PES图被证伪或公共运行时已修复。
- PES实际terminalpeer f514050c保留真实concern，canonical一次crashed archivefab7b5b013ea4e858cf018f37233f6a2，stagecomplete只表示终态归档。原source9c/技术四门/receipt6fce/launchproof/checkpoint不重标；未自动resume/coldstart/patch。任何恢复需具体完整检查点/版本/运行时/资源计划与所需授权。
- 首PES liveobserver1bd2的proc.exists/UID断言失败是观察失败，crash结论来自随后原日志/进程消失/source/完整拷贝独审dbd471而非该断言。AOC后续原生成功不定位或修复PES异常。
- APF/e759旧DataLoader before-forward dtype crash、HPC73ba stopped_unknown/CTS14/BFC overlap和触发样本/RNG/上游causeUNKNOWN保持。旧10hold、M206用户暂停/dispatch_hold/noPID、PCE2+extra1/RSTR2已尽/HAP旧授权消费均不重开或GPU0迁移。

## Running And Queue
- 原AOC PID3437349/start90046755，log /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc_20261029_222527.log；UTC14:26:42→45 TRAIN1/50 156→165/4686，日志96443→98549，原8源/YAML77e/0314/GPU0context保持，valNone，launchpeerb905573a。
- queue launch_verifiedtrue/training_progress但dispatch_phase旧progress_pending不能重派。M206waiting不ready；PES已crashed归档无live槽。FCB blocked exclusive_gpu_slot/resumevalidation，当前canonicalproof80cf279d实际原AOC计算PID占GPU0，parent技术ready，待自然释放再原d4 pairedTRAIN2/resources，无GPU1/驱逐/信号。

## Open Questions And Risks
- AOC差分可能丢共有语义/仿射fine项取消/b=c零差；FCB双marginal代数耦合/全局洗平、原输入本可已global，不宣称新信息/已修瓶颈。FCB源MAC估多.1048576G非wholemodel10G/延迟/显存PASS。
- PES参数迭代异常确因未知；新AOC技术通过与正式首轮增长不能证明长期运行稳定或旧错误消失。纯TRAIN峰值、训练收益与新颖性未知；不添逐map/列/row/pair/bias正性、FP32守恒/Jacobian/多root门。

## Last Tick
- 149ID/0新候选/0模型修订/0新commit；本轮PES崩溃归档1、AOC实际四arm/准入1/正式启动1且严格步增，FCB只技术父ready+资源等待更新。不重复算旧PES原生/历史DCE。
- 主线/runtime已真实推进0314，原user28/status/indexempty和其他146候选保持；当前28生命周期文件（新增AOCreceipt/exp）存post_tick_baseline.json，原0b preflight与合法postPES510c/新sourcebaseline原件不覆盖。未来setup record_utils.SOURCE必须0314并用新baseline，不回退9c/PES原PID/旧观察器。
- 后续fresh tick复用AOC strictobserver实际PID/start/log，先监控原AOC自然完成，再FCB原d4与当时实际兼容0314/receipt/空卡三锁核。全六段report/finish由root按原token收尾，完成以最终receipt为准，不预签。
'''
    assert len(memory.splitlines()) < 120
    notes = {'actions': [
        '原PES在第5/50轮529/4686因参数迭代ValueError异常退出，4次验证partial best0.4211066663265228。完整原日志/原PID消失/8源及YAML/精确指标经独审后canonical一次crashed归档；原因UNKNOWN/inconclusive，不自动恢复或当正常早停。',
        'GPU0真实空闲且三锁可用、canonical旧槽清理后，原AOC9cf/e45执行fresh prepare-stage和四实际臂；两自然TRAIN/common初始化匹配、sharedcell两stage/q两directmean/wholecell原loss梯度与真实更新及原HCG单inst路径通过独审。',
        'AOC同口径资源9.724783692G，median/P90比对照慢约1.99%/4.29%，allocated约低0.617%，15%显存条件未触发；fullunsupported与原测试口径保留，训练收益/纯TRAIN峰值未知。',
        '真实actualpeer绑定新副本后，仅exact9A ff与safe sync0314、真实receipt bf4426准入一次，再canonical GPU0派发一次。原AOC3437349/start90046755在上海22:26:42至45首轮156→165/4686，未输出验证值。',
        'FCB当前实际AOC0314父与技术receipt已就绪，本地guard passes且transport0；GPU0被原AOC占用，freshcanonical查询核忙，FCB原生继续等待。GPU1不使用，旧任务/暂停/失败和用户28文件/index保持。'],
        'decisions': [
            '最佳仍M95 .5020、目标.5100；PES为未完成训练的异常结果，不能作效果/机制否定；AOC只有真实技术准入与正式步增，尚无验证效果。',
            '保留PES原source9c/receipt6fce/技术证据与checkpoint，不因队列容量或本轮heartbeat自动恢复。PES具体运行时原因未知，AOC后续成功不等于修复旧异常。',
            '监控唯一原AOC GPU0任务，不重放旧progress_pending；FCB仅在卡自然释放且fresh owner/原deadline/source/UUID/assets/三锁复核后跑原d4 pairedTRAIN2/resources，过了再准入。',
            '本轮无新模型/新commit，不动goal/bans/资源/数据/seed/schedule/旧授权或调度。新真实基线是0314/28账，后续接管须更新SOURCE和观察器；无需用户重复授权普通项目操作。']}
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        protect()
        before = sha(ROOT / 'pipeline/research_work.json')
        u.save(HERE / 'final_records_intent.json', {'owner': EXPECTED, 'research_work_sha256': before,
            'latest_original_progress': u.ref(progress), 'fresh_FCB_occupation': occupation,
            'scope': 'Memory and report notes only; all actual terminal/native/admission/launch actions already have immutable evidence. No postflight claim.'})
        u.atomic(ROOT / 'pipeline/codex_memory.md', memory, text=True)
        u.save(HERE / 'report_notes.json', notes)
        assert sha(ROOT / 'pipeline/research_work.json') == before
        post = dict(b)
        post.update(owner=EXPECTED, recorded_at=datetime.now(timezone.utc).isoformat(),
                    candidate_digests={c['id']: u.digest(c) for c in work['candidates']}, research_work_sha256=before,
                    fresh_FCB_occupation=occupation, current_original_AOC_progress=u.ref(progress))
        u.save(HERE / 'post_tick_baseline.json', post)
        protect()
        u.save(HERE / 'final_records_result.json', {'owner': EXPECTED,
            'status': 'ACTUAL_PES_CRASH_AOC_ADMISSION_AND_LAUNCH_MEMORY_SAVED_POSTFLIGHT_NOT_YET_RUN',
            'candidate_count': 149, 'new_candidates': 0, 'model_revisions': 0, 'new_commits': 0,
            'terminal_archives': 1, 'native_arms': 4, 'admissions': 1, 'formal_launches': 1,
            'current_primary_runtime_commit': SOURCE, 'memory_lines': len(memory.splitlines()),
            'post_tick_baseline': u.ref(HERE / 'post_tick_baseline.json'),
            'user28_index_and28_lifecycle_preserved_since_verified_launch': True})
        print({'status': 'Actual terminal, admission and verified launch records saved; postflight not yet run',
               'memory_lines': len(memory.splitlines()), 'baseline': u.ref(HERE / 'post_tick_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
