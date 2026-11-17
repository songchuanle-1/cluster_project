"""Actual local CLI rejection under an in-process process/network/Torch fence."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
from contextlib import redirect_stderr, redirect_stdout

OUT=Path(__file__).resolve().parent
ORIGIN=OUT.parent
parser=argparse.ArgumentParser()
parser.add_argument('--output',required=True)
args=parser.parse_args()
target=OUT/args.output
assert target.parent.resolve()==OUT.resolve() and not target.exists()
assert not (ORIGIN/'adapter_release.json').exists()
assert not (ORIGIN/'native/native_manifest.json').exists()
events=[]


def fence(event,values):
    if event in ('subprocess.Popen','os.system','socket.connect'):
        events.append(event);raise AssertionError('Real process/network forbidden')
    if event=='import' and values[0].split('.')[0]=='torch':
        events.append('import torch');raise AssertionError('Torch forbidden')
    if event=='open' and isinstance(values[0],(str,bytes)):
        path,mode,flags=values[:3]
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(1|2|64|512|1024))
        if writing:assert Path(path).resolve()==target.resolve(),'Unexpected file write'
    if event in ('os.mkdir','os.remove','os.rmdir'):
        raise AssertionError('No mutation permitted by entry checks')


sys.addaudithook(fence)
cases=[]
commands=[[],['prepare','--gpu','2'],['probe','--gpu','-1'],['probe'],
          ['run','--mode','invalid','--target','candidate'],['prepare','--gpu','0'],['prepare','--gpu','1']]
for arguments in commands:
    stdout=io.StringIO();stderr=io.StringIO();error=None
    saved=sys.argv;sys.argv=[str(ORIGIN/'adapter.py'),*arguments]
    try:
        with redirect_stdout(stdout),redirect_stderr(stderr):
            runpy.run_path(str(ORIGIN/'adapter.py'),run_name='__main__')
    except BaseException as found:
        error={'class':type(found).__name__,'message':str(found)}
    finally:sys.argv=saved
    assert error is not None,'Unexpected execution success'
    assert error['class'] in ('SystemExit','Refused'),error
    cases.append({'argv':arguments,'refused':True,'exception':error,'stderr_tail':stderr.getvalue()[-1200:],'stdout':stdout.getvalue()})
assert not events and 'torch' not in sys.modules
assert not (ORIGIN/'adapter_release.json').exists()
result={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),
    'scope':'ACTUAL_LOCAL_CLI_REFUSAL_ONLY_NO_EXTERNAL_RELEASE_OR_ACTIVE_MATERIAL',
    'source_sha256':hashlib.sha256((ORIGIN/'adapter.py').read_bytes()).hexdigest(),
    'cases':cases,'case_count':len(cases),'process_network_torch_events':events,
    'native_resources_transport':'NOT_RUN','no_execution_directory_created_by_check':True,
    'limits':'Current real candidate still refers to its prior disabled preparation, and this package has no external static release anchor. Prepare refusals are not a fresh registered-busy integration proof and not a hardware observation.'}
with target.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'cases':len(cases),'events':events,'proof_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
