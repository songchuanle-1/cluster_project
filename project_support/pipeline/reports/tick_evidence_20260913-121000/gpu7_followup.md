# GPU7 Occupancy Correction

2026-09-13 approximately12:11 Asia/Shanghai; read-only SSH nvidia-smi.
The audit.json GPU memory snapshot is correct. Absence of cluster trainers
does not imply an idle GPU; the initially generated report label was corrected.

```text
query-compute-apps=pid,process_name,used_memory
4151473, /data3/songcl/envs/project_3dvlm/bin/python, 14354 MiB
query-gpu=index,utilization.gpu,memory.used,memory.total
7, 0, 14365, 81559
```

No process termination, migration, deployment or scheduler change.
