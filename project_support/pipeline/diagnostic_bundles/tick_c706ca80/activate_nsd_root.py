"""Root-only release of independently reviewed current-owner NSD diagnostics."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
ACT = HERE / "nsd_current_activation"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mother-review", required=True)
    parser.add_argument("--mother-review-sha256", required=True)
    args = parser.parse_args()
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == "c706ca805df642f3b7d41f51206ed921"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 1020
    assert sys.dont_write_bytecode
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[field]
    mother_review = Path(args.mother_review)
    assert mother_review.resolve().is_relative_to(HERE.resolve())
    assert sha(mother_review) == args.mother_review_sha256 and read(mother_review)["passed"] is True
    activation_review = HERE / "nsd_activation_independent_review.json"
    assert sha(activation_review) == "6c9515eda76164fee72bea59d1d508b0fb469489cef29fb2a4c695cd36d08e58"
    assert read(activation_review)["passed"] is True
    for packet in (HERE / "nsd_native_prepare", ACT):
        for name, expected in read(packet / "FROZEN.json")["files"].items():
            assert sha(packet / name) == expected, name
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        work = read(ROOT / "pipeline/research_work.json")
        candidate = next(c for c in work["candidates"] if c["id"] == "hierarchy-native-spatial-dirichlet-composition")
        assert candidate["code_commit"] == "f6257de79148581334ee495e6e2d60ccb525457c"
        assert candidate["stage"] == "implementation"
        with (ACT / "adapter_release.json").open("xb") as stream:
            stream.write((ACT / "release_template.json").read_bytes())
        candidate["worker_preparation"] = {
            "preparation": ref(ACT / "native/preparation.json"),
            "manifest_template": ref(ACT / "native/manifest_template.json"),
            "frozen_producer": ref(HERE / "nsd_native_prepare/native/preparation.json"),
        }
        candidate["execution_adapter"] = {
            "preparation": ref(ACT / "preparation.json"),
            "release": ref(ACT / "adapter_release.json"),
            "current_binding": ref(ACT / "current_binding.json"),
            "independent_activation_review": ref(activation_review),
            "independent_mother_review": ref(mother_review),
        }
        candidate["stage"] = "validation"
        candidate["next_action"] = "Current owner/software/NSD source independently reviewed only. Execute original guarded prepare/stage and actual paired native TRAIN2/core update and complete resources before admission. Expired PSC shim untouched; separate pinned original-base diagnostic transport only."
        for path in (mother_review, activation_review, ACT / "preparation.json", ACT / "current_binding.json", ACT / "adapter_release.json"):
            item = ref(path)
            if item not in candidate["evidence"]:
                candidate["evidence"].append(item)
        (ROOT / "pipeline/research_work.json").write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        with (HERE / "nsd_root_release_and_anchors.json").open("x", encoding="utf8") as stream:
            json.dump({"recorded_at": datetime.now(timezone.utc).isoformat(), "owner_token": owner["token"],
                       "mother_review": ref(mother_review), "activation_review": ref(activation_review),
                       "execution_adapter": candidate["execution_adapter"], "worker_preparation": candidate["worker_preparation"],
                       "native_and_resources_executed": False}, stream, ensure_ascii=False, indent=2)
        print(json.dumps({"status": "ROOT_CURRENT_OWNER_NSD_RELEASE_ANCHORED_NO_GPU_EXECUTION"}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
