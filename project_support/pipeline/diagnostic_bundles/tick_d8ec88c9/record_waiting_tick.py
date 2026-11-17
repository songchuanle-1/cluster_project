"""Record a healthy occupied-resource check; no new research or launch claim."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='d8ec88c9fd7b431b9fbed041905a2596'
CID='hierarchy-parent-spectral-nonlinear-token-coupling'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,value):
    p=Path(p);tmp=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as f:
        if isinstance(value,str):f.write(value)
        else:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    obs=read(HERE/'hrc_training_progress_observation.json')
    assert obs['exact_original_process_and_native_progress_increasing']
    a,b=[row['data'] for row in obs['observations']]
    assert a['pid']==b['pid']==2780804 and a['starttime']==b['starttime']=='29604100'
    assert a['progress']==[17,50,485,4686] and b['progress']==[17,50,495,4686] and not b['errors']
    local=datetime.fromisoformat(obs['recorded_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    boundary=read(HERE/'waiting_boundary_check.json');assert boundary['material_concerns']==[]
    metrics=boundary['HRC_partial_metrics'];assert metrics['best_mIoU_4dp']==0.4883 and metrics['epoch']==17 and metrics['no_improve']==0
    holds=read(HERE/'held_boundary_check.json');assert holds['material_concerns']==[]
    assert sha(HERE/'held_boundary_check.json')=='988ae737e5240613bc1c1b6135b28da33ffa7b43fffdea9ecb4bd010e971a95c'
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        names=['queue.json','running.json','experiments/M208-HRC.json','experiments/M209-PSBR.json','experiments/M206-CGCA.json',
            'experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
        protected={name:sha(ROOT/'pipeline'/name) for name in names}
        work=read(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==CID)
        assert c['stage']=='blocked' and c['resume_stage']=='validation' and c['blocker_kind']=='exclusive_gpu_slot'
        assert c['code_commit']=='43dce016c1a1713c2a5dab7061810dc2efde8954' and c['native_execution_code_commit'] is None
        now=datetime.now(timezone.utc)
        evidence=[ref(HERE/'hrc_training_progress_observation.json'),ref(HERE/'waiting_boundary_check.json')]
        for item in evidence:
            if item not in c['evidence']:c['evidence'].append(item)
        c['blocker']='Only authorized physicalGPU0 occupied by original HRC2780804/start29604100, observed17/50 native485->495 at'+local+' Shanghai. Existing PSBR74f FIFO and primaryHEAD remain protected. Existing complete PSNC source43/operational preparation is reused; no new native slot.'
        c['last_resource_check_at']=now.isoformat();c['retry_after']=(now+timedelta(hours=1)).isoformat()
        hrc=next(c for c in work['candidates'] if c.get('experiment_id')=='M208-HRC')
        for item in evidence:
            if item not in hrc['evidence']:hrc['evidence'].append(item)
        work['historical_hold_boundary_review']=ref(HERE/'held_boundary_check.json')
        work['tick_attempt']={'tick_started_at':owner['generated_at'],'candidate_id':CID,'kind':'resource_check','result':'blocked',
            'command':'python -B pipeline/diagnostic_bundles/tick_d8ec88c9/observe_hrc_training.py',
            'observation':'Exact original HRC process/native17/50 steps485->495 on only allowedGPU0; no native slot. PSBR remains readywaiting74f; M206 paused/GPU1 released. Existing PSNC source43 and complete reviewed operational packet reused, no new scientific result or actionable change. Native/TRAIN/resources unrun.',
            'evidence':evidence}
        work['updated_at']=now.isoformat();save(ROOT/'pipeline/research_work.json',work)
        assert {name:sha(ROOT/'pipeline'/name) for name in names}==protected
        memory=(ROOT/'pipeline/codex_memory.md').read_text(encoding='utf-8').split('\n## Last Tick\n',1)[0]
        lines=memory.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('- 当前foreground'):
                lines[i]='- 当前foreground'+TOKEN+'；actual owner/target01a159c5-29ab-7a22-ba7f-e79174757253一致，generated22:12:37.878024UTC/原deadline23:12:37.878024不延长。前42ce已FINALIZED/released(04:27:04上海)且无headless lock/pending才begin；本轮随后真实report/finish/receipt确认，不预写PASS。'
            elif line.startswith('- HRC/PSBR最终训练效果'):
                lines[i]='- HRC/PSBR最终训练效果仍UNKNOWN；此前真实技术准入保留。PSNC已有独立source43和51项离线检查/独审的完整operational包；本轮只复查原训练进展/资源忙，不重复准备、测试或新增路线。数学/静态/模拟不代签native/资源。'
            elif line.startswith('- 当前2026-10-23 04:08:04'):
                lines[i]='- 当前'+local+'上海真实同HRC PID2780804/start29604100/原argv/cwd/remoteHEAD74f/GPU0 UUID，native17/50两次485→495/4686、logfresh无error，仅GPU0 HRC context；proof SHA'+sha(HERE/'hrc_training_progress_observation.json')+'。begin06:12监控partial best.4883/noimprove0，非终态/非champion。GPU1未查未用，无signal/新GPU计算。'
            elif line.startswith('- PSNC外置包'):
                lines[i]=line.replace('本轮独立完整operational包/static release','此前42ce完整operational包/static release')
            elif line.startswith('- PSNC当前blocked/'):
                lines[i]='- PSNC当前blocked/exclusive_gpu_slot/resumevalidation：已有实现/完整检查工具和静态modulehash release均保持，原42ce真实prepare占卡拒绝不重跑。当前HRC17/50占唯一GPU0，PSBR74f freshdispatch/primaryHEAD继续保护；只等资源/版本条件后freshbinding做原YAML TRAIN2+资源，未准入，不重复造工具或凑候选。'
        memory='\n'.join(lines)+'\n\n## Last Tick\n'
        memory+='- 本轮d8ec begin一次monitor/已有队列派发/goal，design/candidate1/creation1；1HRCrunning/0claiming/1readyPSBRwaiting，M206paused waiting另计，无新终态/运行故障。已有PSBR+PSNC两项具体准备，不为统计缺口新造变体。\n'
        memory+='- '+local+'上海核原HRC17/50步485→495增长、原PID/start/argv/HEAD/UUID/GPU0，资源busy实证；beginpartial best.4883/noimprove0，未完成且champion仍M95.5020/目标.5100/gap.0080。只观测原训练，无新native计算。\n'
        memory+='- PSBR仍waiting74f/nohold/noPID，receiptJSON c85ae4fe未变；主74f/index空，PSNC source43与原native/adapterprep和静态release小元数据hash吻合，沿用42ce审阅。未重hash标准artifact正文/完整packet/重跑51mock/工具guard，无新源变更/提交/sync/运行材料。M206暂停/GPU1让出，不重复问授权。\n'
        memory+='- 8due旧hold仅canonical metadata/引用清单签名/13授权path-size-mtime有界复核同d6，SHA'+sha(HERE/'held_boundary_check.json')+'；655正文/hash/stat复查0，grant正文未重读，范围局限明示。无新scope/reopen/extra revision/human行动，不改原失败和上限。\n'
        memory+='- 当前tick_attempt是真resource_check blocked，新增当前证据同归PSNC；0新模型候选/native/资源profile/receipt/queue/launch/commit/sync。只留本轮健康训练与忙卡事实，无新科学结论/完成/故障/需用户决定，DONT_NOTIFY。只读reader首用legacy可选experiment_id索引KeyError已修get，未改模型/阈值/共享账。\n'
        memory+='- 六段报告/七段memory后真实finish/FINALIZED released及headless lock/pending消失才确认；释放后不回写。不创建重复decision/全局穷尽/冷却，不改调度/白名单/目标/资源，继续既有FIFO和准备，空GPU0且PSBR版本安全才做fresh原生验证。\n'
        assert memory.count('\n## ')==7 and len(memory.splitlines())<120
        save(ROOT/'pipeline/codex_memory.md',memory)
        notes={'actions':[
            '实际会话与foreground target一致，已读canonical SKILL/experimentfirst/foreground/最新memory与goal/SERVERS；goalSHA0441、server4GPU0 max1/GPU1释放/M206暂停/WindowsDisabled保持。前42ce FINALIZED released且无headless lock/pending；原generated22:12:37.878024UTC/deadline23:12:37.878024不改。',
            'begin先monitor/派发已有合格队列/goal一次，operationalissues空、新终态0；1running/0claiming/1readyPSBRwaiting，M206人工paused另计。已有PSBR排队和PSNC完整具体准备，未为候选预算1重复设计或准备工具。',
            local+'上海额外只读核HRC原PID2780804/start29604100/原argv/cwd/HEAD74f/UUID，native17/50步485→495/4686，无error、logfresh/GPU0仅原HRC context。begin06:12partial best.4883/noimprove0，非最终效果/新champion。GPU1未查询/使用，无signal/新计算。',
            '资源仍busy，PSNC仅做当前resource_check blocked；沿用已有source43/完整operationalpacket/静态release。未重跑51mock/guard/旧native或改9源字节，不假造原生PASS。PSBR等待74f/nohold/PIDnull且receiptJSONhash未变；标准artifact正文沿用前42ce验证，不冒称本轮重检。主74f/index空，三个静态metadata/release anchor吻合。',
            '到期8旧hold仅核完整canonical元数据和声明path/hash清单签名、13授权path-size-mtime，无变化；不读/hash/stat655证据正文、不重读grant正文、不重开/增加修订/重复人类问题。M206原paused/GPU1释放保持。',
            '只读辅助reader首用legacy缺experiment_id记录出现KeyError，改为get后完成；失败发生在写artifact前，无模型、协议阈值、台账变更，修复范围如waiting_boundary_check.json所列。',
            '当前tick_attempt真实resource_check blocked证据同归PSNC；仅更新小范围候选当前资源事实/证据和七段memory。0新候选/native/资源profile/标准summary/receipt/queue/launch/Gitcommit/sync，既有queue/running/experiment/receipt字节保持。没有新科学结论、完成、失败或需处理事项，本轮DONT_NOTIFY。',
            '脚本生成完整六段报告后按原token真实finish与receipt/lease释放核验，不预写PASS、不在释放后回写。不写重复decision日志，不建全局穷尽/冷却，不改调度/资源/目标/原失败；下一步仍是等待GPU0与PSBR版本边界安全后用现成工具/freshbinding做真实原YAML TRAIN2+原资源。'
        ],'decisions':['延续既有授权、FIFO与资源等待；无新路线或操作决策，不生成重复decision日志。健康训练/等待状态未变且无可行动事项，静默。']}
        save(HERE/'tick_notes.json',notes)
        save(HERE/'waiting_tick_persistence.json',{'recorded_at':now.isoformat(),'token':TOKEN,'candidate_id':CID,'kind':'resource_check','result':'blocked',
            'evidence':evidence,'held_boundary_review':ref(HERE/'held_boundary_check.json'),'new_scientific_result':False,'notification':'DONT_NOTIFY',
            'protected_registry_unchanged':{name:sha(ROOT/'pipeline'/name)==expected for name,expected in protected.items()},'memory_lines':len(memory.splitlines())})
        print(json.dumps({'recorded':'occupied_resource_check_only','new_scientific_result':False,'notification':'DONT_NOTIFY',
            'native':'NOT_RUN','HRC_progress':[a['progress'],b['progress']],'HRC_partial_best':metrics['best_mIoU_4dp'],'memory_lines':len(memory.splitlines())},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
