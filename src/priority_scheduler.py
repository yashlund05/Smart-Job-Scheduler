"""
Task Scheduler Optimization System
====================================
src/priority_scheduler.py - Priority Queue / Heap-Based Scheduler

This scheduler uses Python's heapq (min-heap) to always process
the task with the best scheduling score next.

Algorithm:
  - EDF (Earliest Deadline First) variant with profit weighting
  - Uses heapq for O(log N) push/pop operations
  - Respects dependency ordering
"""

import heapq
import copy
import time
from collections import defaultdict
from typing import List, Dict

from src.models import Task, Resource


class PriorityQueueScheduler:
    """
    Heap-based scheduler: at each step, picks the ready task with
    the highest (priority * profit / deadline) score.

    Data Structures:
      - Min-Heap (priority queue): O(log N) insert/extract
      - Adjacency list (dependency graph): O(V+E) traversal
      - Hash map (task lookup): O(1) access
    """

    def __init__(self, tasks: List[Task], resources: List[Resource], horizon: int = 72):
        self.tasks = copy.deepcopy(tasks)
        self.resources = copy.deepcopy(resources)
        self.horizon = horizon
        self.task_map: Dict[str, Task] = {t.task_id: t for t in self.tasks}

    def _compute_score(self, task: Task) -> float:
        """
        Scheduling score (lower = higher priority in min-heap).
        Formula: deadline / (priority * profit) — balances urgency vs value.
        """
        return task.deadline_h / (task.priority * max(task.profit, 1))

    def schedule(self) -> List[Task]:
        """
        Schedule tasks using heap-based priority queue.
        """
        # Build dependency graph
        in_degree: Dict[str, int] = defaultdict(int)
        children: Dict[str, List[str]] = defaultdict(list)
        for t in self.tasks:
            if t.task_id not in in_degree:
                in_degree[t.task_id] = 0
            for dep in t.depends_on:
                in_degree[t.task_id] += 1
                children[dep].append(t.task_id)

        # Push tasks with no dependencies into heap
        heap = []
        for t in self.tasks:
            if in_degree[t.task_id] == 0:
                score = self._compute_score(t)
                heapq.heappush(heap, (score, t.task_id))

        # Resource state
        res_cursor = {r.res_id: 0 for r in self.resources}
        earliest_end: Dict[str, int] = {}
        results = []

        while heap:
            _, tid = heapq.heappop(heap)
            task = self.task_map[tid]

            # Earliest start respecting dependencies
            dep_end = max([earliest_end.get(d, 0) for d in task.depends_on], default=0)

            # Find best resource
            best_start, best_rid = None, None
            best_late = float('inf')

            for res in self.resources:
                if not res.can_handle(task.skill):
                    continue
                cur = max(res_cursor[res.res_id], dep_end)
                # Align to shift
                day = cur // 24
                shift_end_abs = res.shift_end_h + day * 24
                while cur + task.duration_h > shift_end_abs:
                    day += 1
                    cur = res.shift_start_h + day * 24
                    shift_end_abs = res.shift_end_h + day * 24
                if cur + task.duration_h > self.horizon:
                    continue
                lateness = max(0, cur + task.duration_h - task.deadline_h)
                if lateness < best_late:
                    best_late = lateness
                    best_start = cur
                    best_rid = res.res_id

            if best_start is None:
                task.is_missed = True
                earliest_end[tid] = self.horizon
            else:
                task.start_h = best_start
                task.end_h = best_start + task.duration_h
                task.assigned_resource = best_rid
                task.lateness_h = max(0, task.end_h - task.deadline_h)
                task.is_late = task.lateness_h > 0
                res_cursor[best_rid] = task.end_h
                earliest_end[tid] = task.end_h

            results.append(task)

            # Unlock dependent tasks
            for child_id in children[tid]:
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    child = self.task_map[child_id]
                    heapq.heappush(heap, (self._compute_score(child), child_id))

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
            "algorithm": "Priority Queue (Heap) - EDF + Profit-Weighted",
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
            "time_complexity": "O(N log N + N*M)",
            "space_complexity": "O(N + M)",
        }