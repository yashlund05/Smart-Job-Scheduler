"""
Task Scheduler Optimization System
====================================
src/dp_scheduler.py - Dynamic Programming Scheduler

Solves the Weighted Job Scheduling Problem:
  - Given N jobs with start times, end times, and profits
  - Find a subset of non-overlapping jobs with maximum total profit
  - Classic DP: dp[i] = max profit using first i jobs (sorted by end time)

Note: This runs on each resource independently then combines.
Time Complexity: O(N^2) or O(N log N) with binary search
"""

import copy
import bisect
import time
from typing import List, Dict, Tuple

from src.models import Task, Resource


class DPScheduler:
    """
    Dynamic Programming scheduler for maximum profit task selection.

    Treats each resource independently and selects the optimal
    non-overlapping subset of compatible tasks to maximize total profit.

    DSA Concepts:
      - 1D DP (Weighted Job Scheduling)
      - Binary search (bisect) for O(log N) predecessor search
      - Sorted arrays
    """

    def __init__(self, tasks: List[Task], resources: List[Resource], horizon: int = 72):
        self.tasks = copy.deepcopy(tasks)
        self.resources = copy.deepcopy(resources)
        self.horizon = horizon
        self.task_map: Dict[str, Task] = {t.task_id: t for t in self.tasks}
        self.dp_traces: Dict[str, Dict] = {}

    def _resolve_dependencies(self) -> Dict[str, int]:
        """Compute earliest start time for each task based on dependencies (simple BFS)."""
        from collections import defaultdict, deque
        in_degree = defaultdict(int)
        children = defaultdict(list)
        for t in self.tasks:
            if t.task_id not in in_degree:
                in_degree[t.task_id] = 0
            for dep in t.depends_on:
                in_degree[t.task_id] += 1
                children[dep].append(t.task_id)

        earliest_start = {t.task_id: 0 for t in self.tasks}
        earliest_end = {}
        queue = deque([t.task_id for t in self.tasks if in_degree[t.task_id] == 0])

        while queue:
            tid = queue.popleft()
            t = self.task_map[tid]
            start = earliest_start[tid]
            end = start + t.duration_h
            earliest_end[tid] = end
            for child in children[tid]:
                earliest_start[child] = max(earliest_start.get(child, 0), end)
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        return earliest_start

    def _dp_for_resource(self, res: Resource, compatible_tasks: List[Task],
                         earliest_start: Dict[str, int]) -> List[Tuple]:
        """
        Classic Weighted Job Scheduling DP for one resource.

        For each task: start = max(resource_free, dep_start)
        End = start + duration
        Sort by end time, then DP.

        Returns list of (task_id, start, end, profit) for chosen tasks.
        """
        # Build (start, end, task) list
        jobs = []
        for t in compatible_tasks:
            s = max(earliest_start.get(t.task_id, 0), res.shift_start_h)
            e = s + t.duration_h
            if e <= self.horizon and e <= t.deadline_h + t.duration_h:
                jobs.append((s, e, t))

        if not jobs:
            return []

        # Sort by end time
        jobs.sort(key=lambda x: x[1])
        n = len(jobs)

        # Binary search: find latest job that doesn't conflict
        ends = [j[1] for j in jobs]

        def latest_non_conflict(i):
            return bisect.bisect_right(ends, jobs[i][0]) - 1

        # DP
        dp = [0] * (n + 1)
        choice = [None] * (n + 1)
        table_trace = []

        for i in range(1, n + 1):
            s, e, t = jobs[i - 1]
            # Profit of including this job
            j = latest_non_conflict(i - 1)
            include_profit = dp[j + 1] + t.profit
            exclude_profit = dp[i - 1]

            if include_profit > exclude_profit:
                dp[i] = include_profit
                choice[i] = ('include', i - 1, j)
                decision = 'INCLUDE'
            else:
                dp[i] = exclude_profit
                choice[i] = ('exclude', i - 1, None)
                decision = 'EXCLUDE'

            table_trace.append({
                "step": i,
                "task_id": t.task_id,
                "interval": f"[{s}h - {e}h]",
                "profit": t.profit,
                "p_idx": j + 1 if j != -1 else 0,
                "p_task": jobs[j][2].task_id if j != -1 else "None",
                "include_val": include_profit,
                "exclude_val": exclude_profit,
                "dp_val": dp[i],
                "decision": decision
            })

        # Backtrack to find selected jobs
        selected = []
        i = n
        while i > 0:
            if choice[i][0] == 'include':
                job_idx = choice[i][1]
                s, e, t = jobs[job_idx]
                selected.append((t.task_id, s, e, t.profit))
                i = choice[i][2] + 1
            else:
                i -= 1

        selected_ids = {item[0] for item in selected}
        self.dp_traces[res.res_id] = {
            "resource": res.res_id,
            "jobs_count": n,
            "jobs": [
                {
                    "idx": k + 1,
                    "task_id": jobs[k][2].task_id,
                    "start": jobs[k][0],
                    "end": jobs[k][1],
                    "duration": jobs[k][2].duration_h,
                    "deadline": jobs[k][2].deadline_h,
                    "profit": jobs[k][2].profit,
                    "pred_idx": latest_non_conflict(k) + 1,
                }
                for k in range(n)
            ],
            "dp_table": dp,
            "trace_steps": table_trace,
            "selected_tasks": list(selected_ids)
        }

        return selected

    def schedule(self) -> List[Task]:
        """Run DP scheduling across all resources."""
        earliest_start = self._resolve_dependencies()
        assignment: Dict[str, Tuple] = {}  # task_id -> (start, end, res_id)

        for res in self.resources:
            compatible = [t for t in self.tasks if res.can_handle(t.skill)]
            selected = self._dp_for_resource(res, compatible, earliest_start)
            for (tid, s, e, _) in selected:
                # Only assign if not already assigned
                if tid not in assignment:
                    assignment[tid] = (s, e, res.res_id)

        results = []
        for t in self.tasks:
            if t.task_id in assignment:
                s, e, rid = assignment[t.task_id]
                t.start_h = s
                t.end_h = e
                t.assigned_resource = rid
                t.lateness_h = max(0, e - t.deadline_h)
                t.is_late = t.lateness_h > 0
                t.is_missed = False
            else:
                t.is_missed = True
            results.append(t)

        return results

    def get_summary(self) -> Dict:
        t0 = time.perf_counter()
        results = self.schedule()
        exec_time_ms = round((time.perf_counter() - t0) * 1000, 3)

        scheduled = [t for t in results if not t.is_missed]
        missed = [t for t in results if t.is_missed]
        on_time = [t for t in scheduled if not t.is_late]
        late = [t for t in scheduled if t.is_late]

        return {
            "algorithm": "Dynamic Programming (Weighted Job Scheduling)",
            "tasks": results,
            "scheduled": scheduled,
            "missed": missed,
            "on_time": on_time,
            "late": late,
            "total_tasks": len(results),
            "scheduled_count": len(scheduled),
            "missed_count": len(missed),
            "on_time_count": len(on_time),
            "late_count": len(late),
            "on_time_pct": round(100 * len(on_time) / len(results), 1) if results else 0,
            "total_profit": sum(t.profit for t in on_time),
            "total_lateness_h": sum(t.lateness_h for t in late),
            "makespan": max((t.end_h for t in scheduled), default=0),
            "execution_time_ms": exec_time_ms,
            "time_complexity": "O(M * N log N)",
            "space_complexity": "O(N)",
            "dp_traces": self.dp_traces,
        }