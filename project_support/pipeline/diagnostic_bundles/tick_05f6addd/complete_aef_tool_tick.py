"""Root-only once recorder of actual static AEF tooling and resource refusal; no native launch."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,os,re,sys
from anchor_bfc_packet import guard
from verify_protected_assets import snapshot
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='05f6addd722d487fbdc663753af44b83';BASE='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563';SOURCE='56b2a96dc48cc8a88f0f7105527ef448113b1060'
AEF='hierarchy-parent-antisymmetric-edge-flux';BEC='hierarchy-cross-level-bipartite-edge-composition'
EXPECTED_REFS={'aef_native_prepare/preparation.json':'78f7c45ea05147009ce67689177486f4344191e8cf3d4eb19fec59e1a71a6e39','aef_operational_prepare/preparation.json':'965ee3343199ab509bb6ce9d643204dc3b93f18322c11dd857047cd0e43d2b70','aef_native_preparation_independent_review.json':'ddf934472d4ac713500d309a69a5817730a8d6c7483efc09078da05be92e9055','aef_operational_preparation_independent_review.json':'447248d4480c140773f3861845b950e69d2c83dfe5c5e56e8e103dc05b154f98','bec_training_progress_observation.json':'f5bb9da8057ccc3b9661ba8750b87bc310873b4700d0c333d499f10476fe1c47','bec_training_progress_independent_review.json':'4b3cdd889187190b4ccf626832f2d54755c4cdcd61e1f2d20bf950f1be8438c9','aef_catalogue_result.json':'5b2beefa0a3c05a26d702e96bc31b6667b3546bf760594b3285e8f222285963b','aef_actual_local_guard.json':'6dd7ac287fbf75a84de0e9d09387c4d5ea1e522a8dcf176a65d90ed2cb9ab5de','aef_catalogue_and_guard_independent_review.json':'791821dead6526c9344f063469c59eb6334fc5301a2ec5c2c33b572d0f4da001'}

def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def exclusive_bytes(p,data):
 with Path(p).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def replace_bytes(p,data):
 temporary=p.with_name(p.name+'.'+TOKEN+'.tools_completion.tmp')
 exclusive_bytes(temporary,data);os.replace(temporary,p)
def others(w):return {c['id']:c for c in w['candidates'] if c['id'] not in (AEF,BEC)}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
 if not args.execute_root:
  print('DRAFT_DEFAULT_READ_ONLY: no recorder execution or shared write');return
 owner=guard();assert owner['token']==TOKEN and os.environ.get('GIT_OPTIONAL_LOCKS')=='0' and sys.dont_write_bytecode
 for name in ['completion_intent.json','completion_before.json','completion_result.json','completion_memory_before.md','completion_preflight_metrics_source.json','report_notes.json']:
  assert not (HERE/name).exists(),'Existing/partial recorder artifact; reconcile read-only, never replay: '+name
 for name,digest in EXPECTED_REFS.items():assert sha(HERE/name)==digest,name
 catalogue=read(HERE/'aef_catalogue_result.json');resource=read(HERE/'aef_actual_local_guard.json');obs=read(HERE/'bec_training_progress_observation.json');peer=read(HERE/'bec_training_progress_independent_review.json')
 actual_peer=read(HERE/'aef_catalogue_and_guard_independent_review.json')
 assert actual_peer['status']=='AEF_STATIC_CATALOGUE_SOURCE_AND_ACTUAL_LOCAL_GUARD_INDEPENDENTLY_REVIEWED_NOT_NATIVE_PASS' and actual_peer['candidate_id']==AEF and actual_peer['code_commit']==SOURCE and actual_peer['material_concerns']==[]
 assert actual_peer['anchors']['actual_catalogue_result']==ref(HERE/'aef_catalogue_result.json') and actual_peer['anchors']['actual_local_guard']==ref(HERE/'aef_actual_local_guard.json')
 assert catalogue['owner_token']==TOKEN and catalogue['candidate_id']==AEF and catalogue['code_commit']==SOURCE and catalogue['status']=='REVIEWED_STATIC_CATALOGUE_ANCHORED_NATIVE_NOT_RUN' and catalogue['active_execution_created'] is False
 assert catalogue['all141_other_candidates_unchanged'] and catalogue['all14_lifecycle_ledgers_unchanged'] and catalogue['primary28_status_bytes_index_and026c_unchanged']
 assert resource['kind']=='resource_check' and resource['result']=='blocked' and resource['candidate_id']==AEF and resource['experiment_id']=='M216-AEF'
 assert resource['owner']=={k:owner[k] for k in resource['owner']} and set(resource['owner'])=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'}
 assert resource['actual_local_guard_events']==[{'physical_gpu':0,'refused':True,'reason':'Selected GPU has registered running task'},{'physical_gpu':1,'refused':True,'reason':'Explicit physical GPU0 is required'}]
 assert all(resource[k]==0 for k in ['transport_calls','Popen_calls','network_calls','GPU_queries','GPU1_queries']) and resource['Torch_imported'] is False and resource['active_execution_created'] is False
 assert resource['native_TRAIN2']==resource['resources']=='NOT_RUN' and resource['native_PASS_or_receipt_queue_created'] is False and resource['material_concerns']==[]
 assert resource['hardware_evidence']==ref(HERE/'bec_training_progress_observation.json') and resource['static_catalogue_result']==ref(HERE/'aef_catalogue_result.json')
 assert obs['owner_token']==TOKEN and obs['native_TRAIN_growth'] is True and peer['material_concerns']==[] and peer['actual_checks_count']==18
 first,last=obs['observations'];assert first['train_progress']==[6,50,2151,4686] and last['train_progress']==[6,50,2160,4686]
 assert all((x['pid'],x['start_ticks'],x['runtime_HEAD'],x['gpu_contexts'])==(1558071,'64444390',BASE,'1558071, 19760') for x in (first,last))
 ctx=read(ROOT/'pipeline/headless/.tick_context.json');line=next(x for x in ctx['preflight']['monitor_output'].splitlines() if '_ctf_hcg_csort_bec]' in x)
 match=re.search(r'Best=([0-9.]+) (\d+)/(\d+) no_improve=(\d+)/(\d+) gpu=(\d+)',line);assert match and match.groups()==('0.4390','6','50','0','10','0')
 preflight_source={'context_ref':ref(ROOT/'pipeline/headless/.tick_context.json'),'generated_at':ctx['generated_at'],'monitor_line':line,'scope':'Exact current begin preflight line preserved before recorder; not a newer remote metric.'};pfb=encoded(preflight_source)
 partial={'best_mIoU_4dp':match.group(1),'epoch':int(match.group(2)),'max_epochs':int(match.group(3)),'no_improve':int(match.group(4)),'patience':int(match.group(5)),'gpu':0,'source':{'path':(HERE/'completion_preflight_metrics_source.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(pfb).hexdigest()},'source_field':'monitor_line copied from original context.preflight.monitor_output','observed_at':ctx['generated_at'],'not_final_efficacy':True}
 sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
 lock=monitor.acquire_lock(str(ROOT));assert lock is not None
 try:
  guard();pre=snapshot();baseline=read(HERE/'protected_assets_before.json')
  assert all(pre[k]==baseline[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert set(pre['candidate_digests'])==set(baseline['candidate_digests']) and len(pre['candidate_digests'])==142
  assert all(v==baseline['candidate_digests'][k] for k,v in pre['candidate_digests'].items() if k!=AEF),'Only already verified static AEF catalogue may differ from begin baseline'
  wp=ROOT/'pipeline/research_work.json';mp=ROOT/'pipeline/codex_memory.md';work=read(wp);out=copy.deepcopy(work)
  a=next(c for c in out['candidates'] if c['id']==AEF);b=next(c for c in out['candidates'] if c['id']==BEC)
  assert a['stage']=='validation' and a['code_commit']==SOURCE and a['source_parent_commit']==BASE and a.get('native_execution_code_commit') is None
  assert a['native_status']==a['resource_status']=='NOT_RUN' and not a.get('revision_history') and not a.get('blocker_kind')
  assert a['worker_preparation']['preparation']==ref(HERE/'aef_native_prepare/preparation.json') and a['execution_adapter']['preparation']==ref(HERE/'aef_operational_prepare/preparation.json') and a['execution_adapter']['release']==catalogue['release']
  assert sha(ROOT/catalogue['release']['path'])==catalogue['release']['sha256'] and (ROOT/catalogue['release']['path']).read_bytes()==(HERE/'aef_operational_prepare/release_template.json').read_bytes()
  assert not (HERE/'aef_execution').exists()
  assert b['stage']=='training' and b['code_commit']==BASE and b['native_execution_code_commit']==BASE and b['training_status']=='running'
  now=datetime.now(timezone.utc).isoformat()
  a.setdefault('preparation_history',[]).append({'recorded_at':now,'reason':'Clarify current scope after actual56 source and reviewed static tool catalogue; frozen150c declarations remain untouched.','prior_preparation_scope':copy.deepcopy(a.get('preparation_scope'))})
  a['preparation_scope']='Current canonical candidate has actual isolated56b2 singleparent026c and reviewed version-bound native/op catalogue. Historical150c9d6 null/preversion software scope remains immutable evidence; actual native/resources NOT_RUN and native_execution_code_commit remains null.'
  a.setdefault('resource_check_history',[]).append({'recorded_at':now,'prior_resource_check':copy.deepcopy(a.get('resource_check')),'prior_current_resource_check':copy.deepcopy(a.get('current_resource_check'))})
  a['resource_check']=ref(HERE/'aef_actual_local_guard.json')
  a['current_resource_check']={'kind':'resource_check','result':'blocked','server':'server-4','physical_gpu':0,'recorded_at':resource['recorded_at'],'evidence':ref(HERE/'aef_actual_local_guard.json'),'hardware_evidence':ref(HERE/'bec_training_progress_observation.json'),'scope':'Actual current root local adapter guards/refusals. Hardware evidence is the separately saved current BEC samples, not a new hardware query or native test.'}
  a['next_action']='Use the existing reviewed AEF56b2 native/op packet only after sole authorized GPU0 is truly idle and a fresh root owner/context/original deadline/source/assets/UUID/three-lock check succeeds. Keep BEC1558071 running; noGPU1, eviction, new source, resampling, revision or old-hold recovery. Actual paired M95/AEF TRAIN2/resources remain NOT_RUN.'
  for entry in [ref(HERE/'aef_catalogue_result.json'),ref(HERE/'aef_actual_local_guard.json'),ref(HERE/'aef_catalogue_and_guard_independent_review.json')]:
   if entry not in a['evidence']:a['evidence'].append(entry)
  b.setdefault('training_progress_history',[]).append(copy.deepcopy(b.get('training_progress_observation')))
  b['training_progress_observation']={'first':first['train_progress'],'last':last['train_progress'],'pid':1558071,'start_ticks':'64444390','observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'independent_review':ref(HERE/'bec_training_progress_independent_review.json'),'preflight_partial_metrics':partial}
  b['current_resource_check']={'result':'original_training_running','server':'server-4','physical_gpu':0,'observed_at':last['observed_at'],'evidence':ref(HERE/'bec_training_progress_observation.json'),'scope':'Root bounded actual source/process/native-step/context evidence, not continuous exclusivity or pureTRAIN peak.'}
  for entry in [ref(HERE/'bec_training_progress_observation.json'),ref(HERE/'bec_training_progress_independent_review.json')]:
   if entry not in b['evidence']:b['evidence'].append(entry)
  if work.get('tick_attempt'):out.setdefault('tick_attempt_history',[]).append(copy.deepcopy(work['tick_attempt']))
  out['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':AEF,'kind':'resource_check','result':'blocked','command':'python -B -X utf8 '+(HERE/'check_aef_actual_guard.py').as_posix()+' --execute-root','observation':'Actual current root AEF catalogue/version/currentpolicy guards passed; prepare0 refused registered BEC occupancy and prepare1 refused authorization before transport. Zero subprocess/network/Torch/new hardware queries or active execution; current root hardware samples separately show original BEC progress on soleGPU0. Static packet and41 metadata software checks are not native/resources PASS.','evidence':[ref(HERE/'aef_actual_local_guard.json'),ref(HERE/'aef_catalogue_result.json'),ref(HERE/'aef_catalogue_and_guard_independent_review.json')]}
  out['updated_at']=now;out['next_action']='Continue original verified BEC1558071/source026c on soleGPU0. AEF56b2 now has complete independently reviewed native/op catalogue; run original matched checks only on genuine fresh authorized idleGPU0. No new candidate/source/revision/admission/queue/launch, no protected-task recovery.'
  assert len(out['candidates'])==len(work['candidates'])==142 and others(out)==others(work)
  memory_old=mp.read_bytes();lines=memory_old.decode('utf8').splitlines();parts={};key=None
  for text in lines:
   if text.startswith('## '):key=text;parts[key]=[]
   elif key:parts[key].append(text)
  headers=['## Goal And Phase','## Champion And Baseline','## Active Hypotheses','## Closed Or Failed Directions','## Running And Queue','## Open Questions And Risks','## Last Tick'];assert set(parts)==set(headers)
  parts[headers[0]][0]='- 当前05f6addd722d487fbdc663753af44b83，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T18:03:58.499009+00:00/deadline19:03:58.499009+00:00原值保持。'
  active=[]
  for text in parts[headers[2]]:
   if text.startswith('- AEF当前native工具尚未完成：'):
    active.append('- AEF现有完整静态native/op工具已准备并外锚：native78f7c45e/18map/12diag/10active null，MD独审ddf93447；op965ee334/7自有map/41小metadata软件检查，独审447248d4；release8913f688为模板精确bytecopy。它不是lease/GPU许可或原生PASS，无真实manifest/activebinding/remote/执行结果，AEF native/resources仍NOT_RUN。')
    active.append('- AEF worker保原M95配对TRAIN2/原loss单backward/optimizer和原资源整函数；未来须实测两W输入列块原loss聚合非零有限grad/更新、真实双向MST/散射与HCG-inst路径及common集合，不借BEC839/CTS843计数、源码或符号性质代测。原YAML/2db协议/9d6源码与56b2源版本未改。')
   else:active.append(text)
  parts[headers[2]]=active
  parts[headers[3]]=[('- 旧held候选本轮不复核，不读655正文/旧grant/checkpoint体、不重开或重测；沿原bounded metadata结论，无新增恢复/修订许可。' if x.startswith('- 旧10本轮未due') else x) for x in parts[headers[3]]]
  parts[headers[4]][0]='- 当前1个确认训练：M215-BEC source026c，server4GPU0 原PID1558071/start64444390；本轮18:08:02→18:08:05 root双样本TRAIN6/50 2151→2160/4686，sole context19760MiB；观测f5bb9da8/18项peer4b3cdd88。source8/YAML/queue/experiment/receipt/R1 digest与唯一selected0 mapping一致，不声称持续独占。'
  parts[headers[4]]=[('- AEF本轮aef_actual_local_guard6dd7ac28为真实resource_check/blocked：当前root/policy/版本/外锚检查后prepare0因registered BEC拒绝、prepare1因GPU1未授权拒绝；0transport/Popen/network/Torch/新GPU查询/active。物理占用依据另采当前root f5bb样本，不能把metadata拒绝当idle检测或原生测试。' if x.startswith('- AEF本轮实际resource_check') else x) for x in parts[headers[4]]]
  parts[headers[4]].insert(1,'- 本轮begin原始监控截至18:03:58Z：BEC partial Best=.4390、6/50、no_improve0/10；来源当前context.preflight.monitor_output原行，不是18:08双样本新验证值，不是最终效果。M95.5020/目标.5100/gap.0080保持。')
  parts[headers[5]]=[('- AEF已具备受审静态native/op工具，但Torch原生forward/backward/实际grad、浮点Σdelta、同口径资源、泛化与准确率均未测；不能拿Git/符号/metadata checks代签。静态release不是当前或未来空卡证明。' if x.startswith('- AEF只有兼容源版本') else x) for x in parts[headers[5]]]
  parts[headers[6]]=['- 新begin一次canonical监控/goal/已有派发；原BEC正常进展，无新终态/运维故障。唯一AEF接续工具准备，不新增候选或重复造工具，未读旧655/旧grant/checkpoint。','- 只准备既有56b2 source的AEF nativeworker/runtime/template和safe adapter/RPC/catalog；原资源AST/2db协议/原YAML保持，native/op独审后root只静态外锚与模板bytecopy，无activelease/远端/GPU计算。41小隔离软件metadata/AST/拒绝检查不是61/98重测或nativePASS。','- 本轮tick_attempt是真实AEF resource_check/blocked，guard6dd7原样保留两拒绝原因并引用当前BEC f5bb硬件样本；0新candidate/模型revision/sourcecommit/准入/入队/训练启动，不伪造FP32或资源实测、不抢卡/换seed。','- 收尾仅AEF准备/实际resource证据与BEC当前进度、七段memory/notes改变；其他140候选/14生命周期账/primary026c/28status+bytes/index保持。report/finish/postflight由root另行执行，以最终receipt/lease释放为准，本脚本不预签其成功。']
  memory='# Codex Research Memory\n\n'+'\n'.join(h+'\n'+'\n'.join(parts[h]).strip()+'\n' for h in headers)+'\n';assert len(memory.splitlines())<120 and memory.count('\n## ')==7
  notes={'actions':['原BEC1558071/start64444390在唯一GPU0真实TRAIN6/50 2151→2160；root观测f5bb与18项独审4b3c只读核源8/YAML/收据/R1 digest/三账，未触GPU1或原进程。','完成并受审外锚既有AEF56b2原生工具和safe adapter/RPC静态catalog：native78f7/op965e、独审ddf934/447248、release8913为模板bytecopy；原9d6/427ee版本/2db协议和模型9文件保持。','41小软件metadata/AST/拒绝检查实过，未重复61/98旧套件；本轮真实NoTransport guard6dd7通过当前root/版本/外锚/白名单后，prepare0 busy/1 unauthorized，0transport/Popen/network/Torch/新GPU查询/active；不是AEF原生或资源PASS。','本轮0新candidate/模型revision/sourcecommit/准入/入队/训练启动；AEF保持validation和native/resources NOT_RUN，current_resource_check blocked不增加exclusive槽位hold，原BEC继续训练。','仅AEF/BEC研究记录与七段memory/notes更新，其他140候选/14生命周期账/primary026c/28用户文件status+bytes/index保持。'], 'decisions':['截至18:03:58Z begin原监控partial Best.4390/6of50/noimprove0of10，与18:08真实步数增长分开记录；尚无新champion或最终效果，目标.5100/M95.5020/gap.0080不变。','已有完整AEF工具可以跨tick静态复用，真实M95/AEF TRAIN2+资源必须等待唯一GPU0自然空闲后fresh currentowner/原deadline/源资产/UUID/三锁；静态release不是执行lease，不以旧binding重放或借BEC结果。','无新审批/用户动作，不恢复M206/BFC/CTS或旧held；后续按真实资源变化推进现成AEF，不为了填队列制造新准备工作。本次postflight/finish仍待root实际执行，不预报成功。']}
  before={'work_sha256':sha(wp),'memory_sha256':sha(mp)}
  before_record={'owner_token':TOKEN,'hashes':before,'protected_snapshot':pre,'AEF_before':next(c for c in work['candidates'] if c['id']==AEF),'BEC_before':next(c for c in work['candidates'] if c['id']==BEC),'tick_attempt_before':work.get('tick_attempt')}
  wb,mb=encoded(out),memory.encode('utf8');nb=encoded(notes)
  intent={'owner_token':TOKEN,'recorded_at':now,'scope':'Only existingAEF actual statictool/resource metadata and currentBEC progress; compactmemory','before':before,'proposed_work_sha256':hashlib.sha256(wb).hexdigest(),'proposed_memory_sha256':hashlib.sha256(mb).hexdigest(),'partial_failure_policy':'No automatic replay or rollback; reconcile exact journal and bytes.'}
  result={'recorded_at':now,'owner_token':TOKEN,'candidate_count':142,'new_candidates':0,'other140_candidates_unchanged':True,'all14_lifecycle_ledgers_unchanged':True,'primary026c_protected28_status_bytes_and_index_unchanged':True,'AEF_source_commit':SOURCE,'AEF_stage':'validation','AEF_native_resources':'NOT_RUN','actual_resource_check':ref(HERE/'aef_actual_local_guard.json'),'new_source_commits':0,'new_training_launches':0,'memory_lines':len(memory.splitlines()),'work_sha256':hashlib.sha256(wb).hexdigest(),'memory_sha256':hashlib.sha256(mb).hexdigest(),'notes':{'path':(HERE/'report_notes.json').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(nb).hexdigest()},'canonical_finish_or_postflight_claimed':False}
  # ALL payloads are serialized before the first durable journal or shared write.
  bb,ib,rb=encoded(before_record),encoded(intent),encoded(result)
  guard();assert sha(wp)==before['work_sha256'] and sha(mp)==before['memory_sha256']
  assert not any((HERE/n).exists() for n in ['completion_intent.json','completion_before.json','completion_result.json','completion_memory_before.md','completion_preflight_metrics_source.json','report_notes.json'])
  exclusive_bytes(HERE/'completion_before.json',bb);exclusive_bytes(HERE/'completion_memory_before.md',memory_old);exclusive_bytes(HERE/'completion_preflight_metrics_source.json',pfb);exclusive_bytes(HERE/'completion_intent.json',ib)
  guard();assert sha(wp)==before['work_sha256'] and sha(mp)==before['memory_sha256']
  replace_bytes(wp,wb);replace_bytes(mp,mb);exclusive_bytes(HERE/'report_notes.json',nb)
  post=snapshot();assert all(post[k]==pre[k] for k in ['head','index_empty','status_hex','files','protected_ledgers'])
  assert read(wp)==out and others(read(wp))==others(work) and mp.read_bytes()==mb
  assert len(post['candidate_digests'])==142 and set(post['candidate_digests'])==set(pre['candidate_digests']) and all(v==pre['candidate_digests'][k] for k,v in post['candidate_digests'].items() if k not in (AEF,BEC))
  guard();exclusive_bytes(HERE/'completion_result.json',rb)
  print(json.dumps({'status':'ACTUAL_AEF_TOOLS_AND_RESOURCE_REFUSAL_RECORDED_NOT_NATIVE_PASS','result':ref(HERE/'completion_result.json'),'memory_lines':len(memory.splitlines())},ensure_ascii=False))
 finally:lock.close()
if __name__=='__main__':main()
