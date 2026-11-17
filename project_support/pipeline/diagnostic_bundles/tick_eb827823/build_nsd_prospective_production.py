"""Author only local disabled NSD production PATH drafts; reuse proved bytes."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
TICK = ROOT / "pipeline/diagnostic_bundles/tick_eb827823"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_d20ca92f"
PACKET = TICK / "nsd_path_production_prepare"
TRANSPORT = TICK / "nsd_path_production_transport"
SOURCE = "f6257de79148581334ee495e6e2d60ccb525457c"
PARENT = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
CID = "hierarchy-native-spatial-dirichlet-composition"
TOKEN = "eb827823f30543d8aa8609643034f996"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
AUTHOR = "01a1a684-e37c-7023-a69a-924d4014a2d5"
KEYS = ("token", "thread_id", "generated_at", "deadline_at",
        "context_sha256", "pending_sha256")
PROOF_REVIEW = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433/psc_cpu_path_proof_actual_independent_review.json"
SOURCE_PROOF = ROOT / "pipeline/diagnostic_bundles/tick_c706ca80/nsd_compatible_source/compatible_source_version.json"
RUNTIME = "/data/songcl/Project/Cluster_project/Cluster_nsd_20261107"
PRODUCER = "/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prepare_eb827823"
PRODUCTION = "/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prod_eb827823"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert os.environ.get("CODEX_THREAD_ID") == AUTHOR != THREAD
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    for name, key in ((".tick_context.json", "context_sha256"),
                      (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    return {key: owner[key] for key in KEYS}


def write(path, value):
    guard()
    path = Path(path)
    assert path.resolve().is_relative_to(TICK.resolve())
    raw = value if isinstance(value, bytes) else (
        value.encode("utf8") if isinstance(value, str) else
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    with path.open("xb") as stream:
        stream.write(raw)


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)


def port(text, owner):
    return (text.replace("PSC", "NSD").replace("psc", "nsd")
            .replace("d20ca92f1b654e24ba9cf29f634307b7", TOKEN)
            .replace("d20ca92f", "eb827823")
            .replace("2026-11-06T18:08:14.169854+00:00", owner["deadline_at"])
            .replace("2026-11-06T17:08:14.169854+00:00", owner["generated_at"])
            .replace("M231-NSD", "M232-NSD"))


def main():
    owner = guard()
    preserved = {
        OLD / "psc_path_production_prepare/FROZEN.json":
        "771579c9df5f1d84199eec1ff85639a90a7e77e7e4acf097c2d43128db89ad6f",
        PROOF_REVIEW:
        "ce4d57c001c6dd4a7c2ea1491563c56fc7a7c4ab4371cc2aedae663b73fcac82",
    }
    for path, digest in preserved.items():
        assert sha(path) == digest
    proof = read(SOURCE_PROOF)
    assert proof["source_commit"] == SOURCE and proof["parent_commit"] == PARENT
    exact9 = proof["source_files_exact9"]
    exact8 = {name: digest for name, digest in exact9.items() if name.endswith(".py")}
    assert len(exact9) == 9 and len(exact8) == 8
    PACKET.mkdir()
    TRANSPORT.mkdir()
    checks = []

    def check(name, value, detail=None):
        assert value, name
        checks.append({"name": name, "passed": True, "detail": detail})

    for name, expected in (
        ("lock_core.py", "c0857d0b79da396da73c4dbefd60a81ce35f9fb3839b76441328a22183e988b3"),
        ("entry_factory.py", "0a8ed26bd62327314de89f4228b53c8c633fdd73e4e1867d674df94b24d073dd"),
    ):
        original = OLD / "psc_path_production_prepare" / name
        assert sha(original) == expected
        write(PACKET / name, original.read_bytes())
        check("proved_bytes_unchanged_" + name, sha(PACKET / name) == expected)

    original_controller = (OLD / "psc_path_production_prepare/production_controller.py").read_text()
    controller = port(original_controller, owner)
    controller = controller.replace(
        'RUNTIME = PROJECT / "Cluster_nsd_20261106"',
        'RUNTIME = PROJECT / "Cluster_nsd_20261107"')
    controller = controller.replace('COMMIT = "' + PARENT + '"', 'COMMIT = "' + SOURCE + '"')
    tree = ast.parse(controller)
    sources_node = next(n for n in tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "EXPECTED_SOURCES"
                                for t in n.targets))
    old_sources = ast.get_source_segment(controller, sources_node)
    controller = replace_once(controller, old_sources, "EXPECTED_SOURCES = " + repr(exact8))
    controller = replace_once(controller, 'OWNER = "' + TOKEN + '"',
                              "EXPECTED_OWNER = " + repr(owner) + '\nOWNER = "' + TOKEN + '"')
    controller = replace_once(controller, '    owner = request["owner"]',
                              '    owner = request["owner"]\n    assert owner == EXPECTED_OWNER')
    controller = replace_once(controller, '    assert receipt["code_commit"] == COMMIT',
                              '    assert receipt["code_commit"] == COMMIT\n'
                              '    assert receipt["candidate_id"] == "' + CID + '"\n'
                              '    assert receipt["goal_sha256"] == "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"')
    compile(controller, "prospective-NSD-controller", "exec")
    write(PACKET / "production_controller.py", controller)
    files = {name: sha(PACKET / name)
             for name in ("production_controller.py", "lock_core.py", "entry_factory.py")}
    for action in ("collect", "render"):
        request = json.loads(port((OLD / ("psc_path_production_prepare/" + action +
                                          "_request.draft.json")).read_text(), owner))
        request.update(owner=owner, files=files, prospective_producer=PRODUCER,
                       prospective_production_stage=PRODUCTION,
                       prospective_runtime=RUNTIME, prospective_source_commit=SOURCE,
                       execution_authorized=False, training_launch_authorized=False)
        write(PACKET / (action + "_request.draft.json"), request)
        check(action + "_request_disabled_exact_owner_files_and_no_actual_facts",
              request["owner"] == owner and request["files"] == files
              and request["execution_authorized"] is False
              and request["actual_deployment_observed"] is False)
    activation = read(OLD / "psc_path_production_prepare/activation_receipt.draft.json")
    activation["owner"] = owner
    write(PACKET / "activation_receipt.draft.json", activation)
    check("activation_actual_fields_still_NULL", all(
        activation[k] is None for k in
        ("actual_observation_sha256", "admission_receipt_sha256", "root_independent_review")))
    # Importing the controller only defines functions/constants: it does not
    # call guard/observe/render or load Torch/model/data.
    spec = importlib.util.spec_from_file_location("disabled_nsd_controller", PACKET / "production_controller.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    check("exact_NSD_external_source8_and_YAML9_literals",
          module.EXPECTED_SOURCES == exact8 and module.COMMIT == SOURCE
          and module.CONFIG in exact9 and module.EXACT_ARGS ==
          ["tools/train.py", module.CONFIG, "--gpu_ids", "0", "--num_gpus", "1"])
    check("current_six_owner_fields_strictly_bound", module.EXPECTED_OWNER == owner)
    check("existing_base_and_three_lock_paths_unchanged",
          module.BASE_SHA == "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
          and module.LOCK_PATHS == ["/tmp/cluster_project_gpu0_" + label + ".lock"
                                    for label in ("training", "diagnostic", "exclusive")])
    shim = module.shim_source("0" * 64)
    bash = Path("C:/Program Files (x86)/Git/bin/bash.exe")
    assert bash.is_file()
    syntax = subprocess.run([str(bash), "--noprofile", "--norc", "-n"],
                            input=shim, capture_output=True, text=True)
    check("generated_shim_Bash_syntax_only", syntax.returncode == 0)
    preview_node = next(n for n in ast.walk(ast.parse(controller))
                        if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "preview_program" for t in n.targets))
    compile(ast.literal_eval(preview_node.value), "canonical-YAML-preview", "exec")
    check("original_canonical_YAML_preview_source_compiles", True)
    write(PACKET / "README.md",
          "Disabled prospective NSD production PATH controller. Exact sourcef625, parent0ccc, "
          "new Cluster_nsd_20261107; owner expires " + owner["deadline_at"] + ".\n"
          "Core/factory and actual Linux CPU proof are reused unchanged, never rerun. "
          "No actual source deployment, admission, collect/render, GPU/resource test, production "
          "binding, install or trainer launch occurred. All actual observation/activation fields remain NULL.\n"
          "Root first needs genuine original native/resources PASS and canonical M232-NSD admission, "
          "then independent new source deployment, current guarded CPU collect, peer review of real "
          "source/YAML/interpreter/three inode facts, actual activation receipt, render and production "
          "review before its separate unique canonical trainer launch. Fixed six training arguments, "
          "GPU0/UUID/free20000MiB/max1/original three locks and original base6c80 remain.\n"
          "Sibling root transport is a default-NOP execution-disabled draft. Its review SHA stays NULL; "
          "a separately reviewed fresh root activation is required before any transport. "
          "Never edit frozen bytes, fill actual facts speculatively, reuse expired owner, replay uncertain "
          "requests, alter resources, or consume/delete the one-shot marker.\n")
    preparation = {
        "status": "DISABLED_PROSPECTIVE_NSD_PRODUCTION_PATH_SOFTWARE_ONLY",
        "owner_provenance_only": owner, "author_thread_id": AUTHOR,
        "candidate_id": CID, "source_commit": SOURCE, "parent_commit": PARENT,
        "prospective_runtime": RUNTIME, "prospective_producer": PRODUCER,
        "prospective_production": PRODUCTION, "source_files_exact9": exact9,
        "source_proof": ref(SOURCE_PROOF),
        "original_controller": ref(OLD / "psc_path_production_prepare/production_controller.py"),
        "original_controller_review": ref(OLD / "psc_path_production_independent_review.json"),
        "reused_actual_CPU_proof_review": ref(PROOF_REVIEW),
        "proof_rerun": False, "actual_observation": None, "production_binding": None,
        "native": "NOT_RUN", "resources": "NOT_RUN", "SSH_GPU": False,
        "actual_collect_render_install": "NOT_RUN", "training_launch": "NOT_RUN",
        "independent_review": "PENDING_EXTERNAL",
    }
    write(PACKET / "preparation.json", preparation)
    frozen = {
        "status": "FROZEN_DISABLED_PROSPECTIVE_NSD_PRODUCTION_PATH",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner_provenance_only": owner, "author_thread_id": AUTHOR,
        "candidate_id": CID, "source_commit": SOURCE, "parent_commit": PARENT,
        "files": {p.name: sha(p) for p in sorted(PACKET.iterdir()) if p.is_file()},
        "actual_CPUproof_reused_not_rerun": ref(PROOF_REVIEW),
        "no_actual_execution_material_created": True, "author_will_not_write_further": True,
    }
    write(PACKET / "FROZEN.json", frozen)

    transport = port((OLD / "psc_path_production_transport/run_controller_once.py").read_text(), owner)
    transport = transport.replace(
        'server["remote_code_root"] == "/data/songcl/Project/Cluster_project/Cluster_hvd_20261106"',
        'server["remote_code_root"] == "/data/songcl/Project/Cluster_project/Cluster_psc_20261106"')
    transport = transport.replace(
        '"6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7"',
        '"' + sha(ROOT / "SERVERS.yaml") + '"')
    transport = transport.replace('admission["code_commit"] == "' + PARENT + '"',
                                  'admission["code_commit"] == "' + SOURCE + '"')
    transport = replace_once(transport,
        'FROZEN_SHA = "771579c9df5f1d84199eec1ff85639a90a7e77e7e4acf097c2d43128db89ad6f"',
        'FROZEN_SHA = "' + sha(PACKET / "FROZEN.json") + '"')
    transport = replace_once(transport,
        'REVIEW_SHA = "c29087cc258f967b6d32fddbe380a9a110759d58f1ec86deeeece765eecd3208"',
        'REVIEW_SHA = None\nDRAFT_EXECUTION_DISABLED = True\nEXPECTED_OWNER = ' + repr(owner))
    transport = replace_once(transport, "def guard():",
        'def guard():\n    assert not DRAFT_EXECUTION_DISABLED and isinstance(REVIEW_SHA, str), '
        '"Disabled prospective transport; fresh independent review/root activation required"')
    transport = replace_once(transport,
        '    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD',
        '    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD\n'
        '    assert {key: owner[key] for key in KEYS} == EXPECTED_OWNER')
    # The stdin transport's remote stage also binds all six fields exactly.
    transport = replace_once(transport,
        "owner=packet['owner']",
        "owner=packet['owner']\nassert owner==" + repr(owner))
    compile(transport, "disabled-NSD-root-transport", "exec")
    write(TRANSPORT / "run_controller_once.py", transport)
    nop = subprocess.run([sys.executable, "-B", "-X", "utf8",
                          str(TRANSPORT / "run_controller_once.py")],
                         capture_output=True, text=True)
    check("actual_default_transport_NOP_no_SSH", nop.returncode == 0
          and json.loads(nop.stdout)["status"] == "DEFAULT_NOP_NO_SSH_OR_MUTATION")
    disabled = subprocess.run([sys.executable, "-B", "-X", "utf8",
                               str(TRANSPORT / "run_controller_once.py"),
                               "--execute-root", "--action", "stage"],
                              capture_output=True, text=True)
    check("actual_execute_flag_refuses_at_DRAFT_before_owner_IO_transport",
          disabled.returncode != 0 and "Disabled prospective transport" in disabled.stderr)
    check("no_actual_intent_request_or_result_created",
          sorted(p.name for p in TRANSPORT.iterdir()) == ["run_controller_once.py"])
    check("all_old_proof_and_controller_anchors_unchanged", all(
        sha(path) == digest for path, digest in preserved.items()))
    check("real_Torch_not_imported", not any(n == "torch" or n.startswith("torch.") for n in sys.modules))
    write(TRANSPORT / "README.md",
          "Default NOP, execution-disabled prospective NSD root transport. REVIEW_SHA=NULL; "
          "no collect/render/stage/intents/requests/results exist. This author did not use SSH.\n"
          "After independent controller review and real native/resources/admission/source-deployment "
          "gates pass, root must create a separately reviewed fresh activation copy with exact peer "
          "review SHA and retained six owner fields, fixed deadline, current SERVERS/context/pending "
          "hashes. Frozen draft is never edited. Existing collect/render process is preserved.\n"
          "Actual activation receipt, observation, interpreter/inodes and production graph stay unfilled "
          "until real CPU collect and root/peer review. No GPU use or trainer launch is authorized.\n")
    write(TRANSPORT / "software_validation.json", {
        "status": "LOCAL_DISABLED_NSD_PROSPECTIVE_PRODUCTION_SOFTWARE_CHECKS_PASS",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "check_count": len(checks),
        "scope": "Compile/import definitions, generated shim Bash -n, actual local default-NOP "
                 "and DRAFT refusal only; no SSH, GPU, source deployment, controller collect/render, "
                 "new proof, real model/data or training.",
        "native": "NOT_RUN", "resources": "NOT_RUN", "proof_rerun": False,
        "independent_review": "PENDING_EXTERNAL",
    })
    write(TRANSPORT / "FROZEN.json", {
        "status": "FROZEN_DISABLED_PROSPECTIVE_NSD_ROOT_TRANSPORT",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner_provenance_only": owner, "author_thread_id": AUTHOR,
        "controller_packet": ref(PACKET / "FROZEN.json"),
        "files": {p.name: sha(p) for p in sorted(TRANSPORT.iterdir()) if p.is_file()},
        "draft_execution_disabled": True, "review_sha256": None,
        "actual_execution_material_created": False, "author_will_not_write_further": True,
    })
    print(json.dumps({
        "controller_FROZEN": ref(PACKET / "FROZEN.json"),
        "transport_FROZEN": ref(TRANSPORT / "FROZEN.json"),
        "checks": len(checks), "source": SOURCE,
        "actual_collect_render_GPU_training": "NOT_RUN",
    }))


if __name__ == "__main__":
    main()
