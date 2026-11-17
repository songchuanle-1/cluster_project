"""Bind a real checkpoint inspection to a reviewable plan; creates no human grant or queue task."""
import datetime as dt
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[2]
def ref(p):return dict(path=p.relative_to(PROJECT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(name,value):
    p=BASE/name
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    return ref(p)
def main():
    capture=json.loads((BASE/'hap_checkpoint_evidence.json').read_text(encoding='utf-8'))
    ck=capture['data'];assert capture['returncode']==0
    assert ck['cpu_inspection']['meta']['epoch']==18 and ck['cpu_inspection']['cuda_initialized'] is False
    inspection=dict(schema_version=1,purpose='cluster_native_resume',id='M207-HAP',
        config='configs/Quard/ctf_hcg_csort_hap/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap.yaml',
        code_commit='f51823bbddf0f8095a9a5813bf1f8169e3d7edb0',server='server-4',gpu='0',
        remote_code_root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1',
        resume_from=ck['resume_from'],checkpoint_sha256=ck['checkpoint_sha256'],cpu_inspection=ck['cpu_inspection'],
        observed_at=ck['observed_at'],evidence=[ref(BASE/'hap_checkpoint_evidence.json')],
        partial_current_epoch_saved=False)
    proof=save('hap_resume_checkpoint_proof.json',inspection)
    plan=dict(schema_version=1,status='PREPARED_AWAITING_EXPLICIT_HUMAN_RESUME_AUTHORIZATION_AND_FREE_GPU0',
        prepared_at=dt.datetime.now(dt.timezone.utc).isoformat(),**{k:inspection[k] for k in
        ('id','config','code_commit','server','gpu','remote_code_root','resume_from','checkpoint_sha256')},
        checkpoint_proof=proof,saved_meta=inspection['cpu_inspection']['meta'],
        intended_native_argv=['python','tools/train.py',inspection['config'],'--gpu_ids','0','--num_gpus','1','--resume',inspection['resume_from']],
        retained_protocol=dict(seed=1999,epochs=50,max_iters=70,num_workers=4,persistent_workers=True),
        expected_first_resume_epoch=19,model_optimizer_scheduler_and_best_patience_state_preserved=True,
        limitations=['Epoch19 partial minibatch progress was not saved.',
            'The checkpoint has meta/model/optimizer/scheduler, no saved full RNG/loader worker state. Exact interrupted minibatch/RNG trajectory is not guaranteed.',
            'Fresh CPU interop tests passed but do not reproduce the failed native sample or long-lived worker; root cause remains UNKNOWN and another crash remains possible.'],
        source_integrity=ref(BASE/'hap_source_integrity.json'),
        cpu_interop=ref(BASE/'cpu_tensor_numpy_check.json'),
        native_admission=ref(PROJECT/'pipeline/admissions/M207-HAP.json'),
        authorization_contract=dict(path='C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/cluster_resume.py',
            function='validate',required='Explicit human resume authorization required',
            current_hap_resume_grant='MISSING',standing_experiment_first_preserves_resume_restrictions=True),
        before_launch_required=['Human exact HAP resume grant bound to this config/commit/checkpoint/server/GPU.',
            'Revalidate actual exact f518 source, allowed native YAML path mappings, checkpoint SHA, conda/data assets.',
            'Revalidate latest GPU0 authorization/physical UUID and fresh empty compute context plus all exclusive leases; preserve every foreign/unregistered process.',
            'Use canonical full-state native resume with no cold-start or fallback checkpoint; verify increasing native training steps.'],
        exclusions=['GPU1 remains released to others; no diagnostics/training there.',
            'M206 remains user-paused; HAP consent does not authorize M206 resume or migration.',
            'No worker-count/NumPy/source/environment/seed/schedule/hyperparameter changes.'],
        queue_task_created=False,resume_authorization_created=False,training_started=False)
    r=save('hap_resume_plan.json',plan)
    md=BASE/'hap_resume_plan.md'
    md.write_text('# M207-HAP 完整状态恢复方案\n\n'
        '- 当前状态：原运行因 DataLoader 转换异常退出，底因仍未知；恢复尚未授权或启动。\n'
        '- 只使用 server4 physical GPU0，等待真实空卡并复核 UUID、独占租约、环境、数据及源码。GPU1 继续让给别人，M206 保持暂停。\n'
        '- 保持已测 f51823bbddf0f8095a9a5813bf1f8169e3d7edb0 与原 YAML、seed1999、50epochs/maxiters70、4workers 不变。\n'
        '- 使用已冻结且 CPU 校验的 last.pth：meta.epoch18，best_miou0.4975287616252899，no_improve0，模型/优化器642states5groups/调度器均在。下一轮为19。\n'
        '- 不包含第19轮未完成的minibatch进度，也不含完整RNG/loader状态，不能保证原中断点的精确随机轨迹。\n'
        '- 新CPU进程1000次及4个持久worker合成2000样本通过；这不证明原生故障已排除。不得据此改训练参数或宣称机制失败。\n'
        '- 原生恢复入口 cluster_resume.validate 强制本次hash绑定的人工恢复授权；现有实验优先授权保留恢复限制。本方案未创建授权、未入队、未启动。\n\n'
        '固定检查点与校验摘要、完整原生参数见同目录 hap_resume_plan.json。\n',encoding='utf-8')
    print(json.dumps(dict(plan=r,checkpoint_proof=proof,markdown=ref(md)),ensure_ascii=False))
if __name__=='__main__':main()
