#!/usr/bin/env python3
"""
Smart Job Scheduler
====================================
Smart Job Scheduling Using Greedy, Dynamic Programming and Backtracking Techniques
main.py - CLI Entry Point & Comparison Engine

Run with:
    python main.py                          # run all algorithms and compare
    python main.py --algo greedy            # run Greedy algorithm
    python main.py --algo dp                # run Dynamic Programming
    python main.py --algo backtracking      # run Backtracking
    python main.py --compare                # side-by-side comparison
    python main.py --benchmark              # run 5, 8, 10, 12 jobs benchmark
    python main.py --add-task               # interactive task addition
"""

import argparse
import sys
import os

# Safe UTF-8 encoding configuration for Windows terminals
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models import (
    load_tasks, load_resources, validate_tasks, Task,
    get_greedy_trap_dataset, get_cycle_demo_dataset, detect_dependency_cycle
)
from src.greedy_scheduler import GreedyScheduler
from src.dp_scheduler import DPScheduler
from src.backtracking_scheduler import BacktrackingScheduler
from src.priority_scheduler import PriorityQueueScheduler
from src.metrics import compute_kpis, compare_algorithms
from src.report_generator import (
    generate_schedule_csv, generate_text_report, generate_comparison_report
)
from src.benchmark import run_benchmarks, print_benchmark_table
try:
    from src.visualizer import plot_runtime_scaling, plot_algorithm_comparison
    HAS_VISUALIZER = True
except ImportError:
    HAS_VISUALIZER = False


# ─── ANSI colors ──────────────────────────────────────────────────────────────
class C:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    CYAN    = '\033[96m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    RED     = '\033[91m'
    PURPLE  = '\033[95m'
    GREY    = '\033[90m'
    WHITE   = '\033[97m'

def color(text, *codes):
    return ''.join(codes) + str(text) + C.RESET

def print_banner():
    banner = f"""
{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                   SMART JOB SCHEDULER                        ║
║  Greedy vs Dynamic Programming vs Backtracking Techniques   ║
║             College DAA Algorithm Project                    ║
╚══════════════════════════════════════════════════════════════╝
{C.RESET}"""
    print(banner)

def print_kpis(summary: dict):
    kpi = compute_kpis(summary)
    print(f"\n  {color('ALGORITHM       :', C.GREY)} {color(kpi['algorithm'], C.CYAN, C.BOLD)}")
    print(f"  {'─'*64}")
    print(f"  {color('Total Tasks     :', C.GREY)} {color(kpi['total_tasks'], C.WHITE, C.BOLD)}")
    print(f"  {color('Scheduled       :', C.GREY)} {color(kpi['scheduled_count'], C.GREEN)}")
    print(f"  {color('On Time         :', C.GREY)} {color(kpi['on_time_count'], C.GREEN)} "
          f"  ({color(kpi['on_time_pct'], C.GREEN)}%)")
    print(f"  {color('Late Tasks      :', C.GREY)} {color(kpi['late_count'], C.YELLOW)}"
          f"  (total lateness: {color(kpi['total_lateness_h'], C.YELLOW)}h)")
    print(f"  {color('Missed          :', C.GREY)} {color(kpi['missed_count'], C.RED)}")
    print(f"  {color('Total Profit    :', C.GREY)} {color(kpi['total_profit'], C.PURPLE, C.BOLD)}"
          f"  ({color(kpi['profit_efficiency_pct'], C.PURPLE)}% efficiency)")
    print(f"  {color('Makespan        :', C.GREY)} {color(kpi['makespan'], C.CYAN)}h")
    print(f"  {color('Measured Time   :', C.GREY)} {color(str(kpi.get('execution_time_ms', 0.0)) + ' ms', C.WHITE, C.BOLD)}")
    print(f"  {color('Time Complexity :', C.GREY)} {color(kpi.get('time_complexity', 'N/A'), C.CYAN)} (Theoretical Big-O)")
    print(f"  {color('Space Complexity:', C.GREY)} {color(kpi.get('space_complexity', 'N/A'), C.CYAN)} (Theoretical Big-O)")
    if 'nodes_explored' in kpi:
        print(f"  {color('Search Nodes    :', C.GREY)} {color(kpi['nodes_explored'], C.YELLOW)} (Backtracking tree nodes)")
    if 'pruned_branches' in summary:
        print(f"  {color('Branches Pruned :', C.GREY)} {color(summary['pruned_branches'], C.GREEN, C.BOLD)} (Branch & Bound cuts)")
    if 'pruning_efficiency_pct' in summary:
        print(f"  {color('Prune Efficiency:', C.GREY)} {color(str(summary['pruning_efficiency_pct']) + '%', C.GREEN, C.BOLD)} state space eliminated")
    if 'theoretical_states' in summary:
        print(f"  {color('State Space Size:', C.GREY)} {color(summary['theoretical_states'], C.GREY)} (M+1)^N potential states")

def print_greedy_trace(summary: dict):
    """Print step-by-step trace of Kahn's topological sort and greedy assignments."""
    print(f"\n  {color('════ STEP-BY-STEP GREEDY ALGORITHM TRACE ════', C.CYAN, C.BOLD)}")

    # 1. Topological Sort Trace
    topo_trace = summary.get('topo_trace', [])
    if topo_trace:
        print("\n  " + color("1. Kahn's Topological Sort (Precedence Resolution):", C.WHITE, C.BOLD))
        print(f"  {'─'*75}")
        print(f"  {'Step':<6} {'Ready Queue (In-Degree=0)':<30} {'Chosen Job':<12} {'Tie-Break Rule'}")
        print(f"  {'─'*75}")
        for step in topo_trace:
            ready_str = "[" + ", ".join(step["ready_set"]) + "]"
            chosen = step["chosen"]
            rule = f"Prio {step['chosen_priority']} | Ddl {step['chosen_deadline']}h"
            print(f"  {step['step']:<6} {ready_str:<30} {color(chosen, C.CYAN, C.BOLD):<20} {color(rule, C.GREY)}")

    # 2. Greedy Decision Allocation Trace
    dec_trace = summary.get('decision_trace', [])
    if dec_trace:
        print(f"\n  {color('2. Greedy Resource Placement (Earliest Compatible Window):', C.WHITE, C.BOLD)}")
        print(f"  {'─'*75}")
        print(f"  {'Job':<8} {'Resource':<10} {'Start':>7} {'End':>7} {'Deadline':>9} {'Lateness':>9} {'Decision':<10}")
        print(f"  {'─'*75}")
        for d in dec_trace:
            if d.get("status") == "MISSED":
                print(f"  {color(d['task_id'], C.RED):<8} {'None':<10} {'N/A':>7} {'N/A':>7} {str(d['deadline'])+'h':>9} {'N/A':>9} {color('MISSED', C.RED)}")
            else:
                st_color = C.GREEN if d["status"] == "ON TIME" else C.YELLOW
                print(f"  {color(d['task_id'], C.GREEN):<8} {d['resource']:<10} {str(d['start'])+'h':>7} {str(d['end'])+'h':>7} {str(d['deadline'])+'h':>9} {str(d['lateness'])+'h':>9} {color(d['status'], st_color)}")
    print(f"  {'─'*75}\n")

def print_dp_trace(summary: dict):
    """Print the exact 1D DP table, binary search predecessor pointers, and backpointers."""
    print(f"\n  {color('════ STEP-BY-STEP DYNAMIC PROGRAMMING TABLE INSPECTOR ════', C.GREEN, C.BOLD)}")
    dp_traces = summary.get('dp_traces', {})
    if not dp_traces:
        print(f"  {color('No DP trace available.', C.GREY)}")
        return

    for res_id, rdata in dp_traces.items():
        print(f"\n  {color('Resource:', C.WHITE, C.BOLD)} {color(res_id, C.GREEN, C.BOLD)} | Total Candidate Intervals: {rdata['jobs_count']}")
        print(f"  Recurrence: {color('DP[i] = max( DP[i-1], Profit[i] + DP[p(i)] )', C.CYAN)}")
        print(f"  Predecessor p(i) found in {color('O(log N)', C.YELLOW)} time using binary search (bisect_right).")
        print(f"  {'─'*88}")
        print(f"  {'i':<4} {'Job':<6} {'Interval':<12} {'Profit':>7} {'p(i)':<10} {'Include Val':>12} {'Exclude Val':>12} {'DP[i]':>8} {'Choice':<10}")
        print(f"  {'─'*88}")

        selected_set = set(rdata.get("selected_tasks", []))
        for step in rdata.get("trace_steps", []):
            is_chosen = step["task_id"] in selected_set and step["decision"] == "INCLUDE"
            mark = color("★ CHOSEN", C.GREEN, C.BOLD) if is_chosen else color(step["decision"], C.WHITE)
            pred_str = f"idx {step['p_idx']} ({step['p_task']})"
            print(f"  {step['step']:<4} {step['task_id']:<6} {step['interval']:<12} {step['profit']:>7} {pred_str:<10} "
                  f"{step['include_val']:>12} {step['exclude_val']:>12} {color(str(step['dp_val']), C.CYAN, C.BOLD):>16} {mark}")
        print(f"  {'─'*88}")
        print(f"  Optimal Subset Selected for {res_id}: {color(str(rdata.get('selected_tasks', [])), C.GREEN, C.BOLD)}")
    print()

def print_backtracking_trace(summary: dict):
    """Print the Branch & Bound state-space search trace and pruning decisions."""
    print(f"\n  {color('════ STEP-BY-STEP BRANCH & BOUND SEARCH TREE TRACE ════', C.PURPLE, C.BOLD)}")
    print(f"  Bounding Function: {color('Upper_Bound(node) = Current_Profit + Remaining_Suffix_Potential', C.CYAN)}")
    print(f"  Admissibility: Never underestimates possible profit; guarantees pruning safety.")
    print(f"  {'─'*85}")

    trace = summary.get('search_trace', [])
    if not trace:
        print(f"  {color('No search tree trace steps recorded.', C.GREY)}")
        return

    print(f"  {'Event':<9} {'Depth':<7} {'Job':<6} {'Current Profit':>15} {'Upper Bound':>13} {'Best Profit':>13} {'Action / Reason'}")
    print(f"  {'─'*85}")
    for item in trace[:25]:  # Display first 25 key decisions
        if item["type"] == "PRUNE":
            action = color(f"✂ PRUNED: {item['reason']}", C.RED)
            print(f"  {color('PRUNE', C.RED):<17} {item['depth']:<7} {item['task_id']:<6} {item['current_profit']:>15} {item['upper_bound']:>13} {item['best_profit']:>13} {action}")
        else:
            action = color(item.get("choice", "Branch"), C.CYAN)
            print(f"  {color('BRANCH', C.GREEN):<17} {item['depth']:<7} {item['task_id']:<6} {item.get('current_profit', 0):>15} {item.get('upper_bound', 0):>13} {item.get('best_profit', 0):>13} {action}")
    if len(trace) > 25:
        print(f"  ... [{len(trace) - 25} additional search events omitted for brevity]")
    print(f"  {'─'*85}\n")

def print_gantt(summary: dict, horizon: int = 72):
    """Print ASCII Gantt chart to terminal."""
    scheduled = sorted(summary.get('scheduled', []), key=lambda t: t.start_h or 0)

    if not scheduled:
        print(f"\n  {color('No scheduled tasks to display.', C.RED)}")
        return

    from collections import defaultdict
    res_tasks = defaultdict(list)
    for t in scheduled:
        res_tasks[t.assigned_resource].append(t)

    max_time = min(max(t.end_h for t in scheduled) + 4, 72)

    print(f"\n  {color('GANTT CHART (ASCII)', C.CYAN, C.BOLD)}  [each block ~ 1h]")
    print(f"  {'─'*70}")

    ruler = '  {:>8}  '.format('Resource')
    for h in range(0, max_time + 1, 8):
        ruler += f'{h:<8}'
    print(color(ruler, C.GREY))

    for rid, tasks in sorted(res_tasks.items()):
        row = ['.'] * max_time
        for t in tasks:
            s, e = t.start_h, min(t.end_h, max_time)
            char = '#' if not t.is_late else '='
            for i in range(s, e):
                if i < max_time:
                    row[i] = char
            tid_chars = list(t.task_id)
            for j, ch in enumerate(tid_chars):
                pos = s + j
                if pos < max_time:
                    row[pos] = ch

        row_str = ''.join(row)
        colored_row = ''
        i = 0
        while i < len(row_str):
            if row_str[i] == '#':
                colored_row += color('#', C.GREEN)
            elif row_str[i] == '=':
                colored_row += color('=', C.YELLOW)
            else:
                colored_row += color(row_str[i], C.GREY)
            i += 1

        print(f"  {color(rid+' ', C.CYAN, C.BOLD):>10}  {colored_row}")

    print(f"\n  {color('# On Time', C.GREEN)}   {color('= Late', C.YELLOW)}")

    if summary.get('missed'):
        print(f"\n  {color('! MISSED TASKS:', C.RED, C.BOLD)}")
        for t in summary['missed']:
            print(f"    {color(t.task_id, C.RED)} -- deadline {t.deadline_h}h, priority {t.priority}, skill {t.skill}, profit {t.profit}")

def print_task_table(summary: dict):
    """Print detailed task execution table."""
    print(f"\n  {color('TASK EXECUTION DETAILS', C.CYAN, C.BOLD)}")
    print(f"  {'─'*92}")
    header = f"  {'Task':<8} {'Res':<5} {'Skill':<10} {'Prio':>5} {'Dur':>5} {'Ddl':>5} {'Start':>6} {'End':>6} {'Late':>6} {'Profit':>7} {'Status':<10}"
    print(color(header, C.GREY))
    print(f"  {'─'*92}")

    all_tasks = sorted(summary.get('scheduled', []), key=lambda t: t.start_h or 0)
    all_tasks += summary.get('missed', [])

    for t in all_tasks:
        if t.is_missed:
            status = color('MISSED', C.RED)
            row = f"  {color(t.task_id, C.RED):<8} {'N/A':<5} {t.skill:<10} {t.priority:>5} {t.duration_h:>5}h {t.deadline_h:>4}h {'N/A':>6} {'N/A':>6} {'N/A':>6} {color(str(t.profit), C.PURPLE):>7} {status}"
        elif t.is_late:
            status = color('LATE', C.YELLOW)
            row = f"  {color(t.task_id, C.YELLOW):<8} {color(t.assigned_resource, C.CYAN):<5} {t.skill:<10} {t.priority:>5} {t.duration_h:>5}h {t.deadline_h:>4}h {t.start_h:>5}h {t.end_h:>5}h {color(str(t.lateness_h), C.YELLOW):>5}h {color(str(t.profit), C.PURPLE):>7} {status}"
        else:
            status = color('OK', C.GREEN)
            row = f"  {color(t.task_id, C.GREEN):<8} {color(t.assigned_resource, C.CYAN):<5} {t.skill:<10} {t.priority:>5} {t.duration_h:>5}h {t.deadline_h:>4}h {t.start_h:>5}h {t.end_h:>5}h {'0':>5}h {color(str(t.profit), C.PURPLE):>7} {status}"
        print(row)

def print_comparison(comp: dict):
    """Print side-by-side algorithm comparison with execution times and theoretical complexities."""
    print(f"\n  {color('ALGORITHM COMPARISON MATRIX (SIDE-BY-SIDE)', C.CYAN, C.BOLD)}")
    print(f"  {'─'*98}")
    header = f"  {'Algorithm':<36} {'OnTime%':>8} {'Profit':>7} {'Late':>6} {'Miss':>5} {'Time(ms)':>9} {'Time Complexity':<18}"
    print(color(header, C.GREY))
    print(f"  {'─'*98}")

    results = comp['comparison']
    max_profit = max(r['total_profit'] for r in results)
    max_ontime = max(float(r['on_time_pct']) for r in results)
    min_late = min(r['total_lateness_h'] for r in results)
    min_time = min(r['execution_time_ms'] for r in results)

    for r in results:
        algo = r['algorithm'][:35]
        profit_c = C.GREEN if r['total_profit'] == max_profit else C.WHITE
        ontime_c = C.GREEN if float(r['on_time_pct']) == max_ontime else C.WHITE
        late_c = C.GREEN if r['total_lateness_h'] == min_late else C.YELLOW
        miss_c = C.GREEN if r['missed_count'] == 0 else C.RED
        time_c = C.GREEN if r['execution_time_ms'] == min_time else C.WHITE

        time_val = r.get("execution_time_ms", 0.0)
        time_str = f"{time_val:.2f}ms"
        print(f"  {color(algo, C.WHITE):<36} "
              f"{color(r['on_time_pct'], ontime_c):>7}% "
              f"{color(r['total_profit'], profit_c):>7} "
              f"{color(r['total_lateness_h'], late_c):>5}h "
              f"{color(r['missed_count'], miss_c):>5} "
              f"{color(time_str, time_c):>9} "
              f"{color(r.get('time_complexity', 'N/A'), C.CYAN):<18}")


    print(f"\n  {color('Best Profit    :', C.GREY)} {color(comp['best_profit_algo'], C.GREEN)}")
    print(f"  {color('Best On-Time   :', C.GREY)} {color(comp['best_ontime_algo'], C.GREEN)}")
    print(f"  {color('Least Lateness :', C.GREY)} {color(comp['best_lateness_algo'], C.GREEN)}")
    print(f"  {color('Fastest Exec   :', C.GREY)} {color(comp.get('fastest_algo', 'N/A'), C.GREEN)}")

def interactive_add_task(tasks):
    """Interactively add a new task."""
    print(f"\n  {color('ADD NEW TASK', C.CYAN, C.BOLD)}")
    print(f"  {'─'*40}")
    tid = input(f"  {color('Task ID:', C.GREY)} ").strip()
    if not tid:
        print(color("  Cancelled.", C.RED))
        return tasks
    dur = int(input(f"  {color('Duration (hours):', C.GREY)} ") or 3)
    ddl = int(input(f"  {color('Deadline (hours):', C.GREY)} ") or 48)
    prio = int(input(f"  {color('Priority (1-5):', C.GREY)} ") or 3)
    skill = input(f"  {color('Skill (backend/frontend/qa):', C.GREY)} ").strip() or 'backend'
    profit = int(input(f"  {color('Profit score:', C.GREY)} ") or 100)
    deps_raw = input(f"  {color('Dependencies (e.g. T1|T2, blank for none):', C.GREY)} ").strip()
    deps = [d.strip() for d in deps_raw.split('|') if d.strip()]

    tasks.append(Task(
        task_id=tid, duration_h=dur, deadline_h=ddl, priority=prio,
        skill=skill, depends_on=deps, profit=profit
    ))
    print(f"  {color(f'Task {tid} added successfully!', C.GREEN)}")
    return tasks


def run_professor_demo(demo_name: str, horizon: int = 72, no_report: bool = False):
    """Run curated academic demonstration scenarios for professor evaluation."""
    if demo_name == 'greedy-trap':
        print(f"\n  {color('╔══════════════════════════════════════════════════════════════╗', C.YELLOW)}")
        print(f"  {color('║    PROFESSOR DEMO 1: THE GREEDY TRAP (COUNTER-EXAMPLE)       ║', C.YELLOW, C.BOLD)}")
        print(f"  {color('║  Proof that Greedy Choice Property fails for Global Optimum  ║', C.YELLOW)}")
        print(f"  {color('╚══════════════════════════════════════════════════════════════╝', C.YELLOW)}\n")
        tasks, resources = get_greedy_trap_dataset()
        print(f"  Single Resource Available: {resources[0].res_id} (Shift: 0-24h)")
        print(f"  Tasks Provided:")
        for t in tasks:
            print(f"    - {t.task_id}: Duration {t.duration_h}h, Deadline {t.deadline_h}h, Priority {t.priority}, Profit {t.profit}")

        print(f"\n  {color('Running all 3 paradigms on Counter-Example...', C.CYAN)}")
        g_sum = GreedyScheduler(tasks, resources, horizon).get_summary()
        dp_sum = DPScheduler(tasks, resources, horizon).get_summary()
        bt_sum = BacktrackingScheduler(tasks, resources, horizon).get_summary()

        comp = compare_algorithms([g_sum, dp_sum, bt_sum])
        print_comparison(comp)

        print(f"\n  {color('ACADEMIC EVALUATION VERDICT:', C.GREEN, C.BOLD)}")
        print(f"  {'─'*70}")
        print(f"  1. Greedy chooses J1 because it has the highest priority (5) and earliest deadline (6h).")
        print(f"     By greedily assigning J1 [0h-6h], the resource becomes busy until t=6h.")
        print(f"     Consequently, J2 and J3 miss their deadlines (7h and 8h). Greedy Profit = {g_sum['total_profit']}.")
        print(f"  2. Dynamic Programming & Backtracking reject J1 and schedule {sorted([t.task_id for t in dp_sum['scheduled']])}.")
        print(f"     Both J2 and J3 finish on time! Optimal Profit = {dp_sum['total_profit']} (+66.7% gain!).")
        print(f"  {color('Conclusion:', C.CYAN, C.BOLD)} Formally disproves that the Greedy Choice Property holds for arbitrary deadlines.")
        print(f"  {'─'*70}\n")

    elif demo_name == 'cycle-trap':
        print(f"\n  {color('╔══════════════════════════════════════════════════════════════╗', C.RED)}")
        print(f"  {color('║    PROFESSOR DEMO 2: PRECEDENCE CYCLE & DEADLOCK DETECTION   ║', C.RED, C.BOLD)}")
        print("  " + color("║  Kahn's Algorithm In-Degree Cycle Trapping Demonstration    ║", C.RED))
        print(f"  {color('╚══════════════════════════════════════════════════════════════╝', C.RED)}\n")
        tasks, resources = get_cycle_demo_dataset()
        print("  Tasks Provided with Circular Dependency:")
        for t in tasks:
            print(f"    - {t.task_id} (depends on: {t.depends_on})")

        has_cycle, cycle_nodes = detect_dependency_cycle(tasks)
        print("\n  " + color("Kahn's Algorithm Execution Result:", C.WHITE, C.BOLD))
        if has_cycle:
            print(f"  {color('✓ CYCLE DETECTED!', C.RED, C.BOLD)} Deadlocked nodes: {color(str(cycle_nodes), C.YELLOW)}")
            print("  Explanation: In Kahn's algorithm, every task in a cycle retains in-degree > 0.")
            print(f"  Since the queue becomes empty before visiting all tasks ({len(tasks)} tasks), the graph is NOT a DAG.")
            print(f"  System successfully blocks scheduling to prevent infinite deadlock.\n")

    elif demo_name == 'scale':
        print(f"\n  {color('╔══════════════════════════════════════════════════════════════╗', C.PURPLE)}")
        print(f"  {color('║    PROFESSOR DEMO 3: EMPIRICAL COMPLEXITY SCALING EXPERIMENT ║', C.PURPLE, C.BOLD)}")
        print(f"  {color('║  Polynomial O(N log N) vs Exponential O((M+1)^N) Growth     ║', C.PURPLE)}")
        print(f"  {color('╚══════════════════════════════════════════════════════════════╝', C.PURPLE)}\n")
        b_res = run_benchmarks([5, 8, 10, 12, 14], horizon)
        print_benchmark_table(b_res)
        chart_path = plot_runtime_scaling(b_res, "outputs/runtime_scaling.png")
        print(f"  {color('✓ Publication-quality scaling plot saved to:', C.GREEN)} {color(chart_path, C.CYAN, C.BOLD)}\n")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Smart Job Scheduler - Greedy, DP, Backtracking Techniques'
    )
    parser.add_argument('--algo', choices=['greedy', 'dp', 'backtracking', 'pq', 'all'], default='all',
                        help='Algorithm to run (default: all)')
    parser.add_argument('--horizon', type=int, default=72, help='Planning horizon in hours (default: 72)')
    parser.add_argument('--compare', action='store_true', help='Compare all algorithms side-by-side')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark comparing 5, 8, 10, 12 jobs')
    parser.add_argument('--trace', action='store_true', help='Display step-by-step algorithm trace & DP tables')
    parser.add_argument('--plot', action='store_true', help='Generate publication-grade PNG comparison charts')
    parser.add_argument('--demo', choices=['greedy-trap', 'cycle-trap', 'scale'],
                        help='Run curated professor evaluation demo scenario')
    parser.add_argument('--add-task', action='store_true', help='Interactively add a task')
    parser.add_argument('--no-report', action='store_true', help='Skip file report generation')
    parser.add_argument('--tasks', default='data/tasks.csv', help='Tasks CSV file path')
    parser.add_argument('--resources', default='data/resources.csv', help='Resources CSV file path')
    args = parser.parse_args()

    print_banner()

    # Professor demo mode
    if args.demo:
        run_professor_demo(args.demo, args.horizon, args.no_report)
        return

    # Benchmark mode
    if args.benchmark:
        print(f"  {color('Running performance benchmark suite across job sizes...', C.CYAN)}")
        b_res = run_benchmarks([5, 8, 10, 12], args.horizon)
        print_benchmark_table(b_res)
        if args.plot:
            p = plot_runtime_scaling(b_res)
            print(f"  {color('Benchmark plot generated at:', C.GREEN)} {color(p, C.CYAN)}")
        return

    # Load data
    print(f"  {color('Loading tasks from', C.GREY)} {color(args.tasks, C.CYAN)}")
    tasks = load_tasks(args.tasks)
    resources = load_resources(args.resources)

    # Validate tasks
    is_valid, errors = validate_tasks(tasks)
    if not is_valid:
        print(f"\n  {color('Input Validation Warnings:', C.YELLOW, C.BOLD)}")
        for err in errors:
            print(f"    - {err}")
    else:
        print(f"  {color('✓ Input validation passed (no errors)', C.GREEN)}")

    print(f"  {color(f'Loaded {len(tasks)} tasks, {len(resources)} resources', C.GREEN)}\n")

    # Interactive add
    if args.add_task:
        tasks = interactive_add_task(tasks)

    summaries = []

    # 1. Greedy Algorithm
    if args.algo in ('greedy', 'all') or args.compare:
        print(f"\n{color('  ► Running Greedy Scheduler (EDF + Priority + TopoSort)...', C.CYAN)}")
        s = GreedyScheduler(tasks, resources, args.horizon).get_summary()
        summaries.append(s)
        print_kpis(s)
        print_gantt(s, args.horizon)
        print_task_table(s)
        if args.trace:
            print_greedy_trace(s)
        if not args.no_report:
            csv_path = generate_schedule_csv(s, 'schedule_greedy.csv')
            txt_path = generate_text_report(s)
            print(f"\n  {color('Reports saved:', C.GREY)} {color(csv_path, C.CYAN)}, {color(txt_path, C.CYAN)}")

    # 2. Dynamic Programming
    if args.algo in ('dp', 'all') or args.compare:
        print(f"\n{color('  ► Running Dynamic Programming Scheduler (Weighted Job Scheduling)...', C.GREEN)}")
        s = DPScheduler(tasks, resources, args.horizon).get_summary()
        summaries.append(s)
        print_kpis(s)
        if args.algo == 'dp':
            print_gantt(s, args.horizon)
            print_task_table(s)
        if args.trace or args.algo == 'dp':
            print_dp_trace(s)
        if not args.no_report:
            generate_schedule_csv(s, 'schedule_dp.csv')
            generate_text_report(s)

    # 3. Backtracking Algorithm
    if args.algo in ('backtracking', 'all') or args.compare:
        print(f"\n{color('  ► Running Backtracking Scheduler (Recursive Branch & Bound)...', C.PURPLE)}")
        if len(tasks) > 15:
            print(f"    {color('Notice:', C.YELLOW)} Backtracking is exponential O((M+1)^N). Running on {len(tasks)} tasks...")
        s = BacktrackingScheduler(tasks, resources, args.horizon).get_summary()
        summaries.append(s)
        print_kpis(s)
        if args.algo == 'backtracking':
            print_gantt(s, args.horizon)
            print_task_table(s)
        if args.trace or args.algo == 'backtracking':
            print_backtracking_trace(s)
        if not args.no_report:
            generate_schedule_csv(s, 'schedule_backtracking.csv')
            generate_text_report(s)

    # 4. Priority Queue (Heap)
    if args.algo == 'pq':
        print(f"\n{color('  ► Running Priority Queue (Min-Heap) Scheduler...', C.YELLOW)}")
        s = PriorityQueueScheduler(tasks, resources, args.horizon).get_summary()
        summaries.append(s)
        print_kpis(s)
        print_gantt(s, args.horizon)
        print_task_table(s)
        if not args.no_report:
            generate_schedule_csv(s, 'schedule_pq.csv')
            generate_text_report(s)

    # Comparison
    if (args.compare or args.algo == 'all') and len(summaries) > 1:
        comp = compare_algorithms(summaries)
        print_comparison(comp)
        if not args.no_report:
            generate_comparison_report(comp)
            print(f"\n  {color('Comparison report saved to outputs/comparison_report.txt', C.CYAN)}")

        if args.plot:
            if not HAS_VISUALIZER:
                print(f"\n  {color('[-] Notice:', C.YELLOW)} matplotlib is required for --plot. Please install with 'pip install matplotlib'.")
            else:
                c_plot = plot_algorithm_comparison(comp, "outputs/algorithm_comparison.png")
                b_res = run_benchmarks([5, 8, 10, 12], args.horizon)
                s_plot = plot_runtime_scaling(b_res, "outputs/runtime_scaling.png")
                print(f"  {color('✓ High-resolution plots generated:', C.GREEN, C.BOLD)}")
                print(f"    - Comparison Bar Chart : {color(c_plot, C.CYAN)}")
                print(f"    - Runtime Scaling Plot : {color(s_plot, C.CYAN)}")

    print(f"\n  {color('✓ Execution complete! Open dashboard.html in your browser for the interactive UI.', C.GREEN, C.BOLD)}\n")


if __name__ == '__main__':
    main()