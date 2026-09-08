"""Measure existing configs in separate processes without changing their models."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    if args.worker:
        assert len(args.configs) == 1
        from tools.validate_hqi import profile
        config = args.configs[0]
        name = Path(config).stem
        result = profile(name, args.data_root, report_dir, config=config)
        (report_dir / f"{name}.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8")
        return
    results = []
    for config in args.configs:
        subprocess.run(
            [sys.executable, __file__, "--configs", config,
             "--data-root", args.data_root, "--report-dir", str(report_dir),
             "--worker"], check=True)
        result = json.loads(
            (report_dir / f"{Path(config).stem}.json").read_text(encoding="utf-8"))
        results.append(result)
    (report_dir / "resource_audit.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    for result in results:
        print(result["config"], result["flops_g"],
              "PASS" if result["flops"] <= 10e9 else "OVER_LIMIT", flush=True)


if __name__ == "__main__":
    main()
