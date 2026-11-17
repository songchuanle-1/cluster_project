"""Record the 2026-09-21 21:40 saved-only diagnostic progress."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "pipeline" / "research_work.json"
RECEIPT = "pipeline/diagnostic_bundles/model_loader_boundary_server6_20260921.json"
RECEIPT_SHA256 = (
    "28906fb270229019a02ba9d120d18c9a014d8f26665cc4f4bffa15404d9b3a07")
PROGRESS = (
    "2026-09-21T21:40:00+08:00: verified the exact three artifact and six data "
    "hashes on server-6 (all nine matched byte-for-byte) and exercised the "
    "model-loader/import boundary against the bound champion package. The "
    "composite model-package source digest and the config digest matched, and "
    "gorilla plus framework/framework.dataset/framework.utils imported and "
    "resolved the champion Network without instantiating it, loading a "
    "checkpoint, building a dataset or starting training."
)
NEXT = (
    "Next bounded step: instantiate the bound champion Network constructor under "
    "an explicit memory budget on server-6 GPU7 (no checkpoint weights, no "
    "dataset, no training, foreign process untouched) and record parameter count "
    "and peak allocation; then attempt one synthetic native forward/backward. "
    "Full-model native backward, the resource gates and admission remain "
    "unverified, and M197 stays stopped_unknown with no restart or successor."
)
DUE = {
    "referent-supervision-axis",
    "referent-causality-audit",
    "modality-identity-preservation",
    "referent-discrimination",
    "instance-identity-representation",
    "referent-query-selection",
    "input-modality-distinguishability",
    "same-target-description-grounding",
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    actual = sha256(ROOT / RECEIPT)
    if actual != RECEIPT_SHA256:
        raise ValueError("Loader-boundary receipt digest changed: " + actual)
    work = json.loads(WORK.read_text(encoding="utf-8"))
    updated = []
    for candidate in work["candidates"]:
        if candidate.get("id") not in DUE:
            continue
        candidate["latest_progress"] = PROGRESS
        candidate["next_action"] = NEXT
        candidate["loader_boundary_progress"] = {
            "receipt": RECEIPT,
            "sha256": RECEIPT_SHA256,
            "artifact_hashes_verified": 3,
            "data_hashes_verified": 6,
            "model_package_source_digest_verified": True,
            "config_digest_verified": True,
            "import_boundary_verified": True,
            "network_instantiated": False,
            "checkpoint_loaded": False,
            "dataset_built": False,
            "training_started": False,
            "full_model_native_backward_verified": False,
            "resources_verified": False,
            "admission": False,
        }
        updated.append(candidate["id"])
    if set(updated) != DUE:
        raise ValueError("Due candidate set mismatch: %s" % sorted(updated))
    work["next_action"] = NEXT
    with WORK.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(work, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("updated %d candidates" % len(updated))


if __name__ == "__main__":
    main()
