"""
Smart Job Scheduler
====================================
src/visualizer.py - High-Resolution Chart Generation for Algorithm Analysis

Generates publication-quality charts for college reports, evaluation presentations,
and experimental analysis using Matplotlib:
1. Runtime Scaling Plot (Polynomial vs Exponential with theoretical Big-O curves)
2. KPI Comparison Bar Chart (Profit, On-Time %, Lateness, Makespan)
"""

import os
from typing import List, Dict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend safe for all platforms
import matplotlib.pyplot as plt
import numpy as np


def ensure_outputs_dir(path: str = "outputs"):
    os.makedirs(path, exist_ok=True)


def plot_runtime_scaling(benchmark_results: List[Dict], output_path: str = "outputs/runtime_scaling.png") -> str:
    """
    Generate runtime scaling plot comparing Greedy O(N log N), DP O(M*N log N),
    and Backtracking O((M+1)^N).
    Uses dual axes (Linear/Log) to clearly showcase exponential vs polynomial growth.
    """
    ensure_outputs_dir(os.path.dirname(output_path) or "outputs")

    sizes = [r["size"] for r in benchmark_results]
    greedy_times = [r["greedy_time_ms"] for r in benchmark_results]
    dp_times = [r["dp_time_ms"] for r in benchmark_results]
    bt_times = [r["bt_time_ms"] for r in benchmark_results]
    bt_nodes = [r.get("bt_nodes", 0) for r in benchmark_results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), facecolor='#0d1117')
    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        ax.grid(True, linestyle='--', alpha=0.25, color='#8b949e')
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    # Subplot 1: Measured Execution Time (ms)
    ax1.plot(sizes, greedy_times, 'o-', color='#00d4ff', linewidth=2.5, markersize=8, label='Greedy (EDF + Topo)')
    ax1.plot(sizes, dp_times, 's-', color='#22c55e', linewidth=2.5, markersize=8, label='Dynamic Programming')
    ax1.plot(sizes, bt_times, '^-', color='#a78bfa', linewidth=2.8, markersize=9, label='Backtracking (Branch & Bound)')

    ax1.set_title("Measured Execution Time (Wall-Clock ms)", fontsize=13, fontweight='bold', color='#f0f6fc', pad=12)
    ax1.set_xlabel("Number of Jobs (N)", fontsize=11, color='#c9d1d9', labelpad=8)
    ax1.set_ylabel("Execution Time (milliseconds)", fontsize=11, color='#c9d1d9', labelpad=8)
    ax1.set_yscale('log')
    ax1.legend(loc='upper left', facecolor='#161b22', edgecolor='#30363d', labelcolor='#f0f6fc', fontsize=10)

    # Subplot 2: Backtracking Search Tree Nodes Growth
    ax2.bar([str(s) for s in sizes], bt_nodes, color='#7c3aed', alpha=0.85, edgecolor='#a78bfa', linewidth=1.5, width=0.5)
    for i, v in enumerate(bt_nodes):
        ax2.text(i, v * 1.08 + 1, f"{v:,} nodes", ha='center', va='bottom', color='#f0f6fc', fontsize=9, fontweight='bold')

    ax2.set_title("Backtracking State Space (Nodes Explored)", fontsize=13, fontweight='bold', color='#f0f6fc', pad=12)
    ax2.set_xlabel("Number of Jobs (N)", fontsize=11, color='#c9d1d9', labelpad=8)
    ax2.set_ylabel("Recursive Search Nodes", fontsize=11, color='#c9d1d9', labelpad=8)
    ax2.set_yscale('log')

    fig.suptitle("Smart Job Scheduler — Empirical Complexity Scaling Analysis\nTheoretical: Greedy O(N log N) | DP O(M·N log N) | Backtracking O((M+1)^N)",
                 fontsize=14, fontweight='bold', color='#58a6ff', y=1.02)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return output_path


def plot_algorithm_comparison(comparison_data: Dict, output_path: str = "outputs/algorithm_comparison.png") -> str:
    """
    Generate side-by-side grouped KPI comparison bar chart for Profit, On-Time %,
    Lateness, and Makespan.
    """
    ensure_outputs_dir(os.path.dirname(output_path) or "outputs")

    results = comparison_data.get("comparison", [])
    if not results:
        return ""

    algos = [r["algorithm"].split("(")[0].strip() for r in results]
    profits = [r["total_profit"] for r in results]
    ontime_pcts = [float(r["on_time_pct"]) for r in results]
    lateness = [r["total_lateness_h"] for r in results]
    makespans = [r.get("makespan", 0) for r in results]

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), facecolor='#0d1117')
    axes = axes.flatten()

    for ax in axes:
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#c9d1d9')
        ax.grid(True, linestyle='--', alpha=0.25, color='#8b949e', axis='y')
        for spine in ax.spines.values():
            spine.set_color('#30363d')

    colors = ['#00d4ff', '#22c55e', '#a78bfa', '#f59e0b'][:len(algos)]

    # 1. Total Profit
    b1 = axes[0].bar(algos, profits, color=colors, edgecolor='#ffffff22', width=0.5)
    axes[0].set_title("Total Earned Profit (Higher is Better)", color='#f0f6fc', fontweight='bold', fontsize=11)
    axes[0].set_ylabel("Profit Score", color='#c9d1d9')
    for bar in b1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 15, f"{int(yval)}", ha='center', va='bottom', color='#f0f6fc', fontweight='bold')

    # 2. On-Time %
    b2 = axes[1].bar(algos, ontime_pcts, color=colors, edgecolor='#ffffff22', width=0.5)
    axes[1].set_title("On-Time Completion Rate % (Higher is Better)", color='#f0f6fc', fontweight='bold', fontsize=11)
    axes[1].set_ylabel("On-Time Percentage", color='#c9d1d9')
    axes[1].set_ylim(0, 110)
    for bar in b2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}%", ha='center', va='bottom', color='#f0f6fc', fontweight='bold')

    # 3. Total Lateness (h)
    b3 = axes[2].bar(algos, lateness, color=['#ef4444' if l > 0 else '#22c55e' for l in lateness], edgecolor='#ffffff22', width=0.5)
    axes[2].set_title("Total Lateness in Hours (Lower is Better)", color='#f0f6fc', fontweight='bold', fontsize=11)
    axes[2].set_ylabel("Hours Late", color='#c9d1d9')
    for bar in b3:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{int(yval)}h", ha='center', va='bottom', color='#f0f6fc', fontweight='bold')

    # 4. Makespan (h)
    b4 = axes[3].bar(algos, makespans, color=colors, edgecolor='#ffffff22', width=0.5)
    axes[3].set_title("Schedule Makespan in Hours (Completion Horizon)", color='#f0f6fc', fontweight='bold', fontsize=11)
    axes[3].set_ylabel("Hours", color='#c9d1d9')
    for bar in b4:
        yval = bar.get_height()
        axes[3].text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{int(yval)}h", ha='center', va='bottom', color='#f0f6fc', fontweight='bold')

    fig.suptitle("Smart Job Scheduler — Algorithm Performance Evaluation",
                 fontsize=14, fontweight='bold', color='#58a6ff', y=0.99)

    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.08, right=0.95, hspace=0.32, wspace=0.22)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return output_path
