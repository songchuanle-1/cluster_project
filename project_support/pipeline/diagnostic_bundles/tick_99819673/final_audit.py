"""Freeze the tested reviewable bundle without committing or launching training."""
import ast
import json
from pathlib import Path
import statistics
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr'


def main():
    c.guard(1200)
    native=c.tick.load(OUT/'validation_r2_controls_candidate_result.json')
    matched=c.tick.load(OUT/'r2_matched_controls_candidate_result.json')
    parent=c.tick.load(OUT/'validation_h2_resources_champion_result.json')
    resource=c.tick.load(OUT/'validation_r2_resources_candidate_result.json')
    assert all(x['execution_completed'] for x in (native,matched,parent,resource))
    assert native['all_full_source_controls_passed'] and native['maximum_full_source_control_error']==0
    assert native['all_observed_gradients_finite']
    assert all(x['input_finite'] and x['output_finite'] and x['input_abs_max']>0 and x['output_abs_max']>0 for x in native['transport_path_gradients'])
    rows=[x for batch in matched['batches'] for x in batch['readouts']]
    ops=[x for batch in matched['batches'] for x in batch['operator']]
    assert max(v for batch in matched['batches'] for v in batch['controls'].values())==0
    assert max(x['weighted_fine_mean_error'] for x in ops)<=1e-6
    assert max(x['strict_equal_mass_conjugacy_error'] for x in ops)<=1e-6
    assert parent['input_sha256']==resource['input_sha256'] and parent['profile']['profiler_file_sha256']==resource['profile']['profiler_file_sha256']
    assert resource['profile']['within10G'] and parent['parameters']==resource['parameters']
    package=ROOT/'Cluster/framework/model/Quard_model'/NAME
    config=ROOT/'Cluster/configs/Quard/ctf_hcg_csort_rstr'/(NAME+'.yaml')
    tested=c.tick.load(OUT/'validation_r2/native_manifest.json')['candidate_source_hashes']
    files=sorted(package.glob('*.py'));assert len(files)==8
    cross=[]
    for path in files:
        assert c.tick.digest(path)==tested[path.name]==c.tick.digest(OUT/'source_r2'/path.name)
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            modules=[node.module or ''] if isinstance(node,ast.ImportFrom) else [a.name for a in node.names] if isinstance(node,ast.Import) else []
            cross.extend(x for x in modules if 'model_base1' in x or 'Quard_model.' in x)
    assert not cross
    assert config.read_bytes()==(OUT/'source_r2/candidate.yaml').read_bytes()
    scenes=[]
    for name in sorted({x['scene_id'] for x in rows}):
        values=[x for x in rows if x['scene_id']==name]
        scenes.append({'scene_id':name,'arms':{arm:{key:statistics.mean(x['arms'][arm][key] for x in values) for key in ('all_mae_delta','foreground_mae_delta','other_mae_delta')} for arm in ('content','wrong_cycle','wrong_equal_mass')}})
    n_worse=sum(x['arms']['content']['foreground_mae_delta']>0 for x in scenes)
    n_better=sum(x['arms']['content']['foreground_mae_delta']<x['arms']['wrong_equal_mass']['foreground_mae_delta'] for x in scenes)
    relevant=[OUT/'preregistration.json',OUT/'matched_control_preregistration.json',OUT/'native_transport_result.json',
        OUT/'validation_h2_controls_candidate_result.json',OUT/'revision1_preregistration.json',OUT/'validation_r1_controls_candidate_result.json',
        OUT/'revision2_preregistration.json',OUT/'validation_r2_controls_candidate_result.json',OUT/'r2_matched_retest_preregistration.json',
        OUT/'r2_matched_controls_candidate_result.json',OUT/'validation_h2_resources_champion_result.json',OUT/'validation_r2_resources_candidate_result.json',
        OUT/'final_diagnostic_release.json',OUT/'original_baseline_resource_assets_probe.json']
    summary=c.save('final_technical_review.json',{'observed_at':c.now(),'candidate_id':c.CID,'revision':2,
        'scenes':scenes,'denominators':{'scenes':8,'expressions':32,'support_expression_pairs':sum(x['supports'] for x in rows),
            'target_support_pairs':sum(x['target_supports'] for x in rows),'multi_fine_leaf_targets':sum(x['target_fine_leaves']>1 for x in rows),
            'strict_control_moved_support_pairs':sum(x['strict_moved_superpoint_rows'] for x in ops)},
        'technical':{'full_source_max_error':0,'native_gradient_tensors':native['gradient_tensor_count'],
            'new_path_finite_nonzero':True,'matched_native_identity':0,
            'weighted_fine_mean_error_max':max(x['weighted_fine_mean_error'] for x in ops),
            'strict_conjugacy_error_max':max(x['strict_equal_mass_conjugacy_error'] for x in ops),
            'content_vs_strict_mask_min':min(x['content_vs_wrong_equal_mass_mask_max_abs'] for x in rows),
            'independence_ast_and_hash':True,'config_bytes_unchanged_from_M95':True,
            'scope':'Actual hierarchy feature pooling + complete active encoder under transported FIXED FPS memberships; not upstream full-backbone/FPS renumbering equivariance.'},
        'task_risk':{'foreground_worse_than_no_transport_scenes':n_worse,'foreground_better_than_strict_mismatch_scenes':n_better,
            'foreground_worse_expressions':sum(x['arms']['content']['foreground_mae_delta']>0 for x in rows),
            'reference':'Same R2 canonical ordering/CSR no-transport native fixed query, not exact historical-M95-source replay.',
            'interpretation':'Mass-preserving stochastic convex mixing contracts weighted variance (measured native sum7574.9363→5549.7301,26.73% reduction). Smoothing can remove target detail. This explains an expected mechanism risk, not a proven causal explanation of every adverse mask change. Retain all negatives; no trained benefit or efficacy PASS.'},
        'resources':{'same_input_and_historical_profiler':True,'parameters':resource['parameters'],'added_parameters':0,
            'parent_median_ms':parent['median_ms'],'candidate_median_ms':resource['median_ms'],'median_ratio':resource['median_ms']/parent['median_ms'],
            'parent_p90_ms':parent['p90_ms'],'candidate_p90_ms':resource['p90_ms'],'standard_flops_g':resource['profile']['flops_g'],
            'parent_standard_flops_g':parent['profile']['flops_g'],'incremental_counted_flops':resource['profile']['flops']-parent['profile']['flops'],
            'peak_allocated_bytes_each':resource['peak_allocated_bytes'],'peak_reserved_bytes_each':resource['peak_reserved_bytes'],
            'memory_ratio':resource['peak_allocated_bytes']/parent['peak_allocated_bytes'],'within_default10G':True,
            'limits':'Same-standard counted ops omit existing/additional unsupported primitives. Latency+25.279%, not free compute or final Pareto success. Full optimizer peak and original no-cluster baseline resource delta UNKNOWN; historical configs/model_base1.yaml absent locally/target/history search, so no substitute config fabricated.'},
        'constraints_review':{'phase1_smell':'New cross-sibling source/value paths, not only distribution scaling; 8heads/d32 inherited, no hyperparameter search.0newparameters but nontrivial new information graph.',
            'historical_scope':'Not M39 full-scale projected attention, PCE physical contacts, FLE same-leaf points, CPA point-coarse routing or HDS supports. Original route failures preserved.',
            'bans':'No new learned gate/residual branch/largeQKV, explicit query or language routing, N²point attention, repeated injection, extra seed/dataset/schedule/tuning. Canonical ordering is actual candidate numerical repair, not a validator exemption.',
            'novelty':'MH and stochastic attention established; overall contribution UNKNOWN, not claimed.',
            'implementation_revisions':'R1failed; R2passed affected tested technical controls. Default2consumed, no extra repair authorization.'},
        'evidence':[c.evidence(x) for x in relevant], 'scientific_admission':False,'trained_efficacy':'UNKNOWN',
        'commit_authorized':False,'queue_added':False,'new_training':0,'optimizer_steps':0})
    manifest=c.save('tested_commit_bundle.json',{'prepared_at':c.now(),'candidate_id':c.CID,'revision':2,
        'requested_operation':'local_git_commit_only','repository':str(ROOT/'Cluster'),
        'files':[{'absolute_path':str(x.resolve()),'repository_path':x.relative_to(ROOT/'Cluster').as_posix(),'sha256':c.tick.digest(x)} for x in files+[config]],
        'tested_source_manifest':c.evidence(OUT/'validation_r2/native_manifest.json'),'technical_review':c.evidence(summary),
        'authorized':False,'existing_authorizations':'Only resource grants and old scoped CPA/HDS operations found; no RSTR or project-wide commit grant.',
        'rule':'closure.md313–317: Do not stage or commit without user permission covering that operation and file scope. A request to continue design is not code-commit consent.'})
    reviewable=OUT/'tested_bundle.md'
    text='# RSTR：已测代码与试验设计\n\n'
    text+='最终R2只准备一个结构候选。同parent细叶按固定质量可逆传输，真实写入inst_feats；没有训练结果。\n\n'
    text+='完整源图数值控制最大0；实际native loss反向642个梯度有限，新传输输入/输出非零。8场景32表达matched identity0，content-vs-strict均非零；前景较无传输7/8场景变差、较strict错配6/8更好。技术可执行不等于任务有效。\n\n'
    text+=f'同口径median {parent["median_ms"]:.3f}→{resource["median_ms"]:.3f}ms（+25.28%）；P90 {parent["p90_ms"]:.3f}→{resource["p90_ms"]:.3f}ms；计数9.762532428→9.763134540G，推理峰值均936763392bytes，参数不增加。完整optimizer峰值、无cluster baseline资源差和整体新颖性未知。\n\n'
    text+='请求范围仅为以下8个独立模型源文件及1份配置的本地Git提交。尚未获得该操作授权。\n\n| 文件 | SHA256 |\n|---|---|\n'
    for path in files+[config]:text+=f'| [{path.name}](<{path.resolve().as_posix()}>) | `{c.tick.digest(path)}` |\n'
    text+='\n原始R0/R1失败、运行时/对照脚本失败及源快照均保留。训练需完整准入收据和既有安全同步/dispatcher链；此清单不授予push或训练例外。\n'
    with reviewable.open('x',encoding='utf-8') as stream:stream.write(text)
    old=ROOT/'pipeline/designs/exp_design_20261020-2359_rstr.md'
    latest=ROOT/'pipeline/designs/exp_design_20261021-0015_rstr_tested.md'
    text=f'# 最终已测版本R2（更新于{c.now()}）\n\n以下原始设计保留历史DRAFT/未完成清单，最终当前状态以末尾§8–9及[已测bundle](<{reviewable.resolve().as_posix()}>)为准。\n\n'+old.read_text(encoding='utf-8')
    text+='\n## 8. Smell Check\n\n参数增量0但并非无新图：同parent细叶之间新增值与内容关联路径；固定π可逆矩阵改变来源依赖，不是仅scaling/norm。原8heads/d32/seed1999/50/70不扫参。新增代码没有learned gate/大QKV/新残差模块，M39等历史whole-mechanism差异与public prior已说明。R1/R2只修实际源图数值顺序，不作为新实验或新贡献。三项结构/可解释固定值/因果假设要求满足；任务益处仍未训练验证。\n'
    text+='\n## 9. 最终实现及剩余边界\n\n独立8源文件+1配置、AST/hash、实际native backward、固定FPS membership下完整pooling+active encoder控制、最终R2的8scene匹配对照及同口径M95资源比较已完成。数值最大0，梯度642有限且传输输入/输出非零；严格对照与weightedmean仍低于原1e-6。R0/R1失败不可删除；R2为最后默认修订。\n\n'
    text+='7/8场景前景较匹配无传输参考变差、6/8较严格错配更好；latency+25.28%，不称有效或轻量Pareto胜出。先前§4训练后评估/子组material-harm规则冻结不变；不额外seed/超参选择，不把tinycohort当训练收益。完整optimizer峰值/无cluster基线资源配置/噪声底/全局新颖性尚未知。\n\n'
    text+=f'完整技术证据：`{summary.relative_to(ROOT).as_posix()}`。可审阅的提交范围：`{manifest.relative_to(ROOT).as_posix()}`。目前未commit/push/production部署/入队/训练，scientific_admission=false。下一步只在具体本地提交授权后继续原准入链，不要求重新授予已有GPU资源权限。\n'
    with latest.open('x',encoding='utf-8') as stream:stream.write(text)
    c.advance([summary,manifest,reviewable,latest,Path(__file__)], 'Await exact local commit authorization for the tested8source+1config RSTR bundle. Preserve all technical/adverse evidence; no stage/commit/push/admission/training from a design request alone.')
    work=c.tick.load(ROOT/'pipeline/research_work.json');candidate=next(x for x in work['candidates'] if x['id']==c.CID)
    results=[c.evidence(OUT/x) for x in ('validation_r2_controls_candidate_result.json','validation_r2_resources_candidate_result.json','r2_matched_controls_candidate_result.json')]
    revision=candidate['revision_history'][-1];assert revision['revision']==2 and revision['result']=='pending'
    revision.update(result='passed',result_evidence=results);revision['evidence']+=results
    candidate['design']=c.evidence(latest);candidate['tested_bundle']=c.evidence(manifest)
    candidate['technical_review']=c.evidence(summary);candidate['scientific_admission']=False
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'reviewable':str(reviewable),'design':str(latest),'files':9,'current_source_r2_verified':True,'scientific_admission':False},ensure_ascii=False))


if __name__=='__main__':main()
