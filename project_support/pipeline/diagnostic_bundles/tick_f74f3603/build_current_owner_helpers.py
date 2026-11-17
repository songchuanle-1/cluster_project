"""Minimal fresh-owner copy of reviewed NSD helpers; never execute their work."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT=Path("D:/project/cluster_project")
TICK=Path(__file__).resolve().parent
OLD=ROOT/"pipeline/diagnostic_bundles/tick_eb827823"
KEYS=("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")
AUTHOR="01a1b166-dcbf-7d01-b0cb-c85fff644605"
TOKEN="f74f3603193a426097a8dc288fd05fde"
THREAD="01a159c5-29ab-7a22-ba7f-e79174757253"
checks=[];ports=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):return {"path":Path(p).relative_to(ROOT).as_posix(),"sha256":sha(p)}
def check(name,value):
    assert value,name
    checks.append({"name":name,"passed":True})
def guard():
    assert os.environ.get("CODEX_THREAD_ID")==AUTHOR
    o=read(ROOT/"pipeline/headless/.foreground.lockdir/owner.json")
    assert o["token"]==TOKEN and o["thread_id"]==THREAD
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o["deadline_at"])
    assert all(sha(ROOT/"pipeline/headless"/n)==o[k] for n,k in (
        (".tick_context.json","context_sha256"),(".tick_context_state.next.json","pending_sha256")))
    return {k:o[k] for k in KEYS}
def save(p,v):
    guard();p=Path(p)
    assert p.resolve().is_relative_to(TICK.resolve())
    raw=v if isinstance(v,bytes) else (v.encode() if isinstance(v,str) else (json.dumps(v,indent=2,allow_nan=False)+"\n").encode())
    with p.open("xb") as f:f.write(raw)
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def freeze(folder,owner,extra):
    value={"status":"FROZEN_CURRENT_OWNER_HELPER_PREPARATION_PENDING_INDEPENDENT_REVIEW",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"owner_provenance_only":owner,
        "author_thread_id":AUTHOR,"files":{p.name:sha(p) for p in sorted(folder.iterdir()) if p.is_file()},
        "author_will_not_write_further":True,"actual_execution_material_created":False,
        "native":"NOT_RUN","resources":"NOT_RUN",**extra}
    save(folder/"FROZEN.json",value)
    check(folder.name+"_complete_frozen_hash_graph",all(sha(folder/n)==d for n,d in value["files"].items()))
    return ref(folder/"FROZEN.json")
def main():
    owner=guard();oldowner=read(OLD/"nsd_path_production_prepare/FROZEN.json")["owner_provenance_only"]
    pairs=[(oldowner[k],owner[k]) for k in KEYS if oldowner[k]!=owner[k]]
    pairs.append(("eb827823","f74f3603"))
    preserved={}
    for folder in ("nsd_result_prepare","nsd_path_production_prepare","nsd_path_production_transport"):
        p=OLD/folder/"FROZEN.json";f=read(p);preserved[str(p)]=sha(p)
        fm=f.get("files",f.get("files_sha256"));assert fm
        check("reviewed_producer_graph_"+folder,all(sha(p.parent/n)==d for n,d in fm.items()))
    nr=OLD/"nsd_result_independent_review.json";pr=OLD/"nsd_path_production_independent_review.json"
    check("both_producer_independent_reviews_PASS",read(nr)["passed"] is True and read(pr)["passed"] is True)
    for p in (nr,pr):preserved[str(p)]=sha(p)
    def port(text,label):
        original=text;used=[]
        for old,new in pairs:
            count=text.count(old)
            if count:text=text.replace(old,new);used.append({"from":old,"to":new,"count":count})
        recovered=text
        for old,new in pairs:recovered=recovered.replace(new,old)
        check(label+"_exact_inverse_metadata_diff",recovered==original)
        ports.append({"file":label,"replacements":used})
        return text
    N=TICK/"nsd_result_prepare";P=TICK/"nsd_path_production_prepare";T=TICK/"nsd_path_production_transport"
    for p in (N,P,T):p.mkdir()
    normalizer=port((OLD/"nsd_result_prepare/normalize_nsd_actual_results.py").read_text(encoding="utf8"),"normalizer")
    save(N/"normalize_nsd_actual_results.py",normalizer)
    m=load("current_owner_normalizer",N/"normalize_nsd_actual_results.py")
    check("normalizer_current_owner_execution_stage_and_source",
        m.TOKEN==TOKEN and m.EXECUTION==TICK/"nsd_execution" and m.ACTIVATION==TICK/"nsd_current_activation"
        and m.CID=="hierarchy-native-spatial-dirichlet-composition"
        and m.SOURCE=="f6257de79148581334ee495e6e2d60ccb525457c"
        and m.PARENT=="0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d")
    check("normalizer_exact_original_four_arms",m.PAIRS==(("smoke","champion"),("smoke","candidate"),("resources","champion"),("resources","candidate")))
    try:m.guard()
    except AssertionError:check("actual_child_normalizer_guard_refuses_without_spoof",True)
    else:raise AssertionError("Child entered root normalizer")
    for mode,target in m.PAIRS:
        value={"candidate_id":"hierarchy-native-spatial-dirichlet-composition",
            "code_commit":"f6257de79148581334ee495e6e2d60ccb525457c"}
        value.update(experiment_id="M232-NSD",goal_sha256="0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85",
            config="configs/Quard/ctf_hcg_csort_nsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd.yaml",
            mode=mode,target=target,model_package="framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"+("_nsd" if target=="candidate" else ""))
        m.validate_external_arm_identity(value,mode,target)
        check("actual_external_literal_fixture_"+mode+"_"+target,True)
        try:m.validate_external_arm_identity(dict(value,candidate_id="hierarchy-native-position-feature-cross-scatter-composition"),mode,target)
        except ValueError:check("actual_PSC_negative_fixture_"+mode+"_"+target,True)
        else:raise AssertionError("Wrong candidate accepted")
    check("worker_runtime_and_protocol_anchors_unchanged",
        sha(TICK/"nsd_current_activation/native/worker.py")=="cd1cb8b000b7109db99b7bb44b69867d1c3bb5e63466a749b51bb4d35fd09112"
        and sha(TICK/"nsd_current_activation/native/native_runtime.py")=="8ca969c6b4d7099fcf4e407d27ef979e93070a2be06f5f9784f3eed8a29c48f9")
    save(N/"README.md","Current-owner metadata adaptation of reviewed eb827823 NSD normalizer only. Exact original algorithm and all gates retained; root-only, never executed here. Requires all four actual same-owner arms, original requests/manifest/binding/lease, source/runtime/root/UUID/hash and common835/TRAIN2/core-gradient/resources evidence. No raw/results/PASS/admission was created. Missing or failed arms cannot create PASS. Independent review of this adaptation remains required.\n")
    save(N/"preparation.json",{"status":"CURRENT_OWNER_UNEXECUTED_NORMALIZER_PREPARATION_PENDING_REVIEW","owner":owner,
        "author_thread_id":AUTHOR,"candidate_id":m.CID,"source_commit":m.SOURCE,"runtime_commit":m.PARENT,
        "producer_FROZEN":ref(OLD/"nsd_result_prepare/FROZEN.json"),"producer_review":ref(nr),
        "normalizer":ref(N/"normalize_nsd_actual_results.py"),"current_native_preparation":ref(TICK/"nsd_current_activation/native/preparation.json"),
        "original_inputs_required":[a+"_"+b+"_execution.json" for a,b in m.PAIRS],
        "normalizer_root_only":True,"native":"NOT_RUN","resources":"NOT_RUN","actual_results_consumed":False,
        "native_resource_PASS_artifacts_created":False,"independent_review":"PENDING_EXTERNAL"})
    controller=port((OLD/"nsd_path_production_prepare/production_controller.py").read_text(encoding="utf8"),"controller")
    save(P/"production_controller.py",controller)
    for name in ("lock_core.py","entry_factory.py"):
        save(P/name,(OLD/"nsd_path_production_prepare"/name).read_bytes())
        check(name+"_proved_bytes_unchanged",sha(P/name)==sha(OLD/"nsd_path_production_prepare"/name))
    files={n:sha(P/n) for n in ("production_controller.py","lock_core.py","entry_factory.py")}
    for action in ("collect","render"):
        req=json.loads(port((OLD/"nsd_path_production_prepare"/(action+"_request.draft.json")).read_text(),action+"_draft"))
        req["files"]=files
        save(P/(action+"_request.draft.json"),req)
        check(action+"_draft_disabled_current_owner_and_hashes",
            req["owner"]==owner and req["files"]==files and not req["execution_authorized"]
            and not req["training_launch_authorized"] and req["actual_deployment_observed"] is False)
    activation=json.loads(port((OLD/"nsd_path_production_prepare/activation_receipt.draft.json").read_text(),"activation_draft"))
    save(P/"activation_receipt.draft.json",activation)
    check("all_actual_activation_fields_remain_NULL",activation["owner"]==owner
        and all(activation[k] is None for k in ("actual_observation_sha256","admission_receipt_sha256","root_independent_review")))
    c=load("prospective_current_owner_controller",P/"production_controller.py")
    check("controller_all_six_fields_exact",c.EXPECTED_OWNER==owner and c.OWNER==TOKEN and c.OWNER_DEADLINE==owner["deadline_at"])
    check("prospective_stage_paths_fresh",str(c.PRODUCER).endswith("nsd_path_prepare_f74f3603") and str(c.PRODUCTION).endswith("nsd_path_prod_f74f3603"))
    check("controller_original_source_base_and_locks",
        c.COMMIT=="f6257de79148581334ee495e6e2d60ccb525457c"
        and c.BASE_SHA=="6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
        and c.LOCK_PATHS==["/tmp/cluster_project_gpu0_"+x+".lock" for x in ("training","diagnostic","exclusive")])
    prep=read(OLD/"nsd_path_production_prepare/preparation.json")
    prep=json.loads(port(json.dumps(prep),"production_preparation"))
    prep.update(owner_provenance_only=owner,author_thread_id=AUTHOR,producer_FROZEN=ref(OLD/"nsd_path_production_prepare/FROZEN.json"),
        producer_review=ref(pr),metadata_adaptation_only=True,independent_review="PENDING_EXTERNAL")
    save(P/"preparation.json",prep)
    save(P/"README.md","Disabled prospective production helper adaptation. Only owner/tick/stage metadata changed from reviewed eb827823 package. Proved core/factory and CPU proof reused unchanged. Actual deployment, admission, collect/render, observation, production binding and training remain unperformed. Current SERVERS/PSC runtime is unchanged. A separately reviewed live activation and actual gates are required.\n")
    save(P/"change_manifest.json",{"ports":ports,"builder":ref(Path(__file__)),"producer_review":ref(pr),
        "algorithm_or_model_changes":False,"CPUproof_rerun":False})
    pf=freeze(P,owner,{"producer_FROZEN":ref(OLD/"nsd_path_production_prepare/FROZEN.json"),"producer_review":ref(pr),"disabled_prospective":True})
    transport=port((OLD/"nsd_path_production_transport/run_controller_once.py").read_text(encoding="utf8"),"transport")
    prior=sha(OLD/"nsd_path_production_prepare/FROZEN.json")
    check("transport_single_FROZEN_anchor",transport.count(prior)==1)
    transport=transport.replace(prior,pf["sha256"],1)
    save(T/"run_controller_once.py",transport)
    t=load("disabled_current_owner_transport",T/"run_controller_once.py")
    check("transport_current_owner_disabled_NULL_review_and_controller_anchor",
        t.EXPECTED_OWNER==owner and t.TOKEN==TOKEN and t.DRAFT_EXECUTION_DISABLED is True
        and t.REVIEW_SHA is None and t.FROZEN_SHA==pf["sha256"])
    try:t.guard()
    except AssertionError as e:check("actual_transport_DRAFT_refusal_prevents_IO",str(e).startswith("Disabled prospective transport"))
    else:raise AssertionError("Transport unexpectedly enabled")
    nop=subprocess.run([sys.executable,"-B","-X","utf8",str(T/"run_controller_once.py")],capture_output=True,text=True,timeout=15)
    check("actual_default_transport_NOP",nop.returncode==0 and json.loads(nop.stdout)["status"]=="DEFAULT_NOP_NO_SSH_OR_MUTATION")
    for path in (N/"normalize_nsd_actual_results.py",P/"production_controller.py",T/"run_controller_once.py",Path(__file__)):
        compile(path.read_bytes(),str(path),"exec")
    check("all_adapted_Python_compile",True)
    check("all_producer_frozen_and_reviews_preserved",all(sha(Path(p))==d for p,d in preserved.items()))
    check("no_actual_outputs_or_requests_or_release",
        not any(p.name.startswith("results_") or p.name in ("adapter_release.json","production_binding.json","actual_observation.json")
            or p.name.endswith(("_intent.json","_result.json")) for folder in (N,P,T) for p in folder.rglob("*")))
    check("SERVERS_current_PSC_policy_unchanged",sha(ROOT/"SERVERS.yaml")=="1f1ba94e90c6f44e2e9cb0e6f1e746568e38cc1e92f398ee49efc5e8c40232bf")
    validation={"status":"MINIMAL_METADATA_ADAPTATION_CHECKS_PASS_PENDING_INDEPENDENT_REVIEW",
        "recorded_at":datetime.now(timezone.utc).isoformat(),"checks":checks,"check_count":len(checks),
        "scope":"Exact reversible owner/tick/path diffs, retained producer hash graphs, imports/compile, actual root-child/DRAFT refusal and default NOP, external literal synthetic arm identity fixtures. Old software suites and CPU proof not repeated.",
        "native":"NOT_RUN","resources":"NOT_RUN","actual_raw_results_consumed":False,"SSH_GPU":False,"actual_collect_render":False}
    save(N/"change_manifest.json",{"ports":[p for p in ports if p["file"]=="normalizer"],"builder":ref(Path(__file__))})
    save(N/"software_validation.json",validation)
    nf=freeze(N,owner,{"producer_FROZEN":ref(OLD/"nsd_result_prepare/FROZEN.json"),"producer_review":ref(nr),"normalizer_root_only":True,"normalizer_executed":False})
    save(T/"README.md","Disabled default-NOP fresh-owner NSD production transport. REVIEW_SHA remains NULL and DRAFT remains True. No transport, intents, requests, observation, collect/render, installation or launch occurred. Separately reviewed live activation is required; frozen draft stays unchanged.\n")
    save(T/"change_manifest.json",{"ports":[p for p in ports if p["file"]=="transport"],"controller_FROZEN_anchor":{"from":prior,"to":pf["sha256"]},"builder":ref(Path(__file__))})
    save(T/"software_validation.json",validation)
    tf=freeze(T,owner,{"controller_packet":pf,"producer_FROZEN":ref(OLD/"nsd_path_production_transport/FROZEN.json"),
        "producer_review":ref(pr),"draft_execution_disabled":True,"review_sha256":None})
    print(json.dumps({"normalizer_FROZEN":nf,"production_FROZEN":pf,"transport_FROZEN":tf,
        "normalizer":ref(N/"normalize_nsd_actual_results.py"),"production_controller":ref(P/"production_controller.py"),
        "check_count":len(checks),"author_writes_stopped":True,"actual_normalize_collect_render_GPU":"NOT_RUN"},indent=2))

if __name__=="__main__":main()
