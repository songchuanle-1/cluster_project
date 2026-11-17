"""Save the reviewed HVD draft in isolated Git objects; never check it out."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "mic_version_guard", HERE / "save_mic_compatible_version.py"
)
guard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard_module)
ROOT, REPO = guard_module.ROOT, guard_module.REPO
git, sha, read = guard_module.git, guard_module.sha, guard_module.read
PACKET = HERE / "new_candidate_prepare"
OUT = HERE / "hvd_version_prepare"
CID = "hierarchy-native-variance-decomposition-composition"
REF = "refs/codex/cluster_project/M230-HVD/265517f1"


def ref(path):
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha(path.read_bytes()),
    }


def main():
    owner = guard_module.guard()
    review_path = HERE / "new_candidate_independent_review.json"
    review = read(review_path)
    assert review.get("passed") is True, "Independent source review must pass first."
    assert review["candidate_id"] == CID
    assert not OUT.exists(), "Preserve any earlier intent; do not replay."
    frozen = read(PACKET / "FROZEN.json")
    assert frozen["writer_stopped"] is True
    for relative, digest in frozen["files"].items():
        assert sha((PACKET / relative).read_bytes()) == digest
    manifest = read(PACKET / "source_manifest.json")
    assert manifest["candidate_id"] == CID
    sources = manifest["source_files_exact9"]
    assert len(sources) == 9
    assert len([p for p in sources if p.endswith(".py")]) == 8
    before = guard_module.protected()
    assert before["head"] == guard_module.BASE
    for path, digest in sources.items():
        actual = PACKET / "staged_repository" / path
        assert sha(actual.read_bytes()) == digest
        if path.endswith(".py"):
            compile(actual.read_bytes(), path, "exec")
        assert subprocess.run(
            [guard_module.GIT, "-C", str(REPO), "cat-file", "-e",
             f"{guard_module.BASE}:{path}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).returncode != 0
    OUT.mkdir()
    intent = {
        "owner": owner, "candidate_id": CID, "base": guard_module.BASE,
        "source_files_exact9": sources, "source_review": ref(review_path),
        "native": "NOT_RUN", "main_checkout_or_index_mutation": False,
    }
    (OUT / "version_intent.json").write_text(
        json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = str(OUT / "isolated.index")
    git("read-tree", guard_module.BASE, env=env)
    for path in sources:
        content = (PACKET / "staged_repository" / path).read_bytes()
        blob = git("hash-object", "-w", "--stdin", data=content).decode().strip()
        git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
    tree = git("write-tree", env=env).decode().strip()
    guard_module.guard()
    commit = git(
        "commit-tree", tree, "-p", guard_module.BASE, "-m",
        "Save M230 hierarchical native variance decomposition draft",
        env=env,
    ).decode().strip()
    diff = git(
        "diff-tree", "--no-commit-id", "--name-status", "-r",
        guard_module.BASE, commit,
    ).decode().splitlines()
    assert sorted(diff) == sorted("A\t" + path for path in sources)
    for path, digest in sources.items():
        assert sha(git("show", f"{commit}:{path}")) == digest
    old_entries = git("ls-tree", "-r", "-z", guard_module.BASE).split(b"\0")
    new_entries = set(git("ls-tree", "-r", "-z", commit).split(b"\0"))
    assert all(entry in new_entries for entry in old_entries if entry)
    git("update-ref", REF, commit, "0" * 40)
    after = guard_module.protected()
    assert before == after
    proof = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": owner, "candidate_id": CID, "experiment_id": "M230-HVD",
        "source_commit": commit, "code_commit": commit,
        "parent_commit": guard_module.BASE,
        "source_parent_commit": guard_module.BASE,
        "pinned_ref": REF, "source_files_exact9": sources,
        "source_preparation": ref(PACKET / "preparation.json"),
        "source_manifest": ref(PACKET / "source_manifest.json"),
        "original_NULL_packet_preserved": ref(PACKET / "FROZEN.json"),
        "independent_source_review": ref(review_path),
        "diff_exact9A": True, "all_prior_tree_entries_unchanged": True,
        "same_source_bytes_as_independently_reviewed": True,
        "protected_before": before, "protected_after": after,
        "main_HEAD_index_dirty_files_and_lifecycle_unchanged": True,
        "native": "NOT_RUN", "resources": "NOT_RUN",
        "scientific_admission": False, "promoted_or_deployed": False,
        "scope": "Local version save only; later main changes require a fresh compatible save.",
    }
    output = OUT / "isolated_source_version.json"
    output.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_commit": commit, "parent": guard_module.BASE,
        "proof": ref(output), "main_and_lifecycle_unchanged": True,
    }))


if __name__ == "__main__":
    main()
