"""Persist upstream review/design, then create a physically independent source bundle."""
import ast
import json
from pathlib import Path
import statistics
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
NEW=NAME+'_rstr'


def main():
    c.guard(1500)
    result=c.tick.load(OUT/'native_transport_result.json')
    assert result['execution_completed'] and result['primitive']['passed']
    rows=[x for b in result['batches'] for x in b['readouts']]
    ops=[x for b in result['batches'] for x in b['operator']]
    scenes=[]
    for scene in sorted({x['scene_id'] for x in rows}):
        values=[x for x in rows if x['scene_id']==scene]
        scenes.append({'scene_id':scene,'expressions':len(values),
            'arms':{arm:{key:statistics.mean(x['arms'][arm][key] for x in values) for key in ('all_mae_delta','foreground_mae_delta','other_mae_delta')} for arm in ('content','wrong_cycle','wrong_equal_mass')}})
    analysis=c.save('diagnosis_analysis.json',{'observed_at':c.now(),'candidate_id':c.CID,
        'source':c.evidence(OUT/'native_transport_result.json'),'scenes':scenes,
        'denominators':{'scenes':8,'expressions':32,'superpoint_expression_pairs':sum(x['supports'] for x in rows),
            'foreground_pairs':sum(x['target_supports'] for x in rows),'multi_leaf_targets':sum(x['target_fine_leaves']>1 for x in rows),
            'strict_control_moved_superpoint_pairs':sum(x['strict_moved_superpoint_rows'] for x in ops)},
        'numerics':{'identity_max':max(v for b in result['batches'] for v in b['controls'].values()),
            'weighted_fine_mean_error_max':max(x['weighted_fine_mean_error'] for x in ops),
            'strict_conjugacy_error_max':max(x['strict_equal_mass_conjugacy_error'] for x in ops),
            'content_vs_strict_mask_min':min(x['content_vs_wrong_equal_mass_mask_max_abs'] for x in rows)},
        'interpretation':'Direct sibling-source path and content association are active. Content FG worse than native7/8scenes, better than strict mismatch6/8. Activity/conservation is not benefit; investigate intact native gradient and source behavior before admission. Same8TRAINscenes, not population evidence.'})
    goal=c.tick.load(ROOT/'pipeline/goal.json')
    stamp='20261020-2359_rstr'
    review=ROOT/'pipeline/reviews'/('motivation_review_'+stamp+'.md')
    design=ROOT/'pipeline/designs'/('exp_design_'+stamp+'.md')
    review_text=f'''# Motivation Review — cluster_project
Created {c.now()}; candidate `{c.CID}`. 原始目标文件 SHA256 {c.GOAL}。

## 1. Goal
目标 mIoU≥.5100，历史最佳M95=.5020，差.0080；完整冻结目标如下，全部原约束沿用。
```json
{json.dumps(goal,ensure_ascii=False,indent=2)}
```

## 2. Story Status（故事线状态）
| 假设 | 状态 | 证据 | 缺口 |
|---|---|---|---|
| 多尺度context有效 | 既有结果支持 | A1 .5012 vs baseline .4894 | 不证明新注意力有效 |
| 直接细叶间依赖缺失 | 计算图支持 | 原CTF每token FFN后直接gather；祖先mean仍含间接信息 | 不称完全没有邻叶信息 |
| sibling交换改变实际mask | 固定诊断支持 | 本轮32表达正确vs严格错配均非零，identity0 | 完整native backward、资源、重复性尚未测 |
| 新结构提高任务质量 | 未知且有不利旗标 | content前景7/8场景变差；比等质量错配6/8更好 | 训练质量未知，不据小样本宣称收益 |

## 3. Experiment Assessment（已有实验的动机视角评估）
| Experiment | mIoU | 与动机的关系 | 对故事线贡献 |
|---|---|---|---|
| M95 | .5020历史最佳 | 已有CTF/HCG/CSORT基线 | 本轮只用epoch16冻结诊断，不等同最佳checkpoint |
| M39-C2C | .4865历史 | 每尺度全连接投影attention+residual/LN | 不能只重命名token交互；本试验固定同parent图与质量可逆性 |
| HDS/FLE/CPA | 不在本轮重估 | 分别互斥支持/同叶点注意力/point-to-coarse | 保留旧拒绝，不重开 |
| PCE R1/R2/R3 | 未训练 | 物理接触点交换；原数值失败保留 | 本方案不使用接触图，不是PCE额外修订 |

## 4. Gap Analysis（Q1: 故事缺什么）
本轮32580有效超点-表达对中目标常跨细叶；新的task relevant假设是共享祖先池化不能保留“哪个细叶向哪个细叶提供内容”的直接依赖。这里只证明可执行的缺失依赖及对照分离，没有证明池化损失能由此恢复。完整数据分母及全部方向见 `{analysis.relative_to(ROOT).as_posix()}`。已有外部诊断的粗尺度删除/纯bias解释/最终ILA缺失解释不能作本方案效益证据。

## 5. Design Rationale（Q2+Q3: 为什么设计这批变体）
只测试一个固定机制：同一中层parent内的细token质量可逆传输。其信息流不同于M39的全尺度Q/K/V/O+LN，也不同于原mean broadcast。质量约束限制任意全局细叶均值漂移，但不保证后续融合/非线性/logit均值。原生不利前景读出须保留并检验完整源图/损失，不能调温度、gate或挑场景解决。

数学primitive不是贡献：[Hastings1970](https://academic.oup.com/biomet/article-abstract/57/1/97/284580)已有可逆Markov构造；[Sinkformers,AISTATS2022](https://proceedings.mlr.press/v151/sander22a.html)使用Sinkhorn双随机attention。本方案使用不等超点质量的MH而非Sinkhorn，局部树sibling图而非全局全尺度交互；是否有整体论文新颖性仍未完成，不能写首次。

## 6. Next Batch
见 `{design.relative_to(ROOT).as_posix()}`。先完整源图/原生loss反向/同口径资源；没有准入不入队。全部原负面证据与默认修订2次不变。
'''
    with review.open('x',encoding='utf-8') as stream:stream.write(review_text)
    design_text=f'''# Experiment Design — cluster_project
Created {c.now()}; upstream `{review.relative_to(ROOT).as_posix()}`; stableID `{c.CID}`。

## 1. Motivation（为什么设计这批实验）
项目动机（原文）：{goal['description']}

本轮用户明确继续设计试验。23:47Shanghai快照active0/target3，candidate_budget3，pending7/8；只准备本候选，不以空GPU增加假设。已验证的是新依赖可到达mask；收益未验证。

## 2. Current Best Results（基于什么数据做决策）
| Experiment ID | Config | State | Best mIoU | Acc@50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
| model_base1 | 原baseline | 历史记录 | .4894 | 本轮未核对 | 本轮未核对 | 本轮未核对 |
| M95 | ctf_hcg_csort | 历史最佳 | .5020 | 本轮未核对 | 本轮未核对 | 本轮未核对 |
| RSTR诊断 | 冻结M95epoch16 | 完成8TRAINscene/32expr | 未训练 | 不适用 | 不适用 | 0 |

## 3. Analysis & Direction（方向分析）
有效既有轴是context/CTF/HCG；显式routing与大型投影等原ban不变。缺口是direct sibling source dependence；不是已有祖先信息完全缺失。新算子前景7/8变差是风险，content优于strict mismatch6/8仅支持内容关联有作用。没有收益方向选择或超参修正。

令T_i∈R^256为最终CTF FFN后的细token，n_i=bincount(point-to-fine)_i计有效超点行；parent来自cluster_ids_list[1]，零mass/padding排除。用原8heads、d=32。各parent各head：
Q_ij=softmax_j(T_i·T_j/√d)；A_ij=min(π_iQ_ij,π_jQ_ji)，π_i=n_i/Σn；i≠j时P_ij=A_ij/π_i，P_ii=1−Σ_j≠iP_ij；T'_i=Σ_jP_ijT_j。

推导：offdiag P_ij=min(Q_ij,π_jQ_ji/π_i)，所以P_ii≥Q_ii≥0，P1=1。π_iP_ij=π_jP_ji，从而πᵀP=πᵀ，逐head Σn_iT'_i=Σn_iT_i。只替换fine bank；middle/coarse、CSORT rawbank loss、原fusion、query与mask suffix沿用。**不声称融合后或logit均值守恒**。

梯度：离散FPS/ids/n固定；T经value和Q两条可微路径进入P T，min等值处采用框架次梯度；无新增trainable tensor，原CTF FFN须从native loss收到有限非零梯度，另retain transport output/input梯度证明新边参与。单token/常量值为identity；高selfdot可能饱和须测mobility，本轮mean offdiag约.494，非no-op。跨parent新算子Jacobian应0（原祖先间接路径不在此断言范围）。

成本 O(CΣ_g k_g²)，attention内存O(HΣ_g k_g²)；原生每表达Σk²=1168–1494，不能假设均匀4叶。参数增加0，但有新非线性图和跨叶依赖，不是仅归一化/缩放或加小Linear。保留原8heads/seed1999/epochs50/max_iters70，无调参。M39/原文差异见upstream，整体新颖性未完成。

## 4. Experiment Plan（具体做什么）
| # | ID | Config Path | Purpose / Hypothesis | Expected Result | Priority | Depends On |
|---|---|---|---|---|---|---|
| 1 | RSTR | configs/Quard/ctf_hcg_csort_rstr/{NEW}.yaml | 同parent细叶内容传输 | 实际native路径与strict control可分；训练mIoU未知 | P0 | 全科学/资源/提交门槛 |

固定对照：无传输；全组fixed cycle affinity（π和值固定，accepted权重分布可能变化）；等n子集fixed cycle affinity（P_c=RPRᵀ，严格同权重多重集，报告可交换覆盖）。对照只诊断，不能按效果选一条训练变体。identity/逆置换/守恒阈值1e-6已冻结。native backward与full-source identity/row inverse/disabled-transport原parent一致比较都须报告，不能将冻结bank测试代替。

后续训练评估预注册：原ScanRefer训练/VAL split与每epoch原评估；test不用于选择。主mIoU与M95 .5020及baseline .4894对比，目标≥.5100；结构首筛seed1999，保持50/70。匹配无传输与固定错配机制对照需沿同训练设置评价，不额外seed搜索。按scene聚类配对区间；有效scene不足/区间跨决策界时标不确定。训练前无独立repeat噪声底，标未知。预定义子组为目标占多个fine叶、单fine叶、目标中层混合度、target/non-target；若子组相对M95下降≥.002且scene聚类95%区间上界<0，记material harm并不宣布稳健收益。小样本单场景不作自动否决。

## 5. GPU Allocation Plan（GPU 分配计划）
| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
| server-4 | 0 | 本轮native诊断/反向/同口径资源 | 本候选 | 严格knownhost+UUID+fresh idle+3flock，顺序单进程 |
| server-4 | 1 | 未分配 | 无 | 保留授权，不占空卡 |
| server-3 | 1 | 未分配 | 无 | 保留授权，不新增并行假设 |
训练后续只经准入receipt与原dispatcher，FIFO无指定卡号；server3GPU0/server6新dispatch禁用。

## 6. Implementation Checklist（实施清单）
- [x] 固定diagnosis、primitive与原生匹配对照，全部方向留档。
- [ ] 独立`{NEW}`包：复制原7源文件，新增sibling_transport.py，只修改CTF fine refined readback前的一处连接；配置数值与原M95完全一致。
- [ ] AST/无跨变体import/独立config；实际native loss backward与新路径gradient；完整source controls；同口径bs1/warmup20/repeat100 median/P90/峰值/FVCore≤10G。
- [ ] 已测bundle方可申请缺少的具体commit范围；目前不commit/push/production sync/入队/训练。授权不能由设计请求推定。
- [ ] 准入receipt/安全同步/原dispatcher/真实训练步增长，尚未执行。

## 7. Risk Assessment（风险评估）
平滑可能损伤目标细节；固定模型读出已见不利前景，是必须保留的风险。控制coverage部分、同8scene不随机、未量化总体噪声/optimizer峰值/整体新颖性；无泛化结论。新算子无参数不代表零计算；原FVCore可能漏不支持op，必须报告新增量和时延内存。资源阈值默认10G，memory+15%需训练+.003，不使用HDS特例。默认最多2个有证据预注册实现修订；失败按implementation/hypothesis/inconclusive区分，保留原R0与全部负面结果，不调精度/阈值/seed/FPS/温度。原M95源包完全保留。

Status: DRAFT / diagnostic implemented; independent bundle and remaining gates pending. No training admission.
'''
    with design.open('x',encoding='utf-8') as stream:stream.write(design_text)
    c.advance([analysis,review,design], 'Build independent RSTR package/config from reviewed fixed design; validate native loss, complete source controls and matched resource pair, preserving adverse readouts.')
    package=ROOT/'Cluster/framework/model/Quard_model'/NEW
    package.mkdir(exist_ok=False)
    source=package.parent/NAME
    files=list(source.glob('*.py'));assert len(files)==7
    for path in files:
        text=path.read_text(encoding='utf-8')
        if path.name=='hier_postprocess.py':
            text='from .sibling_transport import transport as sibling_transport\n'+text
            marker='        point_message = self._cluster_to_points(\n            point_feats, refined_cluster_feats, cluster_ids_list, point_mask)'
            assert text.count(marker)==1
            text=text.replace(marker,'        refined_cluster_feats[0] = _sibling_fine(refined_cluster_feats[0], cluster_ids_list, self.nhead)\n\n'+marker)
            text+='\n\ndef _sibling_fine(fine_tokens, identifiers, heads):\n    output = fine_tokens.clone()\n    for b in range(fine_tokens.shape[0]):\n        parent = identifiers[1][b].long()\n        count = torch.bincount(identifiers[0][b].long(), minlength=parent.numel())\n        output[b, :parent.numel()] = sibling_transport(fine_tokens[b, :parent.numel()], parent, count, heads=heads)\n    return output\n'
        ast.parse(text)
        with (package/path.name).open('x',encoding='utf-8') as stream:stream.write(text)
    transport=(OUT/'transport.py').read_text(encoding='utf-8').split('\ndef primitive_tests')[0]
    ast.parse(transport)
    with (package/'sibling_transport.py').open('x',encoding='utf-8') as stream:stream.write(transport)
    config=ROOT/'Cluster/configs/Quard/ctf_hcg_csort_rstr'/(NEW+'.yaml')
    config.parent.mkdir(exist_ok=False)
    config.write_bytes((ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')).read_bytes())
    assets=[*sorted(package.glob('*.py')),config]
    bundle=c.save('independent_bundle.json',{'created_at':c.now(),'candidate_id':c.CID,'source_config':[c.evidence(p) for p in assets],
        'changed_parent_files':['hier_postprocess.py'],'new_file':'sibling_transport.py','config_bytes_identical':True,'parameters_added':0,
        'static_ast_passed':True,'commit':False,'production_deployment':False,'training':0})
    c.advance([bundle,Path(__file__)], 'Stage exact independent source bundle in a private diagnostic directory; execute native backward, full-source controls and same-standard resources before any commit request.')
    work=c.tick.load(ROOT/'pipeline/research_work.json');candidate=next(x for x in work['candidates'] if x['id']==c.CID)
    candidate['stage']='validation';candidate['design']=c.evidence(design);candidate['review']=c.evidence(review)
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    print(json.dumps({'review':str(review),'design':str(design),'bundle_files':len(assets),'training':0}))


if __name__=='__main__':main()
