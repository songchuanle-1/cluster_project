"""Register one real source-only APF and preserve the one verified original CRE launch."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
CRE='hierarchy-cross-root-directed-edge-broadcast';HPC='hierarchy-tree-resolvent-nonlinear-composition';APF='hierarchy-ancestry-path-factor-composition'
SOURCE='d58576b396cfb54577652be972f3ffaffda508c9';APFCOMMIT='bf6c3fafe0f690e16e838e7c0192f09e789389f9'
def read(p):return json.loads(Path(p).read_text('utf8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,v):
    guard()
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def atomic(p,v,text=False):
    guard();tmp=Path(str(p)+'.01b53a4e.final.tmp');assert not tmp.exists()
    with tmp.open('x',encoding='utf8') as f:f.write(v if text else json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    guard();os.replace(tmp,p)
def git(repo,*args):return subprocess.check_output(['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-C',str(repo),*args])
def source_protection(b):
    repo=ROOT/'Cluster';assert git(repo,'rev-parse','HEAD').decode().strip()==SOURCE
    assert git(repo,'status','--porcelain=v1','--untracked-files=all','-z').hex()==b['status_hex'] and not git(repo,'diff','--cached','--name-only','-z')
    assert all(sha(repo/n)==h for n,h in b['files'].items())
    ff=read(HERE/'cre_root_ff_result.json');assert ff['HEAD']==SOURCE and ff['only_nine_tested_additions'] is True
    assert all(sha(repo/n)==h for n,h in ff['source_paths'].items())
    index=Path(git(repo,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else repo/index
    version=read(HERE/'apf_version_prepare/isolated_source_version.json')
    assert sha(index)==version['primary_index_sha256_after']==version['primary_index_sha256_before']
    for n,h in b['protected_ledgers'].items():
        if n not in {'queue.json','running.json','experiments.csv'}:assert sha(ROOT/'pipeline'/n)==h,n
    return sha(index)
def main():
    guard();b=read(HERE/'protected_assets_before.json');indexsha=source_protection(b)
    assert sha(HERE/'cre_actual_independent_review.json')=='83b616377b904036b00f8be9afa16a773f1e59204b3c0cfd62067afd68f0842d'
    assert sha(HERE/'cre_dispatch_result.json')=='ce971f98ca83842691d51960a36ea3773879ba7757f758b3a3f21a65aada981c'
    assert sha(HERE/'cre_training_progress_observation.json')=='d399876d7499ab603f79e39ee1c6762626ecf71a7c5c6135d4f16bc65e3c3233'
    live=read(HERE/'cre_training_progress_observation.json');ob=live['observation'];samples=ob['samples']
    assert live['owner']==EXPECTED and live['returncode']==0 and samples[-1]['max_native_step']>samples[0]['max_native_step']
    assert ob['identity_before']['pid']==118189 and ob['runtime_commit']==SOURCE
    dispatch=read(HERE/'cre_dispatch_result.json');assert dispatch['canonical_dispatch_invoked_once'] is True and dispatch['verified_native_progress'] is True and dispatch['task_after']['pid']==118189
    prep=HERE/'new_candidate_prepare/preparation.json';assert sha(prep)=='04993a8d0e6ffd6b95b1d5f0e1c9052b4efe726ff0fbfd69587668869068060a'
    assert sha(HERE/'new_candidate_independent_review.json')=='ab88679a854a1ee31d96033b2c609f32ca7f3b6bc50e9ac814c005806039a1a2'
    assert sha(HERE/'apf_actual_source_version_independent_review.json')=='3f02f0828b9a3ff47670cddad3c413ef15e403d115eb5059c6f91ea3d4b50c25'
    p=read(prep)
    for n,h in p['prepared_file_hashes'].items():assert sha(prep.parent/n)==h,n
    versionp=HERE/'apf_version_prepare/isolated_source_version.json';version=read(versionp)
    assert version['code_commit']==APFCOMMIT and version['parent_commit']==SOURCE and version['source_file_count']==9 and version['diff_exact9A'] is True
    wt=Path(version['worktree']);assert git(wt,'rev-parse','HEAD').decode().strip()==APFCOMMIT and not git(wt,'status','--porcelain=v1','--untracked-files=all','-z')
    assert all(sha(wt/n)==h for n,h in version['frozen_source_files'].items())
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline');import pipeline_monitor as mon;import closure
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();source_protection(b);work=read(ROOT/'pipeline/research_work.json');assert len(work['candidates'])==144 and not any(c['id']==APF or c.get('experiment_id')=='M219-APF' for c in work['candidates'])
        assert all(digest(c)==b['candidate_digests'][c['id']] for c in work['candidates'] if c['id']!=CRE)
        queue=read(ROOT/'pipeline/queue.json');task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M217-CRE')
        assert task['status']=='running' and task['pid']==118189 and task['code_commit']==SOURCE and task['launch_verified'] is True and task['launch_verification']=='training_progress'
        assert task['admission_receipt']=='pipeline/admissions/M217-CRE.json' and sha(ROOT/task['admission_receipt'])=='0ab8d1bd7e518322c25ae36bb80344fb62f90c150e5ca09bd856cb53d0a6320b'
        closure.admission(ROOT,task)
        lifecycle={n:sha(ROOT/'pipeline'/n) for n in list(b['protected_ledgers'])+['experiments/M217-CRE.json','admissions/M217-CRE.json']}
        now=datetime.now(timezone.utc).isoformat();save(HERE/'research_records_final_intent.json',{'recorded_at':now,'owner':EXPECTED,'before_research_sha256':sha(ROOT/'pipeline/research_work.json'),'current_lifecycle_sha256':lifecycle,'scope':'One verified existing CRE launch metadata and one budgeted source-only APF; no new training/queue/source action.'})
        cre=next(c for c in work['candidates'] if c['id']==CRE);hpc=next(c for c in work['candidates'] if c['id']==HPC)
        assert cre['stage']=='training' and hpc['stage']=='validation'
        cre.setdefault('native_check_history',[]).append({'recorded_at':now,'prior_current_native_check':copy.deepcopy(cre.get('current_native_check')),'reason':'Preserve prior failed control before current new-owned complete four-arm success.'})
        cre['current_native_check']={'recorded_at':now,'kind':'native_smoke','result':'passed','target':'candidate','code_commit':SOURCE,'optimizer_steps':2,'native_loss_forwards':2,'native_criterion_backwards':2,'evidence':ref(HERE/'cre_native_smoke.json'),'actual_four_result_review':ref(HERE/'cre_actual_four_result_review.json'),'old_import_failure_preserved':True,'root_cause_of_old_import_failure':'UNKNOWN','scope':'Current original native TRAIN2 and path/backward/update checks actually passed; no source/worker/dependency modification or proven root-cause repair.'}
        cre['latest_native_training_progress']={'recorded_at':ob['observed_at'],'pid':118189,'epoch':samples[-1]['max_native_step'][0],'step':samples[-1]['max_native_step'][1],'steps_per_epoch':4686,'observed_steps':samples,'precise_native_validation':live['precise_native_validation'],'evidence':ref(HERE/'cre_training_progress_observation.json'),'scope':'Exact original deployed source8/YAML/runtime d585/GPU0 UUID+computePID, step growth. Validation metric not yet observed; not zero.'}
        cre['latest_canonical_dispatch']=ref(HERE/'cre_dispatch_result.json');cre['source_status']='TESTED_CRE_D585_PRESENT_IN_PRIMARY_AND_RUNTIME'
        cre['current_resource_check']={'recorded_at':ob['observed_at'],'kind':'original_training_occupation','result':'running_original_verified_training','physical_gpu':0,'evidence':ref(HERE/'cre_training_progress_observation.json'),'scope':'Current original M217 physical0 occupation; full resources were separately measured before launch.'}
        for n in ['cre_readiness_retest_plan.json','import_order_prepare/import_order_actual_result.json','import_order_actual_independent_review.json','cre_dispatch_result.json','cre_training_progress_observation.json']:
            if ref(HERE/n) not in cre['evidence']:cre['evidence'].append(ref(HERE/n))
        cre['next_action']='Monitor this exact original M217 PID118189/log/source d585 on server4 GPU0, validation and native growth; efficacy UNKNOWN. Preserve previous0f import failure/negative evidence, no replay or claim of root-cause repair. GPU1 prohibited and M206/other protected holds remain.'
        hpc.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(hpc.get('resource_check')),'prior_current_resource_check':copy.deepcopy(hpc.get('current_resource_check'))})
        hpc['resource_check']=ref(HERE/'cre_training_progress_observation.json');hpc['current_resource_check']={'recorded_at':ob['observed_at'],'result':'blocked','server':'server-4','physical_gpu':0,'evidence':ref(HERE/'cre_training_progress_observation.json'),'scope':'Original admitted CRE occupies sole authorized GPU0. HPC candidate graph/resources remain NOT_RUN; no inherited CRE gate PASS.'}
        hpc['current_version_compatibility']={'existing_source_commit':hpc['code_commit'],'existing_parent_commit':'56b2a96dc48cc8a88f0f7105527ef448113b1060','current_primary_and_runtime':SOURCE,'status':'NEEDS_COMPATIBLE_SOURCE_AND_TOOL_METADATA_BEFORE_FUTURE_NATIVE','scope':'Preserve old2f7/parent56 and all old raw. Same source9 may be packaged compatibly against actual new parent with separate proof; do not sibling-ff or relabel prior native results. No model revision authorized by metadata alone.'}
        hpc['next_action']='Prepare an explicitly versioned compatible copy of unchanged original HPC source9 and reviewed tooling against current d585 while preserving2f7/parent56 and0f failed control. Then use genuinely idle authorizedGPU0/fresh owner/deadline/UUID/three locks for actual pairedTRAIN2/resources. Current CRE running is not to be interrupted; no GPU1, blind retry, sibling ff or borrowed CRE PASS.'
        if ref(HERE/'cre_training_progress_observation.json') not in hpc['evidence']:hpc['evidence'].append(ref(HERE/'cre_training_progress_observation.json'))
        c=copy.deepcopy(read(prep.parent/'candidate_record.json'));c.pop('future_version_parent',None)
        c.update(code_commit=APFCOMMIT,source_commit=APFCOMMIT,source_parent_commit=SOURCE,base_reference_commit='56b2a96dc48cc8a88f0f7105527ef448113b1060',created_at=now,created_in_tick=EXPECTED['token'],created_from_snapshot=EXPECTED['generated_at'],implementation_status='SOURCE_ONLY_ISOLATED_VERSION_SAVED_STATIC_REVIEWED_NATIVE_NOT_RUN',source_status='ISOLATED_EXACT9A_NOT_PROMOTED',source_preparation=ref(prep),source_version=ref(versionp),independent_source_review=ref(HERE/'new_candidate_independent_review.json'),actual_source_version_independent_review=ref(HERE/'apf_actual_source_version_independent_review.json'),native_status='NOT_RUN',resource_status='NOT_RUN',native_execution_code_commit=None,queued=False)
        c['source_preparation_history']=[{'preparation':ref(prep),'original_code_commit':None,'original_source_commit':None,'original_actual_parent_commit':None,'original_reference_parent':'56b2a96dc48cc8a88f0f7105527ef448113b1060','scope':'Frozen NULL/reference56 artifacts unchanged; actual first isolated version separately bf6 childd585.'}]
        for file in [prep,prep.parent/'candidate_record.json',HERE/'new_candidate_independent_review.json',versionp,HERE/'apf_actual_source_version_independent_review.json']:
            if ref(file) not in c['evidence']:c['evidence'].append(ref(file))
        c['current_resource_check']={'recorded_at':ob['observed_at'],'result':'blocked','server':'server-4','physical_gpu':0,'evidence':ref(HERE/'cre_training_progress_observation.json'),'scope':'Only original M217 currently runs; APF requires its own reviewed native/op preparation and true tests before any receipt. No inherited gate PASS.'}
        c['next_action']='Prepare native/op observer tools for exact APF bf6/parent-runtime d585 using frozen61185 protocol. Static35+independent43 checks are not Torch/native/FP32/resource evidence. Wait for genuinely idle authorizedGPU0 with fresh owner/original deadline/assets/UUID/three locks; then original pairedTRAIN2/resources before receipt/queue/launch. No GPU1, interrupting currentCRE, numerical tuning or relabelled old results.'
        work['candidates'].append(c)
        work.setdefault('operational_readiness_history',[]).append(copy.deepcopy(work.get('shared_import_diagnosis')))
        work['latest_operational_readiness']={'recorded_at':now,'current_CPU_order_control':ref(HERE/'import_order_prepare/import_order_actual_result.json'),'independent_CPU_review':ref(HERE/'import_order_actual_independent_review.json'),'current_CRE_actual_four_arm_review':ref(HERE/'cre_actual_four_result_review.json'),'current_training':ref(HERE/'cre_training_progress_observation.json'),'old_import_failure_root_cause':'UNKNOWN','source_worker_library_or_global_cache_changed':False,'scope':'Current original controls and actual native checks/deployment functioned; this is not a proved repair or HPC/APF admission.'}
        work['last_event_tick']=EXPECTED['generated_at'];work['updated_at']=now;work['next_action']='Monitor the exact verified original CRE/M217 source d585 PID118189 on sole authorized server4GPU0. Prepare compatible HPC2f7 source/tool metadata againstd585; APFbf6 source-only new reserve needs its own native/op tools and tests after true idle. Goal still.5100/M95.5020, current CRE validation UNKNOWN; old failures and all resource/hold/resume/bans remain.'
        atomic(ROOT/'pipeline/research_work.json',work)
        for candidate in [cre,hpc,c]:
            for e in candidate['evidence']:closure.artifact(ROOT,e)
        assert all(sha(ROOT/'pipeline'/n)==h for n,h in lifecycle.items()) and source_protection(b)==indexsha
        old={x['id']:digest(x) for x in work['candidates'] if x['id']!=APF};changed=[k for k,h in b['candidate_digests'].items() if old[k]!=h];assert set(changed)=={CRE,HPC}
        sections={};name=None
        for line in (ROOT/'pipeline/codex_memory.md').read_text('utf8').splitlines():
            if line.startswith('## '):name=line[3:];sections[name]=[]
            elif name is not None:sections[name].append(line)
        sections['Goal And Phase'][0]='- 当前01b53a4e60c941719a2eb3bea379789b；actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-27T18:08:35.561778Z/deadline19:08:35.561778Z原值保持不延长。'
        sections['Champion And Baseline']=[s.replace('本轮确认原生正常earlystop','既有原生正常earlystop') for s in sections['Champion And Baseline']]
        active=[]
        for s in sections['Active Hypotheses']:
            if s.startswith('- M216-AEF本轮已正常归档'):s=s.replace('本轮已正常归档','既有正常归档')
            if s.startswith('- 本轮CREd585与HPC2f7'):s=s.replace('- 本轮CREd585与HPC2f7','- 历史0f02 CREd585与HPC2f7')
            if s.startswith('- 两control失败独审0528'):s=s.replace('两现有储备继续validation，故障是原生导入就绪，不是GPU忙。','历史失败保留；本轮CRE新请求实际四臂已过并训练，HPC未借用PASS。')
            if s.startswith('- CRE现有M217兼容source'):s=s.replace('主线/runtime仍AEF56，未promotion/sync/候选图执行/准入。','本轮真实四臂后精确ff/sync至d585并准入训练。')
            if s.startswith('- 新CRE兼容native'):s=s.replace('10active仍null、native/resourcesNOT_RUN。','原冻结模板10active仍null；本轮新owner active执行与真实结果另存01b53a4e，不回填母本。')
            active.append(s)
        active.extend(['- 本轮两个freshCPU顺序控制pccm→gorilla→torch / gorilla→torch→pccm均完整原AttrArgTransformer导入PASS，无denials/CUDA未init，b4969bf0/独审1fc42576；privatecache与CPUhashseed1999条件明确，不复制到原native、不称修复。随后preregister一次当前CRE新请求复测，原worker/source/库没改，旧0f失败仍在。',
            '- CRE本轮新token四臂各terminal0：原两自然TRAIN/common835项155907386参数/hash5c80…同；loss候选见66f687，3map/6W块两步原loss梯度有限非零及slice更新，8真跨root场景/448有向边、原一次mean与三skip/HCG/单inst实核。独审83b61637，summary9fc455b6，准入receipt0ab8d1bd。',
            '- CRE实际9.639849036G vsM959.762532428G，156301370params/−1182720；median34.707585 vs34.047249ms（慢1.9395%），P9037.182044 vs35.867501ms（慢3.6650%），预测/带observer smoke显存均降、15%不触发。pureTRAIN峰值/效果/新颖性未知，不称全面更快。',
            '- 本地主线与runtime精确d585已验证原9source/YAML，28原用户内容/status及空暂存保留；本轮无新CRE sourcecommit。canonical唯一派发/Popen1、receipt字符串及预算通过，原PID118189/launchverified training_progress，resultce971f98。上海02:45:02 TRAIN1/50 602→611/4686，观察d399876d；无验证值时记UNKNOWN不补0。',
            '- 新M219-APF stableID hierarchy-ancestry-path-factor-composition：每真fine节点取原fine/middle/coarse祖先，GELU(W3C→3C)一次联合因子拆u/v/w；fine直接u，上两层仅私有v/w按真实fine路径等权mean，coarse非等middle/pointmass。原3LN/rawskip/rawbanks/CSORT/HCG单inst保持，无learnedscore/gate/新routing。',
            '- APF原04993a8d/19map/8源+原YAML9与0ef045c7/61185eab协议/candidate22bb的code/source/actualparent NULL及reference56冻结保留；35源码/stdlib载体核5ca100f5，原序列化harness失败d1af保留、非模型修订。独立43载体断言及有限源核ab88679a仅静态；真Torch/Linear/GELU/autograd/资源/效果/新颖性未测，9块梯度仅描述、whole-factor聚合trainability为门。',
            '- APF本轮首实际source-only bf6c3fafe0f690e16e838e7c0192f09e789389f9/唯一父d585，恰原9A/blob/clean。actualproof在apf_version_prepare，独审3f02f082；原0499 NULL不回填，主线/runtime未推广APF。当前implementation，待原生工具和空闲GPU0真实TRAIN2/resources，不借CRE通过结果。',
            '- HPC原2f7/父56及原f9a/1362工具/0f失败全保留，当前主线/runtime已d585，需要原9字节兼容包装与独立真测后再准入；不能跨兄弟ff/重标raw。当前M217占用唯一GPU0，GPU1禁用。'])
        sections['Active Hypotheses']=active
        sections['Closed Or Failed Directions']=[s for s in sections['Closed Or Failed Directions'] if not s.startswith('- 旧10 holds')]
        sections['Closed Or Failed Directions'].append('- 本轮due10旧held小字段/完整record digest与0f原记录全相同，原暂停/授权/数值/修订边界不动，不读855历史目标/旧grant/ckptbody。145条中1新APF，原144仅CRE/HPC更新、其他142保持。M216/其他终态未重复归档，snapshot new_terminal标志是前轮已完成事件。')
        sections['Running And Queue'][0]='- 当前唯一正式训练M217-CRE server4 GPU0原PID118189/source-runtime d585；02:45:02 TRAIN1/50 602→611/4686，验证mIoU尚未观测。0ready/0claiming；waiting M206仍用户暂停不可派发。HPC需兼容源包装，APF bf6为已保存未原生测储备。'
        sections['Running And Queue']=[s.replace('旧source56','当前sourced585') for s in sections['Running And Queue'] if not s.startswith('- 上海00:38:35最新GPU0')]
        sections['Open Questions And Risks']=[s for s in sections['Open Questions And Risks'] if not s.startswith('- CRE d585/HPC2f7') and not s.startswith('- 当前精确根因UNKNOWN')]
        sections['Open Questions And Risks'].append('- 原0f两导入故障根因仍UNKNOWN；本轮CPU完整对照/原CRE四臂和实际新训练通过，未改库/worker/cache，不可称已证明修复。持续监视原PID/log，不把复测成功授予HPC/APF；后两者候选图/资源/准确率仍未测。')
        sections['Last Tick']=['- begin一次canonical监控/目标/既有派发，旧M216终态不重复归档；本轮快照creation1/reserve缺口1。',
            '- 新fixedCPU两order完整原pccm/真实Transformer+gorilla/torch通过，无CUDA；旧失败不覆盖。一次预注册新CREcontrol复测及后续candidate/resources均真实过门，原source/worker/库不变，根因未明。',
            '- 四raw独审后summary三标准→精确9A ff/sync d585→receipt0ab8→一次canonicalGPU0派发；原PID118189，原生步数602→611真实递增。主线28/status/空暂存保留，不借CPU对照代原生。',
            '- 独立新APF一次联合祖先路径因子实现，静态35+独立43与源码审；首source-only bf6子d585 exact9A保存/独审，母本NULL/reference56不回填。注册1新candidate，无Torch/native/资源PASS、无新APF启动。',
            '- 旧10 held保持，M206暂停/其他终态/其他项目/调度/资源边界不改。HPC下步兼容包装，APF准备原生工具，均等合法空槽；随后report/finish核释放，不预签完成。']
        names=['Goal And Phase','Champion And Baseline','Active Hypotheses','Closed Or Failed Directions','Running And Queue','Open Questions And Risks','Last Tick'];lines=['# Codex Research Memory','']
        for n in names:lines.extend(['## '+n]+[s for s in sections[n] if s]+[''])
        assert len(lines)<120;atomic(ROOT/'pipeline/codex_memory.md','\n'.join(lines),text=True)
        notes={'actions':['本轮新fixedCPU导入顺序A/B均完整pccm/真实AttrArgTransformer+gorilla/torch通过，privatecache与CPUhashseed条件明确、无CUDA/模型/数据。旧0f失败原样保留，未确定根因或改动依赖/stdlib/全局缓存。随后预注册最多一次新CRE首control复测，使用原source/worker/普通native环境，不重放旧请求。',
            'CRE当前四份真实结果全terminal0：M95/CRE原两TRAIN输入与动态common835项155907386参数匹配，候选两原loss/backward/optimizer及真跨根U/私有mean/D0D1/原skip-HCG-inst路径和六W块更新核通过。实际资源9.639849036G/156301370参数，低于10G；median比M95慢1.9395%、P90慢3.6650%，预测和带observer smoke峰值下降，15%条件不触发。',
            '独审83b与当前三标准后，主线精确ff已测9A到d585，原28用户内容/status/空暂存保持；existing safe sync及实际部署源验证后，receipt0ab8入队并仅调用一次canonical派发/nativePopen1。M217原PID118189、GPU0 UUID/source8/YAML/runtime d585复核，上海02:45:02 TRAIN1/50步602→611/4686，无已观测验证指标；当前是真训练进展。',
            '按本轮唯一创建预算实现M219-APF：真fine→middle→coarse祖先路径一次3C联合因子拆三路输出，上层仅私有fine-path等权消息；原rawbank/三skip/LN/CSORT/HCG单inst保持。35必要软件核、43独立载体断言与有限源审均仅静态；初序列化harness失败保留，未做Torch/native/FP32/资源或效果测量。',
            'APF原8源+原YAML9及NULL/reference56母本冻结；首真实source-only bf6以当前d585为唯一父exact9A/blob/clean保存，独立Git核3f02通过，主线/runtime未推广APF。当前注册1新储备、0模型修订；HPC原2f7/父56和失败历史保留，需兼容包装。',
            'M216终态是前轮已归档事件，本轮未重复归档或声称新增完成。10旧held到期小字段/digest全同，不读855旧目标/旧授权/ckptbody，不恢复M206/BFC/M201或增加PCE/RSTR修订。只用server4GPU0，GPU1禁用，其他项目和调度不动。'],
            'decisions':['当前已有1个实际运行实验CRE；训练效果及新颖性UNKNOWN，尚无验证mIoU，不能把2步或技术准入当精度提升。项目最佳仍M95 0.5020、目标0.5100、差0.0080。旧导入故障根因未明，当前真实复测与新训练通过，不声称证明修复。',
            '继续监视唯一原CRE PID/log/source及后续验证，保持本轮原50epochs/max_iters70、seed1999、数据/优化器/precision不变；无盲重启、额外卡或挤占别人。',
            'HPC先做原9字节在d585上的兼容源/工具包装，APF bf6准备自身native/op观察工具；均在真空闲授权GPU0和fresh owner/原deadline/UUID/三锁核验后真测，过门才准入。不能跨兄弟ff、回填NULL母本、借CRE PASS或把软件载体当native。',
            '本轮完成当前CRE真实四臂/1准入/1已验证启动，新增1独立source-only APF，未填满任何不必要额度。常规操作已有授权，无需重复确认；完整记录后finish并核锁释放。']}
        save(HERE/'report_notes.json',notes)
        save(HERE/'protected_assets_after.json',{'recorded_at':now,'primary_HEAD':SOURCE,'tested_primary_fast_forward_exact9A':True,'original28_status_bytes_and_empty_staging_preserved':True,'primary_index_same_as_post_ff_APF_source_save':indexsha,'all_post_dispatch_lifecycle_bytes_preserved_during_registration':True,'new_candidate':APF,'candidate_count':145,'changed_existing_candidates':changed,'other142_existing_candidates_preserved':True,'source_only_APF_commit':APFCOMMIT,'source_only_APF_parent':SOURCE,'model_implementation_revisions':0,'verified_training_launches':1,'canonical_native_Popen_count':sum(1 for call in read(HERE/'cre_dispatch_transport_calls.json') if call['canonical_native_launch_request']),'new_APF_native_or_training':'NOT_RUN'})
        print(json.dumps({'CRE':'running_verified','PID':118189,'native_progress':samples[-1]['max_native_step'],'APF_source_only':APFCOMMIT,'new_candidates':1,'existing_candidates_preserved_except_CRE_HPC':142,'memory_lines':len(lines),'notes':ref(HERE/'report_notes.json')},ensure_ascii=False))
    finally:lock.close()
if __name__=='__main__':main()
