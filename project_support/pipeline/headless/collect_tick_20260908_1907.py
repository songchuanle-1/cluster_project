"""Read-only collection of live processes, paired validation metrics and GPUs."""
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re


ROOT = Path("D:/project/cluster_project")


def main():
    source = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    spec = importlib.util.spec_from_file_location("tick_monitor", source)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    servers = monitor.load_servers(str(ROOT))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = ROOT / "pipeline/reports" / f"live_{stamp}"
    output.mkdir()
    result = {"collected_at": datetime.now().isoformat(), "servers": {}}
    for name in ("server-4", "server-6"):
        srv = servers[name]
        host, user = srv["host"], srv["user"]
        gpu_rows = monitor.ssh(
            host, user,
            "nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total "
            "--format=csv,noheader,nounits", timeout=15)
        assert gpu_rows
        gpus = []
        for row in gpu_rows.splitlines():
            fields = [int(v.strip()) for v in row.split(",")]
            if fields[0] in srv["allowed_gpus"]:
                gpus.append(dict(zip(("gpu", "util", "used_mib", "total_mib"), fields)))
        processes = monitor.find_running_processes(
            host, user, srv["remote_code_root"])
        runs = []
        for config, (pid, _, gpu, resume, command) in processes.items():
            cfg_name = Path(config).stem
            paths = monitor.ssh(host, user, f"readlink /proc/{int(pid)}/fd/* 2>/dev/null")
            candidates = sorted({
                p for p in paths.splitlines()
                if p.startswith(srv["work_dir"].rstrip("/") + "/" + cfg_name + "/")
                and p.endswith(".log")
            })
            assert len(candidates) == 1, (name, pid, candidates)
            log = candidates[0]
            text = monitor.ssh(
                host, user,
                f"grep -E 'mIoU :|mIOU: |spmIOU: |Early stopping' '{log}'",
                timeout=30)
            tail = monitor.ssh(host, user, f"tail -n 2 '{log}'", timeout=15)
            rows = []
            for line in text.splitlines():
                exact = re.search(r"\bmIoU : ([0-9.]+)", line)
                if exact:
                    rows.append({"epoch": len(rows) + 1, "miou": float(exact[1]),
                                 "remote_time": line.split(" - ")[0]})
                elif rows:
                    acc = re.search(r"\bmIOU:.*?\bAcc_50: ([0-9.]+)", line)
                    spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
                    if acc:
                        rows[-1]["acc50"] = float(acc[1].rstrip("."))
                    if spm:
                        rows[-1]["spmiou"] = float(spm[1].rstrip("."))
            current = re.findall(r"Epoch \[(\d+)/(\d+)\]", tail)
            best = max(rows, key=lambda v: v["miou"]) if rows else None
            runs.append({"config": config, "pid": pid, "gpu": gpu, "log": log,
                         "resume": resume, "best": best, "validations": rows,
                         "current_epoch": current[-1][0] if current else None,
                         "no_improve": len(rows) - best["epoch"] if best else None,
                         "tail": tail})
            (output / f"{cfg_name}_validation.log").write_text(
                text + "\n" + tail, encoding="utf-8")
        result["servers"][name] = {"gpus": gpus, "runs": runs}
    (output / "snapshot.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(output)
    for name, server in result["servers"].items():
        print(name, server["gpus"])
        for run in server["runs"]:
            print(run["pid"], Path(run["config"]).stem, run["current_epoch"],
                  "best", run["best"], "no_improve", run["no_improve"])


if __name__ == "__main__":
    main()
