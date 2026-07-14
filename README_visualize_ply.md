# 点云可视化环境与使用

本说明提供一整套流程：创建 conda 环境、运行脚本、产出结果。

## 1. 创建与激活环境

```bash
cd /data/songcl/3dres/Agent_project/Agent
conda env create -f environment-visualize-ply.yml
# 激活（非交互 Shell 推荐）
source "$(conda info --base)/etc/profile.d/conda.sh" && conda activate plyviz
```

验证 `open3d`：
```bash
python -c "import open3d, sys; print(open3d.__version__)"
```

## 2. 列出与查看点云

```bash
# 列出前 10 个文件
python tools/visualize_ply.py --list --limit 10

# 交互式查看（按索引）
python tools/visualize_ply.py --index 1 --interactive

# 交互式查看（直指文件）
python tools/visualize_ply.py --file /data/songcl/3dres/data/scannetv2/train/scene0000_00_vh_clean_2.ply --interactive

交互模式说明：
- 鼠标拖拽旋转，滚轮缩放，Shift+拖拽平移（Open3D 默认交互）。
- 按 `S` 键：将当前视角截图保存到 `--screenshot_dir`（默认 `work_dirs/plyviz_screens`）。
- 自定义分辨率：`--width 1920 --height 1080`。
```

## 3. 批量保存截图

```bash
# 保存前 5 个为 PNG 到 work_dirs/plyviz_screens
python tools/visualize_ply.py --limit 5 --save work_dirs/plyviz_screens

# 递归全量保存
python tools/visualize_ply.py --recursive --save work_dirs/plyviz_screens

# 只保存原始点云（排除 labels）
python tools/visualize_ply.py --pattern "*vh_clean_2.ply" --limit 5 --save work_dirs/plyviz_screens
```

无显示环境（服务器）如遇截图失败，可用 `xvfb-run`：
```bash
sudo apt-get update && sudo apt-get install -y xvfb
xvfb-run -a python tools/visualize_ply.py --pattern "*vh_clean_2.ply" --limit 1 --save work_dirs/plyviz_screens
```

## 4. 常用参数

- `--dir`：点云目录，默认 `/data/songcl/3dres/data/scannetv2/train`
- `--recursive`：是否递归查找
- `--pattern`：非递归模式匹配，如 `"*.labels.ply"`
- `--width/--height`：截图分辨率

## 5. 产出位置

截图默认输出到 `Agent/work_dirs/plyviz_screens/*.png`（可自定义）。

## 6. 多窗口四视图同步比较 (tools/visualize.py)

脚本 `tools/visualize.py` 支持同时查看四个点云版本：原始、GT 掩码、高版本预测1、高版本预测2，并同步第一窗口的视角。

### 交互模式

需要图形界面 (`DISPLAY` 或 `WAYLAND_DISPLAY`)：
```bash
python tools/visualize.py \
	--compare_json_path /path/to/BQNet_IPDN.json \
	--pc_root_path /data/songcl/3dres/data/scannetv2/val \
	--gt_pmask_root_path /data/songcl/3dres/BQNet/GRES/results_best_gres/gt_pmasks \
	--pre1_pmask_root_path /data/songcl/3dres/BQNet/GRES/results_best_gres/pred_pmasks \
	--pre2_pmask_root_path /data/songcl/3dres/IPDN/IPDN_checkpoints/model/results_best_gres/pred_pmasks \
	--save_img_path /data/songcl/3dres/BQNet/GRES/results_best_gres/compare_img
```

操作说明：
- 在第一个窗口旋转/缩放，其它窗口自动同步视角。
- 按 `S`：同时保存四个窗口当前截图到 `--save_img_path/<sample_id>/`。
- 按 `Q`：结束当前样本，进入下一个。

截图命名格式：`<sample_id>_<suffix>_<timestamp>.png`，`suffix` 属于 `original | gt | pred1 | pred2`。

### Headless 离屏模式

若无显示环境或通过 SSH 想直接批量保存：
```bash
python tools/visualize.py --headless \
	--compare_json_path /path/to/BQNet_IPDN.json \
	--pc_root_path /data/songcl/3dres/data/scannetv2/val \
	--gt_pmask_root_path /data/songcl/3dres/BQNet/GRES/results_best_gres/gt_pmasks \
	--pre1_pmask_root_path /data/songcl/3dres/BQNet/GRES/results_best_gres/pred_pmasks \
	--pre2_pmask_root_path /data/songcl/3dres/IPDN/IPDN_checkpoints/model/results_best_gres/pred_pmasks \
	--save_img_path /data/songcl/3dres/BQNet/GRES/results_best_gres/compare_img
```

该模式直接离屏渲染并保存四张图（不显示窗口），便于服务器批处理。可与 `xvfb-run` 结合使用：
```bash
xvfb-run -a python tools/visualize.py --headless --compare_json_path /path/to/BQNet_IPDN.json \
	--pc_root_path /data/songcl/3dres/data/scannetv2/val \
	--gt_pmask_root_path /data/songcl/3dres/BQNet/GRES/results_best_gres/gt_pmasks \
	--pre1_pmask_root_path /data/songcl/3dres/BQNet/GRES/results_best_gres/pred_pmasks \
	--pre2_pmask_root_path /data/songcl/3dres/IPDN/IPDN_checkpoints/model/results_best_gres/pred_pmasks \
	--save_img_path /data/songcl/3dres/BQNet/GRES/results_best_gres/compare_img
```

### 参数补充
- `--headless`：启用离屏批量四视图保存，不启动交互窗口。
- `--save_img_path`：输出根目录，内部按 `<sample_id>` 分子目录组织结果。
- 掩码 JSON 使用 RLE 编码（脚本内部自动解码）。

