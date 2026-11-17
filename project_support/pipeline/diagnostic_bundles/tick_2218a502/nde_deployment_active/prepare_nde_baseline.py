"""Default NOP. Root-only read-only snapshot into this tick; never deploys or launches."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=Path("D:/project/cluster_project")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute-root",action="store_true");a=p.parse_args()
    if not a.execute_root:
        print(json.dumps({"status":"DEFAULT_NOP_NO_SNAPSHOT_OR_MUTATION"}));return
    spec=importlib.util.spec_from_file_location("nsd_deploy_snapshot_guard",HERE/"deploy_nde.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.guard(90)
    assert m.sha(__file__)==m.read(HERE/"FROZEN.json")["files"]["prepare_nde_baseline.py"]
    original=m.read(m.TICK/"protected_assets_before.json")
    assert original["head"]==m.BASE and len(original["files"])==28 and original["cached_paths_count"]==0
    assert m.git("rev-parse","HEAD").decode().strip()==m.BASE
    status=m.git("status","--porcelain=v1","--untracked-files=all","-z")
    assert status.hex()==original["status_hex"]
    assert not m.git("diff","--cached","--name-only","-z")
    dirty={n:m.sha(m.CODE/n) for n in original["files"]}
    assert dirty==original["files"]
    names={"SERVERS.yaml","pipeline/goal.json","pipeline/closure_policy.json","pipeline/execution_mode.json", "pipeline/queue.json","pipeline/running.json","pipeline/experiments.csv","pipeline/research_work.json","pipeline/codex_memory.md"}
    names.update("pipeline/"+n for n in original["protected_ledgers"])
    names.update(original["fixed_configs"])
    for group in ("WFC_source_paths","LFT_source_paths"):
        names.update("Cluster/"+n for n in original[group])
    protected={n:m.sha(ROOT/n) for n in sorted(names) if (ROOT/n).is_file()}
    index=Path(m.git("rev-parse","--git-path","index").decode().strip())
    if not index.is_absolute():index=m.CODE/index
    assert m.sha(index)==original["index_sha256"]
    value={"schema_version":1,"recorded_at":datetime.now(timezone.utc).isoformat(),"owner":m.EXPECTED,"main_head":m.BASE,"dirty_files":dirty,"protected_project_files":protected,"status_sha256":hashlib.sha256(status).hexdigest(),"index_sha256":m.sha(index),"index_entries_sha256":hashlib.sha256(m.git("ls-files","--stage","-z")).hexdigest(),"original_protected_assets":m.ref(m.TICK/"protected_assets_before.json"),"source_or_shared_mutation":False}
    m.guard(30);dest=m.TICK/"nde_deployment_baseline.json"
    with dest.open("x",encoding="utf8",newline="\n") as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write("\n")
    print(json.dumps({"status":"BASELINE_RECORDED_ONLY","baseline":m.ref(dest),"user_files":len(dirty),"protected_files":len(protected)}))
if __name__=="__main__":main()
