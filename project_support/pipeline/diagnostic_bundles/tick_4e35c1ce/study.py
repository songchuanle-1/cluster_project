"""Current-lease guarded preparation and read-only native support diagnosis."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1",
                  PYTHONIOENCODING="utf-8")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
import yaml

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
TOKEN = "4e35c1cefe914c04b862004d0c677110"
THREAD = "01a04987-fdbe-7301-b2f0-f9b6ab60f74c"
GOAL = "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
CID = "hierarchy-native-batch-minimum-resolution"
REMOTE = "/data/songcl/Project/Cluster_project/pipeline/batch_minimum_4e35c1ce"
SSH = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
       "-o", "ConnectTimeout=10"]


def now():
    return datetime.now(timezone.utc).isoformat()


def guard(seconds=0):
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD == os.environ["CODEX_THREAD_ID"]
    assert (datetime.fromisoformat(owner["deadline_at"])
            - datetime.now(timezone.utc)).total_seconds() > seconds
    assert tick.digest(ROOT / "pipeline/goal.json") == GOAL
    cfg = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]["server-4"]
    assert cfg["host"] == "192.168.1.115" and cfg["expected_hostname"] == "dl04-MS-7E06"
    assert cfg["allowed_gpus"] == [0, 1] and cfg["max_tasks_per_gpu"] == 1
    return owner, cfg


def evidence(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)}


def save(name, value):
    guard()
    path = OUT / name
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return path


def remote_code(code, timeout=120, conda=False):
    _, cfg = guard()
    program = "import socket\nassert socket.gethostname() == 'dl04-MS-7E06'\n" + code
    command = shlex.join(["python" if conda else "/usr/bin/python3", "-B", "-c", program])
    if conda:
        command = shlex.join(["bash", "-lc",
                             "source " + shlex.quote(cfg["conda_source"])
                             + " && conda activate " + shlex.quote(cfg["conda_env"])
                             + " && " + command])
    process = subprocess.run(["ssh", *SSH, cfg["user"] + "@" + cfg["host"], command],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=timeout)
    assert process.returncode == 0, process.stderr[-6000:]
    return json.loads(process.stdout)


def prepare():
    guard(600)
    assert not (OUT / "resolution_protocol.json").exists()
    protocol = {
        "created_at": now(), "token": TOKEN, "candidate_id": CID,
        "hypothesis": "The native minimum-scene-length clamp changes M95 fine hierarchy resolution with the batch peer on actual unchanged TRAIN supports, not merely a constructed short scene.",
        "source_trigger": "PointCloudPartitioner.forward sets layer_nums[0] = min(layer_nums[0], min(lens)).",
        "matched_controls": "Execute the exact AST RHS: large peers retain256; short peer100 changes256to100; row order leaves256; masked tensor padding without changing valid batch_offsets leaves256.",
        "population": "Every unique scene_id in the hash-bound ScanRefer_train_new.json, sorted lexically; no VAL/test or outcome selection.",
        "measurement": "Read original native scene tuple. For points<=2500000, source sample_rdn retains all points and np.unique remapping preserves exact support cardinality. Scenes above the cap are UNKNOWN, not counted as no clamp.",
        "decision": "Reject only the actual-TRAIN batch-minimum-resolution premise if every expected scene is read successfully, every support is exact, and no support<256. If any support<256, retain diagnosis and next run fixed-scene native paired-peer intervention. Missing files/sampled supports are inconclusive.",
        "limits": "No new model, source repair, optimizer, training, query selection, annotation changes or claim of efficacy/novelty. This is not the closed appended-padding/global-mean audit.",
        "runner": evidence(OUT / "native_resolution_census.py"),
        "goal_sha256": GOAL,
    }
    path = save("resolution_protocol.json", protocol)
    work = tick.load(ROOT / "pipeline/research_work.json")
    assert not any(item["id"] == CID for item in work["candidates"])
    work["candidates"].append({
        "id": CID, "stage": "diagnosis", "created_at": protocol["created_at"],
        "hypothesis": protocol["hypothesis"], "matched_control": protocol["matched_controls"],
        "next_action": "Run frozen read-only full TRAIN support census and exact source clamp controls on pinned server4 CPU; classify actual incidence before any model intervention.",
        "scientific_admission": False,
        "evidence": [evidence(path), evidence(OUT / "native_resolution_census.py"),
                     evidence(ROOT / "pipeline/reviews/motivation_review_20261019_4e35c1ce.md"),
                     evidence(ROOT / "pipeline/designs/exp_design_20261019_4e35c1ce.md")],
    })
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"registered": CID, "protocol": evidence(path), "created_at": protocol["created_at"]}))


def run():
    owner, cfg = guard(600)
    protocol = OUT / "resolution_protocol.json"
    lease = save("resolution_execution_lease.json", {
        "project": "cluster_project", "thread_id": THREAD, "token": TOKEN,
        "deadline_at": owner["deadline_at"], "protocol_sha256": tick.digest(protocol),
    })
    remote_code("from pathlib import Path\nimport json\np=Path(" + repr(REMOTE)
                + ")\np.mkdir(parents=True,exist_ok=True)\nprint(json.dumps({'stage':str(p)}))")
    files = [OUT / "native_resolution_census.py", protocol, lease]
    copy = subprocess.run(["scp", *SSH, *map(str, files),
                           cfg["user"] + "@" + cfg["host"] + ":" + REMOTE + "/"],
                          capture_output=True, text=True, timeout=90)
    assert copy.returncode == 0, copy.stderr[-3000:]
    command = shlex.join(["bash", "-lc",
                         "source " + shlex.quote(cfg["conda_source"])
                         + " && conda activate " + shlex.quote(cfg["conda_env"])
                         + " && cd " + shlex.quote(REMOTE)
                         + " && PYTHONDONTWRITEBYTECODE=1 python -B native_resolution_census.py resolution_execution_lease.json"])
    guard(300)
    started = now()
    process = subprocess.run(["ssh", *SSH, cfg["user"] + "@" + cfg["host"], command],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=1250)
    execution = save("resolution_execution.json", {
        "started_at": started, "ended_at": now(), "returncode": process.returncode,
        "stdout_tail": process.stdout[-5000:], "stderr_tail": process.stderr[-6000:],
        "runner": evidence(files[0]), "protocol": evidence(protocol),
        "new_training": 0, "native_gpu_jobs": 0,
    })
    result = remote_code("import json\nfrom pathlib import Path\nprint((Path("
                         + repr(REMOTE) + ")/'native_resolution_result.json').read_text())")
    result_path = save("native_resolution_result.json", result)
    work = tick.load(ROOT / "pipeline/research_work.json")
    candidate = next(item for item in work["candidates"] if item["id"] == CID)
    complete = (result["execution_completed"] and not result["failures"]
                and result["exact_support_scenes"] == result["expected_train_scenes"])
    if complete and result["small_scene_count"] == 0:
        candidate.update(
            stage="rejected", failure_scope="hypothesis",
            gate_result="Actual unchanged TRAIN supports never activate the cross-scene minimum clamp; reject only this native-data resolution-coupling premise, not hierarchical attention.",
            next_action="Do not implement a batch-minimum-only repair or repeat this unchanged full support census. Revisit only on changed native support distribution under this stable ID.",
        )
    else:
        candidate.update(
            stage="validation", failure_scope="inconclusive",
            gate_result="Incidence or unknown support requires the preregistered native paired-peer test; no scientific admission.",
            next_action="Use the first outcome-blind small or sampled-support scene, bind native transformed support, then compare one fixed recipient with large/small native peers without changing query or targets.",
        )
    candidate["updated_at"] = now()
    candidate["evidence"].extend([evidence(execution), evidence(result_path)])
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({
        "candidate_id": CID, "stage": candidate["stage"], "complete_support_census": complete,
        "scenes": result["expected_train_scenes"], "minimum_support": result["minimum_exact_support"],
        "small_scene_count": result["small_scene_count"],
        "sampling_unknown_scenes": result["sampling_unknown_scenes"], "failures": result["failures"],
        "source_controls": result["source_controls"],
    }, indent=2))


def native_prepare():
    guard(900)
    census = tick.load(OUT / "native_resolution_result.json")
    assert census["loaded_train_scenes"] == census["expected_train_scenes"] == 562
    assert not census["failures"] and not census["sampling_unknown_scenes"]
    large = [row for row in census["records"] if row["exact_train_support_count"] >= 256][:4]
    small = [row for row in census["records"] if row["exact_train_support_count"] < 256][:4]
    chosen = [row for pair in zip(large, small) for row in pair]
    program = """import copy,json,logging,sys
import torch,gorilla
sys.path[:0]=['/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b','/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/framework/lib']
from tools import train
from framework.dataset import build_dataset
cfg=gorilla.Config.fromfile('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml')
dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('resolution-cohort'))
first={}
for index,group in enumerate(dataset.scene_inputs):
 first.setdefault(group[0]['scene_id'],(index,group))
selected=SELECTED
cohort=[]
for row in selected:
 index,group=first[row['scene_id']]
 assert len(group)==4
 cohort.append({'scene_id':row['scene_id'],'group_index':index,'exact_train_support_count':row['exact_train_support_count'],'expression_ids':[{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]})
assert not torch.cuda.is_initialized()
print(json.dumps({'cohort':cohort,'cuda_initialized':False}))
""".replace("SELECTED", repr(chosen))
    selected = remote_code(program, timeout=180, conda=True)
    selection = save("native_cohort_selection.json", {"observed_at": now(), **selected,
                      "selection_rule": "First four large and first four small TRAIN scene IDs in lexical census order; no outcome/label selection."})
    folder = OUT / "native"
    shutil.copyfile(ROOT / "pipeline/diagnostic_bundles/tick_30bdd3a5/expression_fix/native_runtime.py", folder / "native_runtime.py")
    protocol = save("native_resolution_protocol.json", {
        "created_at": now(), "candidate_id": CID, "census": evidence(OUT / "native_resolution_result.json"),
        "cohort": evidence(selection), "runner": evidence(folder / "native_resolution_task.py"),
        "question": "With original native prefix/final query/matching/target held, does removing only cross-scene fine-resolution coupling change large-recipient point features and masks? Task error direction is a measured uncertain secondary result, not a promised benefit.",
        "intervention": "Replace original globally clamped hierarchy with unchanged native partitioner applied independently to each expression support, cap256/64/8 unchanged; native aggregation/refinement/readback/ILA/head reused.",
        "controls": "Original point/features/mask/scores/identity and native token reaggregation <=1e-6; original small-peer point/mask unaffected <=1e-6. No threshold waiver; retain any failed control separately and call task interpretation inconclusive.",
        "readout": "Every original native query matched to the primary original target; absolute sigmoid probability error, independent-minus-clamped; average queries within expression and expressions within scene. Queries/expressions are correlated; no population CI.",
        "limits": "4 fixed TRAIN scene pairs/32 expressions, M95epoch16 not verified champion; no full model query feedback, optimizer, tuning, training, scientific admission or repair authorization.",
    })
    prior = tick.load(ROOT / "pipeline/diagnostic_bundles/tick_30bdd3a5/expression_fix/native_manifest.json")
    manifest = {key: prior[key] for key in ("schema_version", "root", "name", "assets", "expected_epoch", "tolerance")}
    manifest.update(candidate_id=CID, stage=REMOTE + "_gpu", cohort=selected["cohort"],
                    protocol=evidence(protocol), physical_gpu=1,
                    gpu_uuid="GPU-7f82edb9-f620-8045-caea-a75232265cd1",
                    scientific_admission=False,
                    diagnostic_files={name: tick.digest(folder / name) for name in ("native_runtime.py", "native_resolution_task.py")})
    with (folder / "native_manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
    work = tick.load(ROOT / "pipeline/research_work.json")
    candidate = next(row for row in work["candidates"] if row["id"] == CID)
    candidate["evidence"].extend([evidence(selection), evidence(protocol), evidence(folder / "native_manifest.json"), evidence(folder / "native_resolution_task.py"), evidence(folder / "native_runtime.py")])
    candidate["next_action"] = "Execute the frozen four current-lease GPU1 native paired interventions with all original strict controls; retain any numerical failures and all error directions."
    candidate["updated_at"] = now()
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({"prepared": True, "cohort": selected["cohort"], "protocol": evidence(protocol)}, indent=2))


def native_run(pair):
    owner, cfg = guard(480)
    folder = OUT / "native"
    manifest = tick.load(folder / "native_manifest.json")
    stage = manifest["stage"]
    lease_path = folder / ("execution_lease_" + str(pair) + ".json")
    with lease_path.open("x", encoding="utf-8") as stream:
        json.dump({"project": "cluster_project", "thread_id": THREAD, "token": TOKEN,
                   "deadline_at": owner["deadline_at"], "native_manifest_sha256": tick.digest(folder / "native_manifest.json")}, stream, indent=2)
    remote_code("from pathlib import Path\nimport json\np=Path(" + repr(stage) + ")\np.mkdir(parents=True,exist_ok=True)\nprint(json.dumps({'stage':str(p)}))")
    files = [folder / name for name in manifest["diagnostic_files"]] + [folder / "native_manifest.json", lease_path]
    copy = subprocess.run(["scp", *SSH, *map(str, files), cfg["user"] + "@" + cfg["host"] + ":" + stage + "/"], capture_output=True, text=True, timeout=90)
    assert copy.returncode == 0, copy.stderr[-3000:]
    command = shlex.join(["bash", "-lc", "source " + shlex.quote(cfg["conda_source"])
                         + " && conda activate " + shlex.quote(cfg["conda_env"])
                         + " && cd " + shlex.quote(stage)
                         + " && PYTHONDONTWRITEBYTECODE=1 python -B native_resolution_task.py --lease "
                         + lease_path.name + " --pair " + str(pair)])
    started = now()
    remaining = (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds()
    process = subprocess.run(["ssh", *SSH, cfg["user"] + "@" + cfg["host"], command], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=min(900, int(remaining) - 180))
    execution = save("native_pair_" + str(pair) + "_execution.json", {"started_at": started, "ended_at": now(),
                     "returncode": process.returncode, "stdout_tail": process.stdout[-3000:], "stderr_tail": process.stderr[-12000:],
                     "manifest": evidence(folder / "native_manifest.json"), "new_training": 0})
    result = remote_code("import json\nfrom pathlib import Path\nprint((Path(" + repr(stage)
                         + ")/" + repr("native_resolution_pair_" + str(pair) + ".json") + ").read_text())")
    result_path = save("native_pair_" + str(pair) + "_result.json", result)
    work = tick.load(ROOT / "pipeline/research_work.json")
    candidate = next(row for row in work["candidates"] if row["id"] == CID)
    candidate["evidence"].extend([evidence(execution), evidence(result_path)])
    candidate["updated_at"] = now()
    candidate["gate_result"] = "Actual current-lease native paired attempt recorded; interpret only controls and readouts actually observed. No automatic scientific admission."
    guard()
    tick.save(ROOT / "pipeline/research_work.json", work)
    print(json.dumps({key: value for key, value in result.items() if key not in ("records", "before")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "run", "native-prepare", "native-run"])
    parser.add_argument("--pair", type=int, choices=range(4))
    args = parser.parse_args()
    if args.action == "native-run":
        assert args.pair is not None
        native_run(args.pair)
    else:
        {"prepare": prepare, "run": run, "native-prepare": native_prepare}[args.action]()
