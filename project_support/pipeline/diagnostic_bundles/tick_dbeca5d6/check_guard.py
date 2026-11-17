"""Read-only busy-card refusal check; no execution lease or GPU acquisition."""
import json
from ops import guard,ssh,save,STAGE

guard()
program='''import sys,json
sys.path.insert(0,%r)
from native_runtime import observe,HANDLES
try:
 observe(True)
 record={'expected_refusal':False,'locks_acquired':len(HANDLES)}
except AssertionError as error:
 record={'expected_refusal':True,'reason':str(error),'locks_acquired':len(HANDLES),'torch_imported':'torch' in sys.modules}
print(json.dumps(record))
'''%STAGE
record=ssh(program)
save('occupied_guard_precheck.json',record)
save('orchestration_quote_failure.json',{'error':'Local inline command SyntaxError:unterminated string literal before remote guard command;replaced by explicit script','remote_calls':0,'cuda_calls':0,'scientific_test':'not_run_in_failed_command'})
assert record['expected_refusal'] and record['locks_acquired']==0 and record['torch_imported'] is False
print(json.dumps(record))
