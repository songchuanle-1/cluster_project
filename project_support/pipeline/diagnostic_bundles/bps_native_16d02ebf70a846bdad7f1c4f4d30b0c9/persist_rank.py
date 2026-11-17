"""Bind the completed ranking screen without changing any scientific gate."""

from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import json

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
from pipeline_monitor import log_decision

PROJECT = Path("D:/project/cluster_project")
PIPE = PROJECT / "pipeline"
BUNDLE = Path(__file__).resolve().parent
TOKEN = "16d02ebf70a846bdad7f1c4f4d30b0c9"
owner = tick.load(PIPE / "headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
rank = tick.load(BUNDLE / "rank_result.json")
assert rank["token"] == TOKEN
summary_path = BUNDLE / "summary.json"
summary = tick.load(summary_path)
assert "query_rank_screen" not in summary
summary["query_rank_screen"] = {key: rank[key] for key in (
    "expressions", "scenes", "counts", "transitions",
    "universal_nonworsening_claim", "scope",
)}
summary["rank_adapter_failure_preserved"] = "V1 IndexError scene-ID metadata; V2 changes only scene indexing"
tick.save(summary_path, summary)
decision = log_decision(
    str(PROJECT), "other", "GT最小配对使原生低IoU掩码损失变正，是否保证更好的目标质量排序？",
    "否定该普遍保证；不把GT配对oracle直接变成训练修复。保留原生反例和原M201训练。",
    "50表达式40场景203048个非同IoU查询对彼此相关，不作独立样本。原1e-6口径：2645个同向变反向，11923个反向变同向；两种变化并存。例scene0141_00/ann5，q24IoU.6346>q50.0816，原cost差-.00355，oracle差+.1180。",
    str(BUNDLE / "rank_result.json"),
)
summary_ref = {"path": summary_path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(summary_path)}
work_path = PIPE / "research_work.json"
work = tick.load(work_path)


def update_summary_reference(value):
    if isinstance(value, dict):
        if value.get("path") == summary_ref["path"]:
            value["sha256"] = summary_ref["sha256"]
        for child in value.values():
            update_summary_reference(child)
    elif isinstance(value, list):
        for child in value:
            update_summary_reference(child)


for candidate in work["candidates"]:
    update_summary_reference(candidate)
bps = next(c for c in work["candidates"] if c["id"] == "m95-native-between-pair-support")
paths = [BUNDLE / name for name in (
    "rank_screen.py", "rank_screen_v2.py", "rank_execution_failure.json",
    "rank_result.json", "persist_rank.py",
)] + [PIPE / "designs/bps_query_rank_prereg_20261014_1334.md", Path(decision)]
for path in paths:
    bps["evidence"].append({"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)})
bps["scientific_scope"] += " NativebankGTminimum-pair universal nonworsening claim disconfirmed:2645separated concordant-to-discordant pairs/11923reverse among203048unequal-IoU pairs/50expr40scenes;correlatednotindependentsamples. No oracle repair admission."
tick.save(work_path, work)
notes_path = PIPE / "reports" / ("notes_" + TOKEN + ".json")
notes = tick.load(notes_path)
notes["actions"].append(
    "完整原生库24576查询中，50表达式有几何/6400查询、142表达式无可用cost；5389低于IoU.5，其中2907原始cost精确零、2155在oracle下超过1e-6。TRAIN indication选择106/192低IoU，其中86库内存在>=.5掩码；不是部署VAL或同类误绑定计数。"
)
notes["actions"].append(
    "CPU排序筛查：原V1场景元数据IndexError保留，V2只修每组单sceneID索引。50表达式40场景203048非同IoU查询对；原1e-6口径2645同向变反向/11923反向变同向，否定普遍不恶化保证。查询对相关，非独立样本/训练效应；全过程不改loss或gate。"
)
notes["decisions"].append(
    "两种排序变化并存，拒绝GT最小配对oracle天然改善目标质量排序的普遍主张；不是否定全部教师监督，也不是BPS训练终态。当前缺独立结构/任务层因果对照，不凑新的训练变体。"
)
tick.save(notes_path, notes)
tick.report("cluster_project", TOKEN, str(notes_path))
print(json.dumps({"bps_evidence_count": len(bps["evidence"]), "summary_sha256": summary_ref["sha256"], "decision": decision}))
