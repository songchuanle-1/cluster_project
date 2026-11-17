"""Persist truthful canonical queue result and the current exclusive-resource wait."""
import copy,json,os,subprocess
from pathlib import Path
import yaml
from prepare_and_queue import ROOT,P,OUT,THREAD,NEW_ROOT,OLD_ROOT,ID,now,load,save,sha,ref,guard,mon,strict_ssh

def main():
    guard(); lock=mon.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard(); q=load(P/'queue.json'); task=next(t for t in q['gpu_queues']['server-4'] if t['id']==ID)
        assert task['status']=='waiting' and task['training_status']=='waiting_resume' and task['resume_authorized'] is True
        assert not task.get('dispatch_hold') and not task.get('pid')
        payload=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
from datetime import datetime,timezone
import json,subprocess
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),gpu0=gpu,contexts_gpu0=contexts,
    GPU1='NOT_QUERIED_NOT_AUTHORIZED',read_only=True,signals_sent=False)))
'''
        cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input=payload,text=True,encoding='utf-8',capture_output=True,timeout=35)
        probe=dict(recorded_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr)
        if cp.returncode==0: probe['data']=json.loads(cp.stdout)
        save(OUT/'final_gpu0_observation.json',probe); assert cp.returncode==0,cp.stderr[-1000:]
        observed=probe['data']; occupied=bool(observed['contexts_gpu0']); assert occupied,'Resource changed; reconcile dispatch before finalizing'
        work=load(P/'research_work.json'); c=next(c for c in work['candidates'] if c.get('experiment_id')==ID)
        c.update(blocker_kind='exclusive_gpu_slot',blocker='Actual physicalGPU0 has a foreign/unregistered CUDA context; canonical dispatch found no exclusive free slot. No training process was started.',
            unblock_condition='Fresh server4 physicalGPU0 UUID/idleness/exclusive ownership validation; then original native full-state --resume on original94 checkout with checkpoint SHA recheck.',
            next_action='WFC is explicitly authorized and queued for full resume from checkpoint25, native epoch26, on GPU0. Automatically dispatch once truly free using canonical resume path; no new permission required. Preserve other CUDA process, LFT/M206 holds and GPU1 ban. No cold start or blind replay.')
        c['evidence'].append(ref(OUT/'final_gpu0_observation.json')); work.update(updated_at=now(),next_action=c['next_action']); save(P/'research_work.json',work)
        before=load(OUT/'before_pipeline__research_work.json')
        assert {c['id']:c for c in before['candidates'] if c.get('experiment_id')!=ID}=={c['id']:c for c in work['candidates'] if c.get('experiment_id')!=ID}
        oldq=load(OUT/'before_pipeline__queue.json'); assert [t for t in oldq['gpu_queues']['server-4'] if t['id']!=ID]==[t for t in q['gpu_queues']['server-4'] if t['id']!=ID]
        assert load(P/'running.json')==load(OUT/'before_pipeline__running.json')
        s=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8')); previous=yaml.safe_load((OUT/'before_SERVERS.yaml').read_text(encoding='utf-8'))
        previous['servers']['server-4']['remote_code_root']=NEW_ROOT; assert s==previous
        cpdata=load(OUT/'runtime_preparation_and_checkpoint.json')['data']; assert cpdata['cpu_inspection']['meta']['epoch']==25
        memory=(OUT/'before_pipeline__codex_memory.md').read_text(encoding='utf-8'); lines=memory.splitlines()
        lines=[('- 最新直接用户先授权“可使用一张卡server4-gpu0”，随后明确“启动”（2026-11-04）。已选择原GPU0 WFC完整续训并入队；当前资源仅GPU0/[0]/dispatchtrue/max1，GPU1禁用，LFT/M206暂停保持。WFC不再需要重复人工恢复授权。' if x.startswith('- 最新直接用户指令') else x) for x in lines]
        memory='\n'.join(lines)+'\n'; a=memory.index('## Running And Queue'); b=memory.index('## Open Questions And Risks',a)
        memory=memory[:a]+'''## Running And Queue
- WFC M226：用户“启动”已解除其单独人工hold，statuswaiting/training_statuswaiting_resume、resume_authorizedtrue、无dispatch_hold/无PID；同ID/source94/原receipt保持，绝非冷启动。LFT和M206仍user_paused/resumefalse。
- 原root4457目录完整保留；为满足canonical精确HEAD94，创建独立git worktree /data/songcl/Project/Cluster_project/Cluster_resume_wfc_20261104，SERVERS.server4.remote_code_root已指该目录。本地主线HEAD4457和原用户文件不动。只复制原ignored pointgroup扩展同SHA，WFC YAML仅原确定性映射77ea。
- 固定WFC last仍原绝对路径 /data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc/20261031_183554/last.pth，SHA6480e3c15f70fbbd9bad8a4b50f51364036da9866372c204cebcdef287d50aeb；fresh CPU完整model/optimizer/scheduler核真，meta25/best0.49711745977401733/noimp5，原生将从26轮继续，半轮和RNG轨迹未精确保存。
- 最新GPU0有外部/未登记PID597420占3300MiB（本账户cwd不可读），canonical queue已尝试派发但无空槽，没有Popen/训练。等待该卡真实空闲，不能驱逐/overlay或改GPU1。新grant pipeline/authorizations/m226_resume_gpu0_20261104.json，CPU/源码/dispatch证据在manual_ops/20261104_wfc_gpu0_start。
- NEC/MIC仍validation/native/resources NOT_RUN，原冻结草案根目录/父版本不能当当前runtime重放，须将来真实空卡后适配新runtime和fresh owner/source/resource元数据。其他154候选与队列保持。

'''+memory[b:]
        a=memory.index('## Last Tick'); memory=memory[:a]+'''## Last Tick
- 2026-11-04用户明确“启动”，本次是manual操作，不创建研究租约、不改原tick或调度。实际root thread与target相同，canonical项目锁内准备并排队原WFC全状态续训；仅GPU0。
- hostname先核dl04/.115；固定原last重新SHA/CPU核完整状态、原source9/train/dataset/TRAIN annotation/pretrain及仅原YAML映射均通过。新独立94工作目录保精确commit，旧4457源/status未改变；没有sync/checkout旧root/重新设计模型/篡改旧收据。
- 新sourcehuman恢复授权原文仅“启动”，同时引用前条GPU0指令和root选择WFC上下文，不伪造用户精确说过WFC。cluster_resume.validate/verify_source及closure.admission通过，canonical _process_queue一次实际派发尝试，无空槽所以statuswaiting、launchfalse/无PID/无running映射，未训练。
- 最终GPU0外部context仍占3300MiB，证据final_gpu0_observation.json；未来空闲后可canonical自动续训WFC，无需再问。LFT/M206所有字段与其他154候选保持，GPU1禁用，Windows项目调度Disabled和heartbeat时序保持。
'''
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        temp=P/'codex_memory.wfc_queue.tmp'; temp.write_text(memory,encoding='utf-8',newline='\n'); os.replace(temp,P/'codex_memory.md')
        report='''# WFC GPU0 原版本完整状态续训已入队

## 结论
直接用户“启动”已执行为WFC完整状态恢复准备和准入队列派发；GPU0当前被其他CUDA进程占用，训练尚未开始。

## 进度
第25轮完整last SHA6480e3c1…、model/optimizer/scheduler与best/no-improve已fresh CPU核验，原生恢复起点为第26轮；当前部分轮和RNG轨迹未精确保存。

## 执行
旧4457运行目录保留，独立worktree取原94。只对WFC YAML做既有确定性路径映射，复制原编译扩展并比对SHA。原source9、train/dataset/annotation/pretrain逐SHA核真；新授权精确绑定原ID/config/source/checkpoint与新目录。

## 验证
canonical admission、cluster_resume.validate和完整verify_source通过，canonical _process_queue已实际尝试，因GPU0占用未发起Popen。未修改其他实验和候选，没有驱逐或使用GPU1。

## 限制
GPU0另有PID597420/3300MiB，进程cwd因权限不可读。不能把waiting写成running；空闲观察也不等于独占许可，启动前仍须当前UUID/空闲/三锁/源与检查点复核。

## 下一步
WFC已获本次启动授权且无人工hold，待GPU0真正空闲时由canonical正常派发，核原生epoch26和步数增长。LFT/M206保持暂停，GPU1禁用。
'''
        (OUT/'manual_report.md').write_text(report,encoding='utf-8',newline='\n')
        logged=subprocess.run(['C:/Program Files (x86)/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','manual',
            '用户要求在GPU0启动实验','WFC原版本完整续训已入队，GPU0被其他任务占用暂未启动','原文启动及前条GPU0单卡授权；原checkpoint25已核，禁止驱逐和GPU1使用',
            'pipeline/manual_ops/20261104_wfc_gpu0_start'],text=True,encoding='utf-8',capture_output=True,timeout=20)
        save(OUT/'manual_decision_log.json',dict(returncode=logged.returncode,stdout=logged.stdout,stderr=logged.stderr)); assert logged.returncode==0
        summary=dict(recorded_at=now(),status='AUTHORIZED_FULL_RESUME_QUEUED_WAITING_GPU0',experiment_id=ID,training_started=False,launch_verified=False,
            expected_start_epoch=26,saved_checkpoint_epoch=25,remaining_foreign_context=observed['contexts_gpu0'],physical_gpu=0,gpu1_used=False,
            original_source_commit=cpdata['code_commit'],remote_code_root=NEW_ROOT,old_runtime_untouched=True,source_and_checkpoint_validation_passed=True,
            no_other_pauses_lifted=True,other154_candidates_unchanged=True,no_duplicate_launch=True,automatic_dispatch_when_exclusively_idle=True,
            canonical_dispatch=ref(OUT/'dispatch_result.json'),resource_observation=ref(OUT/'final_gpu0_observation.json'),manual_report=ref(OUT/'manual_report.md'),memory=ref(P/'codex_memory.md'))
        save(OUT/'operation_summary.json',summary); print(json.dumps(summary,ensure_ascii=False))
    finally: lock.close()
if __name__=='__main__': main()
