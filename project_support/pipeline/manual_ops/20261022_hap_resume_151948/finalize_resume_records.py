"""Publish only the already verified native full-resume result; no remote mutation."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import pipeline_monitor as monitor
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,value):
    tmp=p.with_name(p.name+'.hap_final_151948.tmp')
    with tmp.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def main():
    assert os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert not (ROOT/'pipeline/headless/.foreground.lockdir').exists()
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        proof=read(BASE/'native_resume_progress.json');assert proof['progress_increased'] and proof['native_resume_metadata_verified']
        dispatch=read(BASE/'dispatch_result.json');assert dispatch['verified_native_progress']
        operation=read(BASE/'operation.json');authorization=operation['authorization']
        now=dt.datetime.now(dt.timezone.utc)
        queue=monitor.load_queue(str(ROOT));task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M207-HAP')
        assert task['status']=='running' and task['launch_verified'] is True and task['pid']==1063355
        assert task['resume_authorization']==authorization
        before=read(BASE/'before_queue.json');m206_before=next(t for t in before['gpu_queues']['server-4'] if t['id']=='M206-CGCA')
        assert next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA')==m206_before
        task.update(training_status='running',resume_authorized=True,native_resume_progress=ref(BASE/'native_resume_progress.json'))
        monitor.save_queue(str(ROOT),queue)
        exp=monitor.load_experiment(str(ROOT),'M207-HAP')
        assert exp['status']=='running' and exp['pid']==1063355 and exp['prior_runs']
        exp.update(training_status='running',resume_authorized=True,native_resume_progress=ref(BASE/'native_resume_progress.json'))
        exp.setdefault('history',[]).append(dict(ts=now.isoformat(),action='native_full_resume_metadata_and_increasing_progress_verified',
            epoch=19,from_step=proof['from_step']['step'],to_step=proof['to_step']['step'],
            proof=ref(BASE/'native_resume_progress.json'),authorization=authorization))
        monitor.save_experiment(str(ROOT),exp)
        work_path=ROOT/'pipeline/research_work.json';work=read(work_path)
        for c in work['candidates']:
            if c.get('experiment_id')=='M207-HAP':
                c.update(stage='training',training_status='running',human_hold=False,resume_authorized=True,
                    next_action='Authorized same HAP full resume is actually running physicalGPU0 PID1063355 at native epoch19; start_epoch19/best.4975287616252899/noimprove0 restored and steps71->81 verified. Monitor original protocol and exact process/log; original DataLoader root cause remains unknown. Preserve prior crash and fixed full checkpoint; no retuning or automatic replay after another uncertain launch. GPU1 remains released, M206 manually paused.')
                for ev in (ref(BASE/'dispatch_result.json'),ref(BASE/'native_resume_progress.json')):
                    if ev not in c['evidence']:c['evidence'].append(ev)
            elif c.get('experiment_id') in ('M208-HRC','M209-PSBR'):
                c.update(blocker_kind='exclusive_gpu_slot',blocked_at=now.isoformat(),retry_after=(now+dt.timedelta(hours=1)).isoformat(),
                    blocker='Authorized full-resumed M207-HAP is actually running on the only project GPU0. GPU1 remains released to others.',
                    unblock_condition='HAP natural completion or other human-authorized change, then fresh actual physicalGPU0 idle/UUID/exclusive lease and frozen worker/adapter checks. GPU1 availability is not authorization.')
                if ref(BASE/'native_resume_progress.json') not in c['evidence']:c['evidence'].append(ref(BASE/'native_resume_progress.json'))
        work['updated_at']=now.isoformat()
        work['next_action']='Monitor verified resumed HAP on GPU0 under original protocol. M206 remains user-paused and GPU1 excluded. HRC/PSBR native checks wait for a genuine later GPU0 opening; retain all old holds/budgets/bans.'
        save(work_path,work)
        memory_path=ROOT/'pipeline/codex_memory.md';memory=memory_path.read_text(encoding='utf-8')
        (BASE/'before_codex_memory.md').write_text(memory,encoding='utf-8')
        lines=memory.splitlines()
        lines[3]='- 最近foreground1ee09b795e7d4145a7b52242a7d16bbe已FINALIZED/released（UTC06:16:59）且lock/pending不存在。随后当前manual_ops/20261022_hap_resume_151948在实际owner01a159c5-29ab-7a22-ba7f-e79174757253与target一致下持.pipeline.lock执行人类授权HAP全状态续训；没有新foreground租约/调度变更。'
        memory='\n'.join(lines)+'\n'
        memory=memory.replace('- HAP现blocked/human_authorization/resume_stage training。','- HAP现training/running physicalGPU0 PID1063355；人类已明确授权同实验完整状态续训。')
        memory=memory.replace('预期从epoch19开始。','原生已确认start_epoch19/best.4975287616252899/noimprove0，额外两次exact进度71→81/4686。')
        old_line=next(line for line in memory.splitlines() if line.startswith('- 本次HAP human resume grant'))
        memory=memory.replace(old_line,'- 本次直接人类回复“授权 HAP 在 GPU0 续训”已记录；grant pipeline/authorizations/m207_resume_gpu0_20261022_hap_resume_151948.json SHA21799cd7854fd9e7b2346b7464822b2682e9cebbf5bfc16926544cb8224f13a5，purpose cluster_native_resume精确绑定M207/f518/nativeYAML/GPU0/epoch18固定全state与28ad SHA。旧问答已AUTHORIZED，不再问；不涵盖M206/GPU1/冷启动/参数变更。')
        memory=memory.replace('- HRC/PSBR均blocked/live_external_gpu_occupation/resumevalidation；','- HRC/PSBR均blocked/exclusive_gpu_slot/resumevalidation，唯一GPU0现由真实续训HAP占用；')
        old_line=next(line for line in memory.splitlines() if line.startswith('- 前轮04:25:35UTC HAP crashed归档'))
        memory=memory.replace(old_line,'- 原HAP crashed归档完整保留至当前exp.prior_runs所引用manual prior_crashed_experiment.json及tick5c terminal_archive；新当前exp/queue/running已为同M207 fullresume PID1063355/GPU0、launch_verifiedtrue，旧history/receipt/source保持。M206 waiting/paused_by_user/dispatch_hold/resumefalse逐字段与manual before_queue一致，不计readywaiting。HRC/PSBR未准入/入队。')
        old_line=next(line for line in memory.splitlines() if line.startswith('- GPU0最后fresh实观'))
        memory=memory.replace(old_line,'- 本次GPU0在UTC07:20:31、07:21:57取得3flocks前后、07:22:04均41MiB/util0/no contexts实核空闲。canonical启动前另查UUID/无context；随后实际GPU0为HAP PID1063355，启动后两次PID/starttime/argv/cwd/原checkpoint/原生resume元数据与增长进度核实。GPU1未查询或计算，无kill/reset/抢占。')
        memory=memory.replace('root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1。04:19:03及04:22:48UTC canonical sourceverify确认','root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1。当前manual canonical sourceverify及dispatch重复核确认')
        before_last=memory.split('\n## Last Tick\n')[0]
        tail='''\n## Last Tick
- 最近foreground1ee09b79已按真实报告/finish收尾FINALIZED/released，无新当轮失败；其后人类精确回复HAP GPU0续训，本次独立manual operation已立即接续，不改旧tick报告。
- manual_ops/20261022_hap_resume_151948：新source=human grant21799cd…；freshCPU固定936269892B checkpoint SHA28ad不变、model/optimizer642states5groups/scheduler/meta18/.4975287616/noimprove0，CUDA未初始化。原train/dataset/annotation/pretrain hashes全匹配；GPU0实空/3flocks可取得，未用旧diagnostic lease。
- 原f518 admission61aded与本次fullresume契约通过，remote source只读多次核，无safe_sync/checkout/改YAML/代码/环境。保存完整crashed exp/prior_runs和旧history后，同ID恢复waiting/deployment；仅一次canonical _process_queue→safe_launch --resume，Popen前再核source/ckpt SHA和GPU0空闲；无冷启动/重放/信号。
- 实际新PID1063355/log root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_152545.log；canonical原生进度已验证、额外exact observer epoch19 steps71→81/4686，native resume metadata start19/best.4975287616252899/noimprove0；proof native_resume_progress.json SHA0cc547c0b43c0fd6775d5bdb8248ba629b82e29518671adb0c4882ed5edcda20。不是仅PID登记。
- 0新结构/0修订/0代码提交/0同步/0新科学准入/1已存在实验全状态恢复；M206人工暂停/所有字段不动，GPU1继续给别人，currentallowed[0]/max1及server3/server6禁用/项目调度Disabled不改。原DataLoader根因仍UNKNOWN，不称已修复或机制收益；epoch19部分批次/RNG状态不能精确恢复的限制不变。
- 后续监控同一新HAP进程/日志；若再失败或启动不确定保留现场再诊断，不盲重放。HRC/PSBR已有准备保持NOT_RUN，待HAP自然完成后的真实GPU0空槽，核新owner/context/外锚/原deadline后真TRAIN2和资源pair，才标准汇总/准入；不提前用GPU1或解除旧hold。
'''
        memory=before_last+tail;assert len(memory.splitlines())<120 and memory.count('\n## ')==7
        tmp=memory_path.with_name('codex_memory.hap_final_151948.tmp');tmp.write_text(memory,encoding='utf-8');os.replace(tmp,memory_path)
        report=BASE/'manual_report.md'
        report.write_text('# M207-HAP 完整状态续训记录\n\n'
            '用户已明确授权 HAP 在 GPU0 续训。本操作保持原 f518 版本、原 YAML、seed1999、50epochs/maxiters70、4workers；GPU1 继续留给别人，M206 保持暂停。\n\n'
            '固定 epoch18 完整检查点重新核验 SHA、模型、优化器、调度器与 meta 通过；原生训练/数据源、TRAIN 标注与 pretrain 哈希保持，远端源码仅允许原有路径映射，未同步或修改。GPU0 在启动前多次确认空闲、UUID 匹配且三项 flock 可取得。\n\n'
            '保留原 crashed 完整归档及 history，以同一 M207 原收据执行一次 canonical full resume。新 PID1063355，原生确认从 epoch19 开始、best_miou0.4975287616252899/noimprove0；额外采样训练步数71→81，物理GPU0 context与固定checkpoint argv匹配。\n\n'
            'DataLoader 原故障底因仍未知，此次成功启动不证明已修复。第19轮旧的部分minibatch与完整RNG/worker轨迹未保存，未承诺精确恢复至中断批次。M206队列逐字段保持，无GPU1计算、信号、冷启动、参数/源/环境/调度变更。\n\n'
            '完整证据见本目录 operation.json、fresh_runtime_checkpoint_verification.json、checkpoint_evidence.json、dispatch_result.json、native_resume_progress.json；同目录保存原 crashed exp。\n',encoding='utf-8')
        summary=dict(completed_at=now.isoformat(),operation='human_authorized_same_hap_full_resume',id='M207-HAP',
            status='running',pid=1063355,gpu='0',epoch=19,steps='71->81/4686',
            saved_best_miou=0.4975287616252899,authorization=authorization,
            checkpoint=ref(BASE/'checkpoint_evidence.json'),dispatch=ref(BASE/'dispatch_result.json'),
            progress=ref(BASE/'native_resume_progress.json'),manual_report=ref(report),
            m206_queue_unchanged=True,gpu1_used=False,source_synced=False,model_or_yaml_changed=False,
            scheduler_changed=False,original_failure_fixed=False,needs_further_human_confirmation=False)
        save(BASE/'operation_summary.json',summary)
        print(json.dumps(dict(status='HAP_FULL_RESUME_VERIFIED',pid=1063355,epoch=19,steps='71->81',
            manual_report=str(report),m206_paused_preserved=True,gpu1_used=False),ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
