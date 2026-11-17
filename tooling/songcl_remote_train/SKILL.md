---
name: songcl_remote_train
description: Manage remote GPU training tasks — push code, launch/resume training, view logs/status, kill tasks, pull checkpoints. Works across all projects under /home/songcl/3dres/project/. Use when the user wants to run, monitor, stop, or pull results from training on remote GPU servers.
---

# songcl_remote_train

Manage remote GPU training across the multi-server cluster.

## Context

- Projects live under `/home/songcl/3dres/project/<project_name>/`
- Each project has its own `scripts/` directory and `SERVERS.yaml`
- Servers: `server-2` (192.168.1.163, 2×RTX3090), `server-3` (192.168.1.194, 2×RTX3090), `server-4` (192.168.1.137, 2×RTX5090)
- Monitor dashboard: `http://192.168.1.175:8088/`
- All commands run from the project directory: `cd /home/songcl/3dres/project/<project_name>`

## Identifying the Project

If the user doesn't specify a project, check which project they're working in:
- Look at the current working directory
- Ask if ambiguous

```bash
# List available projects
ls -d /home/songcl/3dres/project/*/SERVERS.yaml | xargs -I{} dirname {} | xargs -I{} basename {}
```

## Operations

### 1. Push Code (sync)

```bash
cd /home/songcl/3dres/project/<project>
bash scripts/sync.sh <server>          # full git push
bash scripts/sync_model.sh <server>    # fast: only framework/model/ + configs/ via rsync
```

- `sync.sh` — full code sync via git push (slower, includes everything)
- `sync_model.sh` — rsync only `framework/model/` + `configs/` + auto path adaptation (fast, for code-only changes)
- Use `sync_model.sh` when only model code or configs changed
- Use `sync.sh` when scripts, tools, or other files changed

### 2. Launch Training

```bash
bash scripts/remote_train.sh <server> <config> <gpu_ids> [num_gpus]
```

Examples:
```bash
# Single GPU
bash scripts/remote_train.sh server-4 configs/Quard/model_xxx.yaml 0

# Multi GPU
bash scripts/remote_train.sh server-4 configs/Quard/model_xxx.yaml 0,1 2
```

**Flow**: auto-commit → sync → check env → path adaptation → nohup launch → record PID

The script automatically:
- Commits uncommitted local changes
- Pushes code to remote
- Replaces `data_root`/`work_dir`/`pretrain` paths in configs (local → remote)
- Launches training in background via `nohup`
- Saves PID to `logs/.pid_<config_name>`

### 3. Resume Training from Checkpoint

```bash
bash scripts/remote_resume.sh <server> <config> <gpu_ids> [checkpoint]
```

Examples:
```bash
# Auto-find latest last.pth
bash scripts/remote_resume.sh server-4 configs/Quard/model_xxx.yaml 1

# Specify checkpoint explicitly
bash scripts/remote_resume.sh server-4 configs/Quard/model_xxx.yaml 1 /path/to/last.pth
```

- If no checkpoint given, auto-finds latest `last.pth` (falls back to `best.pth`)
- Checkpoint path is the REMOTE path (in `work_dir`)
- Same flow as `remote_train.sh` but adds `--resume <checkpoint>` flag

### 4. View Status

```bash
bash scripts/remote_status.sh <server>
```

Shows: GPU temperature/util/memory, running training processes, PID status, latest log tail, disk usage, recent checkpoints.

### 5. View Logs

```bash
bash scripts/remote_log.sh <server>                    # list all logs
bash scripts/remote_log.sh <server> --last             # latest log, 50 lines
bash scripts/remote_log.sh <server> <keyword>          # filter by keyword
bash scripts/remote_log.sh <server> <keyword> 100      # last 100 lines
bash scripts/remote_log.sh <server> <keyword> 0 -f     # live follow
```

- Keyword matches the config basename (e.g. `pointgate`, `noroute`, `posA`)
- When multiple tasks run on one server, use keyword to pick the right log

### 6. Kill Training

```bash
bash scripts/remote_kill.sh <server>                   # list all running tasks
bash scripts/remote_kill.sh <server> <keyword>         # kill by config keyword
bash scripts/remote_kill.sh <server> <pid>             # kill by PID
bash scripts/remote_kill.sh <server> --all             # kill all (confirms)
```

- Safe: only kills processes whose cwd matches the project's `remote_code_root`
- Priority: PID file → SIGTERM → 2s wait → SIGKILL

### 7. Pull Checkpoints / Logs

```bash
bash scripts/remote_pull.sh <server>                   # logs only (fast, ~MB)
bash scripts/remote_pull.sh <server> --full            # logs + .pth checkpoints (slow, ~GB)
```

- Logs save to `Checkpoints/<server>/<variant>/<timestamp>/`
- Checkpoints save to the same structure (alongside logs)
- `--full` can be very large (10-50GB per variant), use sparingly

### 8. Web Dashboard

```bash
# Start unified monitor (if not running)
python3 /home/songcl/3dres/project/monitor_server_all.py 8088 &
```

- `http://192.168.1.175:8088/` — Monitor: all GPUs + tasks + logs (10s auto-refresh)
- `http://192.168.1.175:8088/compare` — Compare: experiment ranking + charts (click rows to compare)

Compare page has **Pull Logs** button that pulls the selected project's logs and auto-refreshes.

## Common Patterns

### Run same config on multiple GPUs simultaneously
```bash
bash scripts/remote_train.sh server-4 configs/xxx.yaml 0   # GPU 0
bash scripts/remote_train.sh server-4 configs/yyy.yaml 1   # GPU 1 (different config)
```

### Run same config across servers
```bash
bash scripts/remote_train.sh server-2 configs/xxx.yaml 0   # server-2 GPU 0
bash scripts/remote_train.sh server-4 configs/xxx.yaml 0   # server-4 GPU 0
```

### Resume after crash/interruption
```bash
# Check what was last saved
bash scripts/remote_status.sh server-4
# Resume from latest checkpoint
bash scripts/remote_resume.sh server-4 configs/xxx.yaml 1
```

### Pull and compare results
```bash
# Pull latest logs from all servers
bash scripts/remote_pull.sh server-2
bash scripts/remote_pull.sh server-3
bash scripts/remote_pull.sh server-4
# Then open http://192.168.1.175:8088/compare
```

## Troubleshooting

### "work_dir not replaced"
Config YAML `work_dir` doesn't match SERVERS.yaml `local.work_dir`. Fix:
```bash
cd /home/songcl/3dres/project/<project>/<code_dir>
LOCAL_WD="/home/songcl/3dres/project/<project>/Checkpoints"
grep -rl "work_dir:" configs/ | while read f; do
    sed -i "s|work_dir:.*|work_dir: $LOCAL_WD|" "$f"
done
git add -A && git commit -m "Fix work_dir"
```

### "No checkpoint found for resume"
The `work_dir` on remote might be empty or at wrong path. Check:
```bash
ssh songcl@<ip> "ls <remote_work_dir>/<config_basename>/*/last.pth"
```

### "Kill doesn't find processes"
Processes were started from a different code path. Force kill:
```bash
ssh songcl@<ip> "pkill -f 'python.*tools/train.*<config_keyword>'"
```

### Port 8088 not accessible
```bash
fuser -k 8088/tcp
python3 /home/songcl/3dres/project/monitor_server_all.py 8088 &
# Or use SSH tunnel from laptop:
# ssh -N -L 8088:localhost:8088 songcl@192.168.1.175
```
