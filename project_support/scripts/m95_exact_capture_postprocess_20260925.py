"""Fail-closed post-processing for the exact M95 full-scan capture.

The running capture must finish before either analyzer is valid. This runner
checks the frozen capture contract first, then executes the component
counterfactual and identity-query analyzers without weakening admission gates.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_MANIFEST_SHA256,
    file_sha256,
    load_artifacts,
    load_json,
    validate_capture,
    validate_manifest_hash,
)
from m95_identity_query_controls_20260923 import PRODUCER_FILES
from m95_exact_capture_reproducibility_20260925 import (
    compare_identity_analyses,
    validate_reference,
)


EXPECTED_PRODUCER_SHA256 = (
    "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
)
EXPECTED_ROWS = 256
EXPECTED_CAPTURE_MODE = "full_train_scan"


def composite_sha256(script_dir, producer_files=PRODUCER_FILES):
    digest = hashlib.sha256()
    for name in producer_files:
        digest.update((Path(script_dir) / name).read_bytes())
    return digest.hexdigest()


def validate_completion_report(
    report,
    expected_producer_sha256=EXPECTED_PRODUCER_SHA256,
):
    required_true = (
        "native_capture_completed",
        "native_match_cause_completed",
        "identity_query_completed",
    )
    for key in required_true:
        if report.get(key) is not True:
            raise ValueError("Capture completion flag differs: %s" % key)

    if report.get("capture_mode") != EXPECTED_CAPTURE_MODE:
        raise ValueError("Capture is not an exact full-train scan")
    if report.get("producer_sha256") != expected_producer_sha256:
        raise ValueError("Capture producer differs from the frozen contract")
    if int(report.get("selected_expressions", -1)) != EXPECTED_ROWS:
        raise ValueError("Capture selected-expression count differs")

    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("Capture does not contain 256 report rows")
    indices = set()
    for row in rows:
        index = int(row.get("manifest_index", -1))
        if index in indices:
            raise ValueError("Duplicate capture manifest index")
        indices.add(index)
        if "native_match_cause" not in row:
            raise ValueError("Capture row lacks native_match_cause")
    if indices != set(range(EXPECTED_ROWS)):
        raise ValueError("Capture manifest coverage differs")


def validate_artifacts(capture_path, report, manifest):
    artifacts = load_artifacts(
        Path(capture_path), report, EXPECTED_MANIFEST_SHA256
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Capture artifact coverage differs")
    for index, artifact in artifacts.items():
        identity = artifact.get("identity_query")
        if not isinstance(identity, dict) or not identity:
            raise ValueError(
                "Artifact %d lacks identity-query bindings" % index
            )
    return artifacts


def validate_postprocess_inputs(
    capture_path,
    manifest_path,
    script_dir,
    expected_producer_sha256=EXPECTED_PRODUCER_SHA256,
):
    capture_path = Path(capture_path).resolve()
    manifest_path = Path(manifest_path).resolve()
    if not capture_path.is_file():
        raise ValueError("Capture report does not exist")
    if not manifest_path.is_file():
        raise ValueError("Frozen manifest does not exist")

    actual_producer_sha256 = composite_sha256(script_dir)
    if actual_producer_sha256 != expected_producer_sha256:
        raise ValueError("Current producer files differ from the frozen contract")

    report = load_json(capture_path)
    validate_completion_report(report, expected_producer_sha256)
    manifest_sha256 = file_sha256(manifest_path)
    manifest = validate_manifest_hash(
        load_json(manifest_path),
        manifest_sha256,
        EXPECTED_MANIFEST_SHA256,
    )
    validate_capture(report, manifest, EXPECTED_CHECKPOINT_SHA256)
    artifacts = validate_artifacts(capture_path, report, manifest)

    return {
        "capture_path": capture_path,
        "capture_sha256": file_sha256(capture_path),
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha256,
        "producer_sha256": actual_producer_sha256,
        "rows": len(report["rows"]),
        "artifacts": len(artifacts),
    }


def build_analyzer_commands(
    component_analyzer,
    identity_analyzer,
    capture_path,
    manifest_path,
    component_output,
    identity_output,
    identity_analysis_output=None,
    python_executable=None,
):
    python_executable = python_executable or sys.executable
    commands = [
        [
            python_executable,
            str(component_analyzer),
            "--capture",
            str(capture_path),
            "--output",
            str(component_output),
            "--manifest",
            str(manifest_path),
        ],
        [
            python_executable,
            str(identity_analyzer),
            "--capture",
            str(capture_path),
            "--output",
            str(identity_output),
        ],
    ]
    if identity_analysis_output is not None:
        commands.append(
            [
                python_executable,
                str(
                    Path(component_analyzer).with_name(
                        "analyze_m95_manifest_identity_controls_20260922.py"
                    )
                ),
                "--capture",
                str(capture_path),
                "--output",
                str(identity_analysis_output),
                "--manifest",
                str(manifest_path),
            ]
        )
    return commands


def run_commands(commands, cwd, runner=subprocess.run):
    completed = []
    for command in commands:
        result = runner(
            command,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
        )
        completed.append(
            {
                "command": command,
                "returncode": int(result.returncode),
                "stdout_sha256": hashlib.sha256(
                    result.stdout.encode("utf-8")
                ).hexdigest(),
                "stderr_tail": result.stderr[-2000:],
            }
        )
        if result.returncode != 0:
            raise RuntimeError(
                "Analyzer failed with exit code %d: %s"
                % (result.returncode, command[1])
            )
    return completed


def write_json(path, document):
    path = Path(path)
    if path.exists():
        raise ValueError("Output already exists: %s" % path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="ascii") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=True, sort_keys=True)
        handle.write("\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--component-output", required=True)
    parser.add_argument("--identity-output", required=True)
    parser.add_argument("--identity-analysis-output", required=True)
    parser.add_argument("--reproducibility-output", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument(
        "--component-analyzer",
        default=str(
            Path(__file__).with_name(
                "native_component_counterfactual_20260924.py"
            )
        ),
    )
    parser.add_argument(
        "--identity-analyzer",
        default=str(
            Path(__file__).with_name(
                "m95_identity_query_controls_20260923.py"
            )
        ),
    )
    parser.add_argument(
        "--expected-producer-sha256",
        default=EXPECTED_PRODUCER_SHA256,
    )
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    component_output = Path(args.component_output).resolve()
    identity_output = Path(args.identity_output).resolve()
    identity_analysis_output = Path(args.identity_analysis_output).resolve()
    reproducibility_output = Path(args.reproducibility_output).resolve()
    receipt_path = Path(args.receipt).resolve()
    for output in (
        component_output,
        identity_output,
        identity_analysis_output,
        reproducibility_output,
        receipt_path,
    ):
        if output.exists():
            raise ValueError("Output already exists: %s" % output)

    script_dir = Path(__file__).resolve().parent
    validation = validate_postprocess_inputs(
        args.capture,
        args.manifest,
        script_dir,
        args.expected_producer_sha256,
    )
    commands = build_analyzer_commands(
        Path(args.component_analyzer).resolve(),
        Path(args.identity_analyzer).resolve(),
        validation["capture_path"],
        validation["manifest_path"],
        component_output,
        identity_output,
        identity_analysis_output,
    )
    document = {
        "schema_version": 1,
        "contract": "m95_exact_capture_postprocess_v1",
        "timestamp": datetime.now().astimezone().isoformat(),
        "status": "validated_no_execution" if args.validate_only else "running",
        "validation": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in validation.items()
        },
        "analyzer_commands": commands,
        "analyzer_results": [],
        "reproducibility_receipt": str(reproducibility_output),
        "admission": False,
        "native_backward_measured": False,
        "resources_measured": False,
        "not_evidence_of": [
            "admission",
            "native backward",
            "resource gate",
            "deployable efficacy",
            "novelty",
            "whole-mechanism benefit",
        ],
    }
    if args.validate_only:
        write_json(receipt_path, document)
        return

    try:
        document["analyzer_results"] = run_commands(commands, script_dir)
        for output in (
            component_output,
            identity_output,
            identity_analysis_output,
        ):
            if not output.is_file():
                raise ValueError("Analyzer did not create %s" % output)
            load_json(output)
        reproducibility = compare_identity_analyses(
            validate_reference(),
            load_json(identity_analysis_output),
        )
        document["reproducibility_status"] = reproducibility["status"]
        document["reproducibility_comparison"] = reproducibility["comparison"]
        write_json(reproducibility_output, reproducibility)
        if reproducibility["status"] != "pass":
            raise ValueError(
                "Exact capture identity analysis does not reproduce"
            )
        document["status"] = "complete"
    except Exception as error:
        document["status"] = "failed"
        document["failure"] = str(error)
        write_json(receipt_path, document)
        raise

    write_json(receipt_path, document)


if __name__ == "__main__":
    main()
