"""
Task Scheduler Optimization System
===================================
src/models.py - Data models for Tasks and Resources
"""

import csv
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Task:
    """Represents a schedulable task with all constraints."""
    task_id: str
    duration_h: int          # Execution time in hours
    deadline_h: int          # Deadline (hours from t=0)
    priority: int            # 1 (low) to 5 (high)
    skill: str               # Required skill
    depends_on: List[str]    # List of task IDs this depends on
    profit: int              # Importance/profit score

    # Scheduled fields (filled after scheduling)
    start_h: Optional[int] = None
    end_h: Optional[int] = None
    assigned_resource: Optional[str] = None
    is_late: bool = False
    lateness_h: int = 0
    is_missed: bool = False

    def __repr__(self):
        return (f"Task({self.task_id}, prio={self.priority}, "
                f"ddl={self.deadline_h}h, dur={self.duration_h}h, profit={self.profit})")


@dataclass
class Resource:
    """Represents a worker/machine with skills and shift windows."""
    res_id: str
    skills: set
    shift_start_h: int       # Shift start (hours, repeated each day)
    shift_end_h: int         # Shift end
    max_hours_per_day: int

    # Scheduling state
    current_time_h: int = 0
    total_hours_assigned: int = 0

    def can_handle(self, skill: str) -> bool:
        return skill in self.skills

    def __repr__(self):
        return f"Resource({self.res_id}, skills={self.skills})"


def load_tasks(path: str = "data/tasks.csv") -> List[Task]:
    """Load tasks from CSV file."""
    tasks = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            deps = [d.strip() for d in (row.get("depends_on") or "").split("|") if d.strip()]
            task = Task(
                task_id=row["task_id"].strip(),
                duration_h=int(row["duration_h"]),
                deadline_h=int(row["deadline_h"]),
                priority=int(row["priority"]),
                skill=row["skill"].strip(),
                depends_on=deps,
                profit=int(row.get("profit", 100))
            )
            tasks.append(task)
    return tasks


def load_resources(path: str = "data/resources.csv") -> List[Resource]:
    """Load resources from CSV file."""
    resources = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills = set(s.strip() for s in (row["skills"] or "").split("|") if s.strip())
            res = Resource(
                res_id=row["res_id"].strip(),
                skills=skills,
                shift_start_h=int(row["shift_start_h"]),
                shift_end_h=int(row["shift_end_h"]),
                max_hours_per_day=int(row["max_hours_per_day"])
            )
            resources.append(res)
    return resources


def validate_tasks(tasks: List[Task]) -> Tuple[bool, List[str]]:
    """
    Validate a list of tasks for common input issues:
    - Empty task list
    - Duplicate task IDs
    - Invalid duration (<= 0)
    - Invalid deadline (<= 0)
    - Negative profit (< 0)
    - Priority outside 1..5
    - Missing dependency references
    Returns (is_valid, list_of_errors).
    """
    errors = []
    if not tasks:
        return False, ["Task list is empty."]

    seen_ids = set()
    for t in tasks:
        if not t.task_id or not t.task_id.strip():
            errors.append("Found task with empty or whitespace-only task_id.")
        elif t.task_id in seen_ids:
            errors.append(f"Duplicate task ID detected: '{t.task_id}'.")
        seen_ids.add(t.task_id)

        if t.duration_h <= 0:
            errors.append(f"Task '{t.task_id}' has invalid duration ({t.duration_h}h). Duration must be positive.")
        if t.deadline_h <= 0:
            errors.append(f"Task '{t.task_id}' has invalid deadline ({t.deadline_h}h). Deadline must be positive.")
        if t.profit < 0:
            errors.append(f"Task '{t.task_id}' has negative profit ({t.profit}). Profit must be >= 0.")
        if not (1 <= t.priority <= 5):
            errors.append(f"Task '{t.task_id}' has priority {t.priority}. Priority should be between 1 and 5.")

    # Check dependencies
    for t in tasks:
        for dep in t.depends_on:
            if dep not in seen_ids:
                errors.append(f"Task '{t.task_id}' depends on '{dep}', which does not exist in the task list.")

    # Cycle detection via Kahn's Algorithm / In-Degree check
    has_cycle, cycle_nodes = detect_dependency_cycle(tasks)
    if has_cycle:
        errors.append(f"Cyclic dependency detected among tasks: {', '.join(cycle_nodes)}. Precedence graph must be a DAG.")

    return len(errors) == 0, errors


def detect_dependency_cycle(tasks: List[Task]) -> Tuple[bool, List[str]]:
    """
    Detect if the task dependency graph contains a cycle using Kahn's Algorithm.
    Returns (has_cycle, list_of_nodes_in_cycle).
    """
    from collections import defaultdict, deque
    in_degree = {t.task_id: 0 for t in tasks}
    children = defaultdict(list)
    valid_ids = set(in_degree.keys())

    for t in tasks:
        for dep in t.depends_on:
            if dep in valid_ids:
                in_degree[t.task_id] += 1
                children[dep].append(t.task_id)

    queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
    visited_count = 0

    while queue:
        node = queue.popleft()
        visited_count += 1
        for child in children[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if visited_count < len(tasks):
        # Nodes with in_degree > 0 are part of or trapped by cycles
        cycle_nodes = [tid for tid, deg in in_degree.items() if deg > 0]
        return True, cycle_nodes
    return False, []


def get_greedy_trap_dataset() -> Tuple[List[Task], List[Resource]]:
    """
    Curated Professor Counter-Example: 'The Greedy Trap'.
    Demonstrates that Greedy Heuristics (EDF + Priority) make locally optimal choices
    that fail to achieve the global optimum, whereas DP and Backtracking succeed.

    Scenario:
      1 Resource (R1).
      - J1: Duration 6h, Deadline 6h, Priority 5, Profit 120. (Greedy choice)
      - J2: Duration 4h, Deadline 7h, Priority 4, Profit 100.
      - J3: Duration 4h, Deadline 8h, Priority 4, Profit 100.

    Result:
      - Greedy picks J1 (earliest deadline & highest priority) -> Total Profit = 120 (J2, J3 missed).
      - DP & Backtracking select {J2, J3} -> Total Profit = 200 (66% higher!).
    """
    tasks = [
        Task("J1", duration_h=6, deadline_h=6, priority=5, skill="backend", depends_on=[], profit=120),
        Task("J2", duration_h=4, deadline_h=7, priority=4, skill="backend", depends_on=[], profit=100),
        Task("J3", duration_h=4, deadline_h=8, priority=4, skill="backend", depends_on=[], profit=100),
    ]
    resources = [
        Resource("R1", {"backend"}, shift_start_h=0, shift_end_h=24, max_hours_per_day=24)
    ]
    return tasks, resources


def get_cycle_demo_dataset() -> Tuple[List[Task], List[Resource]]:
    """
    Professor Edge-Case: Precedence Deadlock / Cycle Detection.
    A cyclic dependency graph: J1 -> J2 -> J3 -> J1.
    """
    tasks = [
        Task("J1", duration_h=2, deadline_h=10, priority=4, skill="backend", depends_on=["J3"], profit=100),
        Task("J2", duration_h=2, deadline_h=10, priority=3, skill="backend", depends_on=["J1"], profit=80),
        Task("J3", duration_h=2, deadline_h=10, priority=5, skill="backend", depends_on=["J2"], profit=120),
    ]
    resources = [
        Resource("R1", {"backend"}, shift_start_h=0, shift_end_h=8, max_hours_per_day=8)
    ]
    return tasks, resources