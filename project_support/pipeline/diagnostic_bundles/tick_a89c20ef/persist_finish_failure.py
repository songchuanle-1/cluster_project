"""Persist the actual failed check before aborting the owning lease."""
from datetime import datetime,timezone
import shutil
from ops import *

owner=guard()
receipt=ROOT/'pipeline/tick_receipts'/str(TOKEN+'.json')
value=tick.load(receipt)
assert value['status']=='INCOMPLETE' and value['context_committed'] is False
assert value['lease_release']=='retained' and value['closure_rc']==1
shutil.copyfile(receipt,OUT/'failed_finish_receipt.json')
failure={'observed_at':datetime.now(timezone.utc).isoformat(),
 'command':'foreground_tick.py cluster_project finish --token '+TOKEN,'returncode':1,
 'stdout':'CLOSURE_INCOMPLETE: Capacity gap remains: continue an executable candidate (including a newly created diagnosis candidate) or document a valid design-cycle stop reason\nPOSTFLIGHT FAILED: lease retained; continue this tick or explicitly abort',
 'context_committed':False,'lease_release':'retained',
 'real_deadline_at':owner['deadline_at'],
 'remaining_seconds':(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds(),
 'honest_disposition':'Two finite diagnostics complete,not two independent rejected/blocked scientific routes;no valid global exhaustion/resource/phase/deadline assertion. Do not falsify stages or invent a new variant for closure.',
 'next_execution_action':'Abort this exact owned token once with specific reason,then verify lease and pending context absent;no post-release project writes.'}
save('finish_failure.json',failure)
for cid in (CID,'hierarchical-ancestry-cover-audit'):
    advance([OUT/'finish_failure.json',OUT/'failed_finish_receipt.json'],candidate_id=cid)
memory=ROOT/'pipeline/codex_memory.md'
text=memory.read_text(encoding='utf-8')
text+='- ACTUAL finish FAILED at04:43Shanghai:Capacity gap remains without continuingcandidate/validdesign-cycle stop;receiptINCOMPLETE/contextnotcommitted/lease retained. Failedreceipt andexacterror preserved. Plannednext:explicitabortonce andverifyrelease;do not claimabort alreadyoccurred from this prerelease memory.\n'
assert len(text.splitlines())<120
memory.write_text(text,encoding='utf-8')
notes=tick.load(OUT/'notes.json')
usage=value['usage']
notes['actions'].append('实际finish返回1：容量缺口研究没有可继续候选或合法design-cycle停止原因，postflight未通过，context未提交，租约暂保留。finish_failure.json及失败收据已归档。两项诊断的科学结果保留；本轮执行INCOMPLETE，不重试相同证据的finish，不修改校验器或等待截止，下一步对本令牌abort并核实释放。')
notes['actions'].append('失败收据用量窗口为上海时间04:12:41至04:43:06，仅33条当时可见响应：输入4378715（含缓存4276736）、输出42890（含推理17565），输入+输出4421605；未缓存输入101979。缓存和推理均为子集，不再重复相加，不是账单且不含窗口外记录。最终abort收据可能不同。收据实际产出为新候选记录2、变化记录6（含4项辅助保留复核）、证据引用21、训练/准入0，不代表6项实验或科学成功。')
notes['decisions'].append('规范finish实际失败，本轮不能称完成；按契约保存错误后abort一次并在任务中只读核实释放。科学诊断完成与流程未完整结束分开报告，不把server4空闲写成资源阻塞。')
save('notes_after_finish_failure.json',notes)
print(json.dumps({'failure_preserved':True,'execution_status':'INCOMPLETE','remaining_seconds':failure['remaining_seconds'],'abort_not_yet_executed':True}))
