#!/usr/bin/env bash
# 决策日志 — 记录流水线所有自主决策（自动 + Claude 研究决策）
# 用法: bash log_decision.sh <project> <type> <question> <decision> [rationale] [evidence]
#
# type 取值:
#   early_stop   自动早停 kill
#   queue_push   自动队列推送
#   next_batch   下一批实验选择（Claude 研究决策）
#   route_change 路线扩展/放弃（Claude 研究决策）
#   question     提出但未自行拍板、留给用户确认的问题
#   other        其他
#
# 写入 pipeline/decisions/ 目录（每次决策一个独立 MD + 汇总索引 _index.md）:
#   pipeline/decisions/<YYYYMMDD-HHMMSS>_<type>.md   单次决策详情
#   pipeline/decisions/_index.md                     决策索引表
set -u

PROJECT=${1:?Usage: $0 <project> <type> <question> <decision> [rationale] [evidence]}
TYPE=${2:?}
QUESTION=${3:?}
DECISION=${4:?}
RATIONALE=${5:-}
EVIDENCE=${6:-}

ROOT="${PROJECT_ROOT:-/home/songcl/3dres/project}"
PROJECT_DIR=$ROOT/$PROJECT
if [ ! -d "$PROJECT_DIR" ]; then
  echo "错误: 项目目录不存在: $PROJECT_DIR"
  exit 1
fi

TSHUMAN=$(date '+%Y-%m-%d %H:%M:%S')
TSTAG=$(date '+%Y%m%d-%H%M%S')
DEC_DIR=$PROJECT_DIR/pipeline/decisions
mkdir -p "$DEC_DIR"

# 1. 写入独立决策文件
DEC_FILE=$DEC_DIR/${TSTAG}_${TYPE}.md
cat > "$DEC_FILE" << EOF
# ${PROJECT} 决策记录

- **时间**: $TSHUMAN
- **类型**: $TYPE
- **问题**: $QUESTION
- **决策**: $DECISION
EOF
[ -n "$RATIONALE" ] && echo "- **依据**: $RATIONALE" >> "$DEC_FILE"
[ -n "$EVIDENCE" ] && echo "- **证据**: $EVIDENCE" >> "$DEC_FILE"

# 2. 更新决策索引表 _index.md
INDEX_FILE=$DEC_DIR/_index.md
if [ ! -f "$INDEX_FILE" ]; then
  printf '# %s 决策索引\n\n| 时间 | 类型 | 问题 | 决策 |\n|------|------|------|------|\n' "$PROJECT" > "$INDEX_FILE"
fi

# 截断问题/决策到合理长度避免表格炸裂
Q_SHORT=$(echo "$QUESTION" | head -c 60 | tr '\n' ' ')
D_SHORT=$(echo "$DECISION" | head -c 60 | tr '\n' ' ')
printf '| %s | [%s](%s) | %s | %s |\n' \
  "$TSHUMAN" "$TYPE" "${TSTAG}_${TYPE}.md" "$Q_SHORT" "$D_SHORT" \
  >> "$INDEX_FILE"

echo "已记录决策 [$TYPE] -> $DEC_FILE"
