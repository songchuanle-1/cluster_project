#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练日志分析脚本
从多个训练日志中提取每轮的 mIoU，生成对比表格和图表
"""

import re
import os
import glob
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适用于服务器环境
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
from typing import List, Dict, Tuple


def parse_log_file(log_path: str) -> List[float]:
    """
    解析单个日志文件，提取每个 epoch 的 mIoU

    Args:
        log_path: 日志文件路径

    Returns:
        List[float]: 每个 epoch 的 mIoU 值
    """
    mious = []

    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 匹配 "mIoU: 0.xxxx" 格式
            match = re.search(r'mIoU\s*:\s*(\d+\.\d+)', line)
            if match:
                miou = float(match.group(1))
                mious.append(miou)

    return mious


def find_log_files(checkpoint_dir: str) -> Dict[str, str]:
    """
    在 checkpoint 目录中查找所有日志文件

    Args:
        checkpoint_dir: checkpoint 根目录

    Returns:
        Dict[str, str]: {模型名称: 日志文件路径}
    """
    log_files = {}

    # 遍历所有模型目录
    for model_dir in glob.glob(os.path.join(checkpoint_dir, 'model_*')):
        if not os.path.isdir(model_dir):
            continue

        model_name = os.path.basename(model_dir)

        # 查找最新的日志文件（按时间戳目录）
        log_candidates = []
        for timestamp_dir in glob.glob(os.path.join(model_dir, '20*')):
            if os.path.isdir(timestamp_dir):
                log_path = os.path.join(timestamp_dir, f'{os.path.basename(timestamp_dir)}.log')
                if os.path.exists(log_path):
                    log_candidates.append((timestamp_dir, log_path))

        # 选择最新的日志文件
        if log_candidates:
            log_candidates.sort(key=lambda x: x[0], reverse=True)
            log_files[model_name] = log_candidates[0][1]

    return log_files


def read_log_list(log_list_path: str) -> Dict[str, str]:
    """
    从 txt 文件中读取日志路径列表

    支持两种格式：
    1. 每行一个路径: /path/to/log (模型名从路径中推断)
    2. 每行 "名称 路径": model_name /path/to/log (用空格或tab分隔)
    3. 以 # 开头的行为注释，会被忽略

    Args:
        log_list_path: txt 文件路径

    Returns:
        Dict[str, str]: {模型名称: 日志文件路径}
    """
    log_files = {}

    with open(log_list_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue

            # 尝试解析 "名称 路径" 格式
            parts = line.split(None, 1)  # 按空白字符分割，最多分2部分

            if len(parts) == 2:
                # 格式: model_name /path/to/log
                model_name, log_path = parts
            elif len(parts) == 1:
                # 格式: /path/to/log (从路径推断模型名)
                log_path = parts[0]
                # 从路径中提取模型名（取倒数第二或第三层目录）
                path_parts = Path(log_path).parts
                # 通常路径结构: .../model_name/timestamp/timestamp.log
                if len(path_parts) >= 3:
                    model_name = path_parts[-3]  # 倒数第三层
                elif len(path_parts) >= 2:
                    model_name = path_parts[-2]
                else:
                    model_name = Path(log_path).stem
            else:
                print(f"⚠ 第 {line_num} 行格式错误，跳过: {line}")
                continue

            # 检查文件是否存在
            if not os.path.exists(log_path):
                print(f"⚠ 日志文件不存在，跳过: {log_path}")
                continue

            log_files[model_name] = log_path

    return log_files


def extract_results(log_files: Dict[str, str], max_epochs: int = None) -> pd.DataFrame:
    """
    从多个日志文件中提取结果

    Args:
        log_files: {模型名称: 日志文件路径}
        max_epochs: 最大 epoch 数（可选）

    Returns:
        pd.DataFrame: 结果表格
    """
    results = {}

    for model_name, log_path in log_files.items():
        mious = parse_log_file(log_path)

        # 限制 epoch 数
        if max_epochs is not None:
            mious = mious[:max_epochs]

        results[model_name] = mious

    # 转换为 DataFrame
    max_len = max(len(v) for v in results.values()) if results else 0

    # 填充缺失值
    for model_name in results:
        if len(results[model_name]) < max_len:
            results[model_name].extend([None] * (max_len - len(results[model_name])))

    df = pd.DataFrame(results)
    df.index = range(1, max_len + 1)
    df.index.name = 'Epoch'

    return df


def generate_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成统计摘要

    Args:
        df: 原始结果 DataFrame

    Returns:
        pd.DataFrame: 统计摘要
    """
    stats = {}

    for model_name in df.columns:
        mious = df[model_name].dropna()

        if len(mious) > 0:
            stats[model_name] = {
                'Best mIoU': mious.max(),
                'Best Epoch': mious.idxmax(),
                'Final mIoU': mious.iloc[-1],
                'Avg mIoU': mious.mean(),
                'Total Epochs': len(mious)
            }
        else:
            stats[model_name] = {
                'Best mIoU': None,
                'Best Epoch': None,
                'Final mIoU': None,
                'Avg mIoU': None,
                'Total Epochs': 0
            }

    return pd.DataFrame(stats).T


def plot_comparison(df: pd.DataFrame, output_path: str, title: str = "Model Comparison"):
    """
    生成对比曲线图

    Args:
        df: 结果 DataFrame
        output_path: 输出图片路径
        title: 图表标题
    """
    plt.figure(figsize=(12, 8))

    # 设置不同的线型和颜色
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    for i, model_name in enumerate(df.columns):
        color = colors[i % len(colors)]
        mious = df[model_name].dropna()

        if len(mious) > 0:
            plt.plot(mious.index, mious.values,
                    label=f'{model_name} (best: {mious.max():.4f})',
                    color=color, linewidth=2, marker='o', markersize=3)

    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('mIoU', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, loc='best')
    plt.grid(True, alpha=0.3)

    # 添加最佳 mIoU 水平线
    max_miou = df.max().max()
    if pd.notna(max_miou):
        plt.axhline(y=max_miou, color='red', linestyle='--', alpha=0.5,
                   label=f'Best overall: {max_miou:.4f}')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 图表已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='分析训练日志并生成对比结果')
    parser.add_argument('--log_list', type=str,
                       default='log_list.txt',
                       help='日志路径列表的 txt 文件（每行一个路径，格式: 名称 路径）')
    parser.add_argument('--checkpoint_dir', type=str,
                       default='/data/songcl/3dres/Cluster_project2/Cluster_checkpoints',
                       help='Checkpoint 目录路径（当不提供 --log_list 时使用）')
    parser.add_argument('--models', type=str, nargs='+',
                       help='指定要分析的模型名称（可选，不指定则分析所有模型）')
    parser.add_argument('--max_epochs', type=int, default=None,
                       help='最大 epoch 数（可选）')
    parser.add_argument('--output_dir', type=str,
                       default='gbcr_current_comparison',
                       help='输出目录')

    args = parser.parse_args()
    # args.output_dir = os.path.abspath(args.log_list) 
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 获取日志文件
    if args.log_list:
        # 从 txt 文件读取日志路径
        print(f"正在从文件读取日志路径: {args.log_list}")
        log_files = read_log_list(args.log_list)
    else:
        # 扫描 checkpoint 目录
        print(f"正在扫描目录: {args.checkpoint_dir}")
        log_files = find_log_files(args.checkpoint_dir)

        # 过滤指定的模型
        if args.models:
            log_files = {k: v for k, v in log_files.items() if k in args.models}

    if not log_files:
        print("未找到任何日志文件！")
        return

    print(f"\n找到 {len(log_files)} 个模型的日志：")
    for model_name, log_path in log_files.items():
        print(f"  - {model_name}: {log_path}")

    # 提取结果
    print("\n正在提取结果...")
    df = extract_results(log_files, args.max_epochs)

    # 保存 CSV
    csv_path = os.path.join(args.output_dir, 'epoch_results.csv')
    df.to_csv(csv_path)
    print(f"✓ 结果表格已保存到: {csv_path}")

    # 生成统计摘要
    stats_df = generate_summary_stats(df)
    stats_path = os.path.join(args.output_dir, 'summary_stats.csv')
    stats_df.to_csv(stats_path)
    print(f"✓ 统计摘要已保存到: {stats_path}")

    # 打印统计摘要
    print("\n" + "="*80)
    print("模型性能统计摘要")
    print("="*80)
    print(stats_df.to_string())
    print("="*80)

    # 生成对比图
    plot_path = os.path.join(args.output_dir, 'comparison_plot.png')
    plot_comparison(df, plot_path, "Early Exit Variants Comparison")

    # 生成前 20 轮的详细对比图
    if len(df) > 20:
        df_first20 = df.iloc[:20]
        plot_path_20 = os.path.join(args.output_dir, 'comparison_first20.png')
        plot_comparison(df_first20, plot_path_20, "Early Exit Variants Comparison (First 20 Epochs)")

    print(f"\n✓ 分析完成！所有结果已保存到: {args.output_dir}")


if __name__ == '__main__':
    main()
