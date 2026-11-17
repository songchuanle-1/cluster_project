"""Reuse verified detached launcher with BCA-specific locked admission checks."""
from pathlib import Path
source = Path("D:/project/cluster_project/pipeline/headless/launch_cps_20260914.py").read_text()
source = source.replace('ID = "M195-CTF-HCG-CSORT-CPS"', 'ID = "M196-CTF-HCG-CSORT-BCA"')
start = source.index('    origin = ')
end = source.index('    assert ssh(f"git -C', start)
source = source[:start] + '''    origin = "server-6"
    assert not any(t["id"] == ID for group in queue["gpu_queues"].values() for t in group)
    head = subprocess.check_output(["git","-C",str(ROOT/"Cluster"),"rev-parse","HEAD"],text=True).strip()
    assert head.startswith("a490710")
    task = dict(id=ID,config="configs/Quard/ctf_hcg_csort_bca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca.yaml",
                status="waiting",gpu=None,depends_on=[],patience=10,
                label="M196 Boundary Conditional Assignment",code_commit=head,
                measured_flops_g=9.762532428,
                validation_report="pipeline/reports/bca_admission_20260914-2234.md",
                design="pipeline/designs/exp_design_20260914-2217.md")
    queue["gpu_queues"]["server-6"].append(task)
''' + source[end:]
source = source.replace('assert util < 10 and memory < 1024, gpu',
                        'assert 81559 - memory > 20480, gpu')
old = '    assert running.get("server-6", {}).get("7") in (None, ID) if REPAIR else not running.get("server-6", {}).get("7")'
source = source.replace(old, '''    previous = running.get("server-6", {}).get("7")
    occupants = previous if isinstance(previous,list) else ([previous] if previous else [])
    assert len(occupants) < 2 and ID not in occupants
    assert sum(t["status"] in ("running","claiming","waiting") for group in queue["gpu_queues"].values() for t in group) <= 4''')
source = source.replace('running.setdefault("server-6", {})["7"] = ID',
                        'running.setdefault("server-6", {})["7"] = occupants + [ID]')
source = source.replace('"20260914-194215_manual.md"', '"20260914-223459_next_batch.md"')
exec(compile(source, "<bca-launch>", "exec"))
