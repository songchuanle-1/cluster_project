#!/usr/bin/env python3
"""Read-only source inventory; writes only migration handoff artifacts.

From an exported repository root:
  python -B experiments/build_experiment_inventory.py --project-root project_support --verify

From the original source project root:
  python -B pipeline/handoffs/20261117_github_migration/experiments/build_experiment_inventory.py --project-root . --verify

Uses Python's standard library. Does not import project code, Torch, models,
pipeline control code, or read diagnostic-bundle contents. No network access.
Verification preserves the historical snapshot. Layout-dependent config lookup
fields and the historical producer stamp are not training facts.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import pathlib
import re
import sys
from typing import Any

sys.dont_write_bytecode = True

DEFAULT_AS_OF = "2026-11-17"
DONE_STATES = {"done_complete", "done_earlystop"}
TERMINAL_STATES = DONE_STATES | {"stopped_unknown", "crashed", "withdrawn"}
STATE_ORDER = [
    "done_complete", "done_earlystop", "stopped_unknown", "crashed",
    "paused_by_user", "waiting", "withdrawn", "running", "unknown",
]
KEY_ANALYSES = {
    "C2-posC": "C2-posC_done_earlystop_20260719-101945.md",
    "F1-2layer": "F1-2layer_stopped_unknown_20260719-233147.md",
    "M17-ORT": "M17-ORT_done_earlystop_20260724-060301.md",
    "M22-XCA": "M22-XCA_done_earlystop_20260725-210301.md",
    "M95-CTF-HCG-CSORT": "M95-CTF-HCG-CSORT_done_earlystop_20260816-031216.md",
    "M174-CTF-HCG-CSORT-MQHC":
        "M174-CTF-HCG-CSORT-MQHC_done_earlystop_20260908-011244.md",
    "M184-CTF-HCG-CSORT-MQST-TR":
        "M184-CTF-HCG-CSORT-MQST-TR_done_earlystop_20260912-171500.md",
    "M195-CTF-HCG-CSORT-CPS":
        "M195-CTF-HCG-CSORT-CPS_done_earlystop_20260915-2110.md",
    "M196-CTF-HCG-CSORT-BCA":
        "M196-CTF-HCG-CSORT-BCA_done_earlystop_20260916-0710.md",
    "M202-HDS": "M202-HDS_done_earlystop_20261017_21500d1a.md",
    "M226-WFC":
        "M226-WFC_done_earlystop_ead6b5a9edf2466ea96e2587c931c865_native.md",
    "M235-SINC":
        "M235-SINC_crashed_b75c9152d7fd4ecea9af538101d777d4_supplement.md",
}
KNOWN_COMPLETION_LIMITS = {
    "M174-CTF-HCG-CSORT-MQHC": {
        "scope": "partial_patience_monitor_parser_defect",
        "last_complete_validation": 22, "failed_partial_epoch": 23,
        "note": "VAL17峰值后只有5次完整验证；monitor把spmIOU误匹配为mIoU，未完成patience10。",
    },
    "M195-CTF-HCG-CSORT-CPS": {
        "scope": "termination_provenance_unconfirmed_partial",
        "last_complete_validation": 27, "failed_partial_epoch": 28,
        "failed_partial_step": 1410,
        "note": "native日志止于epoch28 step1410；峰值后仅7次完整验证，无native早停footer，停止归因未核实。",
    },
    "M196-CTF-HCG-CSORT-BCA": {
        "scope": "termination_provenance_unconfirmed_partial",
        "last_complete_validation": 22, "failed_partial_epoch": 23,
        "failed_partial_step": 260,
        "note": "native日志止于epoch23 step260；峰值后仅5次完整验证，patience10完成未建立。",
    },
}


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def display(value: Any) -> str:
    return "" if value is None else str(value)


def count_values(values: Any) -> dict[str, int]:
    counts = collections.Counter(values)
    return {k: counts[k] for k in sorted(counts, key=str)}


def sort_id(exp_id: str) -> tuple[Any, ...]:
    match = re.match(r"^M(\d+)(?:-|$)", exp_id)
    return (0, int(match[1]), exp_id) if match else (1, 0, exp_id)


def m_number(exp_id: str) -> int | None:
    match = re.match(r"^M(\d+)(?:-|$)", exp_id)
    return int(match[1]) if match else None


def dig(value: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def pointer_refs(value: Any, limit: int = 8) -> list[dict[str, str]]:
    """Select bounded path/hash references, never copy contexts/logs/owners."""
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def visit(obj: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(obj, str) and obj.startswith("pipeline/"):
            pair = (obj, "")
            if pair not in seen:
                found.append({"path": obj})
                seen.add(pair)
        elif isinstance(obj, dict):
            path = obj.get("path")
            if isinstance(path, str):
                digest = obj.get("sha256")
                pair = (path, str(digest or ""))
                if pair not in seen:
                    item = {"path": path}
                    if isinstance(digest, str):
                        item["sha256"] = digest
                    found.append(item)
                    seen.add(pair)
            for key in ("evidence", "receipt", "admission"):
                if key in obj:
                    visit(obj[key])
        elif isinstance(obj, list):
            for item in obj:
                visit(item)
                if len(found) >= limit:
                    break

    visit(value)
    return found


class Sources:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.manifest: dict[str, dict[str, Any]] = {}

    def read(self, relative: str) -> str:
        value = (self.root / relative).read_bytes()
        self.manifest[relative] = {
            "path": relative, "bytes": len(value), "sha256": sha256_bytes(value),
        }
        return value.decode("utf-8-sig")

    def json(self, relative: str) -> Any:
        return json.loads(self.read(relative))

    def validate_unchanged(self) -> None:
        for relative, item in self.manifest.items():
            current = (self.root / relative).read_bytes()
            if sha256_bytes(current) != item["sha256"]:
                raise RuntimeError(f"Input changed during inventory: {relative}")


def build(root: pathlib.Path, as_of: str) -> dict[str, str]:
    src = Sources(root)
    csv_text = src.read("pipeline/experiments.csv")
    reader = csv.DictReader(io.StringIO(csv_text, newline=""))
    csv_columns = list(reader.fieldnames or [])
    csv_rows = list(reader)
    csv_by_id: dict[str, list[tuple[int, dict[str, str]]]] = collections.defaultdict(list)
    for line, row in enumerate(csv_rows, start=2):
        if not row.get("id"):
            raise ValueError(f"CSV row {line} has no id")
        csv_by_id[row["id"]].append((line, row))

    archives: dict[str, dict[str, Any]] = {}
    archive_paths: dict[str, str] = {}
    archive_schemas: collections.Counter[str] = collections.Counter()
    for path in sorted((root / "pipeline/experiments").glob("*.json")):
        relative = path.relative_to(root).as_posix()
        record = src.json(relative)
        exp_id = record.get("id", path.stem)
        if exp_id in archives:
            raise ValueError(f"Duplicate full archive ID: {exp_id}")
        archives[exp_id] = record
        archive_paths[exp_id] = relative
        for key in record:
            archive_schemas[key] += 1

    work = src.json("pipeline/research_work.json")
    candidates = work["candidates"]
    candidate_by_exp: dict[str, list[tuple[int, dict[str, Any]]]] = collections.defaultdict(list)
    for index, candidate in enumerate(candidates):
        if candidate.get("experiment_id"):
            candidate_by_exp[candidate["experiment_id"]].append((index, candidate))
    if len({c["id"] for c in candidates}) != len(candidates):
        raise ValueError("Candidate IDs are duplicated; add explicit resolution before proceeding")

    queue = src.json("pipeline/queue.json")
    queue_by_id: dict[str, dict[str, Any]] = {}
    queue_refs: dict[str, str] = {}
    queue_servers: dict[str, str] = {}
    for server, records in queue["gpu_queues"].items():
        for index, record in enumerate(records):
            exp_id = record["id"]
            if exp_id in queue_by_id:
                raise ValueError(f"Duplicate full queue ID: {exp_id}")
            queue_by_id[exp_id] = record
            queue_refs[exp_id] = f"pipeline/queue.json#/gpu_queues/{server}/{index}"
            queue_servers[exp_id] = server

    analyses: dict[str, str] = {}
    analysis_paths: dict[str, str] = {}
    for exp_id, filename in KEY_ANALYSES.items():
        relative = "pipeline/analyses/" + filename
        analyses[exp_id] = src.read(relative)
        analysis_paths[exp_id] = relative
    # Curated evidence associations are assertions against actual saved text.
    # They are not generated training results.
    assert "0.4968" in analyses["C2-posC"] and "State: done_earlystop" in analyses["C2-posC"]
    assert "stopped_unknown" in analyses["F1-2layer"] and "无任何验证" in analyses["F1-2layer"]
    assert "partial-patience" in analyses["M174-CTF-HCG-CSORT-MQHC"]
    assert "not independently confirmed" in analyses["M195-CTF-HCG-CSORT-CPS"]
    assert "completion and converged plateau are not established" in analyses["M196-CTF-HCG-CSORT-BCA"]
    assert "0.5024607181549072" in analyses["M202-HDS"]
    assert "NOT verified as historical champion weights" in analyses["M202-HDS"]
    assert "0.4894491136074066" in analyses["M184-CTF-HCG-CSORT-MQST-TR"]

    ids = set(csv_by_id) | set(archives) | set(queue_by_id) | set(candidate_by_exp)
    status_conflicts: list[dict[str, Any]] = []
    metric_conflicts: list[dict[str, Any]] = []
    candidate_stale_fields: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []

    for exp_id in sorted(ids, key=sort_id):
        rows = csv_by_id.get(exp_id, [])
        archive = archives.get(exp_id, {})
        queued = queue_by_id.get(exp_id, {})
        linked = candidate_by_exp.get(exp_id, [])
        candidate = linked[-1][1] if linked else {}
        notes: list[str] = []
        evidence: list[str] = []
        if rows:
            line, selected = rows[-1]
            status = selected["state"]
            status_source = f"pipeline/experiments.csv:{line}"
            resolution = "latest_csv_append"
            reported_best = selected.get("best_miou")
            epochs = selected.get("epochs", "")
            finished = selected.get("finished_at", "")
            config = selected.get("config", "")
            server = selected.get("server", "")
            gpu = selected.get("gpu", "")
            evidence.extend(f"pipeline/experiments.csv:{n}" for n, _ in rows)
        elif queued and queued.get("status") != "running":
            selected = queued
            status = selected.get("status", "unknown")
            status_source = queue_refs[exp_id]
            resolution = "queue_terminal_or_waiting_without_csv"
            reported_best = selected.get("final_best")
            epochs = selected.get("epochs_final", "")
            finished = selected.get("finished_at", "")
            config = selected.get("config", "")
            server = selected.get("server") or queue_servers.get(exp_id, "")
            gpu = selected.get("gpu", "")
        else:
            selected = archive or queued
            status = selected.get("status", "unknown")
            status_source = archive_paths.get(exp_id, queue_refs.get(exp_id, ""))
            resolution = "archive_without_terminal_csv_or_queue"
            reported_best = selected.get("final_best")
            epochs = selected.get("epochs_final", "")
            finished = selected.get("finished_at", "")
            config = selected.get("config", candidate.get("config", ""))
            server = selected.get("server", "")
            gpu = selected.get("gpu", "")

        metric_source = status_source
        if archive:
            evidence.append(archive_paths[exp_id])
        if queued:
            evidence.append(queue_refs[exp_id])
        for index, _ in linked:
            evidence.append(f"pipeline/research_work.json#/candidates/{index}")
        if exp_id in analysis_paths:
            evidence.append(analysis_paths[exp_id])

        pause_record = archive if archive.get("training_status") == "paused_by_user" else queued
        paused = pause_record.get("training_status") == "paused_by_user"
        if paused:
            status = "paused_by_user"
            resolution = "explicit_manual_pause_overrides_generic_waiting"
            status_source = (
                archive_paths[exp_id] if archive.get("training_status") == "paused_by_user"
                else queue_refs[exp_id]
            )
            notes.append("人工暂停；未获自动恢复授权。等待不等于从未训练。")
        if exp_id == "C2-posC":
            status, reported_best = "done_earlystop", "0.4968"
            epochs, finished = "23/50 (analysis)", "2026-07-19T10:15 (analysis)"
            resolution = "targeted_saved_terminal_analysis_over_stale_running"
            status_source = metric_source = analysis_paths[exp_id]
        if exp_id == "F1-2layer":
            status, reported_best = "stopped_unknown", None
            epochs, finished = "partial epoch1 iter410/4686; validation0", "2026-07-19T23:09 (analysis)"
            resolution = "targeted_saved_terminal_analysis_over_stale_running"
            status_source = metric_source = analysis_paths[exp_id]
            notes.append("手动终止让位；完整epoch0、验证0、无checkpoint。")
        if exp_id == "M236-CSO":
            assert candidate.get("full_training_started") is False
            assert candidate.get("native_status") == "PASSED"
            assert candidate.get("resource_status") == "PASSED"
            notes.append("native/resources技术准入PASS、已入队；完整训练尚未启动，efficacy/novelty UNKNOWN。")
        if exp_id in KNOWN_COMPLETION_LIMITS:
            notes.append(KNOWN_COMPLETION_LIMITS[exp_id]["note"])

        result_scope = {
            "done_complete": "ledger_reports_finished_not_comprehensive_native_audit",
            "done_earlystop": "ledger_reports_finished_not_comprehensive_native_audit",
            "stopped_unknown": "stopped_completion_unknown",
            "crashed": "crashed_incomplete_no_efficacy_claim",
            "paused_by_user": "paused_incomplete",
            "waiting": "not_started_waiting",
            "withdrawn": "withdrawn_no_completed_training_evidence",
            "running": "running_snapshot_unverified_current_process",
        }.get(status, "unknown")
        patience = "not_comprehensively_audited"
        if exp_id in KNOWN_COMPLETION_LIMITS:
            result_scope = KNOWN_COMPLETION_LIMITS[exp_id]["scope"]
            patience = "not_established"
        if exp_id in {"M17-ORT", "M22-XCA", "M202-HDS", "M226-WFC", "M229-MIC"}:
            patience = "explicit_saved_evidence_of_patience10"

        raw_statuses: list[dict[str, Any]] = []
        raw_metrics: list[dict[str, Any]] = []
        if rows:
            line, row = rows[-1]
            raw_statuses.append({"source": f"pipeline/experiments.csv:{line}", "status": row["state"]})
            raw_metrics.append({"source": f"pipeline/experiments.csv:{line}", "raw_best": row["best_miou"]})
        if archive:
            raw_statuses.append({"source": archive_paths[exp_id], "status": archive.get("status")})
            raw_metrics.append({"source": archive_paths[exp_id], "raw_best": archive.get("final_best")})
        if queued:
            raw_statuses.append({"source": queue_refs[exp_id], "status": queued.get("status")})
            raw_metrics.append({"source": queue_refs[exp_id], "raw_best": queued.get("final_best")})
        if exp_id in {"C2-posC", "F1-2layer"}:
            raw_statuses.append({"source": analysis_paths[exp_id], "status": status})
        status_conflict = len({r["status"] for r in raw_statuses}) > 1
        if status_conflict:
            status_conflicts.append({
                "experiment_id": exp_id, "sources": raw_statuses, "selected_status": status,
                "selected_source": status_source, "rule": resolution,
            })
        numeric_metrics = [number(r["raw_best"]) for r in raw_metrics]
        numeric_metrics = [value for value in numeric_metrics if value is not None]
        metric_conflict = len(numeric_metrics) > 1 and max(numeric_metrics) - min(numeric_metrics) > 0.0001
        if metric_conflict:
            metric_conflicts.append({
                "experiment_id": exp_id, "sources": raw_metrics,
                "selected_raw_best": reported_best, "selected_source": metric_source,
                "rule": "retain_selected_status_record_metric_and_expose_source_disagreement",
            })
        stale = candidate.get("training_status")
        if stale == "running" and status in TERMINAL_STATES:
            candidate_stale_fields.append({
                "experiment_id": exp_id, "candidate_training_status": stale,
                "selected_status": status, "selected_source": status_source,
                "rule": "candidate_stage_and_historical_fields_do_not_override_terminal_training_archive",
            })
            notes.append("candidate.training_status残留running；以实际terminal账本为准。")
        if archive.get("status") == "running" and status != "running":
            notes.append("实验JSON的running为旧快照，已有后续终态证据。")

        precise: Any = None
        precise_kind = ""
        precise_source = ""
        saved_epoch: Any = None
        last_validation: Any = None
        partial_epoch: Any = None
        partial_step: Any = None

        if exp_id in KNOWN_COMPLETION_LIMITS:
            limit = KNOWN_COMPLETION_LIMITS[exp_id]
            last_validation = limit.get("last_complete_validation")
            partial_epoch = limit.get("failed_partial_epoch")
            partial_step = limit.get("failed_partial_step")
        analysis_metrics = {
            "model_base1": ("0.4894491136074066", "exact_baseline_reference_cited_not_reaudited",
                            analysis_paths["M184-CTF-HCG-CSORT-MQST-TR"]),
            "M95-CTF-HCG-CSORT": ("0.5024607181549072", "frozen_M95_reference_historical_weight_identity_unverified",
                                   analysis_paths["M202-HDS"]),
            "M174-CTF-HCG-CSORT-MQHC": ("0.4934916496", "recovered_native_log_precise_cited",
                                       analysis_paths["M174-CTF-HCG-CSORT-MQHC"]),
            "M195-CTF-HCG-CSORT-CPS": ("0.4986896216869354", "native_log_exact_cited_incomplete_termination",
                                      analysis_paths["M195-CTF-HCG-CSORT-CPS"]),
            "M196-CTF-HCG-CSORT-BCA": ("0.47992366552352905", "native_log_exact_cited_incomplete_termination",
                                      analysis_paths["M196-CTF-HCG-CSORT-BCA"]),
            "M202-HDS": ("0.4946560263633728", "complete_native_best_and_frozen_full_VAL",
                         analysis_paths["M202-HDS"]),
            "M226-WFC": ("0.49711745977401733", "complete_experiment_restored_history_exact_best",
                         analysis_paths["M226-WFC"]),
            "M235-SINC": ("0.2787637412548065", "saved_checkpoint_metadata_partial_training",
                          analysis_paths["M235-SINC"]),
        }
        if exp_id in analysis_metrics:
            precise, precise_kind, precise_source = analysis_metrics[exp_id]
            if exp_id != "model_base1":
                assert str(precise) in src.read(precise_source)
            evidence.append(precise_source)
        if paused:
            paused_run = pause_record.get("paused_run", {})
            meta = paused_run.get("meta") or paused_run.get("checkpoint_meta") or {}
            precise = meta.get("best_miou")
            precise_kind = "saved_checkpoint_metadata_paused_not_final"
            precise_source = status_source + "#/paused_run"
            saved_epoch = meta.get("epoch")
        if exp_id == "M229-MIC":
            term = candidate.get("terminal_result", {})
            precise = term.get("best_miou")
            precise_kind = "complete_native_terminal_result"
            precise_source = evidence[-1] if not linked else f"pipeline/research_work.json#/candidates/{linked[-1][0]}/terminal_result"
            last_validation = term.get("completed_validation_count")
        if exp_id == "M230-HVD":
            precise = candidate.get("exact_saved_best")
            precise_kind = "saved_checkpoint_metadata_crashed_not_final"
            precise_source = f"pipeline/research_work.json#/candidates/{linked[-1][0]}/exact_saved_best"
            saved_epoch = candidate.get("last_complete_epoch")
            partial_epoch = candidate.get("failed_partial_epoch")
            partial_step = candidate.get("failed_partial_step")
        if exp_id == "M231-PSC":
            saved_epoch, partial_epoch, partial_step = 1, 2, 984
            notes.append("candidate.next_action记载saved epoch1、partial epoch2/984；未据此推定完整训练。")
        if exp_id == "M232-NSD":
            training = candidate.get("training", {})
            saved_epoch = training.get("complete_epochs")
            last_validation = training.get("complete_validation_count")
            partial_epoch = training.get("last_observed_partial_epoch")
            partial_step = training.get("last_observed_partial_step")
        if exp_id == "M233-NDE":
            training = candidate.get("native_full_training", {})
            saved_epoch = training.get("complete_epochs_observed")
            last_validation = training.get("completed_validations")
            partial_epoch, partial_step = training.get("epoch"), training.get("native_step")
        if exp_id == "M234-RVE":
            terminal = candidate.get("terminal_observation", {})
            precise = terminal.get("saved_checkpoint_best_miou")
            precise_kind = "saved_checkpoint_metadata_crashed_not_canonical_archive_best"
            precise_source = f"pipeline/research_work.json#/candidates/{linked[-1][0]}/terminal_observation"
            saved_epoch = terminal.get("saved_complete_epoch")
            partial_epoch, partial_step = terminal.get("partial_epoch"), terminal.get("partial_batch")
            notes.append("canonical best为UNKNOWN；另列checkpoint epoch1标量，二者不可互相替代。")
        if exp_id == "M235-SINC":
            saved_epoch, partial_epoch, partial_step = 1, 2, 1870
            notes.append("仅完整saved epoch1及partial epoch2/1870；0.2790为归档舍入值。")
        if exp_id == "M95-CTF-HCG-CSORT":
            notes.append("历史champion账本0.5020；0.5024607181549072是frozen M95 epoch16 full-VAL参考，权重历史身份未核实。")

        config = config or archive.get("config") or queued.get("config") or candidate.get("config", "")
        inventory.append({
            "experiment_id": exp_id,
            "m_number": m_number(exp_id),
            "id_family": "M" if m_number(exp_id) is not None else "legacy_non_M",
            "canonical_status": status,
            "training_result_scope": result_scope,
            "patience10_evidence": patience,
            "reported_best_raw": reported_best,
            "reported_best_miou": number(reported_best),
            "reported_metric_source": metric_source,
            "precise_or_reference_best_miou": precise,
            "precise_metric_kind": precise_kind,
            "precise_metric_source": precise_source,
            "epochs_reported": epochs,
            "saved_complete_epoch": saved_epoch,
            "last_complete_validation": last_validation,
            "failed_partial_epoch": partial_epoch,
            "failed_partial_step": partial_step,
            "config": config,
            "config_exists_at_repo_root": (root / config).is_file() if config else False,
            "config_exists_at_Cluster_root": (root / "Cluster" / config).is_file() if config else False,
            "config_local_paths_checked_roots_only": ";".join(
                str(path.relative_to(root).as_posix())
                for path in [root / config, root / "Cluster" / config]
                if config and path.is_file()
            ),
            "server": server or archive.get("server") or queue_servers.get(exp_id, ""),
            "gpu": gpu if gpu is not None else "",
            "launched_at": archive.get("launched") or queued.get("launched")
                or dig(pause_record, "paused_run", "launched")
                or dig(pause_record, "paused_run", "original_task", "launched") or "",
            "finished_at": finished,
            "source_commit": archive.get("code_commit") or queued.get("code_commit")
                or candidate.get("code_commit") or candidate.get("source_commit") or "",
            "csv_row_count": len(rows),
            "csv_line_numbers": ";".join(str(line) for line, _ in rows),
            "archive_path": archive_paths.get(exp_id, ""),
            "archive_id": archive.get("archive_id", ""),
            "queue_ref": queue_refs.get(exp_id, ""),
            "candidate_ids": ";".join(c["id"] for _, c in linked),
            "candidate_stages": ";".join(str(c.get("stage", "")) for _, c in linked),
            "candidate_native_status": candidate.get("native_status") or candidate.get("native") or "",
            "candidate_resource_status": candidate.get("resource_status") or candidate.get("resources") or "",
            "candidate_technical_admission": candidate.get("technical_admission"),
            "candidate_scientific_admission": candidate.get("scientific_admission"),
            "candidate_efficacy": candidate.get("efficacy", ""),
            "candidate_novelty": candidate.get("novelty", ""),
            "selected_status_source": status_source,
            "resolution_rule": resolution,
            "source_status_conflict": status_conflict,
            "source_metric_conflict": metric_conflict,
            "evidence_refs": ";".join(dict.fromkeys(evidence)),
            "notes": " ".join(notes),
        })

    inv_by_id = {r["experiment_id"]: r for r in inventory}
    numbers = sorted({r["m_number"] for r in inventory if r["m_number"] is not None})
    number_aliases = {
        str(num): [r["experiment_id"] for r in inventory if r["m_number"] == num]
        for num in numbers if sum(r["m_number"] == num for r in inventory) > 1
    }
    exact_groups: dict[tuple[str, ...], list[int]] = collections.defaultdict(list)
    for line, row in enumerate(csv_rows, 2):
        exact_groups[tuple(row[column] for column in csv_columns)].append(line)
    duplicated_ids = [
        {"experiment_id": exp_id, "csv_lines": [line for line, _ in rows],
         "states_in_append_order": [row["state"] for _, row in rows],
         "selected_last_line": rows[-1][0]}
        for exp_id, rows in sorted(csv_by_id.items(), key=lambda pair: sort_id(pair[0]))
        if len(rows) > 1
    ]

    candidate_compact: list[dict[str, Any]] = []
    cross: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for index, candidate in enumerate(candidates):
        exp_id = candidate.get("experiment_id")
        result = inv_by_id.get(exp_id, {})
        stage = candidate.get("stage", "unknown")
        if exp_id:
            cross[stage][result.get("canonical_status", "unknown")] += 1
        candidate_compact.append({
            "id": candidate["id"], "stage": stage, "experiment_id": exp_id,
            "training_status_from_inventory": result.get("canonical_status"),
            "candidate_training_status_raw": candidate.get("training_status"),
            "native_status_raw": candidate.get("native_status") or candidate.get("native"),
            "resource_status_raw": candidate.get("resource_status") or candidate.get("resources"),
            "technical_admission_raw": candidate.get("technical_admission"),
            "scientific_admission_raw": candidate.get("scientific_admission"),
            "full_training_started_raw": candidate.get("full_training_started"),
            "efficacy_raw": candidate.get("efficacy"),
            "novelty_raw": candidate.get("novelty"),
            "source_ref": f"pipeline/research_work.json#/candidates/{index}",
            "evidence_pointers_not_opened": pointer_refs(
                [candidate.get("admission_receipt"), candidate.get("evidence", [])]
            ),
        })

    ledger_done = [r for r in inventory if r["canonical_status"] in DONE_STATES]
    counts = {
        "csv_rows": len(csv_rows),
        "csv_unique_full_ids": len(csv_by_id),
        "csv_excess_rows_over_full_id_dedup": len(csv_rows) - len(csv_by_id),
        "csv_ids_with_multiple_rows": len(duplicated_ids),
        "csv_identical_row_duplicate_excess": sum(len(lines) - 1 for lines in exact_groups.values()),
        "csv_raw_row_states": count_values(r["state"] for r in csv_rows),
        "csv_latest_append_states": count_values(rows[-1][1]["state"] for rows in csv_by_id.values()),
        "experiment_json_files": len(archives),
        "experiment_json_unique_full_ids": len(archives),
        "experiment_json_raw_states": count_values(r.get("status", "unknown") for r in archives.values()),
        "queue_records_all_states": len(queue_by_id),
        "queue_raw_states": count_values(r.get("status", "unknown") for r in queue_by_id.values()),
        "union_unique_full_ids": len(inventory),
        "union_M_full_ids": sum(r["m_number"] is not None for r in inventory),
        "union_non_M_full_ids": sum(r["m_number"] is None for r in inventory),
        "M_full_ids_by_number_range": {
            label: sum(low <= r["m_number"] <= high for r in inventory if r["m_number"] is not None)
            for label, low, high in [
                ("M1-M64", 1, 64), ("M65-M95", 65, 95), ("M96-M138", 96, 138),
                ("M139-M196", 139, 196), ("M197-M236", 197, 236),
            ]
        },
        "unique_M_numbers": len(numbers),
        "highest_M_number": max(numbers),
        "M_number_gaps_not_in_any_read_ledger": sorted(set(range(1, max(numbers) + 1)) - set(numbers)),
        "M_number_aliases_kept_as_separate_full_ids": number_aliases,
        "normalized_status_by_full_id": count_values(r["canonical_status"] for r in inventory),
        "normalized_status_M_full_id_only": count_values(
            r["canonical_status"] for r in inventory if r["m_number"] is not None
        ),
        "normalized_status_non_M_only": count_values(
            r["canonical_status"] for r in inventory if r["m_number"] is None
        ),
        "ledger_reports_done_full_ids": len(ledger_done),
        "known_done_label_with_partial_or_unconfirmed_termination": len(KNOWN_COMPLETION_LIMITS),
        "ledger_reports_done_without_these_known_exceptions_not_native_audited":
            len(ledger_done) - len(KNOWN_COMPLETION_LIMITS),
        "source_status_conflict_full_ids": len(status_conflicts),
        "source_metric_conflict_full_ids_threshold_0_0001": len(metric_conflicts),
        "stale_candidate_running_field_overridden_by_terminal": len(candidate_stale_fields),
        "candidate_records": len(candidates),
        "candidate_unique_ids": len({c["id"] for c in candidates}),
        "candidate_stage_counts": count_values(c.get("stage", "unknown") for c in candidates),
        "candidate_records_with_experiment_id": sum(bool(c.get("experiment_id")) for c in candidates),
        "candidate_records_without_experiment_id": sum(not c.get("experiment_id") for c in candidates),
        "config_paths_present_at_repo_root": sum(r["config_exists_at_repo_root"] for r in inventory),
        "config_paths_present_at_Cluster_root": sum(r["config_exists_at_Cluster_root"] for r in inventory),
        "config_paths_unlocated_in_these_two_roots_only": sum(
            not r["config_exists_at_repo_root"] and not r["config_exists_at_Cluster_root"]
            for r in inventory
        ),
        "candidate_linked_stage_counts": count_values(
            c.get("stage", "unknown") for c in candidates if c.get("experiment_id")
        ),
        "candidate_unlinked_stage_counts": count_values(
            c.get("stage", "unknown") for c in candidates if not c.get("experiment_id")
        ),
        "candidate_stage_training_status_crosstab": {
            stage: dict(sorted(values.items())) for stage, values in sorted(cross.items())
        },
    }
    assert sum(counts["normalized_status_by_full_id"].values()) == len(inventory)
    assert counts["candidate_records"] == (
        counts["candidate_records_with_experiment_id"] + counts["candidate_records_without_experiment_id"]
    )
    assert inv_by_id["M206-CGCA"]["canonical_status"] == "paused_by_user"
    assert inv_by_id["M227-LFT"]["canonical_status"] == "paused_by_user"
    assert inv_by_id["M235-SINC"]["canonical_status"] == "crashed"
    assert inv_by_id["M236-CSO"]["canonical_status"] == "waiting"

    csv_out = io.StringIO(newline="")
    writer = csv.DictWriter(csv_out, fieldnames=list(inventory[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(inventory)

    source_rows = [src.manifest[key] for key in sorted(src.manifest)]
    source_set_sha = sha256_bytes(
        "".join(row["path"] + "\t" + row["sha256"] + "\n" for row in source_rows).encode("utf-8")
    )
    producer_sha = sha256_bytes(pathlib.Path(__file__).read_bytes())
    common = {
        "schema_version": 1, "as_of_local_date": as_of, "timezone": "Asia/Shanghai",
        "scope": "local saved ledgers and selected analyses; no remote/live-state verification",
        "source_set_sha256": source_set_sha, "producer_sha256": producer_sha,
    }
    summary = {
        **common, "counts": counts,
        "reference_metrics": {
            "historical_champion_experiment_id": "M95-CTF-HCG-CSORT",
            "historical_champion_ledger_best": "0.5020",
            "frozen_M95_epoch16_full_VAL_reference": "0.5024607181549072",
            "frozen_reference_scope": "Historical champion weight identity not verified; do not rewrite ledger0.5020.",
            "exact_baseline_reference_cited": "0.4894491136074066",
            "target_miou": "0.5100",
            "source": analysis_paths["M202-HDS"],
            "baseline_reference_source": analysis_paths["M184-CTF-HCG-CSORT-MQST-TR"],
        },
        "candidate_records": candidate_compact,
        "known_completion_limits": KNOWN_COMPLETION_LIMITS,
        "read_scope": {
            "monolithic_pipeline_experiments_json_exists": (root / "pipeline/experiments.json").exists(),
            "diagnostic_bundle_contents_read": False,
            "network_or_remote_connections": False,
            "project_models_or_training_imported": False,
            "source_ledgers_modified": False,
            "live_running_process_claim": False,
        },
    }
    conflicts = {
        **common, "csv_duplicate_full_ids": duplicated_ids,
        "identical_csv_row_groups": [
            {"csv_lines": lines} for lines in exact_groups.values() if len(lines) > 1
        ],
        "status_disagreements": status_conflicts,
        "metric_disagreements": metric_conflicts,
        "candidate_stale_training_fields": candidate_stale_fields,
        "known_completion_limits": KNOWN_COMPLETION_LIMITS,
        "priority_rules": [
            "Full experiment_id is the dedup key; M81-CONS and M81-CTF-HCG remain separate.",
            "Explicit user pause normalizes waiting to paused_by_user; no resume is implied.",
            "Last CSV append is a corrected register view, not chronological max(finished_at).",
            "Without CSV, use saved terminal/waiting queue record, then experiment JSON.",
            "C2-posC/F1-2layer saved terminal analyses supplement obsolete running snapshots.",
            "Candidate stage, queued flags, technical gates and historical running fields never prove completed training.",
            "Preserve all raw source disagreements; do not change original ledgers or promote partial metrics.",
            "Precise/reference/checkpoint values are separate from the selected record's reported metric.",
        ],
    }
    manifest = {
        **common, "source_file_count": len(source_rows), "sources": source_rows,
        "ledger_schema": {
            "experiments_csv_columns": csv_columns,
            "experiments_json_archive_field_presence_counts": dict(sorted(archive_schemas.items())),
            "research_work_top_level_keys": sorted(work),
            "candidate_stage_key": "candidates[].stage",
            "candidate_experiment_link_key": "candidates[].experiment_id (optional)",
            "queue_record_location": "gpu_queues[server][] (lists, not GPU-indexed dicts)",
            "queue_server_record_counts": {server: len(records) for server, records in queue["gpu_queues"].items()},
        },
    }

    statuses = counts["normalized_status_by_full_id"]
    table = "\n".join(
        f"| `{status}` | {statuses[status]} |"
        for status in STATE_ORDER if status in statuses
    )
    recent = []
    for num in range(226, 237):
        row = next(r for r in inventory if r["m_number"] == num)
        precise = row["precise_or_reference_best_miou"]
        metric = row["reported_best_raw"]
        if row["canonical_status"] == "waiting":
            metric_text = "完整训练未启动"
        elif precise is not None:
            metric_text = f"{precise}（{row['precise_metric_kind']}）"
        elif number(metric) is not None:
            metric_text = f"{metric}（账本）"
        else:
            metric_text = "UNKNOWN"
        progress = row["epochs_reported"] or (
            f"saved epoch{row['saved_complete_epoch']}" if row["saved_complete_epoch"] is not None else "—"
        )
        recent.append(f"| {row['experiment_id']} | `{row['canonical_status']}` | {progress} | {metric_text} |")
    cross_table = "\n".join(
        f"| `{stage}` | " + "、".join(f"`{key}`={value}" for key, value in sorted(values.items())) + " |"
        for stage, values in sorted(cross.items())
    )
    group_counts = counts["M_full_ids_by_number_range"]
    candidate_stages = counts["candidate_stage_counts"]
    md = f"""# cluster_project 实验统计与迁移事实表

统计日期：{as_of}（Asia/Shanghai）。本表读取本地已保存记录；没有连接服务器、运行训练、派发候选或改变研究状态。原账本最后记录的时间和统计日期不是同一概念。源文件集合 SHA256：`{source_set_sha}`。

## 应怎样理解“做了多少实验”

当前源材料合计 **{counts['union_unique_full_ids']} 个去重完整实验 ID**，其中 M 系列 **{counts['union_M_full_ids']} 个完整 ID、{counts['unique_M_numbers']} 个不同 M 编号**，另有 {counts['union_non_M_full_ids']} 个早期非 M ID。最大编号 M{counts['highest_M_number']} 不代表做完了 {counts['highest_M_number']} 次训练；{len(counts['M_number_gaps_not_in_any_read_ledger'])} 个中间编号不在本次读到的账本中，M81-CONS 与 M81-CTF-HCG 又共用数字 81，明细保留二者。

实验 CSV 有 **{counts['csv_rows']} 行、{counts['csv_unique_full_ids']} 个完整 ID**。{counts['csv_ids_with_multiple_rows']} 个 ID 多次入账，共有 {counts['csv_excess_rows_over_full_id_dedup']} 行超出去重数量；其中只有 {counts['csv_identical_row_duplicate_excess']} 行属于全字段完全重复，其余包含等待、崩溃、修正或恢复后的历史。不能把每一行算作独立、完成的训练。

`pipeline/experiments/` 有 **{counts['experiment_json_files']} 份 JSON**，其中原始 `running` 有 {counts['experiment_json_raw_states'].get('running', 0)} 份，多数是旧快照。`queue.json` 有 {counts['queue_records_all_states']} 条跨状态记录，包含已结束和已撤回历史，不能把队列条数理解成待训练数量。当前不存在单体 `pipeline/experiments.json`。

## 按完整 ID 去重后的状态

| 归一状态 | ID 数 |
|---|---:|
{table}

账本标为 `done_complete` 或 `done_earlystop` 的合计 **{counts['ledger_reports_done_full_ids']} 个 ID**。其中 **M174、M195、M196 共 {counts['known_done_label_with_partial_or_unconfirmed_termination']} 个**有明确的 partial-patience / 停止归因问题。余下 **{counts['ledger_reports_done_without_these_known_exceptions_not_native_audited']} 个只是“账本报告已结束，且不含这 3 个已知例外”**，本导出没有逐条审计所有原生训练日志，不能将此数宣称为严格验证过的完整训练总数。`done_complete`/早停完成也不等于都跑满 50 个 epoch。

{statuses.get('stopped_unknown', 0)} 个 `stopped_unknown` 的完成性未知；{statuses.get('crashed', 0)} 个 `crashed` 保留不完整训练的局部指标；{statuses.get('paused_by_user', 0)} 个人工暂停保留 checkpoint；{statuses.get('waiting', 0)} 个 waiting 尚未开始完整训练；{statuses.get('withdrawn', 0)} 个 withdrawn 没有完成训练证据。这里没有把旧快照 `running` 当成当前仍在运行的进程，也没有通过本地记录宣称服务器当前无训练。

M 系列独立口径：`done_earlystop`={counts['normalized_status_M_full_id_only'].get('done_earlystop', 0)}，`stopped_unknown`={counts['normalized_status_M_full_id_only'].get('stopped_unknown', 0)}，`crashed`={counts['normalized_status_M_full_id_only'].get('crashed', 0)}，人工暂停={counts['normalized_status_M_full_id_only'].get('paused_by_user', 0)}，waiting={counts['normalized_status_M_full_id_only'].get('waiting', 0)}，withdrawn={counts['normalized_status_M_full_id_only'].get('withdrawn', 0)}。41 个 `done_complete` 全属于早期非 M ID。

## 实验路线覆盖

下面按原始 ID 和 config 名称整理路线，数量是完整 ID 数，包含中断、撤回及准备状态，不能再次当作已完成训练数量。逐项状态和配置均在 CSV 中。

| 记录范围 | 去重完整 ID 数 | 代表性实验与路线 |
|---|---:|---|
| 早期非 M | {counts['union_non_M_full_ids']} | model_base1/base2、quard2/c2f/encoder lite、posA/B/C、layerscale、GBCR、detail/2layer 等基础与组件比较 |
| M1–M64 | {group_counts['M1-M64']} | QGC/QSF、ORT、XCA、CTF、CSF、DCA、FILM 等 query/context 与跨尺度组件 |
| M65–M95 | {group_counts['M65-M95']} | HCG、ITER/REAG、CCP、CTF×HCG、DET、MLAY、CSORT；含历史 champion M95 |
| M96–M138 | {group_counts['M96-M138']} | 多 seed 对照、MEMBANK、SRL、LCC、MFP、MLAY、DCA/DCM、DUAL 等组合 |
| M139–M196 | {group_counts['M139-M196']} | CL*、object/query/support 系列、MQ* 与 MQ*-TR、CPS、BCA 等候选 |
| M197–M236 | {group_counts['M197-M236']} | PIRS/PDC/BEI/TMR/BPS、HDS/CPA/MDC、层次点特征与组合结构、各候选技术准入及原生运行 |

## 候选与技术准入另算

`research_work.json` 有 **{counts['candidate_records']} 条去重候选记录**，stage 分布为 complete={candidate_stages.get('complete', 0)}、rejected={candidate_stages.get('rejected', 0)}、blocked={candidate_stages.get('blocked', 0)}、deployment={candidate_stages.get('deployment', 0)}。只有 **{counts['candidate_records_with_experiment_id']} 条**带 experiment_id；另 {counts['candidate_records_without_experiment_id']} 条没有实验 ID，包含诊断、否决与准备工作。stage=`complete` 是候选工作流结束，不等同于完整训练。

带 experiment_id 的候选阶段与实际实验账本交叉表如下：

| 候选 stage | 对应训练状态 |
|---|---|
{cross_table}

native TRAIN2 / backward / resources PASS 及 `technical_admission=true` 仅证明相应技术门槛，不证明原生长程稳定性、完成训练、达到目标或科学新颖性。候选中的原始 `scientific_admission` 语义有历史差异，导出保留原值，不据此计训练数。

## 当前参考与最近实验

历史 champion ID 仍为 **M95-CTF-HCG-CSORT**，历史账本值 **0.5020**。已保存的 frozen M95 epoch16 full-VAL 参考为 **0.5024607181549072**，baseline 精确参考引用为 **0.4894491136074066**，目标为 **0.5100**。M202 的原分析明确说 frozen M95 权重与历史 champion 权重的身份尚未核实，因此两个 M95 数值分列保留，不用精确参考回写历史 ledger。

| 实验 | 状态 | 进度记载 | mIoU 与证据范围 |
|---|---|---|---|
{chr(10).join(recent)}

M226 完整实验 best 为恢复历史的 0.49711745977401733，不能以恢复段最后验证值代替。M229 有 26 次完整验证、epoch26 原生 patience10 早停，best 0.49881425499916077@16；尚未超过 M95。

M206-CGCA checkpoint epoch24/best 0.4952535927295685，M227-LFT checkpoint epoch22/best 0.4977978467941284，二者都是**人工暂停中的局部结果**，没有自动恢复授权。

M230-HVD 保存完整 epoch4，崩溃于 partial epoch5/1449；M231-PSC 保存 epoch1、partial epoch2/984；M232-NSD 只有 partial epoch1/1961、完整验证0；M233-NDE 只有 partial epoch1/932、完整验证0。M234-RVE canonical best UNKNOWN，另有 epoch1 checkpoint 元数据 0.3192218840122223，二者不互相替换。M235-SINC 仅有完整 saved epoch1（元数据 best 0.2787637412548065）和 partial epoch2/1870；账本 2/50 并不表示完成两轮。

**M236-CSO：native=PASSED、resources=PASSED、technical_admission=true、已入队，full_training_started=false，完整训练尚未启动，efficacy/novelty UNKNOWN。** 本地队列保留 GPU0 启动资源不足及新 owner 重新绑定执行阶段的约束；不得从技术准入或候选编号推断已训练。

## 已知冲突与取值优先级

本次发现 **{len(status_conflicts)} 个完整 ID 的来源状态不一致**；另有 {len(metric_conflicts)} 个来源数值差异大于 0.0001 的 ID，完整列表在 `ledger_conflicts.json`。状态修正只发生在导出视图：

1. 完整 experiment_id 是去重键；不按 config 相同或 M 数字相同擅自合并。
2. 人工暂停的明确标记覆盖通用 waiting，保留未授权恢复的约束。
3. 同一 ID 的 CSV 取最后追加行；部分补记的时间倒序，所以不能简单取 finished_at 最大者。所有旧行号留在明细表。
4. 没有 CSV 记录时，用已保存 terminal/waiting 队列记录，再用 experiment JSON。
5. C2-posC / F1-2layer 的保存终态分析补足旧 running 快照；分别为早停结束和手动中断。
6. M82 的 CSV/JSON 是 stopped_unknown，而 queue 写 done_earlystop；保留 CSV/JSON 口径并揭示冲突。M17、M22 的最后 CSV 与保存分析相符，旧 JSON stopped_unknown 不覆盖修正；M98/M106–M108 的最后追加 crash 修正保留。
7. candidate.stage、queued 历史布尔值、技术门槛不覆盖训练终态。M226、M235 的 candidate.training_status 仍残留 running，实际分别是 done_earlystop、crashed。
8. 精确参考、checkpoint 元数据、canonical 舍入值分列；partial 和未知值不进入完整训练效果结论。

M174 的 monitor 将 spmIOU 误匹配进早停序列，只有5次真实峰后验证；M195 native 没有早停 footer、只有7次峰后验证；M196 只有5次峰后验证且实际 kill 的执行来源未核实。三者原始 done_earlystop 原样保留，训练范围另列为不完整/未核实。

## 交付与复算

- `experiments_inventory.csv`：{len(inventory)} 行，以完整 ID 去重，含状态、范围、报告/精确指标、配置、来源、行号、冲突标记和证据。
- `candidate_status_summary.json`：完整计数、{counts['candidate_records']} 条候选的紧凑状态、训练状态交叉表；只引用证据指针，不展开诊断包。
- `ledger_conflicts.json`：重复行、状态/指标冲突、候选残留字段、优先规则。
- `source_manifest.json`：所有实际读取输入的大小、SHA256 及原账本 schema。
- `build_experiment_inventory.py`：仅标准库的 producer；`--verify` 只读校验历史源哈希、去重明细、候选统计和冲突事实，不改原账本或历史导出。

最终交接仓库采用训练代码在根、原项目支持资料在 `project_support/`、统计产物在 `experiments/` 的布局。在**导出仓库根目录**校验：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B experiments/build_experiment_inventory.py --project-root project_support --verify
```

在**原本地项目根目录**使用原位置的脚本校验：

```powershell
python -B pipeline/handoffs/20261117_github_migration/experiments/build_experiment_inventory.py --project-root . --verify
```

`--project-root` 指原始账本所在的支持资料根，即它下面应有 `pipeline/experiments.csv`；`--output-dir` 默认是脚本所在的 `experiments/`，用于读取已保存产物。`--verify` 不重制统计、不更新 CSV/JSON，也不改写其中的源 SHA；JSON 的 `producer_sha256` 保留最初生成时的版本，兼容校验脚本会另行报告当前脚本 SHA。显式 `--rebuild` 才会重建输出，迁移核验无需使用。

配置路径通常相对于训练代码根目录保存。历史明细在**原项目根与原 `Cluster/`**分别检查：前者命中 {counts['config_paths_present_at_repo_root']} 个 ID，后者命中 {counts['config_paths_present_at_Cluster_root']} 个 ID，有 {counts['config_paths_unlocated_in_these_two_roots_only']} 个 ID 在这两个根未定位。未检查 `isolated_versions`、保留 source commit 或远端 runtime 中的完整代码，此数不能解释为“代码丢失”。交接仓库已把原 `Cluster/` 展平到根，布局变化可能改变这些配置定位辅助值；`--verify` 会报告这些差异，但只对训练/候选事实及原始证据进行严格比较，不据此回写历史事实。配置字符串、状态、metrics、source/evidence、重复记录和源哈希仍须一致。

统计范围只包含 manifest 明列的 CSV、{counts['experiment_json_files']} 份 experiment JSON、research_work、queue 和选定分析文本。没有读取诊断包巨量 JSON、CRlogs、owner.work_before、账号文件或密码。脚本不导入项目控制代码或模型，不发起联网、训练、恢复、派发、前台接管或服务器操作。原日志、checkpoint、未包含账本中的历史启动次数及所有 seed 的科学有效性不由此表新增推断。
"""
    src.validate_unchanged()
    return {
        "EXPERIMENT_SUMMARY.md": md,
        "experiments_inventory.csv": csv_out.getvalue(),
        "candidate_status_summary.json": stable_json(summary),
        "ledger_conflicts.json": stable_json(conflicts),
        "source_manifest.json": stable_json(manifest),
    }


CONFIG_AUXILIARY_COUNTS = {
    "config_paths_present_at_repo_root",
    "config_paths_present_at_Cluster_root",
    "config_paths_unlocated_in_these_two_roots_only",
}
CONFIG_AUXILIARY_COLUMNS = {
    "config_exists_local",  # Earlier producer revision, if retained in a copied snapshot.
    "config_exists_at_repo_root",
    "config_exists_at_Cluster_root",
    "config_local_paths_checked_roots_only",
}


def infer_project_root() -> pathlib.Path:
    script = pathlib.Path(__file__).resolve()
    possible = [
        script.parent.parent / "project_support",
        pathlib.Path.cwd() / "project_support",
    ]
    if len(script.parents) > 4:
        possible.append(script.parents[4])
    possible.append(pathlib.Path.cwd())
    return next(
        (path for path in possible if (path / "pipeline/experiments.csv").is_file()),
        pathlib.Path.cwd(),
    )


def verify_saved_inventory(
    root: pathlib.Path, output: pathlib.Path, as_of: str
) -> dict[str, Any]:
    """Verify preserved facts, without rewriting snapshots after a layout move.

    Producer stamps describe the historical generation, not the current
    compatibility verifier. Config existence probes describe the old directory
    layout. Every other CSV/JSON field, plus every input byte hash, is compared.
    The authored Markdown instructions are allowed to change, but must retain
    the historical source-set digest.
    """
    json_names = [
        "candidate_status_summary.json", "ledger_conflicts.json", "source_manifest.json",
    ]
    required = ["experiments_inventory.csv", "EXPERIMENT_SUMMARY.md", *json_names]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        return {"verified": False, "missing_outputs": missing, "writes_performed": False}
    saved = {
        name: json.loads((output / name).read_text(encoding="utf-8"))
        for name in json_names
    }
    manifest = saved["source_manifest.json"]
    source_failures = []
    for item in manifest["sources"]:
        path = (root / item["path"]).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            source_failures.append({"path": item["path"], "reason": "outside_project_root"})
            continue
        if not path.is_file():
            source_failures.append({"path": item["path"], "reason": "missing"})
        elif sha256_bytes(path.read_bytes()) != item["sha256"]:
            source_failures.append({"path": item["path"], "reason": "sha256_mismatch"})
    if source_failures:
        return {
            "verified": False, "source_failures": source_failures,
            "source_set_sha256": manifest["source_set_sha256"], "writes_performed": False,
        }

    fresh_text = build(root, as_of)
    fresh = {name: json.loads(fresh_text[name]) for name in json_names}
    mismatches = []
    for name in json_names:
        before = json.loads(json.dumps(saved[name]))
        after = json.loads(json.dumps(fresh[name]))
        before.pop("producer_sha256", None)
        after.pop("producer_sha256", None)
        if name == "candidate_status_summary.json":
            for key in CONFIG_AUXILIARY_COUNTS:
                before["counts"].pop(key, None)
                after["counts"].pop(key, None)
        if before != after:
            mismatches.append(name)

    before_rows = list(csv.DictReader(
        io.StringIO((output / "experiments_inventory.csv").read_text(encoding="utf-8"), newline="")
    ))
    after_rows = list(csv.DictReader(io.StringIO(fresh_text["experiments_inventory.csv"], newline="")))
    before_facts = [
        {key: value for key, value in row.items() if key not in CONFIG_AUXILIARY_COLUMNS}
        for row in before_rows
    ]
    after_facts = [
        {key: value for key, value in row.items() if key not in CONFIG_AUXILIARY_COLUMNS}
        for row in after_rows
    ]
    if before_facts != after_facts:
        mismatches.append("experiments_inventory.csv")
    if manifest["source_set_sha256"] not in (output / "EXPERIMENT_SUMMARY.md").read_text(encoding="utf-8"):
        mismatches.append("EXPERIMENT_SUMMARY.md:historical_source_set_sha256")
    before_counts = saved["candidate_status_summary.json"]["counts"]
    after_counts = fresh["candidate_status_summary.json"]["counts"]
    config_count_differences = [
        {"field": key, "historical": before_counts.get(key), "current_layout": after_counts.get(key)}
        for key in sorted(CONFIG_AUXILIARY_COUNTS)
        if before_counts.get(key) != after_counts.get(key)
    ]
    config_row_differences = sum(
        any(before.get(key) != after.get(key) for key in CONFIG_AUXILIARY_COLUMNS)
        for before, after in zip(before_rows, after_rows)
    )
    return {
        "verified": not mismatches,
        "verification_mode": "preserved_historical_sources_and_training_facts",
        "mismatched_fact_outputs": mismatches,
        "source_files_verified": len(manifest["sources"]),
        "experiment_full_ids_verified": len(before_rows),
        "source_set_sha256": manifest["source_set_sha256"],
        "historical_producer_sha256": manifest.get("producer_sha256"),
        "current_verifier_sha256": sha256_bytes(pathlib.Path(__file__).read_bytes()),
        "auxiliary_layout_differences_not_written_back": {
            "config_rows": config_row_differences,
            "config_count_differences": config_count_differences,
        },
        "writes_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=pathlib.Path, default=infer_project_root())
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true", help="Read-only: verify historical source hashes and training facts")
    mode.add_argument("--rebuild", action="store_true", help="Explicitly regenerate output snapshots; not needed for migration verification")
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = args.output_dir.resolve()
    if args.verify:
        result = verify_saved_inventory(root, output, args.as_of)
        print(stable_json(result), end="")
        return 0 if result["verified"] else 1
    allowed = [
        pathlib.Path(__file__).resolve().parent,
        (root / "pipeline/handoffs/20261117_github_migration/experiments").resolve(),
    ]
    if output not in allowed:
        raise SystemExit("Rebuild output is limited to the script's experiment directory or original migration directory.")
    artifacts = build(root, args.as_of)
    output.mkdir(parents=True, exist_ok=True)
    for name, text in artifacts.items():
        temporary = output / (name + ".tmp")
        temporary.write_bytes(text.encode("utf-8"))
        temporary.replace(output / name)
    summary = json.loads(artifacts["candidate_status_summary.json"])
    print(stable_json({
        "written": list(artifacts), "source_set_sha256": summary["source_set_sha256"],
        "counts": summary["counts"],
    }), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
