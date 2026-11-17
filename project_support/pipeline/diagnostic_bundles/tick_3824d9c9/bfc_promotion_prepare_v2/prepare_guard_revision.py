"""Local V2 safety-only revision; preserve frozen V1, no operation is enabled."""
from pathlib import Path
import ast
import hashlib

HERE=Path(__file__).resolve().parent
V1=HERE.parent/'bfc_promotion_prepare'
assert hashlib.sha256((V1/'preparation.json').read_bytes()).hexdigest()=='82d11e19477cafb96c7578722f074aa782ebf74efeb52e23406cc9a7d21f8a53'
for name in ('promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py'):
    with (HERE/name).open('xb') as stream:stream.write((V1/name).read_bytes())

path=HERE/'promotion_common.py';text=path.read_text(encoding='utf-8')
node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='protected_lifecycle')
lines=text.splitlines(keepends=True)
replacement='''
def physical_gpu(value):
    """Accept only explicit physical0or1 integer/string, never bool/coercion."""
    if type(value) is int and value in (0,1):return value
    if type(value) is str and value in ('0','1'):return int(value)
    raise RuntimeError('Unknown or malformed physical GPU assignment; no bool/string coercion')


def running_assignments():
    running=read(ROOT/'pipeline/running.json')
    require(type(running) is dict,'Malformed running registry')
    assignments=[];seen=set();known={'M211-BTC','M212-BCR',EXP}
    for server,gpus in running.items():
        require(type(server) is str and type(gpus) is dict,'Malformed server/GPU running map')
        for raw_gpu,eid in gpus.items():
            require(server=='server-4','Unknown nonempty running server; reconcile first')
            gpu=physical_gpu(raw_gpu)
            require((server,gpu) not in seen and type(eid) is str and eid in known,'Unknown/duplicate/malformed active running assignment')
            seen.add((server,gpu));assignments.append((server,gpu,eid))
    require(len({eid for _,_,eid in assignments})==len(assignments),'Same experiment reserved on multiple cards')
    return sorted(assignments)


def protected_lifecycle(queue=None):
    """Exact original active identities or explicit canonical terminal states."""
    queue = read(ROOT/'pipeline/queue.json') if queue is None else queue
    assignments=running_assignments()
    expected = {
        'M211-BTC':('00e2b18c6b8d568a64edb496e6979d766440883c','93756329046cf30357c258848d6b3287c25b4b0c96ef69b0ffd5f3b8710f2a36',2784474,0),
        'M212-BCR':('11a811618179ab1ddc0cee299194667413b7fdb9','b8532405ba05101355898016aeeb45e1776217bc95a64a2ae449c1ff02ef60ac',1215422,1),
    }
    terminal={'done_complete','done_earlystop'}
    result={}
    for eid,(commit,receipt_sha,pid,gpu) in expected.items():
        rows=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')==eid]
        require(len(rows)<=1,'Duplicate protected experiment row')
        exp_path=ROOT/'pipeline/experiments'/str(eid+'.json');experiment=read(exp_path)
        require(experiment['id']==eid and experiment['code_commit']==commit,'Protected experiment identity changed')
        receipt_relative='pipeline/admissions/'+eid+'.json';receipt_path=ROOT/receipt_relative
        require(sha(receipt_path)==receipt_sha,'Protected original receipt changed')
        reserved=[item for item in assignments if item[2]==eid]
        if rows:
            row=rows[0]
            require(row['code_commit']==commit and row['admission_receipt']==receipt_relative and physical_gpu(row['gpu'])==gpu,'Protected row source/receipt/physical GPU differs from original admitted experiment')
            if row['status']=='running':
                require(type(row.get('pid')) is int and row['pid']==pid and row.get('launch_verified') is True and experiment['status']=='running','Uncertain or replaced protected active process; reconcile first')
                require(reserved==[('server-4',gpu,eid)],'Protected original active row/running mapping disagree')
            else:
                require(row['status'] in terminal and experiment['status']==row['status'] and not reserved,'Unexpected old-row state or terminal experiment still reserved')
        else:
            require(experiment['status'] in terminal and not reserved,'Missing old row requires explicit canonical terminal status and no remaining reservation')
        result[eid]={'queue_rows':copy.deepcopy(rows),'experiment_sha256':sha(exp_path),'receipt_sha256':receipt_sha}
    paused=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')=='M206-CGCA']
    require(len(paused)==1 and paused[0].get('dispatch_hold') and paused[0].get('resume_authorized') is False,'M206 user pause cannot be resumed by resource authorization')
    require(not any(item[2]=='M206-CGCA' for item in assignments),'Paused M206 must not be registered active')
    result['M206-CGCA']={'queue_rows':copy.deepcopy(paused),'experiment_sha256':sha(ROOT/'pipeline/experiments/M206-CGCA.json')}
    result['other_running_mappings']=[(server,str(gpu),eid) for server,gpu,eid in assignments if eid!=EXP]
    return result
'''
text=''.join(lines[:node.lineno-1])+replacement.strip()+'\n'+''.join(lines[node.end_lineno:])
path.write_text(text,encoding='utf-8',newline='\n')

path=HERE/'dispatch_bfc.py';text=path.read_text(encoding='utf-8')
text=text.replace("str(task['gpu'])==str(SELECTED_GPU)","common.physical_gpu(task['gpu'])==SELECTED_GPU")
text=text.replace("common.require(all(str(t['gpu'])!=str(SELECTED_GPU) for t in active)","common.require(all(common.physical_gpu(t['gpu'])!=SELECTED_GPU for t in active)")
old="""        registered=monitor.load_running(str(ROOT)).get('server-4',{})
        common.require(str(SELECTED_GPU) not in registered and all(eid in ('M211-BTC','M212-BCR') for eid in registered.values()),'Selected or unknown registered running mapping remains; no overwrite')
        busy={str(t['gpu']) for t in active}"""
new="""        registered=common.running_assignments()
        common.require(not any(server=='server-4' and gpu==SELECTED_GPU for server,gpu,eid in registered),'Selected running mapping remains; no overwrite')
        common.require(all(eid in ('M211-BTC','M212-BCR') for server,gpu,eid in registered),'Unknown/new registered task requires reconciliation first')
        busy={str(common.physical_gpu(t['gpu'])) for t in active}"""
assert old in text;text=text.replace(old,new)
old="""        after=monitor.load_queue(str(ROOT));final=next(t for t in after['gpu_queues']['server-4'] if t['id']==EXP)
        common.require(common.protected_lifecycle(after)==lifecycle_before,'Protected BTC/BCR/M206 queue/experiment/receipt or other running mapping changed')"""
new="""        after=monitor.load_queue(str(ROOT));final=next(t for t in after['gpu_queues']['server-4'] if t['id']==EXP)
        common.require(common.physical_gpu(final['gpu'])==SELECTED_GPU,'Canonical target moved off its actual selected binding')
        target_mappings=[item for item in common.running_assignments() if item[2]==EXP]
        common.require(not target_mappings or target_mappings==[('server-4',SELECTED_GPU,EXP)],'Target reserved on a nonselected card')
        common.require(common.protected_lifecycle(after)==lifecycle_before,'Protected BTC/BCR/M206 queue/experiment/receipt or other running mapping changed')"""
assert old in text;text=text.replace(old,new)
path.write_text(text,encoding='utf-8',newline='\n')
for name in ('promotion_common.py','fast_forward_tested_bfc.py','dispatch_bfc.py'):ast.parse((HERE/name).read_text(encoding='utf-8'))
print('V2 guard-only private sources created; V1 unchanged and execution remains disabled')
