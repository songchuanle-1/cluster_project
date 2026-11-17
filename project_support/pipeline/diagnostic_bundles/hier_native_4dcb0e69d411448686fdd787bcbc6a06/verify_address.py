"""Verify only the registered address changed and the monitor's probe now works."""
import copy
from datetime import datetime,timezone
import json
import shutil
import sys
import yaml
from run import BUNDLE,ROOT,TOKEN,guard,tick
guard()
before=yaml.safe_load((BUNDLE/'servers_snapshot.yaml').read_text(encoding='utf-8'))
after=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))
assert before['servers']['server-3']['host']=='192.168.1.194'
assert after['servers']['server-3']['host']=='192.168.1.120'
identity=tick.load(BUNDLE/'target_inventory_result.json')
assert identity['verified_current_ip']=='192.168.1.120' and identity['hostname']=='sysu311-MS-7C59'
assert 'GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0' in identity['gpu']
comparison=copy.deepcopy(after)
comparison['servers']['server-3']['host']='192.168.1.194'
assert comparison==before,'Unrelated resource configuration changed.'
assert not (BUNDLE/'address_repair.json').exists()
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import pipeline_monitor as monitor
response=monitor.ssh('192.168.1.120','songcl','echo ok')
assert response=='ok',repr(response)
shutil.copy2(ROOT/'SERVERS.yaml',BUNDLE/'servers_after.yaml')
record={'token':TOKEN,'observed_at':datetime.now(timezone.utc).isoformat(),
    'old_ip':'192.168.1.194','new_ip':'192.168.1.120',
    'old_direct_ssh_result':'Connection timed out; actual tool observation 2026-10-16T08:54:29+08:00',
    'new_direct_ssh_hostname':'sysu311-MS-7C59','pinned_gpu_uuid':'GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0',
    'monitor_connection_probe':response,'full_monitor_reexecuted':False,
    'only_server3_host_field_changed':True,'all_whitelists_capacities_and_other_fields_unchanged':True,
    'goal_sha256_unchanged':tick.digest(ROOT/'pipeline/goal.json'),
    'before_sha256':tick.digest(BUNDLE/'servers_snapshot.yaml'),
    'after_sha256':tick.digest(BUNDLE/'servers_after.yaml'),
    'scope':'Connection-address correction for the same pinned server/GPU, not a new allocation or scheduler/policy change.'}
guard()
tick.save(BUNDLE/'address_repair.json',record)
print(json.dumps(record,indent=2))
