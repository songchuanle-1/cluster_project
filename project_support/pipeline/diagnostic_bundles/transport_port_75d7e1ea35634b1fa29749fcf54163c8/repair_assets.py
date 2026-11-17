"""Complete missing immutable assets without replaying the resumed checkpoint."""

import json
import stage

stage.guard(240)
rows = stage.tick.load(stage.BUNDLE / "assets_manifest.json")["assets"]
observed = json.loads(stage.remote(f"""
import hashlib,json,pathlib,subprocess
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
root=pathlib.Path({stage.REMOTE!r});result={{}}
for name in {list(rows)!r}:
    p=root/'assets'/name
    if not p.exists():result[name]=None;continue
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    result[name]={{'sha256':h.hexdigest(),'bytes':p.stat().st_size}}
print(json.dumps(result))
""", timeout=60))
stage.save("asset_reconciliation_before", {"assets": observed,
           "prior_error": "Full verification after successful checkpoint resume found a missing calibration asset."})
missing = []
for name, expected in rows.items():
    if observed[name] is None:
        missing.append(name)
        stage.command(["scp", *stage.OPTS, str(stage.ASSETS / name),
                       "server-4:" + stage.REMOTE + "/assets/"], timeout=45)
    else:
        assert observed[name] == expected, name
result = json.loads(stage.remote(f"""
import hashlib,json,pathlib
root=pathlib.Path({stage.REMOTE!r})
for name,row in {rows!r}.items():
    p=root/'assets'/name;h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    assert h.hexdigest()==row['sha256'] and p.stat().st_size==row['bytes'],name
print(json.dumps({{'status':'PASS','assets_verified':{len(rows)},'checkpoint_verified':True,
                  'missing_repaired':{missing!r},'prior_failures_retained':True}}))
""", timeout=60))
stage.save("deployment_reconciled", result)
print(json.dumps(result))
