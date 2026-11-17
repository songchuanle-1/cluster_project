"""Root-only external anchors for independently reviewed current-owner PSC."""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import os
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
ACT = HERE / "psc_current_activation"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import pipeline_monitor as mon


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == "0bb874337dde412e98bbbaac369f3370"
assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert sha(ROOT / "pipeline/headless" / name) == owner[key]
review_path = HERE / "psc_current_activation_independent_review.json"
review = read(review_path)
assert review.get("passed") is True
assert sha(ACT / "preparation.json") == "f1f38236ff1ed88f1efa8361392df5bfffa96304b8ab3fa3b2ffb0d94fe4454e"
assert sha(ACT / "native/preparation.json") == "87f1a31ea34511b940ec9683ea160360c537bcf8e866a5d398572088c1301983"
assert sha(ACT / "native/worker.py") == "530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8"
frozen = read(ACT / "FROZEN.json")
for path, digest in frozen["files"].items():
    assert sha(ACT / path) == digest
lock = mon.acquire_lock(str(ROOT))
assert lock is not None
try:
    target = ACT / "adapter_release.json"
    assert not target.exists()
    with target.open("xb") as stream:
        stream.write((ACT / "release_template.json").read_bytes())
    work_path = ROOT / "pipeline/research_work.json"
    work = read(work_path)
    candidate = next(c for c in work["candidates"] if c["id"] == "hierarchy-native-position-feature-cross-scatter-composition")
    assert candidate["source_commit"] == candidate["code_commit"] == "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
    before = {"worker_preparation": copy.deepcopy(candidate.get("worker_preparation")),
              "execution_adapter": copy.deepcopy(candidate.get("execution_adapter"))}
    candidate.setdefault("operational_preparation_history", []).append({
        "recorded_at": datetime.now(timezone.utc).isoformat(), "previous": before,
        "scope": "Fresh current-owner root activation, original frozen packets unchanged; native/resources not run yet.",
    })
    candidate["worker_preparation"] = {
        "preparation": ref(ACT / "native/preparation.json"),
        "manifest_template": ref(ACT / "native/manifest_template.json"),
        "frozen_producer": ref(ROOT / "pipeline/diagnostic_bundles/tick_2e51495f/psc_native_prepare/native/preparation.json"),
    }
    candidate["execution_adapter"] = {
        "preparation": ref(ACT / "preparation.json"), "release": ref(target),
        "current_binding": ref(ACT / "current_binding.json"),
        "independent_activation_review": ref(review_path),
    }
    for path in (ACT / "preparation.json", ACT / "native/preparation.json", ACT / "current_binding.json", review_path):
        item = ref(path)
        if item not in candidate["evidence"]:
            candidate["evidence"].append(item)
    candidate["updated_at"] = work["updated_at"] = datetime.now(timezone.utc).isoformat()
    temp = work_path.with_name("research_work.0bb87433.activation.tmp")
    with temp.open("x", encoding="utf8") as stream:
        json.dump(work, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, work_path)
    result = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner_token": owner["token"], "root_static_release_created": True,
        "static_release": ref(target), "native_preparation": ref(ACT / "native/preparation.json"),
        "review": ref(review_path), "execution_binding_or_lease_created": False,
        "remote_stage_or_native_run": False,
    }
    with (HERE / "psc_root_activation_anchors.json").open("x", encoding="utf8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False))
finally:
    lock.close()
