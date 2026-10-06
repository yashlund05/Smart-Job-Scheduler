"""
Task Scheduler Optimization System
====================================
src/greedy_scheduler.py - Greedy Heuristic Scheduler

Algorithm:
1. Build topological order (respect dependencies)
2. Within topo-order, sort by: highest priority → earliest deadline
3. For each task, find the best resource (skill match + earliest available slot)
4. Assign task to resource slot
5. Mark tasks that miss deadlines
"""

import copy
import time
from collections import defaultdict, deque
from typing import List, Dict, Tuple

from src.models import Task, Resource


class GreedyScheduler:
    """
    Greedy scheduler that uses priority + EDF (Earliest Deadline First)
    with dependency-aware topological ordering.

    Time Complexity: O(T * R * log T) where T=tasks, R=resources
    Space Complexity: O(T + R)
    Data Structures Used: Priority Queue (via sorted), Graph (adjacency list), Deque (BFS)
    """

    def __init__(self, tasks: List[Task], resources: List[Resource], horizon: int = 72):
        self.tasks = copy.deepcopy(tasks)
        self.resources = copy.deepcopy(resources)
        self.horizon = horizon
        self.task_map: Dict[str, Task] = {t.task_id: t for t in self.tasks}
        self.res_map: Dict[str, Resource] = {r.res_id: r for r in self.resources}
        # Resource time cursor: tracks next available time per resource
        self.res_cursor: Dict[str, int] = {r.res_id: 0 for r in self.resources}
        self.earliest_end: Dict[str, int] = {}
        self.topo_trace: List[Dict] = []
        self.decision_trace: List[Dict] = []

    def _topological_sort(self) -> List[str]:
        """
        Kahn's algorithm for topological sort.
        Tie-breaking: higher priority first, then earlier deadline.
        Returns ordered list of task IDs.
        """
        in_degree: Dict[str, int] = defaultdict(int)
        children: Dict[str, List[str]] = defaultdict(list)

        for t in self.tasks:
            if t.task_id not in in_degree:
                in_degree[t.task_id] = 0
            for dep in t.depends_on:
                in_degree[t.task_id] += 1
                children[dep].append(t.task_id)

        # Initialize queue with zero in-degree tasks
        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        topo_order = []
        step = 1

        while queue:
            # Sort by (-priority, deadline) for greedy tie-breaking
            candidates = sorted(
                list(queue),
                key=lambda x: (-self.task_map[x].priority, self.task_map[x].deadline_h)
            )
            chosen = candidates[0]
            queue.remove(chosen)
            topo_order.append(chosen)

            self.topo_trace.append({
                "step": step,
                "ready_set": list(candidates),
                "chosen": chosen,
                "chosen_priority": self.task_map[chosen].priority,
                "chosen_deadline": self.task_map[chosen].deadline_h,
                "chosen_profit": self.task_map[chosen].profit,
                "in_degrees": {k: v for k, v in in_degree.items() if v > 0}
            })
            step += 1

            for child in children[chosen]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        return topo_order

    def _find_best_slot(self, task: Task, dep_end: int) -> Tuple[int, str]:
        """
        Find the best (start_time, resource_id) for a task.
        Scoring: minimize lateness, prefer higher utilization.
        """
        best_score = float('inf')
        best_start = None
        best_rid = None

        for res in self.resources:
            if not res.can_handle(task.skill):
                continue

            # Earliest possible start = max(resource free time, dep end time, horizon check)
            cur = max(self.res_cursor[res.res_id], dep_end)

            # Align to shift window (simulate day-by-day)
            day = cur // 24
            shift_start_abs = res.shift_start_h + day * 24
            shift_end_abs = res.shift_end_h + day * 24

            # If cursor is past shift end for today, move to next day
            while cur >= shift_end_abs or cur + task.duration_h > shift_end_abs:
                day += 1
                shift_start_abs = res.shift_start_h + day * 24
                shift_end_abs = res.shift_end_h + day * 24
                cur = shift_start_abs

            # Can we finish before horizon?
            if cur + task.duration_h > self.horizon:
                continue

            end_time = cur + task.duration_h
            lateness = max(0, end_time - task.deadline_h)
            # Score: lower is better (lateness weighted by inverse priority)
            score = lateness * (6 - task.priority) - task.profit * 0.1

            if score < best_score:
                best_score = score
                best_start = cur
                best_rid = res.res_id

        return best_start, best_rid

    def schedule(self) -> List[Task]:
        """
        Main scheduling method.
        Returns list of Task objects with start/end/resource filled in.
        """
        topo_order = self._topological_sort()
        scheduled = []
        missed = []

        for tid in topo_order:
            task = self.task_map[tid]

            # Dependency constraint: can't start until all deps are done
            dep_end = max([self.earliest_end.get(d, 0) for d in task.depends_on], default=0)

            start, rid = self._find_best_slot(task, dep_end)

            if start is None:
                # Task cannot be scheduled (horizon exceeded)
                task.is_missed = True
                missed.append(task)
                self.earliest_end[tid] = self.horizon
                self.decision_trace.append({
                    "task_id": tid,
                    "resource": "None",
                    "start": None,
                    "end": None,
                    "deadline": task.deadline_h,
                    "status": "MISSED",
                    "reason": "Horizon exceeded or no compatible slot"
                })
                continue

            end = start + task.duration_h
            task.start_h = start
            task.end_h = end
            task.assigned_resource = rid
            task.lateness_h = max(0, end - task.deadline_h)
            task.is_late = task.lateness_h > 0
            task.is_missed = False

            # Update resource cursor
            self.res_cursor[rid] = end
            self.earliest_end[tid] = end
            scheduled.append(task)

            self.decision_trace.append({
                "task_id": tid,
                "resource": rid,
                "start": start,
                "end": end,
                "deadline": task.deadline_h,
                "lateness": task.lateness_h,
                "status": "LATE" if task.is_late else "ON TIME",
                "profit": task.profit if not task.is_late else 0
            })

        return scheduled + missed

    def get_summary(self) -> Dict:
        """Run schedule and return summary statistics."""
        t0 = time.perf_counter()
        results = self.schedule()
        exec_time_ms = round((time.perf_counter() - t0) * 1000, 3)

        scheduled = [t for t in results if not t.is_missed]
        missed = [t for t in results if t.is_missed]
        on_time = [t for t in scheduled if not t.is_late]
        late = [t for t in scheduled if t.is_late]

        total_profit = sum(t.profit for t in on_time)
        total_lateness = sum(t.lateness_h for t in late)

        return {
            "algorithm": "Greedy (Priority + EDF + Topo-Sort)",
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
            "total_profit": total_profit,
            "total_lateness_h": total_lateness,
            "makespan": max((t.end_h for t in scheduled), default=0),
            "execution_time_ms": exec_time_ms,
            "time_complexity": "O(N log N + N*M)",
            "space_complexity": "O(N + M)",
            "topo_trace": self.topo_trace,
            "decision_trace": self.decision_trace,
        }