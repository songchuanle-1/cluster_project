"""Private exact final-record copy with the reviewed file-lock fix and current metadata."""
from pathlib import Path
from datetime import datetime,timezone
import ast,difflib,json,os
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def save(p,data):
    guard()
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def main():
    guard();origin=HERE/'final_hpc_tick_prepare';dest=HERE/'final_hpc_tick_execute'
    assert sha(origin/'finalize_hpc_tick.py')=='9fc00a79d86e294e74326f1cb9a76998630ddac4e66e3d869cfbb88f5ec04243'
    assert sha(origin/'actual_bindings.json')=='84163350551615db4753c5b17ffbf427fc284f2c1158de9d043c21a0999a3ec6'
    old=(origin/'finalize_hpc_tick.py').read_text('utf8');s=old
    for a,b in [('DRAFT_EXECUTION_DISABLED = True','DRAFT_EXECUTION_DISABLED = False'),
                ("HERE = TICK / 'final_hpc_tick_prepare'","HERE = TICK / 'final_hpc_tick_execute'"),
                ('finally: lock.release()','finally: lock.close()'),
                ('不读旧855/grant/checkpoint正文','不追读旧目标/grant/checkpoint正文')]:
        assert s.count(a)==1,a;s=s.replace(a,b,1)
    needle="        h=by[u.HPC]; a=by[u.APF]; assert h['stage']=='training' and h['code_commit']==SOURCE"
    extra="""
        h['source_status']='TESTED_HPC6282_PRESENT_IN_PRIMARY_AND_RUNTIME'
        h['next_action']='Monitor exact original M218 PID187081/source-runtime6282 on authorized GPU0 and native validation. Preserve old2f7 import failure/root-cause UNKNOWN; no replay/restart/tuning or GPU1.'
        h.setdefault('current_version_compatibility_history',[]).append(copy.deepcopy(h.get('current_version_compatibility')))
        h['current_version_compatibility']={'current_source_commit':SOURCE,'source_parent_commit':'d58576b396cfb54577652be972f3ffaffda508c9','current_primary_and_runtime':SOURCE,'status':'TESTED_SOURCE_PRESENT_IN_PRIMARY_AND_RUNTIME','scope':'Raw native manifest runtime parentd585 retained as historical actual test input; current canonical admitted training source/runtime6282 independently verified.'}
"""
    assert s.count(needle)==1;s=s.replace(needle,needle+extra,1)
    needle="        a['requires_current_runtime_compatible_copy']=True"
    extra="""
        a.setdefault('current_version_compatibility_history',[]).append(copy.deepcopy(a.get('current_version_compatibility')))
        a['current_version_compatibility']={'existing_source_commit':a['code_commit'],'existing_parent_commit':'d58576b396cfb54577652be972f3ffaffda508c9','current_primary_and_runtime':SOURCE,'status':'NEEDS_COMPATIBLE_SOURCE_AND_TOOL_METADATA_BEFORE_FUTURE_NATIVE','scope':'Preserve bf6/parentd585 source and frozen old native/op/NULL artifacts. Package unchanged nine files against actual current6282 with a new version proof; no sibling ff or borrowed test PASS.'}
"""
    assert s.count(needle)==1;s=s.replace(needle,needle+extra,1)
    needle="    loaded={k:u.read(ROOT/v['path']) for k,v in bound.items()}"
    assert s.count(needle)==1;s=s.replace(needle,needle+"\n    assert loaded['held']['owner']==EXPECTED and loaded['held']['unchanged'] is True",1)
    ast.parse(s);compile(s,str(dest/'finalize_hpc_tick.py'),'exec')
    bindings=u.read(origin/'actual_bindings.json')
    held=HERE/'held_boundary_observation.json';assert sha(held)=='5bc9be95d3636f942ce5150fc322eed6a936a5d42c5b053543bea4ba7a841c16'
    bindings['held']=u.ref(held);u.check_refs(list(bindings.values()))
    assert not dest.exists() and not (HERE/'hpc_final_activation.json').exists()
    diff=''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='draft9fc',tofile='root-enabled-current-records'))
    guard();dest.mkdir(exist_ok=False)
    save(dest/'finalize_hpc_tick.py',s.encode('utf8'))
    save(dest/'actual_bindings.json',(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n').encode())
    save(HERE/'hpc_final_activation.diff',diff.encode('utf8'))
    out={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
         'original_source':u.ref(origin/'finalize_hpc_tick.py'),'original_bindings':u.ref(origin/'actual_bindings.json'),
         'activated_source':u.ref(dest/'finalize_hpc_tick.py'),'activated_bindings':u.ref(dest/'actual_bindings.json'),
         'exact_diff':u.ref(HERE/'hpc_final_activation.diff'),
         'changes':['private execution directory and explicit DRAFT flag','actual file-lock close API','HPC live next action/source status/current compatibility','APF current6282 compatibility hold while frozen bf6 retained','bind actual unchanged held digest proof; remove unneeded historical evidence count'],
         'no_shared_state_source_queue_native_or_receipt_operation':True}
    save(HERE/'hpc_final_activation.json',(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps(out['activated_source']))
if __name__=='__main__':main()
