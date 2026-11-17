"""Default NOP. Create tick-local drafts only; never apply shared state."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import re

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
CANDIDATE = "fine-leaf-receiver-conditioned-vector-exchange"
SOURCE = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
REVISION = "daaf3041ebd3a9beacf487c60346d214374fd81a9a9411379801232e4450377f"
RESOURCE = "43530085aff3937dec2d6eb42ffd94b0a631000f16cbf749a2dca345195915d4"
SECTIONS = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
            "Closed Or Failed Directions", "Running And Queue",
            "Open Questions And Risks", "Last Tick")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def write(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-drafts", action="store_true")
    parser.add_argument("--label")
    parser.add_argument("--failure-evidence", type=Path)
    args = parser.parse_args()
    if not args.write_drafts:
        print("DEFAULT_NOP_TICK_LOCAL_DRAFTS_ONLY_NO_SHARED_APPLY")
        return
    assert args.label and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", args.label)
    owner = read(TICK / "current_owner_binding.json")
    now = datetime.now(timezone.utc).isoformat()
    work_path, memory_path = ROOT / "pipeline/research_work.json", ROOT / "pipeline/codex_memory.md"
    base_work_sha, base_memory_sha = sha(work_path), sha(memory_path)
    work = read(work_path)
    candidate = next(x for x in work["candidates"] if x.get("id") == CANDIDATE)
    revisions = copy.deepcopy(candidate["revision_history"])
    revision = next(x for x in revisions if x["revision"] == 1)
    assert canonical(revision) == REVISION and revision["result"] == "passed"
    queue_path = ROOT / "pipeline/queue.json"
    queue_sha = sha(queue_path)
    tasks = [t for ts in read(queue_path)["gpu_queues"].values() for t in ts if t.get("id") == "M234-RVE"]
    assert len(tasks) == 1
    task = tasks[0]
    assert task["code_commit"] == SOURCE
    names = [
        "resource_actual.json", "resource_observe_intent.json",
        "source_verify_prepare/FROZEN.json", "source_verify_execution/verify_actual.json",
        "rvec_production_prepare/FROZEN.json",
        "rvec_setup_execution/stage_actual.json", "rvec_setup_execution/collect_actual.json",
        "rvec_setup_execution/collect_result.json", "rvec_setup_execution/production_activation.json",
        "rvec_setup_execution/render_actual.json", "rvec_setup_execution/render_result.json",
        "rvec_pointer_execution/switch_result.json",
        "rvec_dispatch_execution/rvec_prelaunch_actual_resources.json",
        "rvec_dispatch_execution/rvec_dispatch_intent.json",
        "rvec_dispatch_execution/rvec_dispatch_result.json",
        "dispatch_proof_execution/capture_actual.json", "dispatch_proof_execution/dispatch_proof.json",
    ]
    names += [p.relative_to(TICK).as_posix() for p in sorted((TICK / "operational_review").glob("*.json"))]
    names += [p.relative_to(TICK).as_posix() for p in sorted((TICK / "launch_observe_prepare").glob("*.actual.json"))]
    if args.failure_evidence:
        failure = args.failure_evidence.resolve()
        assert failure.is_relative_to(TICK.resolve()) and failure.is_file()
        names.append(failure.relative_to(TICK.resolve()).as_posix())
    values, evidence = {}, []
    for name in dict.fromkeys(names):
        path = TICK / name
        if not path.exists():
            continue
        value = read(path)
        if "owner" in value:
            assert value["owner"] == owner, name
        values[name] = value
        evidence.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)})
    resource = values["resource_actual.json"]
    assert sha(TICK / "resource_actual.json") == RESOURCE
    ro = resource["observation"]
    assert resource["certainty"] == "terminal" and resource["returncode"] == 0
    assert ro["memory_budget_satisfied"] is True and ro["free_memory_mib"] >= 20000
    resource_peer = values["operational_review/current_resource_actual_independent_review.json"]
    assert resource_peer["passed"] is True and resource_peer["resource_actual_sha256"] == RESOURCE
    verify = values["source_verify_execution/verify_actual.json"]
    assert verify["passed"] is True and verify["source_commit"] == SOURCE and verify["new_sync_performed"] is False
    dispatch = values.get("rvec_dispatch_execution/rvec_dispatch_result.json")
    proof = values.get("dispatch_proof_execution/dispatch_proof.json")
    observations = [(name, value) for name, value in values.items()
                    if name.startswith("launch_observe_prepare/") and name.endswith(".actual.json")]
    live = [(name, value) for name, value in observations
            if value.get("certainty") == "terminal" and value.get("returncode") == 0
            and "observation" in value and not value.get("parse_or_identity_error")]
    verified = bool(dispatch and dispatch.get("launch_verified") is True
                    and task.get("launch_verified") is True and task["status"] == "running")
    growth = False
    for _, value in live:
        if not value.get("native_step_growth_observed"):
            continue
        new = value["observation"]
        previous = next((old["observation"] for _, old in live
                         if sha(TICK / _) == value.get("previous_sha256")), None)
        assert previous and all(previous[k] == new[k] for k in ("pid", "start_ticks", "source_commit"))
        assert previous["latest_native_step"] and new["latest_native_step"]
        assert tuple(new["latest_native_step"]) > tuple(previous["latest_native_step"])
        growth = True
    if verified:
        assert dispatch["owner_token"] == owner["token"] and proof and live
        assert int(task["pid"]) == proof["pid"] == int(dispatch["task"]["pid"])
        assert task["log"] == proof["log"] == dispatch["task"]["log"]
        assert proof["source_commit"] == SOURCE and proof["actual_identity_capture"]["PID_start_checked_twice"] is True
        for _, value in live:
            observation = value["observation"]
            assert value["dispatch_proof_sha256"] == sha(TICK / "dispatch_proof_execution/dispatch_proof.json")
            assert all(observation[k] == proof[k] for k in ("pid", "start_ticks", "source_commit", "marker_sha256"))
        next_action = "Protect the existing verified M234 process; use bounded canonical progress/validation monitoring. Never relaunch or replay its consumed entry."
    else:
        assert args.failure_evidence, "No complete actual launch/observer proof yet; supply genuine failure evidence or wait."
        next_action = "Reconcile the preserved current failure/uncertain launch evidence and queue/PID/marker before any further action; never replay an existing intent."
    stage = "training" if verified else "deployment"
    latest = [v["observation"] for _, v in live][-2:]
    outcome = {"owner": owner, "as_of": now, "launch_verified": verified,
               "native_step_growth_observed": growth, "actual_pid": task.get("pid"),
               "actual_log": task.get("log"), "latest_native_steps": [x.get("latest_native_step") for x in latest],
               "current_verification_sha256": sha(TICK / "source_verify_execution/verify_actual.json"),
               "actual_render_result_sha256": sha(TICK / "rvec_setup_execution/render_result.json")
               if "rvec_setup_execution/render_result.json" in values else None}
    proposed = {"stage": stage, "updated_at": now, "training_started": verified,
                "blocker": None if verified else "Current actual failure/uncertainty requires reconciliation",
                "next_action": next_action, "current_owner_operational_readiness": outcome}
    attempt_evidence = [entry for entry in evidence if entry["path"].endswith(
        ("resource_actual.json", "current_resource_actual_independent_review.json",
         "rvec_prelaunch_actual_resources.json"))]
    attempt = {"tick_started_at": owner["generated_at"], "owner": owner,
               "candidate_id": CANDIDATE, "kind": "resource_check", "result": "passed",
               "command": "python -B -X utf8 " + (TICK / "resource_observe_once.py").as_posix() + " --execute-root",
               "observation": f"Actual GPU0 resource snapshot at {ro['observed_at']}: free{ro['free_memory_mib']}MiB >=20000MiB, original3locks available and no project trainer; independent current review passed. Subsequent actual launch_verified={verified}, native_step_growth_observed={growth}; source/runtime d214 unchanged, no efficacy claim.",
               "evidence": attempt_evidence}
    successor = copy.deepcopy(work)
    target = next(x for x in successor["candidates"] if x.get("id") == CANDIDATE)
    old_readiness = copy.deepcopy(target.get("current_owner_operational_readiness"))
    if old_readiness:
        target.setdefault("operational_readiness_history", []).append(old_readiness)
    target.update(proposed)
    for entry in evidence:
        if entry not in target["evidence"]:
            target["evidence"].append(entry)
    successor.setdefault("tick_attempt_history", []).append(copy.deepcopy(work.get("tick_attempt", {})))
    successor.update(updated_at=now, next_action=next_action, tick_attempt=attempt)
    assert target["revision_history"] == revisions
    assert all(c == d for c, d in zip(work["candidates"], successor["candidates"]) if c["id"] != CANDIDATE)
    assert all(e in target["evidence"] for e in candidate["evidence"])
    actions = [
        f"当前真实资源检查{ro['observed_at']}：GPU0空闲{ro['free_memory_mib']}MiB，达到20000MiB门槛；原三锁和项目并发检查通过，独审通过。",
        "本轮仅只读复核d214源码并复用原558同步；当前CPU stage/collect/render与独审证据按实际文件逐项绑定，未重做原生科学门槛。",
        f"实际M234状态={task['status']}，PID={task.get('pid')}；canonical launch_verified={verified}，同PID/start/source原生步数增长={growth}，实际步数={[x.get('latest_native_step') for x in latest]}。",
        "RVE已passed revision1全部字段和历史负证据完整保留；本轮证据只追加candidate外层。报告与finish的后续结果尚未发生，未宣称收尾通过。",
    ]
    decisions = [
        next_action,
        "仅server4物理GPU0、共享外部负载、free>=20000MiB和maxproject1政策保持；不信号、不驱逐、不重放旧owner/intent/已消费入口，M206/M227人工暂停保持。",
        "本轮真实resource_check passed及新增候选外层证据用于收尾；不强凑创建配额，不把早期进度写成效力、完整epoch/验证或长期稳定性PASS。",
    ]
    notes = {"actions": actions, "decisions": decisions, "as_of": now, "owner": owner,
             "draft_only": True, "finish_result_claimed": False, "actual_outcome": outcome}
    baseline = memory_path.read_text(encoding="utf-8")
    section = {name: baseline.split("## " + name, 1)[1].split("\n## ", 1)[0].strip()
               for name in SECTIONS}
    section["Active Hypotheses"] = re.sub(
        r"(?m)^- M234-RVE[^\n]*",
        "- M234-RVE稳定ID fine-leaf-receiver-conditioned-vector-exchange；source d21477b0、原canonical准入和原owner同步保持；21ebd237当前操作与启动状态见下。效力/novelty UNKNOWN。",
        section["Active Hypotheses"], count=1).replace("本轮r1", "历史r1")
    section["Running And Queue"] = "\n".join([
        f"- M234实际status={task['status']}；PID={task.get('pid')}；log={task.get('log')}；launch_verified={verified}。",
        f"- 当前实际observer同PID/start/source增长={growth}；采样原生步数={[x.get('latest_native_step') for x in latest]}。仅早期进度，完整epoch/验证和效力未由此证明。",
        f"- 资源{ro['observed_at']}实际free{ro['free_memory_mib']}MiB>=20000，review通过；真正派发另有当前live资源门。外部进程保持，M206/M227人工暂停保持。",
        "- runtime /data/songcl/Project/Cluster_project/Cluster_nsd_20261107/HEAD d214；localmain0747/index/user28/r0九文件保持。558同步保留原owner，21ebd237是只读验证，无新sync。",
        "- 当前生产stage /data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_21ebd237；真实render/指针/dispatch/marker状态均由本轮实际artifact支持。",
        "- 旧ee6资源阻断与全部失败证据保留为历史；不得重放旧lease/shim。下一步：" + next_action,
    ])
    section["Last Tick"] = "\n".join([
        f"- tick21ebd237；快照{owner['generated_at']}；deadline{owner['deadline_at']}；本草稿截至{now}。",
        "- 本轮resource_check实际passed，当前source/CPU/setup/生产/实际启动证据均按文件发现并哈希；无新模型/native/GPU测试。",
        f"- 实际launch_verified={verified}；native_step_growth={growth}。效力/novelty/长期稳定性仍UNKNOWN；finish尚未执行，未声称postflight通过。",
        "- RVE passed revision1 digest " + REVISION + "；整个revision_history逐字段保持，新证据仅candidate外层。",
        "- 下一步：" + next_action,
    ])
    memory = "# Codex Research Memory\n\n" + "\n\n".join("## " + name + "\n" + section[name] for name in SECTIONS) + "\n"
    assert len(memory.splitlines()) < 120 and len(re.findall(r"(?m)^## ", memory)) == 7
    assert all(isinstance(x, str) and x for key in ("actions", "decisions") for x in notes[key])
    assert sha(work_path) == base_work_sha and sha(memory_path) == base_memory_sha and sha(queue_path) == queue_sha
    out = HERE / args.label
    out.mkdir(exist_ok=False)
    patch = {"draft_only": True, "base_research_work_sha256": base_work_sha,
             "base_memory_sha256": base_memory_sha, "queue_sha256": queue_sha,
             "immutable_revision1_sha256_before_and_required_after": REVISION,
             "candidate_id": CANDIDATE, "candidate_outer_fields_proposed": proposed,
             "append_only_candidate_outer_evidence": evidence, "tick_attempt": attempt,
             "application": "Root rechecks base hashes/current facts, then applies successor drafts. Helper has no shared apply mode."}
    for name, value in (("report_notes.draft.json", notes), ("candidate_outer_patch.draft.json", patch),
                        ("research_work.successor.draft.json", successor), ("tick_attempt.draft.json", attempt)):
        write(out / name, value)
    with (out / "codex_memory.successor.draft.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(memory)
    write(out / "DRAFT_MANIFEST.json", {"owner": owner, "as_of": now, "draft_only": True,
          "base_research_work_sha256": base_work_sha, "base_memory_sha256": base_memory_sha,
          "queue_sha256": queue_sha, "immutable_passed_revision_digest": REVISION,
          "shared_state_modified_by_author": False, "launch_verified": verified,
          "native_step_growth_observed": growth, "memory_lines": len(memory.splitlines()),
          "files": {p.name: sha(p) for p in sorted(out.iterdir())}})
    print(json.dumps({"draft_directory": str(out), "manifest_sha256": sha(out / "DRAFT_MANIFEST.json"),
                      "launch_verified": verified, "native_step_growth_observed": growth}))


if __name__ == "__main__":
    main()
