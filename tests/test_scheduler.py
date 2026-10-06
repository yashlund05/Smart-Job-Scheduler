"""
Smart Job Scheduler
====================================
tests/test_scheduler.py - Unit Test Suite

Tests:
  - Greedy Scheduler (Dependencies, Skills, No-Overlap, Lateness)
  - Dynamic Programming Scheduler
  - Backtracking Scheduler (Optimal profit, Branch & Bound correctness)
  - Priority Queue Scheduler
  - 5-Job Sample Demo Dataset
  - Empty Input Handling across all schedulers
  - Incompatible / Impossible task skills
  - Validation of Invalid Input & Duplicate Job IDs
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Task, Resource, validate_tasks
from src.greedy_scheduler import GreedyScheduler
from src.priority_scheduler import PriorityQueueScheduler
from src.dp_scheduler import DPScheduler
from src.backtracking_scheduler import BacktrackingScheduler


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_tasks():
    return [
        Task('T1', 4, 24, 3, 'backend',  [],       300),
        Task('T2', 6, 32, 2, 'frontend', ['T1'],   200),
        Task('T3', 2, 20, 5, 'qa',       ['T1'],   500),
        Task('T4', 8, 40, 1, 'backend',  [],       100),
        Task('T5', 3, 28, 4, 'frontend', [],       400),
    ]

def make_resources():
    return [
        Resource('R1', {'backend', 'qa'},       0, 8, 8),
        Resource('R2', {'frontend', 'qa'},      0, 8, 8),
        Resource('R3', {'backend', 'frontend'}, 0, 8, 8),
    ]

def make_sample_college_jobs():
    """
    Standard sample dataset from college DAA assignment:
    J1 | Duration 2 | Deadline 3 | Profit 100
    J2 | Duration 1 | Deadline 2 | Profit 50
    J3 | Duration 2 | Deadline 4 | Profit 80
    J4 | Duration 1 | Deadline 2 | Profit 40
    J5 | Duration 3 | Deadline 5 | Profit 120
    """
    return [
        Task('J1', 2, 3, 5, 'backend', [], 100),
        Task('J2', 1, 2, 4, 'backend', [], 50),
        Task('J3', 2, 4, 3, 'backend', [], 80),
        Task('J4', 1, 2, 2, 'backend', [], 40),
        Task('J5', 3, 5, 5, 'backend', [], 120),
    ]


# ─── Verification Helpers ─────────────────────────────────────────────────────

def assert_dependencies_respected(results):
    end_times = {}
    for t in results:
        if not t.is_missed:
            end_times[t.task_id] = t.end_h

    for t in results:
        if not t.is_missed:
            for dep in t.depends_on:
                dep_end = end_times.get(dep, 0)
                assert t.start_h >= dep_end, \
                    f"FAIL: {t.task_id} starts at {t.start_h} but dep {dep} ends at {dep_end}"
    print("    [+] Dependency ordering respected")


def assert_skills_matched(results, resources):
    skill_map = {r.res_id: r.skills for r in resources}
    for t in results:
        if not t.is_missed and t.assigned_resource:
            assert t.skill in skill_map[t.assigned_resource], \
                f"FAIL: {t.task_id} skill '{t.skill}' not in {skill_map[t.assigned_resource]} for {t.assigned_resource}"
    print("    [+] Skill constraints satisfied")


def assert_no_overlap(results):
    from collections import defaultdict
    res_intervals = defaultdict(list)
    for t in results:
        if not t.is_missed and t.assigned_resource:
            res_intervals[t.assigned_resource].append((t.start_h, t.end_h, t.task_id))

    for rid, intervals in res_intervals.items():
        intervals.sort()
        for i in range(len(intervals) - 1):
            _, e1, t1 = intervals[i]
            s2, _, t2 = intervals[i+1]
            assert e1 <= s2, f"FAIL: Overlap on {rid}: {t1} ends at {e1}, {t2} starts at {s2}"
    print("    [+] No resource overlaps")


def assert_lateness_correct(results):
    for t in results:
        if not t.is_missed:
            expected = max(0, t.end_h - t.deadline_h)
            assert t.lateness_h == expected, \
                f"FAIL: {t.task_id} lateness should be {expected}, got {t.lateness_h}"
    print("    [+] Lateness calculations correct")


# ─── Test Cases ───────────────────────────────────────────────────────────────

def test_greedy():
    print("\n[TEST 1] Greedy Scheduler (Priority + EDF + Topo-Sort)")
    tasks = make_tasks()
    resources = make_resources()
    s = GreedyScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_dependencies_respected(results)
    assert_skills_matched(results, resources)
    assert_no_overlap(results)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    assert summary['total_profit'] > 0
    assert 'execution_time_ms' in summary
    assert 'time_complexity' in summary
    print(f"    [+] Greedy scheduled {summary['scheduled_count']}/{summary['total_tasks']}, profit={summary['total_profit']}")


def test_priority_queue():
    print("\n[TEST 2] Priority Queue Scheduler (Min-Heap)")
    tasks = make_tasks()
    resources = make_resources()
    s = PriorityQueueScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_dependencies_respected(results)
    assert_skills_matched(results, resources)
    assert_no_overlap(results)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    print(f"    [+] PQ scheduled {summary['scheduled_count']}/{summary['total_tasks']}, profit={summary['total_profit']}")


def test_dp():
    print("\n[TEST 3] Dynamic Programming Scheduler (Weighted Job Scheduling)")
    tasks = make_tasks()
    resources = make_resources()
    s = DPScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_skills_matched(results, resources)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    assert summary['total_profit'] > 0
    print(f"    [+] DP scheduled {summary['scheduled_count']}/{summary['total_tasks']}, profit={summary['total_profit']}")


def test_backtracking():
    print("\n[TEST 4] Backtracking Scheduler (Recursive Branch & Bound)")
    tasks = make_tasks()
    resources = make_resources()
    s = BacktrackingScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    results = summary['tasks']
    assert_dependencies_respected(results)
    assert_skills_matched(results, resources)
    assert_no_overlap(results)
    assert_lateness_correct(results)
    assert summary['total_tasks'] == 5
    assert summary['total_profit'] > 0
    assert summary['nodes_explored'] > 0
    assert 'execution_time_ms' in summary
    print(f"    [+] Backtracking explored {summary['nodes_explored']} nodes, scheduled {summary['scheduled_count']}/{summary['total_tasks']}, profit={summary['total_profit']}")


def test_college_sample_dataset():
    print("\n[TEST 5] College 5-Job Sample Dataset on all 3 Algorithms")
    jobs = make_sample_college_jobs()
    resources = [Resource('R1', {'backend'}, 0, 8, 8)]

    g_sum = GreedyScheduler(jobs, resources, horizon=24).get_summary()
    dp_sum = DPScheduler(jobs, resources, horizon=24).get_summary()
    bt_sum = BacktrackingScheduler(jobs, resources, horizon=24).get_summary()

    assert g_sum['total_tasks'] == 5
    assert dp_sum['total_tasks'] == 5
    assert bt_sum['total_tasks'] == 5

    # Backtracking finds optimal or equal to heuristic profit
    assert bt_sum['total_profit'] >= dp_sum['total_profit']
    print(f"    [+] Greedy Profit: {g_sum['total_profit']} | DP Profit: {dp_sum['total_profit']} | Backtracking Profit: {bt_sum['total_profit']}")


def test_empty_tasks():
    print("\n[TEST 6] Empty Task List Handling")
    resources = make_resources()
    assert GreedyScheduler([], resources, horizon=72).get_summary()['total_tasks'] == 0
    assert DPScheduler([], resources, horizon=72).get_summary()['total_tasks'] == 0
    assert BacktrackingScheduler([], resources, horizon=72).get_summary()['total_tasks'] == 0
    print("    [+] All schedulers handled empty task list gracefully")


def test_single_task():
    print("\n[TEST 7] Single Task Scheduling")
    tasks = [Task('T1', 3, 24, 5, 'backend', [], 500)]
    resources = make_resources()
    s = BacktrackingScheduler(tasks, resources, horizon=72)
    summary = s.get_summary()
    assert summary['scheduled_count'] == 1
    assert summary['total_profit'] == 500
    print("    [+] Single task scheduled correctly by Backtracking")


def test_impossible_task():
    print("\n[TEST 8] Incompatible Skill Handling")
    tasks = [Task('T1', 3, 24, 5, 'devops', [], 500)]  # No devops resource
    resources = make_resources()
    summary = BacktrackingScheduler(tasks, resources, horizon=72).get_summary()
    assert summary['missed_count'] == 1
    assert summary['scheduled_count'] == 0
    print("    [+] Incompatible skill correctly marked as missed")


def test_input_validation():
    print("\n[TEST 9] Input Validation & Duplicate Job ID Detection")
    # Empty
    ok, errs = validate_tasks([])
    assert not ok and "empty" in errs[0].lower()

    # Duplicates
    dup_tasks = [
        Task('T1', 2, 10, 3, 'backend', [], 100),
        Task('T1', 4, 20, 2, 'frontend', [], 200),
    ]
    ok, errs = validate_tasks(dup_tasks)
    assert not ok and any("Duplicate" in e for e in errs)

    # Invalid duration and deadline
    bad_tasks = [
        Task('T1', 0, -5, 3, 'backend', [], -50),
    ]
    ok, errs = validate_tasks(bad_tasks)
    assert not ok and len(errs) >= 3

    print("    [+] Validation correctly caught empty, duplicates, and invalid numbers")


def test_cycle_detection():
    print("\n[TEST 10] Kahn's Algorithm Dependency Cycle Detection")
    from src.models import detect_dependency_cycle, get_cycle_demo_dataset
    tasks, _ = get_cycle_demo_dataset()
    has_cycle, cycle_nodes = detect_dependency_cycle(tasks)
    assert has_cycle is True, "Cycle should be detected"
    assert len(cycle_nodes) == 3, "All 3 cyclic nodes should be detected"
    print("    [+] Circular dependency correctly identified by Kahn's in-degree logic")


def test_greedy_trap():
    print("\n[TEST 11] Professor Counter-Example (The Greedy Trap)")
    from src.models import get_greedy_trap_dataset
    tasks, resources = get_greedy_trap_dataset()
    g_res = GreedyScheduler(tasks, resources, horizon=24).get_summary()
    bt_res = BacktrackingScheduler(tasks, resources, horizon=24).get_summary()

    # Greedy picks J1 (profit 120), blocking J2 and J3
    assert g_res['total_profit'] == 120, f"Greedy profit was {g_res['total_profit']}"
    # Backtracking selects J2 and J3 (profit 100 + 100 = 200)
    assert bt_res['total_profit'] == 200, f"Backtracking profit was {bt_res['total_profit']}"
    assert bt_res['total_profit'] > g_res['total_profit'], "Backtracking must beat Greedy on counter-example"
    print("    [+] Counter-example confirmed: Backtracking strictly outperforms Greedy (200 vs 120 profit)")


def test_traces_and_pruning_stats():
    print("\n[TEST 12] Step-by-Step Algorithm Traces & Pruning Metrics")
    tasks = make_tasks()
    resources = make_resources()

    dp_sum = DPScheduler(tasks, resources, horizon=72).get_summary()
    assert "dp_traces" in dp_sum and len(dp_sum["dp_traces"]) > 0
    assert "steps" in dp_sum["dp_traces"]["R1"] or "trace_steps" in dp_sum["dp_traces"]["R1"]

    bt_sum = BacktrackingScheduler(tasks, resources, horizon=72).get_summary()
    assert "pruned_branches" in bt_sum
    assert "pruning_efficiency_pct" in bt_sum
    assert "search_trace" in bt_sum

    g_sum = GreedyScheduler(tasks, resources, horizon=72).get_summary()
    assert "topo_trace" in g_sum
    assert "decision_trace" in g_sum

    print("    [+] DP recurrence traces, Kahn's topo trace, and B&B pruning stats verified")


def test_chart_generation():
    print("\n[TEST 13] Matplotlib Publication-Grade Chart Generation")
    try:
        import matplotlib
    except ImportError:
        print("    [+] matplotlib not installed in this Python environment; optional visualizer check skipped")
        return
    from src.visualizer import plot_runtime_scaling, plot_algorithm_comparison
    from src.benchmark import run_benchmarks
    from src.metrics import compare_algorithms

    b_res = run_benchmarks([5, 8], horizon=72)
    s_path = plot_runtime_scaling(b_res, "outputs/test_scaling.png")
    assert os.path.exists(s_path) and os.path.getsize(s_path) > 1000

    tasks = make_tasks()
    resources = make_resources()
    g_sum = GreedyScheduler(tasks, resources, horizon=72).get_summary()
    dp_sum = DPScheduler(tasks, resources, horizon=72).get_summary()
    bt_sum = BacktrackingScheduler(tasks, resources, horizon=72).get_summary()
    comp = compare_algorithms([g_sum, dp_sum, bt_sum])

    c_path = plot_algorithm_comparison(comp, "outputs/test_comparison.png")
    assert os.path.exists(c_path) and os.path.getsize(c_path) > 1000

    # Cleanup test files
    if os.path.exists("outputs/test_scaling.png"):
        os.remove("outputs/test_scaling.png")
    if os.path.exists("outputs/test_comparison.png"):
        os.remove("outputs/test_comparison.png")

    print("    [+] High-resolution PNG plots generated and validated successfully")


# ─── Run Suite ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SMART JOB SCHEDULER -- TEST SUITE")
    print("  Greedy | Dynamic Programming | Backtracking")
    print("="*60)
    tests = [
        test_greedy,
        test_priority_queue,
        test_dp,
        test_backtracking,
        test_college_sample_dataset,
        test_empty_tasks,
        test_single_task,
        test_impossible_task,
        test_input_validation,
        test_cycle_detection,
        test_greedy_trap,
        test_traces_and_pruning_stats,
        test_chart_generation,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"    [-] FAILED: {e}")
        except Exception as e:
            print(f"    [-] ERROR: {e}")
    print(f"\n  {'='*60}")
    print(f"  Test Results: {passed}/{len(tests)} tests passed successfully!")
    print("="*60 + "\n")
    if passed < len(tests):
        sys.exit(1)