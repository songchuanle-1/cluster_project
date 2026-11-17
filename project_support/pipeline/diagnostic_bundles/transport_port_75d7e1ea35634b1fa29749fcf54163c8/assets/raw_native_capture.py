"""Shared, bounded native forward capture; no training loss intervention."""
import argparse
import copy
import datetime
import fcntl
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = "7"
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import torch

torch.set_num_threads(2)
UUID = "GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a"
PACKAGE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def input_hash(value):
    h = hashlib.sha256()

    def visit(item):
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu().contiguous()
            h.update(str((tensor.dtype, tuple(tensor.shape))).encode())
            h.update(tensor.numpy().tobytes())
        elif isinstance(item, dict):
            for key in sorted(item):
                h.update(str(key).encode())
                visit(item[key])
        elif isinstance(item, (tuple, list)):
            for child in item:
                visit(child)
        else:
            h.update(repr(item).encode())

    visit(value)
    return h.hexdigest()


def guard(root):
    assert subprocess.check_output(["hostname"], text=True).strip() == "das"
    line = subprocess.check_output([
        "nvidia-smi", "-i", "7",
        "--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits"], text=True).strip()
    cells = [part.strip() for part in line.split(",")]
    assert cells[0] == "7" and cells[1] == UUID
    assert int(cells[4]) >= 32768, "Live shared-memory guard refused"
    processes = subprocess.check_output([
        "nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory",
        "--format=csv,noheader,nounits"], text=True)
    rows = [row for row in processes.splitlines() if UUID in row]
    project = {}
    for row in rows:
        pid = int(row.split(",")[1].strip())
        if pid == os.getpid():
            continue
        try:
            cwd = Path(os.readlink("/proc/" + str(pid) + "/cwd"))
            argv = Path("/proc/" + str(pid) + "/cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if cwd == root and any(part.endswith(b"tools/train.py") for part in argv):
            configs = [part.decode() for part in argv
                       if part.startswith(b"configs/") and part.endswith(b".yaml")]
            for config in configs:
                project[config] = pid
    assert len(project) < 2, "Project slots occupied; no diagnostic launch"
    return dict(gpu=line, processes=rows, observed_project_tasks=project)


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, default=lambda x: x.item()) + "\n")
    temporary.replace(path)


def run(args):
    root = Path(args.code_root)
    first_guard = guard(root)
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    torch.cuda.set_per_process_memory_fraction(.25, 0)
    import gorilla
    from framework import resolve_network
    from framework.dataset import build_dataset

    population = json.loads(Path(args.population).read_text())
    assert population["complete"] and digest(args.population) == (
        "e930143cfd9476c6336ba4f0a89278a86280d6d15d70450c1de30c7bb73a01c5")
    manifest = json.loads(Path(args.source_manifest).read_text())
    folder = root / "framework/model/Quard_model" / PACKAGE
    for name, expected in manifest["package"].items():
        assert digest(folder / name) == expected, "Candidate source changed"
    cfg = gorilla.Config.fromfile(str(root / args.config))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and cfg.lr_scheduler.max_iters == 70
    checkpoint = Path(args.checkpoint)
    before = checkpoint.stat()
    frozen = Path(args.output).parent / "checkpoint_snapshot.pth"
    assert not frozen.exists(), "Snapshot already exists; reconcile before retry"
    shutil.copyfile(checkpoint, frozen)
    after = checkpoint.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    checkpoint_sha = digest(frozen)
    saved = torch.load(frozen, map_location="cpu", weights_only=False, mmap=True)
    state = saved["state_dict"]
    Network = resolve_network(args.config)
    assert Network.__module__.startswith("framework.model.Quard_model." + PACKAGE)
    gorilla.set_random_seed(1999)
    model = Network(**cfg.model)
    model.load_state_dict(state, strict=True)
    model.cuda()
    model.train()
    logger = logging.getLogger("bps_native_pair_capture")
    logger.addHandler(logging.NullHandler())
    dataset = build_dataset(cfg.data.train, logger)
    wanted = {(r["scene"], r["ann_id"]) for r in population["rows"]
              if r["status"] == "physical_masks_evaluated"}
    groups, found = [], set()
    for index, group in enumerate(dataset.scene_inputs):
        keys = {(r["scene_id"], int(r["ann_id"])) for r in group}
        if keys & wanted:
            groups.append(index)
            found.update(keys & wanted)
    assert found == wanted and len(wanted) == 49
    loss_module = importlib.import_module(
        "framework.model.Quard_model." + PACKAGE + ".loss")
    original = loss_module.support_excess
    captures = []

    def capture(masks, targets, indices, num_boxes, supports):
        actual = original(masks, targets, indices, num_boxes, supports)
        decomposed, oracle = 0.0, 0.0
        queries, masks_cpu = [], []
        for expression, (mask, target, index, support) in enumerate(
                zip(masks, targets, indices, supports)):
            src, tgt = index
            masks_cpu.append(mask.detach().cpu().clone())
            if not support["costs"]:
                continue
            counts = support["counts"].to(mask.device)
            for q, g in zip(src.tolist(), tgt.tolist()):
                gt = target["masks"][g:g+1]
                weight = gt.double() * counts
                weight /= weight.sum(-1, keepdim=True)
                restricted = {**support, "costs": []}
                for field in support["costs"]:
                    expected = weight @ field.to(mask.device)
                    keep = (expected[0] == expected[0].min()).cpu()
                    restricted["costs"].append(field[:, keep])
                selection = [(torch.tensor([0], device=mask.device),
                              torch.tensor([0], device=mask.device))]
                normal = original([mask[q:q+1]], [{"masks": gt}], selection, num_boxes, [support])
                anchored = original([mask[q:q+1]], [{"masks": gt}], selection, num_boxes, [restricted])
                decomposed += float(normal)
                oracle += float(anchored)
                queries.append(dict(expression=expression, src=q, tgt=g,
                                    normalized_component=float(normal),
                                    normalized_oracle=float(anchored)))
        captures.append(dict(component=float(actual), decomposed=decomposed,
                             decomposition_abs_delta=abs(float(actual)-decomposed),
                             oracle=oracle, matched_event_queries=queries, masks=masks_cpu))
        return actual

    loss_module.support_excess = capture
    rows = []
    try:
        for number, index in enumerate(groups):
            guard(root)
            gorilla.set_random_seed(1999)
            batch = dataset.collate_fn([dataset[index]])
            before_hash = input_hash(batch)
            trials = []
            for trial in range(2):
                model.load_state_dict(state, strict=True)
                model.train()
                gorilla.set_random_seed(1999)
                captures.clear()
                with torch.no_grad():
                    full_loss, loss_dict = model(batch, mode="loss")
                assert len(captures) == 1 and bool(torch.isfinite(full_loss).all())
                trials.append((float(full_loss), captures[0]))
                assert input_hash(batch) == before_hash
            a, b = trials[0][1], trials[1][1]
            tensor_delta = max(float((left-right).abs().max())
                               for left, right in zip(a["masks"], b["masks"]))
            a.pop("masks")
            b.pop("masks")
            row = dict(group_index=index, ann_ids=list(map(int, batch["ann_ids"])),
                       scan_ids=batch["scan_ids"], input_sha256=before_hash,
                       full_loss=[trials[0][0], trials[1][0]], captures=[a, b],
                       mask_repeat_max_abs_delta=tensor_delta,
                       full_loss_repeat_abs_delta=abs(trials[0][0]-trials[1][0]),
                       pass_repeat1e6=tensor_delta<=1e-6 and abs(trials[0][0]-trials[1][0])<=1e-6,
                       pass_decomposition1e6=max(a["decomposition_abs_delta"],
                                                b["decomposition_abs_delta"])<=1e-6)
            rows.append(row)
            print("completed native group " + str(index), flush=True)
            torch.cuda.empty_cache()
    finally:
        loss_module.support_excess = original
    result = dict(token=args.token, remote_observed_at=datetime.datetime.now(
                  datetime.timezone.utc).isoformat(), script_sha256=digest(__file__),
                  checkpoint_sha256=checkpoint_sha, checkpoint_meta=saved.get("meta", {}),
                  checkpoint_source=str(checkpoint), groups_planned=groups, rows=rows,
                  guard_before=first_guard, guard_after=guard(root),
                  allocator_fraction=.25, peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
                  extra_optimizer_steps=0, model_backward_calls=0,
                  scope="Unchanged native TRAIN forward with actual checkpoint/matcher/masks; "
                        "GT-pair oracle measured only, never returned to model loss. Not efficacy.")
    save(Path(args.output), result)
    print(json.dumps(dict(groups=len(rows), sha256=digest(args.output))), flush=True)


def main():
    parser = argparse.ArgumentParser()
    for name in ("code-root", "config", "checkpoint", "source-manifest", "population", "output", "token"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    locks = []
    try:
        for path in ("/tmp/cluster_project_gpu7_exclusive.lock",
                     "/tmp/cluster_project_gpu7_diagnostic.lock",
                     "/tmp/cluster_project_gpu7_slot2_diagnostic.lock"):
            assert Path(path).is_file(), "Existing diagnostic lock unavailable"
            handle = open(path, "a+b")
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locks.append(handle)
        run(args)
    finally:
        for handle in reversed(locks):
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()


if __name__ == "__main__":
    main()
