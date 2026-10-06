"""
Task Scheduler Optimization System
====================================
src/report_generator.py - Generate CSV and text reports
"""

import csv
import os
from datetime import datetime
from typing import Dict, List
from src.models import Task


def ensure_outputs_dir(path="outputs"):
    os.makedirs(path, exist_ok=True)


def generate_schedule_csv(summary: Dict, filename: str = None, output_dir: str = "outputs"):
    """Export scheduled tasks to CSV."""
    ensure_outputs_dir(output_dir)
    if not filename:
        algo_short = summary["algorithm"].split()[0].lower()
        filename = f"schedule_{algo_short}_{datetime.now().strftime('%H%M%S')}.csv"

    filepath = os.path.join(output_dir, filename)
    tasks = summary.get("tasks", [])

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Task ID", "Priority", "Skill", "Deadline (h)",
            "Duration (h)", "Profit", "Start (h)", "End (h)",
            "Assigned Resource", "Lateness (h)", "Status"
        ])
        for t in tasks:
            if t.is_missed:
                status = "MISSED"
            elif t.is_late:
                status = "LATE"
            else:
                status = "ON TIME"
            writer.writerow([
                t.task_id, t.priority, t.skill, t.deadline_h,
                t.duration_h, t.profit,
                t.start_h if not t.is_missed else "N/A",
                t.end_h if not t.is_missed else "N/A",
                t.assigned_resource or "N/A",
                t.lateness_h if not t.is_missed else "N/A",
                status
            ])
    return filepath


def generate_text_report(summary: Dict, output_dir: str = "outputs") -> str:
    """Generate a human-readable text performance report."""
    ensure_outputs_dir(output_dir)
    algo_short = summary["algorithm"].split()[0].lower()
    filepath = os.path.join(output_dir, f"report_{algo_short}.txt")

    lines = []
    sep = "=" * 60

    lines.append(sep)
    lines.append("  TASK SCHEDULER OPTIMIZATION SYSTEM - PERFORMANCE REPORT")
    lines.append(sep)
    lines.append(f"  Algorithm : {summary['algorithm']}")
    lines.append(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(sep)

    lines.append("\n  SUMMARY STATISTICS")
    lines.append("-" * 60)
    lines.append(f"  Total Tasks      : {summary['total_tasks']}")
    lines.append(f"  Scheduled        : {summary['scheduled_count']}")
    lines.append(f"  On Time          : {summary['on_time_count']}  ({summary['on_time_pct']}%)")
    lines.append(f"  Late             : {summary['late_count']}")
    lines.append(f"  Missed           : {summary['missed_count']}")
    lines.append(f"  Total Profit     : {summary['total_profit']}")
    lines.append(f"  Total Lateness   : {summary['total_lateness_h']}h")
    lines.append(f"  Makespan         : {summary['makespan']}h")

    lines.append("\n  OPTIMIZED SCHEDULE")
    lines.append("-" * 60)
    header = f"  {'Task':<8} {'Res':<5} {'Start':>6} {'End':>6} {'Ddl':>6} {'Late':>6} {'Status':<10}"
    lines.append(header)
    lines.append("  " + "-" * 55)

    for t in sorted(summary.get("scheduled", []), key=lambda x: x.start_h or 0):
        status = "LATE" if t.is_late else "OK"
        lines.append(
            f"  {t.task_id:<8} {t.assigned_resource or '':<5} "
            f"{t.start_h:>6} {t.end_h:>6} {t.deadline_h:>6} "
            f"{t.lateness_h:>6}h  {status:<10}"
        )

    if summary.get("missed"):
        lines.append("\n  MISSED TASKS (could not be scheduled)")
        lines.append("-" * 60)
        for t in summary["missed"]:
            lines.append(f"  {t.task_id:<8} priority={t.priority} deadline={t.deadline_h}h")

    lines.append("\n" + sep)
    lines.append("  END OF REPORT")
    lines.append(sep)

    report = "\n".join(lines)
    with open(filepath, 'w') as f:
        f.write(report)

    return filepath



def generate_comparison_report(comparison: Dict, output_dir: str = "outputs") -> str:
    """Generate algorithm comparison report."""
    ensure_outputs_dir(output_dir)
    filepath = os.path.join(output_dir, "comparison_report.txt")

    lines = []
    sep = "=" * 90
    lines.append(sep)
    lines.append("  SMART JOB SCHEDULER — ALGORITHM COMPARISON REPORT")
    lines.append("  Greedy vs Dynamic Programming vs Backtracking")
    lines.append(sep)

    header = f"  {'Algorithm':<36} {'OnTime%':>8} {'Profit':>7} {'Late':>6} {'Miss':>5} {'Time(ms)':>9} {'Time Complexity':<18}"
    lines.append(header)
    lines.append("  " + "-" * 88)

    for c in comparison["comparison"]:
        algo_short = c["algorithm"][:35]
        exec_t = f"{c.get('execution_time_ms', 0.0):.2f}ms"
        lines.append(
            f"  {algo_short:<36} {c['on_time_pct']:>7}% {c['total_profit']:>7} "
            f"{c['total_lateness_h']:>5}h {c['missed_count']:>5} {exec_t:>9} {c.get('time_complexity', 'N/A'):<18}"
        )

    lines.append("\n  SUMMARY & WINNERS")
    lines.append("-" * 90)
    lines.append(f"  Best Profit    : {comparison['best_profit_algo']}")
    lines.append(f"  Best On-Time   : {comparison['best_ontime_algo']}")
    lines.append(f"  Least Lateness : {comparison['best_lateness_algo']}")
    lines.append(f"  Fastest Exec   : {comparison.get('fastest_algo', 'N/A')}")
    lines.append(sep)

    report = "\n".join(lines)
    with open(filepath, 'w') as f:
        f.write(report)
    return filepath