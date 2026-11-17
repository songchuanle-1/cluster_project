"""Persist current crash/resume review decision using the canonical helper."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[2]
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import pipeline_monitor as monitor
def ref(p):return dict(path=p.relative_to(PROJECT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
    lock=monitor.acquire_lock(str(PROJECT));assert lock is not None
    try:
        directory=PROJECT/'pipeline/decisions';before=set(directory.glob('*.md'))
        rationale=('HAP原PID消失且精确原日志DataLoader Tensor.numpy AttributeError；已canonical归档crashed，非机制证伪。'
            '原last完整快照CPU校验meta18/best.4975287616252899/noimprove0，模型/优化器642states5groups/调度器保留；'
            'canonical源码f518检查通过，新CPU1000次与4持久worker合成2000样本通过，但不证明原样本/长worker故障修复。'
            'cluster_resume.validate强制source=human本次配置/版本/检查点绑定恢复授权；已在所属会话询问一次，当前PENDING，未制造授权或入队。'
            'server4GPU0最新12:26仍有未登记compute context，不可驱逐；GPU1释放给别人，M206人工暂停状态/队列不动。'
            'HRC/PSBR保持已准备源码/worker/adapter，不因HAP退出认定空卡；只在真正授权空槽做真实native检查。'
            '不改seed1999/50epochs/maxiters70/4workers/禁用项/修订/资源/调度。')
        args=['C:/Program Files (x86)/Git/bin/bash.exe',str(SKILL/'log_decision.sh'),'cluster_project','question',
            'HAP crashed; exact full-state resume?', 'Await HAP GPU0 resume grant and free GPU0',rationale,
            'pipeline/diagnostic_bundles/tick_5c46f46a/hap_terminal_archive.json; hap_resume_plan.json; hap_resume_checkpoint_proof.json; hap_source_integrity.json; cpu_tensor_numpy_check.json; gpu0_slot_final.json']
        r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=25)
        assert r.returncode==0,r.stderr
        created=list(set(directory.glob('*.md'))-before);assert len(created)==1
        decision_ref=ref(created[0])
        work_path=PROJECT/'pipeline/research_work.json'
        work=json.loads(work_path.read_text(encoding='utf-8-sig'))
        new=[ref(BASE/n) for n in ('hap_terminal_archive.json','hap_resume_checkpoint_proof.json','hap_resume_plan.json','hap_resume_plan.md','gpu0_slot_final.json')]+[decision_ref]
        for c in work['candidates']:
            if c.get('experiment_id')=='M207-HAP':
                for x in new:
                    if x not in c['evidence']:c['evidence'].append(x)
                c['pending_human_resume_question']=dict(asked_in_owning_thread=True,status='PENDING',plan=ref(BASE/'hap_resume_plan.json'),decision=decision_ref)
            elif c.get('experiment_id') in ('M208-HRC','M209-PSBR'):
                x=ref(BASE/'gpu0_slot_final.json')
                if x not in c['evidence']:c['evidence'].append(x)
        work['tick_attempt'].update(command='python -B pipeline/diagnostic_bundles/tick_5c46f46a/check_gpu0_slot.py',
            observation='Actual04:26:30UTC/Shanghai12:26:30 pinned physicalGPU0 still has non-HAP/unregistered PID181902 compute context1656MiB. No torch/GPU computation/signals; GPU1 not queried or used. Prepared HRC/PSBR native/resources remain NOT_RUN.',
            evidence=[ref(BASE/'gpu0_slot_final.json')])
        work['updated_at']=dt.datetime.now(dt.timezone.utc).isoformat()
        tmp=work_path.with_name('research_work.tick_5c46f46a.tmp')
        with tmp.open('x',encoding='utf-8') as f:json.dump(work,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,work_path)
        result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=args,returncode=r.returncode,
            stdout=r.stdout,stderr=r.stderr,decision=decision_ref,authorization_created=False)
        target=BASE/'decision_record.json'
        with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print(json.dumps(dict(decision=decision_ref,authorization_status='PENDING',training_started=False),ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
