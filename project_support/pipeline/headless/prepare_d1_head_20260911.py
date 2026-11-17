"""Create the frozen head-ownership audit directory and protocol."""
from datetime import datetime
import json
from pathlib import Path

from close_tick_20260911_0707 import EXPECTED
from d1_candidate_bank_20260911 import sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_head_20260911-171500"


def main():
    assert not OUT.exists()
    assert {n: sha(P / n) for n in EXPECTED} == EXPECTED
    protocol = dict(
        created=datetime.now().isoformat(),
        purpose="CPU-only head ownership and synthetic parameter-coupling audit",
        baseline_audit="reports/d0_checkpoint_identity_20260911-0413/d0_baseline_identity_20260911.json",
        m95_audit="reports/d0_checkpoint_identity_20260911-0413/d0_m95_identity_20260911.json",
        baseline_audit_sha256=sha(P / "reports/d0_checkpoint_identity_20260911-0413/d0_baseline_identity_20260911.json"),
        m95_audit_sha256=sha(P / "reports/d0_checkpoint_identity_20260911-0413/d0_m95_identity_20260911.json"),
        source_files={name: sha(P / "headless" / name) for name in (
            "d1_head_ownership_20260911.py",
            "prepare_d1_head_20260911.py",
        )},
        finite_difference_epsilon=1e-5,
        synthetic_seed=1999,
        no_cuda=True,
        no_checkpoint_write=True,
        no_training=True,
        no_real_data_forward=True,
        goal_sha256=sha(P / "goal.json"),
    )
    OUT.mkdir(parents=True)
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    print(OUT, protocol["created"])


if __name__ == "__main__":
    main()
