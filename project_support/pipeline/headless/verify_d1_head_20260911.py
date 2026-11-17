"""Verify the CPU head-ownership audit and render its bounded diagnostic report."""
from datetime import datetime
import json
from pathlib import Path

from d1_candidate_bank_20260911 import sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_head_20260911-171500"


def close(a, b, tolerance=1e-6):
    return abs(float(a) - float(b)) <= tolerance


def main():
    protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
    execution = json.loads((OUT / "execution.json").read_text(encoding="utf-8"))
    baseline = json.loads((OUT / "baseline.json").read_text(encoding="utf-8"))
    m95 = json.loads((OUT / "m95.json").read_text(encoding="utf-8"))
    assert execution["baseline_returncode"] == execution["m95_returncode"] == 0
    assert execution["baseline_sha256"] == sha(OUT / "baseline.json")
    assert execution["m95_sha256"] == sha(OUT / "m95.json")
    assert execution["no_training"] is True
    assert execution["no_real_data_forward"] is True
    assert execution["no_checkpoint_write"] is True
    assert baseline["cuda_visible_devices"] == m95["cuda_visible_devices"] == ""
    assert baseline["workers"][0]["cuda_initialized"] is False
    assert m95["workers"][0]["cuda_initialized"] is False

    b = baseline["workers"][0]
    m = m95["workers"][0]
    assert b["model"] == "baseline" and m["model"] == "m95"
    assert b["checkpoint_sha256"] == "dbc37e8fe8428f0f295121df61fae8a9ffd7dd98c10913ef911354345ff16745"
    assert m["checkpoint_sha256"] == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    assert b["ownership"]["layer_count"] == m["ownership"]["layer_count"] == 6
    assert b["ownership"]["unique_head_module_ids"] == 1
    assert b["ownership"]["shared_module_object"] is True
    assert b["ownership"]["shared_parameter_object"] is True
    assert b["ownership"]["shared_storage_pointer"] is True
    assert b["ownership"]["unique_head_parameter_objects"] == 6
    assert b["ownership"]["total_head_parameter_objects"] == 36
    assert b["ownership"]["state_head_key_count"] == 36
    assert len(b["ownership"]["duplicate_value_groups"]) == 6
    assert all(group["all_equal"] for group in b["ownership"]["duplicate_value_groups"])
    assert len(b["ownership"]["checkpoint_duplicate_value_groups"]) == 6
    assert all(group["checkpoint_values_equal"] is True
               for group in b["ownership"]["checkpoint_duplicate_value_groups"])
    assert m["ownership"]["unique_head_module_ids"] == 6
    assert m["ownership"]["shared_module_object"] is False
    assert m["ownership"]["shared_parameter_object"] is False
    assert m["ownership"]["shared_storage_pointer"] is False
    assert m["ownership"]["unique_head_parameter_objects"] == 36
    assert m["ownership"]["total_head_parameter_objects"] == 36
    assert m["ownership"]["state_head_key_count"] == 36
    assert m["ownership"]["duplicate_value_groups"] == []
    assert m["ownership"]["checkpoint_duplicate_value_groups"] == []

    for worker in (b, m):
        tied = worker["synthetic_shared"]
        independent = worker["synthetic_independent"]
        assert tied["shared_parameters"] is True
        assert independent["shared_parameters"] is False
        assert abs(tied["cross_layer_coupling"]) > 1e-6
        assert independent["cross_layer_coupling"] == 0
        assert close(tied["local_margin_velocity"] + tied["cross_layer_coupling"],
                     tied["total_margin_velocity"])
        assert close(independent["local_margin_velocity"],
                     independent["total_margin_velocity"])
        assert close(tied["finite_difference"], tied["total_margin_velocity"])
        assert close(independent["finite_difference"], independent["total_margin_velocity"])
        assert tied["finite_difference_error"] <= 1e-6
        assert independent["finite_difference_error"] <= 1e-6
        assert not tied["relu_crossing_warning"]
        assert not independent["relu_crossing_warning"]

    current_sources = {
        name: sha(P / "headless" / name)
        for name in ("d1_head_ownership_20260911.py", "run_d1_head_20260911.py")
    }
    retry_protocol = dict(protocol)
    retry_protocol.update(
        protocol_initial_sha256=sha(OUT / "protocol.json"),
        source_files_current=current_sources,
        repair_history=[
            "attempt0 failed before model load: margin output was not scalar",
            "attempt1 failed before model load: importing baseline and M95 in one process collided on gorilla criterion registration",
            "attempt2 completed but the finite-difference control exposed a sign mismatch in the synthetic comparison",
            "attempt3 passed all ownership, coupling, finite-difference, and CUDA-hidden checks",
        ],
    )
    (OUT / "protocol_retry3.json").write_text(
        json.dumps(retry_protocol, indent=2), encoding="utf-8"
    )

    result = dict(
        status="passed",
        created=datetime.now().isoformat(),
        protocol_initial_sha256=sha(OUT / "protocol.json"),
        protocol_retry3_sha256=sha(OUT / "protocol_retry3.json"),
        baseline=dict(
            head_module_ids=b["ownership"]["layer_head_module_ids"],
            unique_head_module_ids=b["ownership"]["unique_head_module_ids"],
            shared_module_object=b["ownership"]["shared_module_object"],
            shared_parameter_object=b["ownership"]["shared_parameter_object"],
            shared_storage_pointer=b["ownership"]["shared_storage_pointer"],
            unique_parameter_objects=b["ownership"]["unique_head_parameter_objects"],
            total_parameter_objects=b["ownership"]["total_head_parameter_objects"],
            duplicate_checkpoint_groups=len(b["ownership"]["checkpoint_duplicate_value_groups"]),
            duplicate_checkpoint_values_equal=all(
                group["checkpoint_values_equal"]
                for group in b["ownership"]["checkpoint_duplicate_value_groups"]
            ),
        ),
        m95=dict(
            head_module_ids=m["ownership"]["layer_head_module_ids"],
            unique_head_module_ids=m["ownership"]["unique_head_module_ids"],
            shared_module_object=m["ownership"]["shared_module_object"],
            shared_parameter_object=m["ownership"]["shared_parameter_object"],
            shared_storage_pointer=m["ownership"]["shared_storage_pointer"],
            unique_parameter_objects=m["ownership"]["unique_head_parameter_objects"],
            total_parameter_objects=m["ownership"]["total_head_parameter_objects"],
            duplicate_checkpoint_groups=len(m["ownership"]["checkpoint_duplicate_value_groups"]),
        ),
        synthetic=dict(
            baseline=dict(
                tied=b["synthetic_shared"],
                independent=b["synthetic_independent"],
            ),
            m95=dict(
                tied=m["synthetic_shared"],
                independent=m["synthetic_independent"],
            ),
            tolerance=1e-6,
        ),
        source_hashes=current_sources,
        limitations=[
            "No real ScanRefer forward pass and no real head-input features.",
            "No optimizer, Adam state, dropout, augmentation, or full loss replay.",
            "Parameter tying and chain-rule coupling are standard methods, not primary novelty.",
            "The audit establishes implementation identity only; it does not explain M95 errors.",
        ],
    )
    (OUT / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    report = f"""# D1 Head Ownership And Synthetic Coupling Audit

Completed {datetime.now().isoformat()} Asia/Shanghai. This is a CPU-only
implementation audit. It performed no real-data forward pass, no training, no
checkpoint write, and no GPU allocation.

## Contract

The baseline checkpoint resolves all six decoder-layer `indi_embedding`
attributes to one module object:

    unique module objects       = 1
    unique parameter objects    = 6
    total parameter references  = 36
    state head keys             = 36
    duplicate checkpoint groups = 6
    all duplicate values equal  = True

The M95 checkpoint resolves to six independent module objects:

    unique module objects       = 6
    unique parameter objects    = 36
    total parameter references  = 36
    state head keys             = 36
    duplicate checkpoint groups = 0

Thus the earlier source-text difference is confirmed at the object, storage,
state-dict, and checkpoint levels. The baseline truly ties its layer heads; M95
does not.

## Synthetic Gradient Check

For tied heads, the exact chain-rule decomposition is:

    dm_1/dt = local_margin_velocity + cross_layer_coupling
            = 178.2748994052913 + 178.2748994052913
            = 356.5497988105826

The centered finite-difference value is 356.5497997229938, error
9.124111670644197e-7. For the independent control, the cross-layer term is
exactly zero and the finite-difference error is 1.1405705890865647e-7.
The minimum absolute ReLU preactivation is 2.4493639190169967, so no ReLU
crossing contaminated this synthetic check.

The M95 synthetic tied control gives 60.275037792112315 versus finite difference
60.27503783002374, error 3.7911426886694244e-8. Its independent control gives
30.137518896056157 and is consistent with finite difference to 4.8e-9.

## Interpretation

This confirms an implementation difference, not an error cause. A tied head has
a standard cross-layer gradient path; independent heads do not. The real losses,
real inputs, optimizer state, dropout, augmentation, and full decoder graph
remain outside the audit. Parameter tying and the chain rule are not novel.

The result also does not make a shared head an admissible replacement. The
baseline already has tied heads and is below M95 in this frozen diagnostic
sample. The next research step cannot be "adopt sharing" or any successor
selector/readback variant.

## Decision

Record the exact ownership contract and keep the shared-head question as a
diagnostic fact. Do not admit a mechanism and do not enqueue training. Any real
head-input capture must wait for a separately justified protocol and free
resource allocation. The next admissible work remains the search for one
evidence-selected mechanism with a non-standard forward/loss graph, explicit
gradient derivation, primary-source comparison, matched control, and
preregistered rejection condition.

## Provenance

- Initial protocol: `{sha(OUT / "protocol.json")}`
- Retry protocol: `{sha(OUT / "protocol_retry3.json")}`
- Baseline result: `{sha(OUT / "baseline.json")}`
- M95 result: `{sha(OUT / "m95.json")}`
- Worker: `{current_sources["d1_head_ownership_20260911.py"]}`
- Runner: `{current_sources["run_d1_head_20260911.py"]}`

The first two helper failures and the finite-difference sign repair are
preserved in `baseline_attempt1.log`, `m95_attempt1.log`, and
`execution_attempt1.json`.
"""
    (OUT / "diagnostic_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
