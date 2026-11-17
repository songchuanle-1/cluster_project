"""Bounded rejection of one duplicate graph idea; never creates a candidate."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import os
import subprocess

ROOT=Path("D:/project/cluster_project")
HERE=Path(__file__).resolve().parent
REPO=ROOT/"Cluster"
OWNER_KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
DCE=ROOT/"pipeline/diagnostic_bundles/tick_01d9102a/new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce/directed_cavity.py"
TARGETS=("M211-BTC","M212-BCR","M218-HPC","M220-DCE","M224-SFC","M228-NEC","M230-HVD","M231-PSC","M232-NSD")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def save(name,value):
    p=HERE/name;assert p.resolve().is_relative_to(HERE.resolve())
    with p.open("x",encoding="utf8",newline="\n") as f:json.dump(value,f,indent=2);f.write("\n")
def guard():
    assert os.environ.get("CODEX_THREAD_ID")=="01a1b166-dcbf-7d01-b0cb-c85fff644605"
    o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    assert o["token"]=="eb827823f30543d8aa8609643034f996" and o["thread_id"]=="01a159c5-29ab-7a22-ba7f-e79174757253"
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    assert sha(ROOT/"pipeline/headless/.tick_context.json")==o["context_sha256"]
    assert sha(ROOT/"pipeline/headless/.tick_context_state.next.json")==o["pending_sha256"]
    return {k:o[k] for k in OWNER_KEYS}
def snapshot():
    git=["C:/Program Files (x86)/Git/cmd/git.exe","--no-optional-locks","-c","core.fsmonitor=false","-C",str(REPO)]
    env=dict(os.environ,GIT_OPTIONAL_LOCKS="0",GIT_TERMINAL_PROMPT="0")
    def query(*args):return subprocess.check_output(git+list(args),env=env,text=True,encoding="utf8",timeout=15).strip()
    index=Path(query("rev-parse","--git-path","index"))
    if not index.is_absolute():index=REPO/index
    original=read(HERE.parent/"protected_assets_before.json")
    return {"HEAD":query("rev-parse","HEAD"),"index_sha256":sha(index),
        "protected_28":{name:sha(REPO/name) for name in original["files"]},
        "SERVERS_sha256":sha(ROOT/"SERVERS.yaml")}

def main():
    owner=guard();before=snapshot()
    assert before["HEAD"]=="0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
    work=read(ROOT/"pipeline/research_work.json")
    records=[c for c in work["candidates"] if c.get("experiment_id") in TARGETS]
    assert len(records)==len(TARGETS)
    history=[{k:c[k] for k in ("id","experiment_id","stage","hypothesis","source_preparation","config","code_commit") if k in c} for c in records]
    text=DCE.read_text(encoding="utf8")
    assert sha(DCE)=="a8141fe8a86d9846bdd2a812a9d3d8be99dc48b6485b206e0900c1ba6f8ad55e"
    tree=ast.parse(text)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_cavity_plan")
    pure={}
    exec(compile(ast.Module(body=[node],type_ignores=[]),"actual_existing_DCE_plan","exec"),pure)
    p=pure["build_cavity_plan"]([0,1,2,3,4],[0,0,1,2,2],[0,0,1],[5,3,2])
    checks=[]
    def check(name,value):
        assert value,name
        checks.append({"name":name,"passed":True})
    check("actual_existing_DCE_fine_parent_groups",p["fine_groups"]==[[0,1],[2],[3,4]])
    check("actual_existing_DCE_middle_parent_groups",p["middle_groups"]==[[0,1],[2]])
    check("existing_exclusive_sibling_schedule_matches_screened_idea",
        [[j for j in group if j!=i] for group in p["middle_groups"] for i in group]==[[1],[0],[]])
    check("existing_exclusive_fine_schedule_matches_screened_idea",
        [[j for j in group if j!=i] for group in p["fine_groups"] for i in group]==[[1],[0],[],[4],[3]])
    check("actual_DCE_source_already_has_both_directed_exclusions",
        "other_middle=exclusive_group_sums(up,mg)" in text
        and "other_fine=exclusive_group_sums(z[0],fg)" in text
        and "down_middle=self.activation" in text
        and "down_root=self.activation" in text)
    try:pure["build_cavity_plan"]([5],[0,0,1,2,2],[0,0,1],[5,3,2])
    except ValueError:check("actual_existing_DCE_invalid_membership_refused",True)
    else:raise AssertionError("Invalid membership accepted")
    unused=not any(str(c.get("experiment_id","")).startswith("M233") for c in work["candidates"])
    check("no_M233_registered_in_current_candidate_ledger",unused)
    check("protected_primary_index28_and_SERVERS_unchanged",snapshot()==before)
    guard()
    result={"schema_version":1,"status":"NO_SUITABLE_NEW_VARIANT_DUPLICATE_GRAPH_REJECTED_BEFORE_CANDIDATE_CREATION",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"owner":owner,
        "scope":"One bounded structural idea screened against full current goal bans and nine relevant historical graph hypotheses; actual existing DCE pure planner exercised with stdlib. No Tensor/model/autograd execution.",
        "screened_idea":{"description":"Recipient-specific hierarchy junction messages: summarize children upward and send parent/sibling context downward after excluding each reverse incoming branch before the nonlinear readout.",
            "candidate_id":None,"experiment_id":None,"decision":"DO_NOT_CREATE",
            "reason":"The defining reverse-edge-exclusion schedule and original three-level information-flow graph already exist in M220-DCE. M211-BTC and M212-BCR also cover sibling/complement summaries. Rephrasing recipient complement or changing its statistic is insufficient to justify a new independent graph.",
            "scientific_scope":"Rejecting a duplicate proposal does not refute the existing DCE mechanism or infer efficacy from its software properties."},
        "other_screening_constraints":[
            "A moment, curvature or contrast statistic substituted into HVD/PSC/NSD is not a justified new information-flow graph.",
            "A fixed hierarchy consistency solve overlaps HPC; generic synchronous node/edge feedback overlaps SFC/NEC.",
            "No new fixed-TRAIN error or task-response evidence here distinguishes another structural hypothesis; no data resampling or efficacy claim is invented.",
            "No routing, attention-pooling, residual-family, repeated injection, large Q/K/V/O, single-operator or numerical-distribution variant is created."],
        "history_review":history,"goal_snapshot_ref":ref(ROOT/"pipeline/goal.json"),
        "actual_existing_DCE_source":ref(DCE),"actual_CPU_checks":checks,"check_count":len(checks),
        "M233_absent_from_current_candidate_ledger":unused,"M233_allocated_or_reserved":False,
        "new_candidate_count":0,"new_source_files":0,"new_YAML":0,"private_index_or_source_commit_created":False,
        "protected_snapshot":before,"native":"NOT_RUN","resources":"NOT_RUN","Torch_autograd":"NOT_RUN","SSH_GPU":False,
        "candidate_or_shared_ledger_written":False,"NSD_remains_first_for_actual_authorized_resources":True}
    save("decision.json",result)
    files={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob("*")) if p.is_file()}
    save("FROZEN.json",{"status":"AUTHOR_FROZEN_BOUNDED_VARIANT_REJECTION_NO_CANDIDATE",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"files":files,"author_will_not_write_further":True,
        "new_candidate_count":0,"source_or_native_execution":False})
    print(json.dumps({"decision":ref(HERE/"decision.json"),"FROZEN":ref(HERE/"FROZEN.json"),
        "check_count":len(checks),"new_candidate_count":0,"author_writes_stopped":True},indent=2))

if __name__=="__main__":main()
