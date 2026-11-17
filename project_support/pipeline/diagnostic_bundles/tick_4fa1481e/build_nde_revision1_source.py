"""Save the preregistered affine factorization without touching the main checkout."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
ORIGINAL = ROOT / "pipeline/diagnostic_bundles/tick_13eb9f90/nde_prepare/source"
PARENT = "f6257de79148581334ee495e6e2d60ccb525457c"
ORIGINAL_COMMIT = "46adb90573118902d0a7c7723ce8817a085f38b9"
CORE = "framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde/distribution_embedding.py"
GIT = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
       "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def put(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def main():
    prereg = read(HERE / "nde_revision1_preregistration.json")
    assert prereg["result"] == "pending" and prereg["revision"] == 1
    before = read(HERE / "protected_assets_before.json")
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")

    def git(*args, data=None, custom_env=env):
        return subprocess.check_output(GIT + list(args), input=data, env=custom_env)

    assert git("rev-parse", "HEAD").decode().strip() == PARENT
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    assert sha(index) == before["index_sha256"]
    original_record = read(HERE / "nde_original_record_before_revision.json")
    prepared = HERE / "nde_revision1_source"
    prepared.mkdir()
    source = prepared / "source"
    files = {}
    for name, expected in original_record["source_files_exact9"].items():
        original = ORIGINAL / name
        assert sha(original) == expected
        data = original.read_bytes()
        if name == CORE:
            text = data.decode("utf-8")
            text = text.replace("import torch.nn as nn\n", "import torch.nn as nn\nimport torch.nn.functional as F\n", 1)
            anchor = "\n\nclass HierarchicalDistributionEmbedding(nn.Module):"
            assert text.count(anchor) == 1
            factor = '''

class _ConditionalAnalysis(nn.Sequential):
    """Same affine parameters; reuse the parent half before child gathering."""

    def forward(self, values, parent, labels):
        first = self[0]
        channels = values.shape[-1]
        value_affine = F.linear(values, first.weight[:, :channels], first.bias)
        parent_affine = F.linear(parent, first.weight[:, channels:], None)
        hidden = value_affine + parent_affine.index_select(0, labels)
        return self[2](self[1](hidden))
'''
            text = text.replace(anchor, factor + anchor, 1)
            assert text.count("self.analysis = nn.Sequential(") == 1
            text = text.replace("self.analysis = nn.Sequential(", "self.analysis = _ConditionalAnalysis(", 1)
            substitutions = [
                ("self.analysis(torch.cat(\n                (valid, selected[0].index_select(0, p0)), dim=-1))",
                 "self.analysis(valid, selected[0], p0)"),
                ("self.analysis(torch.cat(\n                (fine_state, selected[1].index_select(0, p1)), dim=-1))",
                 "self.analysis(fine_state, selected[1], p1)"),
                ("self.analysis(torch.cat(\n                (middle_state, selected[2].index_select(0, p2)), dim=-1))",
                 "self.analysis(middle_state, selected[2], p2)"),
            ]
            for old, new in substitutions:
                assert text.count(old) == 1
                text = text.replace(old, new, 1)
            data = text.encode("utf-8")
            ast.parse(text)
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)
        files[name] = sha(target)
    changed = [name for name, value in files.items()
               if value != original_record["source_files_exact9"][name]]
    assert changed == [CORE]
    temporary_index = prepared / "candidate.gitindex"
    separate_env = dict(env, GIT_INDEX_FILE=str(temporary_index))
    git("read-tree", PARENT, custom_env=separate_env)
    for name in files:
        blob = git("hash-object", "-w", "--stdin", data=(source / name).read_bytes()).decode().strip()
        git("update-index", "--add", "--cacheinfo", "100644," + blob + "," + name,
            custom_env=separate_env)
    tree = git("write-tree", custom_env=separate_env).decode().strip()
    message = prepared / "commit_message.txt"
    message.write_text("Preserve NDE parameters while factoring shared parent affine computation\n", encoding="utf-8")
    commit = git("commit-tree", tree, "-p", PARENT, "-F", str(message)).decode().strip()
    ref = "refs/pipeline/candidates/M233-NDE-r1"
    git("update-ref", ref, commit, "0" * 40)
    assert git("rev-parse", "refs/pipeline/candidates/M233-NDE").decode().strip() == ORIGINAL_COMMIT
    diff = git("diff", "--name-status", PARENT, commit).decode().splitlines()
    assert len(diff) == 9 and all(line.startswith("A\t") for line in diff)
    assert git("rev-parse", "HEAD").decode().strip() == PARENT
    assert sha(index) == before["index_sha256"]
    assert git("status", "--porcelain=v1", "--untracked-files=all", "-z").hex() == before["status_hex"]
    result = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": prereg["owner"], "candidate_id": prereg["candidate_id"],
        "experiment_id": "M233-NDE", "revision": 1,
        "source_commit": commit, "source_parent_commit": PARENT, "tree": tree,
        "retained_ref": ref, "original_retained_commit": ORIGINAL_COMMIT,
        "preregistration": {"path": (HERE / "nde_revision1_preregistration.json").relative_to(ROOT).as_posix(),
                            "sha256": sha(HERE / "nde_revision1_preregistration.json")},
        "source_files": files, "exact_nine_additions": True,
        "only_changed_from_original": changed,
        "parameter_initialization_and_state_dict_definition_unchanged": True,
        "main_HEAD_unchanged": True, "main_index_unchanged": True,
        "main_worktree_unchanged": True, "native": "NOT_RUN", "resources": "NOT_RUN",
        "Torch_autograd": "NOT_RUN", "queued": False, "deployed": False,
        "training_started": False, "efficacy": "UNKNOWN", "novelty": "UNKNOWN",
    }
    put(prepared / "source_version.json", result)
    print(json.dumps({"status": "REVISION_SOURCE_SAVED_NOT_TESTED",
                      "source_commit": commit, "changed_files": len(changed),
                      "source_version_sha256": sha(prepared / "source_version.json")}))


if __name__ == "__main__":
    main()
