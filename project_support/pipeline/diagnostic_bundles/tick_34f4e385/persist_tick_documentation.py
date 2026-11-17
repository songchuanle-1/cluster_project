"""Root-only factual memory/report notes and optional unexecuted tool-prep binding."""
from pathlib import Path
from datetime import datetime, timezone
import sys
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
WFC='hierarchy-wedge-factor-incidence-composition'

def main():
    guard();sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        guard();base=u.read(HERE/'protected_assets_before.json')
        u.primary_protection(base);u.lifecycle_protection(base)
        workpath=ROOT/'pipeline/research_work.json';memorypath=ROOT/'pipeline/codex_memory.md'
        before=sha(workpath);work=u.read(workpath)
        assert u.read(HERE/'source_reserve_final_record_result.json')['work_after_sha256']==before
        others={c['id']:u.digest(c) for c in work['candidates'] if c['id']!=WFC}
        candidate=next(c for c in work['candidates'] if c['id']==WFC)
        assert candidate['stage']=='validation'
        notes=u.read(HERE/'final_report_notes_base.json')
        occ=u.read(HERE/'source_reserve_gpu_occupation_validation.json')
        assert all(not s['state']['idle_gpu_ids'] and s['state']['busy_gpu_ids']==[0,1] for s in occ['states'])
        notes['actions'].append('本轮'+occ['observed_at']+' 新鲜只读物理查询核实server4 GPU0/1的固定UUID及两原训练compute PID，canonical validated_state复算两卡busy/无idle；原训练不被驱逐，源码储备等待真实空卡做原生检查。')
        toolpath=HERE/'wfc_native_prepare/preparation.json'
        toolrefs=[]
        tool_note='WFC原生工具仍未完成；下轮保留已写DRAFT，先续做检查脚本准备。'
        if toolpath.exists():
            tool=u.read(toolpath)
            assert tool['candidate_id']==WFC and tool['code_commit']==candidate['code_commit']
            assert tool['source_files']==u.read(HERE/'new_candidate_prepare/preparation.json')['source_files']
            assert tool['draft_execution_disabled'] and tool['operational_ready'] is False
            assert tool['native']==tool['resources']=='NOT_RUN'
            for name,value in tool['prepared_file_hashes'].items():assert sha(toolpath.parent/name)==value,name
            toolrefs.append(u.ref(toolpath))
            peerpath=HERE/'wfc_native_preparation_independent_review.json'
            if peerpath.exists():
                review=u.read(peerpath);assert review.get('material_concerns')==[]
                assert review['candidate_id']==WFC and review['anchors']['preparation']==u.ref(toolpath)
                toolrefs.append(u.ref(peerpath))
            for r in toolrefs:
                if r not in candidate['evidence']:candidate['evidence'].append(r)
            candidate['native_tool_preparation']=u.ref(toolpath)
            candidate['native_tool_preparation_review']=toolrefs[1] if len(toolrefs)>1 else None
            candidate['native_tool_status']='DRAFT_STATIC_ONLY_UNEXECUTED_REQUIRES_FRESH_OWNER_COMPATIBILITY_AND_IDLE_CARD_ACTIVATION'
            candidate['next_action']='Both physical authorized cards retain protected original SFC/ELC. Preserve source94 on parent18e and DRAFT-only native tool preparation; complete any pending tool review, bind actual then-current compatible source/manifest/fresh owner and genuine idle selected physicalGPU0 guard, then execute frozen paired natural TRAIN2 and original resources once per arm. Current draft selectsGPU0; if allowedGPU1 opens first, separately freeze/review the actual physical-card operational adaptation without model/protocol changes. No current native/resource PASS, receipt, queue or launch; no blind sibling source promotion or modification of original prototype6595.'
            tool_note='WFC原生工具准备已外置冻结并按实际独审状态绑定，仍为DRAFT/未执行，当前草案选GPU0；激活需下次真实owner、实际兼容版本及授权空卡。GPU1先空闲时另冻结实际物理卡适配，不改模型/协议；不能直接当作可运行实验或原生PASS。'
        notes['actions'].append(tool_note)
        notes['decisions'].append('原始GPU占用与工具证据和两个独立源码原型均已绑定；本轮不预签postflight，最终是否完成以foreground finish真实结果为准。')
        draft=(HERE/'final_memory_draft.md').read_text(encoding='utf-8')
        draft=draft.rstrip()+'\n- 本轮最新GPU查询 '+occ['observed_at']+' 确认原两任务仍物理占用GPU0/1；'+tool_note+'\n'
        assert len(draft.splitlines())<120
        u.check_refs(candidate['evidence'])
        u.save(HERE/'documentation_record_intent.json',dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),work_before_sha256=before,memory_before_sha256=sha(memorypath),draft=u.ref(HERE/'final_memory_draft.md'),tool_evidence=toolrefs,other152_digests=others,scope='Only WFC unexecuted tool refs/nextaction and seven-section current factual memory plus six-section report notes. No result/queue/source/launch changes.'))
        guard();assert sha(workpath)==before
        assert {c['id']:u.digest(c) for c in work['candidates'] if c['id']!=WFC}==others
        if toolrefs:u.atomic(workpath,work)
        u.atomic(memorypath,draft,text=True)
        u.save(HERE/'final_report_notes.json',notes)
        u.primary_protection(base);u.lifecycle_protection(base)
        assert {c['id']:u.digest(c) for c in u.read(workpath)['candidates'] if c['id']!=WFC}==others
        u.save(HERE/'documentation_record_result.json',dict(owner=EXPECTED,recorded_at=datetime.now(timezone.utc).isoformat(),work_sha256=sha(workpath),memory_sha256=sha(memorypath),memory_lines=len(draft.splitlines()),notes=u.ref(HERE/'final_report_notes.json'),tool_evidence=toolrefs,primary_user28_index_all34_lifecycle_unchanged=True,other152_unchanged=True,no_native_queue_or_launch=True))
        print('Factual memory and final report notes persisted; no postflight result pre-signed.')
    finally:lock.close()

if __name__=='__main__':main()
