"""Record the honest capacity-gap disposition mismatch before explicit abort."""
import copy
import repair

c = repair.c
ROOT, OUT = repair.ROOT, repair.OUT
c.guard(60)
message = 'Capacity gap remains: continue an executable candidate (including a newly created diagnosis candidate) or document a valid design-cycle stop reason'
failure = c.save('closure_failure.json', {
    'recorded_at': c.now(), 'token': c.TOKEN, 'postflight_passed': False,
    'failed_check': message, 'scientific_test_execution_completed': True,
    'candidate_scientific_result': 'R3 failed; no admission or training',
    'reason_not_retried': 'No new independent tested hypothesis or truthful global stop certificate was produced. Scoped final PCE repair is complete and further PCE edits are forbidden without new scope. Do not invent filler candidates, resource blocks, phase holds or an elapsed deadline; preserve the mismatch and abort.',
    'same_scope_permission_requested_again': False,
    'next_independent_work': 'A separately evidenced, prediction-blind point-feature diagnosis under existing mainline scope, without reopening historical routes or renaming the failed PCE patch.'})
work = c.tick.load(ROOT / 'pipeline/research_work.json')
candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
before = copy.deepcopy(candidate)
candidate['evidence'].extend([c.evidence(failure), c.evidence(__file__)])
repair.closure.validate_revisions(ROOT, candidate, before)
c.tick.save(ROOT / 'pipeline/research_work.json', work)
memory = ROOT / 'pipeline/codex_memory.md'
text = memory.read_text(encoding='utf-8')
text = text.replace('Scientific tests finished; tick finish not yet claimed.',
    'Scientific tests finished; finishFAILED capacity-gap disposition (no valid independent candidate/stopcertificate). Explicit abort planned; no COMPLETED claim.')
text += '\n- Currentfinish actuallyFAILED: '+message+'. Archiveclosure_failure.json; do not replay unchangedfinish. Canonicalreportupdated beforeexplicitabort; verify ownedlease/pendingabsence andINCOMPLETEreceipt. No postreleasewrites.\n'
assert len(text.splitlines()) < 120
memory.write_text(text, encoding='utf-8')
notes = c.tick.load(OUT / 'report_notes.json')
notes['actions'].append('收尾校验实际失败：容量缺口仍缺可执行独立候选或有效design-cycle停止依据；已保存closure_failure.json。本轮科研测试完成，流水线未通过，准备显式abort并核实释放。')
notes['decisions'].append('不重放同证据finish、不延长deadline、不改checker、不声称资源阻塞/全局穷尽；保留失败与后续独立点特征诊断缺口，按INCOMPLETE收尾。')
c.save('report_notes_final.json', notes)
print('Exact closure failure and pre-abort disposition saved; lease still owned.')
