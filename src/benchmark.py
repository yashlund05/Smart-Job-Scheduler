"""
Smart Job Scheduler
====================================
src/benchmark.py - Algorithm Benchmark Suite

Compares Greedy, Dynamic Programming, and Backtracking on different task sizes:
5, 8, 10, 12 tasks. Measures real execution time (ms) and showcases the
theoretical complexity trade-offs (Polynomial vs Exponential).
"""

import copy
import sys
import time
from typing import List, Dict

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from src.models import Task, Resource
from src.greedy_scheduler import GreedyScheduler
from src.dp_scheduler import DPScheduler
from src.backtracking_scheduler import BacktrackingScheduler


def generate_benchmark_tasks(count: int) -> List[Task]:
    """Generate a realistic set of benchmark tasks of given size."""
    raw_pool = [
        # (id, dur, ddl, prio, skill, deps, profit)
        ('J1', 2, 8,  5, 'backend',  [],        100),
        ('J2', 1, 6,  4, 'frontend', [],        50),
        ('J3', 2, 10, 4, 'qa',       ['J1'],    80),
        ('J4', 1, 6,  3, 'frontend', [],        40),
        ('J5', 3, 14, 5, 'backend',  ['J1'],    120),
        ('J6', 2, 12, 3, 'qa',       ['J2'],    70),
        ('J7', 4, 18, 4, 'frontend', ['J4'],    110),
        ('J8', 2, 16, 2, 'backend',  ['J5'],    60),
        ('J9', 3, 22, 5, 'qa',       ['J3'],    130),
        ('J10', 1, 20, 3, 'backend', [],        45),
        ('J11', 2, 24, 4, 'frontend', ['J7'],   90),
        ('J12', 3, 26, 5, 'qa',      ['J9'],    140),
        ('J13', 2, 28, 2, 'backend', [],        55),
        ('J14', 4, 30, 3, 'frontend', ['J11'],  105),
        ('J15', 2, 32, 4, 'qa',      ['J12'],   85),
    ]

    selected = raw_pool[:count]
    tasks = []
    selected_ids = {item[0] for item in selected}
    for item in selected:
        valid_deps = [d for d in item[5] if d in selected_ids]
        tasks.append(Task(
            task_id=item[0],
            duration_h=item[1],
            deadline_h=item[2],
            priority=item[3],
            skill=item[4],
            depends_on=valid_deps,
            profit=item[6]
        ))
    return tasks


def get_standard_resources() -> List[Resource]:
    return [
        Resource('R1', {'backend', 'qa'},       0, 8, 8),
        Resource('R2', {'frontend', 'qa'},      0, 8, 8),
        Resource('R3', {'backend', 'frontend'}, 0, 8, 8),
    ]


def run_benchmarks(sizes: List[int] = [5, 8, 10, 12], horizon: int = 72) -> List[Dict]:
    """
    Run empirical benchmarks for Greedy, DP, and Backtracking.
    Measures actual execution time with time.perf_counter().
    """
    resources = get_standard_resources()
    results = []

    for size in sizes:
        tasks = generate_benchmark_tasks(size)

        # 1. Greedy
        g_sched = GreedyScheduler(copy.deepcopy(tasks), copy.deepcopy(resources), horizon)
        t0 = time.perf_counter()
        g_sum = g_sched.get_summary()
        g_time = (time.perf_counter() - t0) * 1000

        # 2. Dynamic Programming
        dp_sched = DPScheduler(copy.deepcopy(tasks), copy.deepcopy(resources), horizon)
        t0 = time.perf_counter()
        dp_sum = dp_sched.get_summary()
        dp_time = (time.perf_counter() - t0) * 1000

        # 3. Backtracking
        bt_sched = BacktrackingScheduler(copy.deepcopy(tasks), copy.deepcopy(resources), horizon)
        t0 = time.perf_counter()
        bt_sum = bt_sched.get_summary()
        bt_time = (time.perf_counter() - t0) * 1000

        results.append({
            "size": size,
            "greedy_time_ms": round(g_time, 3),
            "greedy_profit": g_sum["total_profit"],
            "dp_time_ms": round(dp_time, 3),
            "dp_profit": dp_sum["total_profit"],
            "bt_time_ms": round(bt_time, 3),
            "bt_profit": bt_sum["total_profit"],
            "bt_nodes": bt_sum.get("nodes_explored", 0),
        })

    return results


def print_benchmark_table(results: List[Dict]):
    """Print formatted benchmark comparison table."""
    print("\n" + "=" * 86)
    print("  SMART JOB SCHEDULER — PERFORMANCE BENCHMARK (MEASURED EXECUTION TIME)")
    print("  Theoretical Big-O: Greedy O(N log N) | DP O(M·N log N) | Backtracking O((M+1)^N)")
    print("=" * 86)
    print(f"  {'Jobs':<6} | {'Greedy Time':<13} {'Profit':<8} | {'DP Time':<13} {'Profit':<8} | {'Backtracking Time':<18} {'Profit':<8} {'Nodes':<6}")
    print("  " + "-" * 82)
    for r in results:
        print(
            f"  {r['size']:<6} | "
            f"{r['greedy_time_ms']:>8.3f} ms   {r['greedy_profit']:<8} | "
            f"{r['dp_time_ms']:>8.3f} ms   {r['dp_profit']:<8} | "
            f"{r['bt_time_ms']:>10.3f} ms        {r['bt_profit']:<8} {r['bt_nodes']:<6}"
        )
    print("=" * 86)
    print("  Observation: Backtracking search nodes grow exponentially with job count,")
    print("  while Greedy and Dynamic Programming remain ultra-fast and scale polynomially.")
    print("=" * 86 + "\n")


if __name__ == '__main__':
    res = run_benchmarks([5, 8, 10, 12])
    print_benchmark_table(res)
