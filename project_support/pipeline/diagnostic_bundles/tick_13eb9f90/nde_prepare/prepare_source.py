"""Materialize only the isolated nine-file NDE source from the exact parent."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
PARENT = "f6257de79148581334ee495e6e2d60ccb525457c"
OLD = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd"
NEW = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nde"
OLD_PACKAGE = "framework/model/Quard_model/" + OLD
NEW_PACKAGE = "framework/model/Quard_model/" + NEW
OLD_CONFIG = "configs/Quard/ctf_hcg_csort_nsd/" + OLD + ".yaml"
NEW_CONFIG = "configs/Quard/ctf_hcg_csort_nde/" + NEW + ".yaml"
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_bytes())
    assert owner["token"] == "13eb9f90892a472b8102218b83e99ea8"
    assert owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
    assert os.environ.get("CODEX_THREAD_ID")
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sys.dont_write_bytecode and os.environ["GIT_OPTIONAL_LOCKS"] == "0"
    git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
           "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]
    assert subprocess.check_output(git + ["rev-parse", "HEAD"], timeout=15).decode().strip() == PARENT
    entries = []
    for name in ("__init__.py", "backbone.py", "dec.py", "hier_postprocess.py",
                 "loss.py", "network.py", "sample_model.py"):
        old_path = OLD_PACKAGE + "/" + name
        data = subprocess.check_output(git + ["show", PARENT + ":" + old_path], timeout=15)
        original = data
        if name == "hier_postprocess.py":
            replacements = {
                b"from .spatial_dirichlet import HierarchicalSpatialDirichlet":
                    b"from .distribution_embedding import HierarchicalDistributionEmbedding",
                b"'NSD requires the original three hierarchy scales'":
                    b"'NDE requires the original three hierarchy scales'",
                b"self.spatial_dirichlet = HierarchicalSpatialDirichlet(d_model)":
                    b"self.distribution_embedding = HierarchicalDistributionEmbedding(d_model)",
                b"changes = self.spatial_dirichlet(":
                    b"changes = self.distribution_embedding(",
                b"point_feats, point_positions, point_mask, normalized, cluster_ids_list)":
                    b"point_feats, point_mask, normalized, cluster_ids_list)",
            }
            for old, new in replacements.items():
                assert data.count(old) == 1, old
                data = data.replace(old, new, 1)
        new_path = NEW_PACKAGE + "/" + name
        target = SOURCE / new_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == data, "Partial source differs; reconcile without overwrite"
        else:
            with target.open("xb") as stream:
                stream.write(data)
        entries.append({"path": new_path, "sha256": sha(data),
                        "parent_path": old_path, "parent_sha256": sha(original),
                        "byte_exact_parent": data == original})
    data = subprocess.check_output(git + ["show", PARENT + ":" + OLD_CONFIG], timeout=15)
    target = SOURCE / NEW_CONFIG
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == data, "Partial config differs; reconcile without overwrite"
    else:
        with target.open("xb") as stream:
            stream.write(data)
    entries.append({"path": NEW_CONFIG, "sha256": sha(data),
                    "parent_path": OLD_CONFIG, "parent_sha256": sha(data),
                    "byte_exact_parent": True})
    core = SOURCE / NEW_PACKAGE / "distribution_embedding.py"
    assert core.is_file()
    entries.append({"path": core.relative_to(SOURCE).as_posix(),
                    "sha256": sha(core.read_bytes()), "parent_path": None,
                    "new_mechanism": True})
    assert len(entries) == 9
    value = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner_provenance_only": {key: owner[key] for key in KEYS},
        "producer_agent": "/root/reserve_variant",
        "producer_thread_id": os.environ["CODEX_THREAD_ID"],
        "root_identity_impersonated": False,
        "delegated_scope": "Isolated local source and software checks only; no execution binding.",
        "candidate_id": "hierarchy-native-distribution-embedding-composition",
        "experiment_id": "M233-NDE",
        "source_parent_commit": PARENT,
        "isolated_source_root": str(SOURCE),
        "config": NEW_CONFIG,
        "file_count": len(entries),
        "files": entries,
        "command": [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve())],
        "main_index_queue_or_old_source_modified": False,
        "source_commit": None,
        "runtime_root": None,
        "execution_binding": None,
        "native": "NOT_RUN",
        "resources": "NOT_RUN",
        "efficacy": "UNKNOWN",
        "novelty": "UNKNOWN",
    }
    with (HERE / "source_version.json").open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "ISOLATED_NDE_SOURCE_ONLY", "files": len(entries),
                      "source_parent_commit": PARENT}))


if __name__ == "__main__":
    main()
