import copy
import os
from pathlib import Path
import shlex
import subprocess
from pause_both import ROOT,P,OUT,SKILL,THREAD,REQUEST,now,load,sha,evidence,save,guard,pm

def main():
    guard(); lock=pm.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard(); stopped=load(OUT/'stop_confirmation.json')['data']
        params=dict(targets=stopped['targets'],original_member_pids=[r['pid'] for r in stopped['exact_members']])
        payload='PARAMS='+repr(params)+'\n'+(OUT/'checkpoint_after_stop.py').read_text(encoding='utf-8')
        command=shlex.join(['bash','-lc','source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B -'])
        cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115',command],
            input=payload,text=True,encoding='utf-8',capture_output=True,timeout=120)
        record=dict(observed_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr)
        if cp.returncode==0: record['data']=__import__('json').loads(cp.stdout)
        if (OUT/'checkpoint_confirmation.json').exists():
            assert load(OUT/'checkpoint_confirmation.json')['returncode']!=0
            (OUT/'checkpoint_confirmation.json').rename(OUT/'checkpoint_confirmation_attempt1_failed.json')
        save(OUT/'checkpoint_confirmation.json',record)
        assert cp.returncode==0,cp.stderr[-2000:]
        info=record['data']; q=load(P/'queue.json'); work=load(P/'research_work.json')
        for row in info['checkpoints']:
            task=next(t for t in q['gpu_queues']['server-4'] if t['id']==row['id'])
            checkpoint=row['last_complete_checkpoint']; task['paused_run'].update(checkpoint_full_state_validation='CPU_VALIDATED_SAVED_COMPLETE_EPOCH',
                checkpoint=checkpoint['path'],checkpoint_meta=checkpoint['meta'],checkpoint_evidence=evidence(OUT/'checkpoint_confirmation.json'))
            task.update(resume_from=checkpoint['path'],resume_checkpoint_evidence=evidence(OUT/'checkpoint_confirmation.json'))
            ep=P/'experiments'/f"{row['id']}.json"; exp=load(ep)
            exp.update(paused_run=copy.deepcopy(task['paused_run']),resume_from=task['resume_from'],resume_checkpoint_evidence=task['resume_checkpoint_evidence']); save(ep,exp)
            candidate=next(c for c in work['candidates'] if c.get('experiment_id')==row['id'])
            candidate.update(paused_run=copy.deepcopy(task['paused_run']))
            candidate['evidence'].append(evidence(OUT/'checkpoint_confirmation.json'))
        save(P/'queue.json',q); save(P/'research_work.json',work)
        memory=(OUT/'before_pipeline__codex_memory.md').read_text(encoding='utf-8')
        memory=memory.replace('## Goal And Phase\n','## Goal And Phase\n- 最新直接用户指令“先暂停这两个实验 停止使用”（2026-11-01）：WFC/LFT均人工暂停，server4 allowed_gpus=[]/dispatch_enabled=false；GPU0/1停止使用，后续显式授权前禁止自动恢复、替补训练、GPU诊断或迁移。历史双卡授权已被本次暂停覆盖。\n',1)
        memory=memory.replace('- 只用server4物理0/1各1任务；goal0441/SERVERS19b3/closure2993/standing2e89/GPU1grant6529保持，其他服务器新dispatch禁用，Pipeline-cluster_project仍Disabled。',
            '- 目前无GPU使用授权：server4两卡停止使用，其他服务器新dispatch仍禁用；goal0441/closure2993及历史科学协议不变，旧SERVERS19b3和GPU1grant6529仅为历史，Pipeline-cluster_project仍Disabled。')
        a=memory.index('## Running And Queue'); b=memory.index('## Open Questions And Risks',a)
        checkpoint_lines=[]
        for row in info['checkpoints']:
            meta=row['last_complete_checkpoint']['meta']
            checkpoint_lines.append(f"- {row['id']}：原日志及last/best保留，last CPU完整model/optimizer/scheduler核验通过，meta epoch={meta['epoch']}、best_miou={meta['best_miou']}；当前半轮未另存。")
        section='## Running And Queue\n- 最新手动操作20261101_dual_user_pause：WFC PID2085005/start105948793及LFT PID2685912/start106767833与12个同身份worker已通过pidfd SIGTERM停止，无SIGKILL；CUDA contexts已清空，两卡不再给本项目派发。\n- queue/experiment为waiting + paused_by_user/user_paused，保留paused_run，清当前PID/running映射；resume_authorized=false且dispatch_hold生效。M206原暂停及其他153候选保持。\n'+'\n'.join(checkpoint_lines)+'\n- NEC/MIC仍validation，native/resources NOT_RUN，未入队；不能作为替补启动。两运行历史source9/receipt/launch证据保留，不记作模型失败或完成，不改冠军。\n\n'
        memory=memory[:a]+section+memory[b:]
        a=memory.index('## Last Tick')
        memory=memory[:a]+'## Last Tick\n- 最近研究tick25fc0b57已FINALIZED/PASS/released；本次是后续直接人工暂停操作，未创建研究tick/租约、不改调度、不启动新实验。\n- 所属thread核对一致，canonical project monitor锁内先落禁用资源和dispatch_hold，再核hostname/dl04、原PID/start/UID/cwd/argv/stdout/source9/物理UUID，向14个精确原进程发SIGTERM，确认全退出及CUDA contexts清空。\n- 停止后只用CPU检查完整已保存last与SHA、保留best及日志；不声称保存暂停瞬间半轮，后续恢复需显式用户指令与当时源码/检查点/资源再核。\n- 原证据及停止/检查点回执：pipeline/manual_ops/20261101_dual_user_pause；SERVERS只改server4 allowed[]/dispatchfalse，GPU0/1停止使用。\n'
        tmp=P/'codex_memory.manual_pause.tmp'; tmp.write_text(memory,encoding='utf-8',newline='\n'); os.replace(tmp,P/'codex_memory.md')
        report='''# 用户暂停 WFC/LFT 并停止两卡使用\n\n## 结论\n直接用户要求已执行：两个原训练与其已核身份worker停止，CUDA contexts清空；两卡后续派发禁用。\n\n## 实验进展\n这是操作暂停，不是科学终态；原协议、源码、冠军和已有部分验证保持。\n\n## 本轮执行\n核对真实thread、持项目锁，先落server4 allowed_gpus=[]和dispatch_enabled=false及两task hold；hostname/PID/start/UID/cwd/argv/stdout/source/UUID核验后精确pidfd SIGTERM，无SIGKILL。\n\n## 结果证据\nstop_confirmation.json记录14个原进程退出及context释放；checkpoint_confirmation.json记录CPU完整last和last/best SHA及原日志存在。\n\n## 限制与风险\n训练入口无SIGTERM临时保存handler，当前半轮未保存；可用完整保存轮见检查点meta。暂停不证明机制有效或失败。\n\n## 下一步\n等待显式恢复/资源授权，不自动恢复WFC/LFT/M206，不启动NEC/MIC替补，不运行GPU诊断，不变更调度。\n'''
        (OUT/'manual_report.md').write_text(report,encoding='utf-8',newline='\n')
        bash='C:/Program Files (x86)/Git/bin/bash.exe'
        logged=subprocess.run([bash,str(SKILL/'log_decision.sh'),'cluster_project','manual','用户要求暂停WFC/LFT并停止两卡使用',
            '已精确停止两个原任务；禁用server4双卡派发，保留保存点，等待显式恢复',REQUEST,
            'pipeline/manual_ops/20261101_dual_user_pause/stop_confirmation.json ; checkpoint_confirmation.json'],text=True,encoding='utf-8',capture_output=True,timeout=20)
        save(OUT/'manual_decision_log_result.json',dict(returncode=logged.returncode,stdout=logged.stdout,stderr=logged.stderr)); assert logged.returncode==0
        print(__import__('json').dumps(dict(checkpoint_summary=[dict(id=r['id'],meta=r['last_complete_checkpoint']['meta']) for r in info['checkpoints']],
            contexts=info['contexts'],gpus=info['gpus'],manual_decision_logged=True,memory_saved=True),ensure_ascii=False))
    finally: lock.close()
if __name__=='__main__': main()
