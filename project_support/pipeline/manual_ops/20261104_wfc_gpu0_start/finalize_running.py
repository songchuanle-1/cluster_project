"""Fresh original-resume progress proof and final manual lifecycle record."""
import copy,hashlib,json,os,subprocess
from pathlib import Path
import yaml
from prepare_and_queue import ROOT,P,OUT,ID,NEW_ROOT,OLD_ROOT,now,load,save,sha,ref,guard,mon

PAYLOAD=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
from datetime import datetime,timezone
import json,os,re,subprocess,time
from pathlib import Path
def sample():
    p=Path('/proc')/str(PARAMS['pid']); tail=(p/'stat').read_text().rsplit(')',1)[1].split()
    args=[a.decode() for a in (p/'cmdline').read_bytes().split(b'\0') if a]
    assert args==['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1','--resume',PARAMS['resume_from']]
    assert os.readlink(p/'cwd')==PARAMS['remote_code_root'] and p.stat().st_uid==os.getuid()
    assert os.readlink(p/'fd/1')==PARAMS['log']
    logfile=Path(PARAMS['log'])
    with logfile.open('rb') as f:
        header=f.read(2000000).decode(errors='replace'); f.seek(max(0,logfile.stat().st_size-160000)); text=f.read().decode(errors='replace')
    assert not any(s in text for s in ('Traceback (most recent call last):','CUDA out of memory','RuntimeError:'))
    matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
    progress=[dict(epoch=int(m[1]),epochs=int(m[2]),step=int(m[3]),steps=int(m[4])) for m in matches[-2:]]
    resume=re.findall(r'resume start_epoch:(\d+),best_miou:([^,\r\n]+),epochs_no_improve:(\d+)',header)
    assert resume and any(int(e)==26 and abs(float(b)-0.49711745977401733)<1e-7 and int(n)==5 for e,b,n in resume)
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
    rows=[line for line in contexts.splitlines() if line.split(',')[0].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
    assert any(int(line.split(',')[1])==PARAMS['pid'] for line in rows)
    return dict(observed_at=datetime.now(timezone.utc).isoformat(),pid=PARAMS['pid'],starttime=tail[19],state=tail[0],argv=args,
        cwd=PARAMS['remote_code_root'],log=PARAMS['log'],log_bytes=logfile.stat().st_size,native_progress=progress,
        native_resume_meta=[dict(start_epoch=int(e),best_miou=float(b),epochs_no_improve=int(n)) for e,b,n in resume],physical_gpu0_contexts=rows)
a=sample(); time.sleep(3); b=sample()
assert a['starttime']==b['starttime'] and a['native_progress'] and b['native_progress']
pa=a['native_progress'][-1]; pb=b['native_progress'][-1]
assert pa['epoch']==pb['epoch']==26 and pb['step']>pa['step']
print(json.dumps(dict(recorded_at=datetime.now(timezone.utc).isoformat(),observations=[a,b],progress_increased=True,
    restored_epoch25_to_native26=True,model_optimizer_scheduler_resume_contract_verified=True,
    pid=PARAMS['pid'],starttime=a['starttime'],from_step=pa,to_step=pb,signals_sent=False,GPU1='NOT_QUERIED_NOT_AUTHORIZED')))
'''
def main():
    guard(); lock=mon.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard(); q=load(P/'queue.json'); task=next(t for t in q['gpu_queues']['server-4'] if t['id']==ID)
        assert task['status']=='running' and task['launch_verified'] is True and task['resume_authorized'] is True and not task.get('dispatch_hold')
        params={k:task[k] for k in ('pid','config','resume_from','log')}; params['remote_code_root']=NEW_ROOT
        if (OUT/'native_resume_progress.json').exists():
            proof=load(OUT/'native_resume_progress.json'); assert proof['returncode']==0 and proof['data']['pid']==task['pid']
        else:
            cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input='PARAMS='+repr(params)+'\n'+PAYLOAD,text=True,encoding='utf-8',capture_output=True,timeout=40)
            proof=dict(recorded_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr)
            if cp.returncode==0: proof['data']=json.loads(cp.stdout)
            save(OUT/'native_resume_progress.json',proof); assert cp.returncode==0,cp.stderr[-1500:]
        observed=proof['data']; assert observed['progress_increased']
        resource=ref(P/'authorizations/server4_gpu0_20261104.json')
        task.update(training_status='running',native_resume_progress=ref(OUT/'native_resume_progress.json'),runtime_starttime=observed['starttime'],remote_code_root=NEW_ROOT,resource_authorization=resource)
        mon.save_queue(str(ROOT),q)
        ep=P/'experiments/M226-WFC.json'; exp=load(ep); assert exp['status']=='running' and exp['pid']==task['pid']
        exp.update(training_status='running',resume_authorized=True,native_resume_progress=ref(OUT/'native_resume_progress.json'),runtime_starttime=observed['starttime'],remote_code_root=NEW_ROOT,resource_authorization=resource)
        if not any(h.get('action')=='full_resume_epoch26_actual_increasing_progress_verified' and h.get('proof')==ref(OUT/'native_resume_progress.json') for h in exp.setdefault('history',[])):
            exp['history'].append(dict(ts=now(),action='full_resume_epoch26_actual_increasing_progress_verified',saved_checkpoint_epoch=25,
                from_step=observed['from_step'],to_step=observed['to_step'],authorization=task['resume_authorization'],proof=ref(OUT/'native_resume_progress.json')))
        save(ep,exp)
        w=load(P/'research_work.json'); c=next(c for c in w['candidates'] if c.get('experiment_id')==ID)
        c.update(stage='training',training_status='running',human_hold=False,resume_authorized=True,remote_code_root=NEW_ROOT,resource_authorization=resource,
            next_action='Original WFC94 is actually full-state resumed on physicalGPU0 in isolated original checkout. Native epoch26/best .49711745977401733/no-improve5 restored and fresh exact PID/start/argv plus increasing steps verified. Monitor same run under original protocol. Preserve original4457 root, LFT/M206 holds and GPU1 ban; no replay or extra restart.')
        for k in ('blocker','blocker_kind','unblock_condition','blocked_at','retry_after'): c.pop(k,None)
        for e in [ref(OUT/'reconciled_dispatch_result.json'),ref(OUT/'native_resume_progress.json')]:
            if e not in c['evidence']: c['evidence'].append(e)
        w.update(updated_at=now(),next_action=c['next_action']); save(P/'research_work.json',w)
        b=load(OUT/'before_pipeline__research_work.json'); assert {c['id']:c for c in b['candidates'] if c.get('experiment_id')!=ID}=={c['id']:c for c in w['candidates'] if c.get('experiment_id')!=ID}
        oldq=load(OUT/'before_pipeline__queue.json'); assert [t for t in oldq['gpu_queues']['server-4'] if t['id']!=ID]==[t for t in q['gpu_queues']['server-4'] if t['id']!=ID]
        run=load(P/'running.json'); expected=load(OUT/'before_pipeline__running.json'); expected['server-4']['0']=ID; assert run==expected
        assets=load(P/'diagnostic_bundles/tick_25fc0b57/protected_assets_before.json')
        for n,h in assets['files'].items(): assert sha(ROOT/'Cluster'/n)==h,n
        for n,h in assets['protected_ledgers'].items():
            if n not in {'queue.json','running.json','experiments/M226-WFC.json','experiments/M227-LFT.json'}: assert sha(P/n)==h,n
        # LFT was legitimately paused on Nov01 after the Oct31 asset baseline.
        lft=P/'experiments/M227-LFT.json'; lft_exp=load(lft)
        assert lft.stat().st_mtime_ns < (OUT/'human_request.json').stat().st_mtime_ns
        lft_task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M227-LFT')
        assert lft_exp['status']==lft_task['status']=='waiting' and lft_exp['training_status']==lft_task['training_status']=='paused_by_user'
        assert lft_exp['paused_run']==lft_task['paused_run'] and lft_exp['resume_authorized'] is False
        git=['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-c','core.fsmonitor=false','-C',str(ROOT/'Cluster')]
        def g(*args): return subprocess.check_output(git+list(args))
        assert g('rev-parse','HEAD').decode().strip()==assets['head']
        assert g('status','--porcelain=v1','--untracked-files=all','-z').hex()==assets['status_hex'] and not g('diff','--cached','--name-only')
        ix=Path(g('rev-parse','--git-path','index').decode().strip()); ix=ix if ix.is_absolute() else ROOT/'Cluster'/ix; assert sha(ix)==assets['index_sha256']
        s=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8')); old=yaml.safe_load((OUT/'before_SERVERS.yaml').read_text(encoding='utf-8')); old['servers']['server-4']['remote_code_root']=NEW_ROOT; assert old==s
        memory=(OUT/'before_pipeline__codex_memory.md').read_text(encoding='utf-8'); lines=memory.splitlines()
        lines=[('- 最新用户先授权“可使用一张卡server4-gpu0”，随后明确“启动”（2026-11-04）。已恢复原GPU0 WFC完整续训；仅GPU0/[0]/dispatchtrue/max1，GPU1禁用，LFT/M206暂停保持。WFC无需重复人工恢复授权。' if x.startswith('- 最新直接用户指令') else x) for x in lines]
        memory='\n'.join(lines)+'\n'; a=memory.index('## Running And Queue'); z=memory.index('## Open Questions And Risks',a)
        memory=memory[:a]+f'''## Running And Queue
- M226-WFC已真实续训running/GPU0/PID{task['pid']}/start{observed['starttime']}，原94/source9/receipt保持；原完整checkpoint25恢复optimizer/scheduler与best .49711745977401733/noimp5，第26轮实际步数{observed['from_step']['step']}→{observed['to_step']['step']}/4686。LFT/M206仍user_paused/resumefalse，GPU1禁用。
- 当前SERVERS.server4.remote_code_root={NEW_ROOT}，独立git worktree精确HEAD94；旧{OLD_ROOT}保持HEAD4457/source/status不动。本地主线4457及用户28files/status/index保持；只复制ignored pointgroup .so同SHA，WFC YAML仅原确定性路径映射77ea。
- 原last路径仍/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc/20261031_183554/last.pth，SHA6480e3c15f70fbbd9bad8a4b50f51364036da9866372c204cebcdef287d50aeb，fresh CPU全状态核真；暂停时半轮/RNG轨迹未保存，不称精确batch恢复。
- grant pipeline/authorizations/m226_resume_gpu0_20261104.json，human_request原文仅“启动”并附前条GPU0授权/root选择WFC上下文；原paused_run/旧日志和11-01停止证据保留。新日志{task['log']}。
- NEC/MIC仍validation/native/resources NOT_RUN；原草案root/父runtime元数据不可冒充当前工作目录，未来真实空卡前不做CUDA。原其他154候选及队列保持；其他服务器禁用和Windows项目调度Disabled不变。

'''+memory[z:]
        a=memory.index('## Last Tick'); memory=memory[:a]+f'''## Last Tick
- 2026-11-04用户明确“启动”，本次manual_ops/20261104_wfc_gpu0_start持canonical项目锁完成全状态恢复，未创建研究租约或改旧tick。真实owner01a159c5-29ab-7a22-ba7f-e79174757253与target一致。
- 原source9/train/dataset/TRAIN annotation/pretrain/checkpoint SHA及CPU model/optimizer/scheduler通过；只新建原94独立工作目录、WFC原YAML映射和同SHA ignored扩展，旧4457目录不动。新root精确源通过canonical完整verify_git；不伪造task.code_commit或绕过HEAD检查。
- 初次卡被PID597420占3300MiB，只入队未Popen；卡释放后一次wrapper在原生命令执行前line9拒绝瞬时context，canonical保守记claiming。known_prelaunch_reconciliation证实native命令未执行、WFC无进程/无日志且三次空卡，才恢复waiting；不是盲重试未知训练。
- 随后唯一真正Popen成功，三flocks持至canonical启动返回、UUID/空闲/检查点即时再核；canonical及额外原PID/start/argv/cwd/stdout/UUID两次native步数{observed['from_step']['step']}→{observed['to_step']['step']}实证epoch26/best/noimp恢复。0冷启动/0模型修订/0额外科学准入/0信号/GPU1计算。
- 下一轮监控同一WFC原生进度与完整日志；不得因旧资源等待或旧人工暂停文字又恢复/重启一次。LFT/M206与其他154候选、旧holds/bans/revision预算保持。证据见native_resume_progress.json和operation_summary.json。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        temp=P/'codex_memory.wfc_running.tmp'; temp.write_text(memory,encoding='utf-8',newline='\n'); os.replace(temp,P/'codex_memory.md')
        report=f'''# WFC 已在 server4 GPU0 全状态续训

## 结论
用户“启动”已落实。WFC PID{task['pid']}在GPU0真实运行，从完整checkpoint25恢复到第26轮，额外原生步数{observed['from_step']['step']}→{observed['to_step']['step']}，LFT/M206继续暂停，GPU1禁用。

## 实验进度
原best_miou .49711745977401733/no-improve5及模型、优化器、调度器恢复，仍是原实验部分结果，不改冠军或协议。暂停当轮和RNG轨迹未完整保存，不承诺逐batch精确恢复。

## 执行
原94独立git worktree满足canonical精确源契约，旧4457目录保持。原source9、train/dataset/annotation/pretrain/checkpoint逐SHA及CPU全状态核验；YAML只原路径映射，ignored pointgroup扩展原SHA。

## 验证
原admission与新human原文“启动”上下文授权、canonical resume.validate/verify_source/safe_launch/verify_progress通过。额外同PID/start/argv/cwd/stdout/physicalUUID及第26轮两个增长采样通过，用户28files/status/index和其他154候选及非目标账保持。

## 启动前拦截
外部GPU0占用时初次dispatch未启动。随后wrapper在native命令前拒绝瞬时context，未产生WFC日志或进程；有可复核的known-prelaunch证据和三次空卡后，唯一真正Popen成功。没有驱逐、重复训练或未知启动盲重放。

## 下一步
监控同一WFC续训的原生验证/早停结果，GPU0仅1任务。LFT/M206保持暂停，GPU1继续禁用；后续候选需遵守当时实际runtime/源/预算和空槽。
'''
        (OUT/'manual_report.md').write_text(report,encoding='utf-8',newline='\n')
        logged=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','manual',
            '用户要求GPU0启动实验','WFC从完整第25轮检查点续训，第26轮步数已增长','原文启动及前条GPU0单卡授权；保原94版本和协议，LFT/M206/GPU1继续暂停',
            'pipeline/manual_ops/20261104_wfc_gpu0_start/native_resume_progress.json'],text=True,encoding='utf-8',capture_output=True,timeout=20)
        save(OUT/'manual_decision_log.json',dict(returncode=logged.returncode,stdout=logged.stdout,stderr=logged.stderr)); assert logged.returncode==0
        summary=dict(recorded_at=now(),status='WFC_FULL_RESUME_RUNNING_VERIFIED',experiment_id=ID,pid=task['pid'],starttime=observed['starttime'],physical_gpu=0,
            epoch=26,from_step=observed['from_step'],to_step=observed['to_step'],code_commit=task['code_commit'],remote_code_root=NEW_ROOT,
            training_started=True,launch_verified=True,original_runtime_untouched=True,only_one_actual_training_Popen=True,
            prior_known_prelaunch_failure_reconciled=True,GPU1_used=False,LFT_and_M206_pauses_preserved=True,other154_candidates_unchanged=True,
            user28_status_index_and_source18_protected=True,non_target_lifecycle_preserved=True,
            authorization=task['resume_authorization'],checkpoint_evidence=task['resume_checkpoint_evidence'],native_progress=ref(OUT/'native_resume_progress.json'),
            dispatch=ref(OUT/'reconciled_dispatch_result.json'),manual_report=ref(OUT/'manual_report.md'),memory=ref(P/'codex_memory.md'))
        save(OUT/'operation_summary.json',summary); print(json.dumps(summary,ensure_ascii=False))
    finally: lock.close()
if __name__=='__main__': main()
