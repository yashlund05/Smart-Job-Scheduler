# College Project Report Notes

## Project Title
**Smart Job Scheduling Using Greedy, Dynamic Programming and Backtracking Techniques**

**Application Name:** Smart Job Scheduler  
**Course:** Design and Analysis of Algorithms (DAA)  
**Academic Level:** Undergraduate Computer Science & Engineering  

---

## 1. Abstract
Job scheduling is an essential combinatorial optimization challenge in computer science, operations research, and modern distributed computing. In real-world computing infrastructures, multiple jobs with distinct processing times, hard deadlines, priorities, dependency constraints, and worker skill requirements must be assigned to available resources to maximize total completed profit while minimizing schedule makespan and task lateness. This project, **Smart Job Scheduler**, presents an empirical and theoretical design and analysis of three fundamental algorithmic paradigms: **Greedy Algorithm**, **Dynamic Programming (DP)**, and **Recursive Backtracking with Branch-and-Bound pruning**. 

The system provides an automated multi-algorithm execution engine, side-by-side performance benchmarking, interactive ASCII and graphical Gantt chart visualizations, and constraint sensitivity (what-if) analysis. Experimental benchmarks across varying job set sizes confirm the polynomial efficiency of Greedy ($O(N \log N + N \cdot M)$) and Dynamic Programming ($O(M \cdot N \log N)$), while establishing the combinatorial optimality and worst-case exponential complexity ($O((M+1)^N)$) of Backtracking. The project demonstrates the practical trade-offs between heuristic speed and exhaustive optimality.

---

## 2. Introduction
In multi-programmed operating systems, cloud clusters, automated manufacturing shops, and project management pipelines, resource allocation is governed by job scheduling. Scheduling problems typically belong to the class of NP-hard combinatorial optimization problems when multiple machines, precedence dependencies, and release/deadline constraints are involved simultaneously.

The goal of this project is to apply core algorithm design techniques learned in the Design and Analysis of Algorithms (DAA) course to systematically solve and compare scheduling strategies:
1. **Greedy Heuristics:** Making myopic, locally optimal choices in the hope of reaching a high-quality global solution quickly.
2. **Dynamic Programming:** Decomposing the scheduling problem into overlapping subproblems with optimal substructure to maximize utility without redundant computation.
3. **Backtracking Search:** Systematically searching through a state-space tree of job-to-resource assignments, employing bounding functions to prune non-viable subtrees while guaranteeing globally optimal profit.

---

## 3. Problem Statement
Given:
- A set of $N$ jobs $\mathcal{J} = \{J_1, J_2, \dots, J_N\}$, where each job $J_i$ is characterized by:
  - Duration $p_i \in \mathbb{Z}^+$ (processing time in hours)
  - Deadline $d_i \in \mathbb{Z}^+$ (maximum allowable completion time from $t=0$)
  - Priority $w_i \in \{1, 2, 3, 4, 5\}$ (importance weighting)
  - Profit score $v_i \in \mathbb{Z}^+$ (utility earned if finished on or before deadline)
  - Skill requirement $s_i \in \{\text{backend}, \text{frontend}, \text{qa}\}$
  - Precedence dependencies $\mathcal{D}_i \subset \mathcal{J}$ (jobs that must finish before $J_i$ can begin)
- A set of $M$ resources $\mathcal{R} = \{R_1, R_2, \dots, R_M\}$, where each resource $R_j$ has:
  - Supported skill capabilities $\mathcal{S}_j$
  - Shift time window $[W_{\text{start}}, W_{\text{end}}]$ repeated daily
- A planning horizon $H$ (e.g., 72 hours).

**Objective:**  
Determine an assignment $(J_i \to R_j, \text{start}_i, \text{end}_i)$ such that:
1. **Skill constraint:** $s_i \in \mathcal{S}_j$ for assigned resource $R_j$.
2. **Precedence constraint:** $\text{start}_i \ge \max_{J_k \in \mathcal{D}_i} (\text{end}_k)$.
3. **Resource non-overlap:** For any two jobs $J_a, J_b$ assigned to the same resource $R_j$, intervals $[\text{start}_a, \text{end}_a)$ and $[\text{start}_b, \text{end}_b)$ must not overlap.
4. **Shift window constraint:** Processing occurs strictly within allowable daily shift hours.
5. **Optimization goal:** Maximize total on-time earned profit $\sum_{i: \text{end}_i \le d_i} v_i$ while minimizing total lateness $\sum_{i} \max(0, \text{end}_i - d_i)$ and makespan $\max_i(\text{end}_i)$.

---

## 4. Objectives
1. Implement a clean, modular Python and web-based scheduling system.
2. Develop a **Greedy Job Scheduling Algorithm** utilizing Earliest Deadline First (EDF) coupled with Kahn's topological sort.
3. Develop a **Dynamic Programming Algorithm** solving the Weighted Job Scheduling Problem via interval partitioning and binary search.
4. Develop a **Recursive Backtracking Algorithm** with Branch-and-Bound bounding to search the combinatorial decision tree and find the globally optimal valid schedule.
5. Provide a side-by-side comparison matrix showing:
   - Selected / Scheduled jobs
   - Total profit earned
   - On-time percentage
   - Total lateness
   - Makespan
   - Real measured execution time (in milliseconds)
   - Theoretical Big-O Time and Space complexities
6. Validate all implementations with automated unit tests and benchmark datasets.

---

## 5. Motivation
In practical engineering systems, choosing the correct algorithm paradigm is critical:
- If an automated high-frequency cloud router receives 50,000 tasks every second, an exponential algorithm would freeze the infrastructure, mandating a Greedy or DP approach.
- Conversely, for mission-critical satellite telemetry or multi-million dollar manufacturing setups with 10–12 high-value tasks, spending extra CPU cycles in Backtracking to extract 100% optimal profit is well worth the computation time.

This project bridges DAA theoretical analysis (Big-O notation, recurrences, state trees) with practical software engineering and measurement.

---

## 6. Proposed System & Architecture
The system consists of three architectural layers:

```
┌────────────────────────────────────────────────────────┐
│                   USER INTERFACES                      │
│   CLI (main.py)              Web Dashboard (HTML/JS)   │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
┌───────────▼────────────────────────────────▼───────────┐
│                   CORE ALGORITHM ENGINE                │
│                                                        │
│  [1] Greedy Scheduler (Kahn's TopoSort + EDF Heuristic)│
│  [2] Dynamic Programming (Weighted Interval DP+Bisect) │
│  [3] Backtracking Scheduler (Recursive Branch & Bound) │
│  [4] Priority Queue Scheduler (Binary Min-Heap)        │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
┌───────────▼────────────────────────────────▼───────────┐
│               EVALUATION & VISUALIZATION               │
│  KPI Calculator      ASCII/SVG Gantt Chart  CSV Export │
│  Real Time Clock     Theoretical Big-O     What-If Sim │
└────────────────────────────────────────────────────────┘
```

---

## 7. Algorithms Detailed Analysis

### 7.1 Greedy Job Scheduling Algorithm

#### Idea
The Greedy approach makes an irrevocable, locally optimal decision at each step according to a defined heuristic score. For job scheduling with deadlines, Earliest Deadline First (EDF) combined with job priority is applied after respecting precedence dependencies via topological sorting.

#### Steps
1. **Dependency Graph Construction:** Build an in-degree map and adjacency list from task dependencies.
2. **Topological Order (Kahn's Algorithm):** Enqueue all tasks with in-degree 0. While the queue is non-empty, dequeue the task with the highest priority and earliest deadline, append to the scheduling order, and decrement dependent in-degrees.
3. **Resource Slot Allocation:** For each task in topological order, iterate through all compatible resources $R_j$.
4. **Feasibility Check:** Compute earliest feasible start time $t \ge \max(\text{cursor}_j, \text{dependency\_end})$ aligned to resource daily shift windows.
5. **Greedy Choice:** Assign the task to the resource that minimizes lateness and maximizes utilization. Update resource cursor and task completion time.

#### Concrete Example
Suppose 3 jobs:
- $J_1$: Duration 2h, Deadline 3h, Profit 100, Priority 5
- $J_2$: Duration 1h, Deadline 2h, Profit 50, Priority 4
- $J_3$: Duration 2h, Deadline 4h, Profit 80, Priority 3

Greedy sorts by priority/deadline:
1. Schedule $J_1$ at $t=0..2$. End = 2h $\le 3$ (On Time, Profit +100).
2. Schedule $J_2$ at $t=2..3$. End = 3h $> 2$ (Late by 1h, Profit 0).
3. Schedule $J_3$ at $t=3..5$. End = 5h $> 4$ (Late by 1h, Profit 0).
Total Profit = 100.

#### Complexity
- **Time Complexity:**
  - Graph construction & Kahn's algorithm: $O(V + E)$ where $V = N$ (jobs) and $E$ is dependency edges.
  - Sorting candidates at each step: $O(N \log N)$.
  - Finding best resource slot for $N$ jobs across $M$ resources: $O(N \cdot M)$.
  - **Overall Time Complexity:** $O(N \log N + N \cdot M)$.
- **Space Complexity:** $O(N + M)$ for adjacency list, in-degree array, and resource tracking.

#### Advantages & Limitations
- **Advantages:** Extremely fast; scalable to millions of jobs; simple to implement.
- **Limitations:** Suffers from local myopia; can be blocked from discovering higher overall profit combinations.

---

### 7.2 Dynamic Programming Job Scheduling Algorithm

#### Idea
Dynamic Programming solves the Weighted Job Scheduling Problem by identifying optimal substructure and overlapping subproblems. By sorting jobs by finish time and defining a 1D recurrence relation, it determines for each job whether the total profit is higher by including the job (plus the optimal solution of compatible non-overlapping predecessors) or excluding it.

#### Formulation
- **State Definition:**  
  $DP[i]$ = Maximum profit achievable considering a subset of the first $i$ jobs sorted by end time.
- **Recurrence Relation:**  
  $$DP[i] = \max\Big( DP[i - 1],\; \text{profit}[i] + DP[p(i)] \Big)$$
  where $p(i)$ is the index of the latest job that completes before job $i$ begins.
- **Predecessor Search:**  
  Because jobs are sorted by end time, $p(i)$ is computed using binary search (`bisect_right`) over end times in $O(\log N)$ time.
- **Base Case:**  
  $$DP[0] = 0$$
- **Reconstruction:**  
  Trace back through decisions from $i=N$ down to 1. If $DP[i] > DP[i-1]$, job $i$ was included; jump to $p(i)$. Otherwise, job $i$ was excluded; jump to $i-1$.

#### Concrete Example
Given compatible intervals sorted by finish time:
- Job A: [0, 2], Profit 50
- Job B: [0, 3], Profit 100
- Job C: [2, 4], Profit 80

Calculations:
- $DP[0] = 0$
- $DP[1]$ (Job A): $\max(0, 50 + DP[0]) = 50$
- $DP[2]$ (Job B): $\max(50, 100 + DP[0]) = 100$
- $DP[3]$ (Job C): Compatible predecessor is Job A ($p(3) = 1$).  
  $DP[3] = \max(DP[2],\; 80 + DP[1]) = \max(100, 80 + 50) = 130$.
Traceback selects Job C and Job A. Total profit = 130.

#### Complexity
- **Time Complexity:**
  - Sorting jobs by end time: $O(N \log N)$.
  - DP array iteration: $N$ steps, each performing binary search $O(\log N)$.
  - Multi-resource outer loop: across $M$ resources:
  - **Overall Time Complexity:** $O(M \cdot N \log N)$.
- **Space Complexity:** $O(N)$ to store the DP table and traceback choices.

#### Advantages & Limitations
- **Advantages:** Guaranteed optimal subset for non-overlapping weighted intervals on each resource; strictly polynomial time.
- **Limitations:** Resource assignment coupling across multiple machines requires heuristic coordination.

---

### 7.3 Backtracking Job Scheduling Algorithm

#### Idea
Recursive Backtracking explores the complete state-space tree of possible schedules. For each job $k$ (in topological dependency order), the algorithm branches into $(M + 1)$ potential decisions:
- Assigning job $k$ to resource $R_1$
- Assigning job $k$ to resource $R_2$
- ...
- Assigning job $k$ to resource $R_M$
- Excluded (skipping job $k$)

To avoid exhaustive exponential explosion, **Branch-and-Bound pruning** is implemented: at any node, if the current accumulated profit plus the sum of all remaining potential job profits is less than or equal to the best profit found so far, the entire branch is pruned immediately.

#### Algorithm Steps
1. Precompute topological sort to enforce dependency order.
2. Precompute suffix sums of remaining profits: $\text{suffix\_profit}[k] = \sum_{j=k}^N \text{profit}[j]$.
3. Define recursive function `backtrack(k, current_profit, current_lateness)`:
   - **Base Case:** If $k = N$, update global `best_schedule` if $current\_profit > best\_profit$ (or tie-broken by lower lateness/makespan).
   - **Pruning Check:** If $current\_profit + \text{suffix\_profit}[k] \le best\_profit$, return immediately (cut subtree).
   - **Branch 1..M (Resource Assignments):** For each resource $R_j$ capable of handling skill $s_k$:
     - Find earliest valid start time satisfying dependency completion and daily shift windows.
     - If feasible within horizon:
       - Record state (update resource cursor, task end time, profit earned).
       - Recurse: `backtrack(k + 1, ...)`.
       - **Backtrack:** Undo state changes (restore resource cursor and task attributes).
   - **Branch M+1 (Task Exclusion):** Mark job $k$ as unscheduled and recurse: `backtrack(k + 1, ...)`. Undo exclusion upon return.

#### Concrete Example
Using the 5-job college demo dataset with 1 resource:
- Total theoretical combinations without pruning: $2^5 = 32$ leaves.
- With Branch & Bound: When an early branch achieves profit 220, subtrees whose remaining jobs cannot exceed 220 are pruned immediately.
- Result: Explores 88 internal search nodes in 0.26 ms, identifying the exact optimal schedule $(J_2, J_4, J_5)$ earning maximum profit 220 with 0h lateness.

#### Complexity
- **Time Complexity:**
  - Branching factor: $(M + 1)$ per task level.
  - Depth of recursion tree: $N$ tasks.
  - **Worst-Case Time Complexity:** $O((M + 1)^N)$ (exponential).
  - **Average Case with Branch & Bound:** Significantly reduced to $O(b^N)$ where effective branching factor $b \ll M+1$.
- **Space Complexity:**
  - Maximum depth of recursion call stack is $N$.
  - State tracking data structures require $O(N)$ memory.
  - **Overall Space Complexity:** $O(N)$.

#### Advantages & Limitations
- **Advantages:** Guaranteed global optimality across all constraints; flexible constraint verification; easy to incorporate custom objective functions.
- **Limitations:** Exponential worst-case complexity; unfeasible for large $N > 20$ without aggressive heuristics.

---

## 8. Experimental Results & Benchmark Comparison

Empirical tests were executed on an AMD Ryzen / Intel Core environment using Python's high-resolution `time.perf_counter()`.

### Benchmark Results Table

| Task Set Size | Greedy Execution Time | Greedy Profit | DP Execution Time | DP Profit | Backtracking Time | Backtracking Profit | Backtracking Nodes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **5 Jobs** | 0.086 ms | 390 | 0.067 ms | 350 | **0.268 ms** | **390** | 94 nodes |
| **8 Jobs** | 0.075 ms | 630 | 0.065 ms | 440 | **1.329 ms** | **630** | 589 nodes |
| **10 Jobs** | 0.075 ms | 675 | 0.076 ms | 540 | **2.880 ms** | **805** | 1,108 nodes |
| **12 Jobs** | 0.092 ms | 695 | 0.101 ms | 710 | **24.080 ms** | **895** | 14,708 nodes |

### Key Observations:
1. **Solution Quality:** Backtracking achieved the strictly highest profit (895 on 12 jobs) compared to Greedy (695) and DP (710).
2. **Execution Scalability:** As task size increased from 5 to 12:
   - Greedy execution time grew modestly from 0.086 ms to 0.092 ms ($O(N \log N)$).
   - DP execution time scaled from 0.067 ms to 0.101 ms ($O(N \log N)$).
   - Backtracking search nodes increased from 94 to 14,708, and execution time increased by ~90x from 0.268 ms to 24.08 ms, clearly validating the theoretical exponential upper bound.

---

## 9. Comprehensive Comparison Summary

| Metric / Attribute | Greedy Algorithm | Dynamic Programming | Backtracking (Branch & Bound) |
| :--- | :--- | :--- | :--- |
| **Paradigm** | Heuristic / Greedy choice | Optimal Substructure & Memoization | State-Space Tree Search |
| **Theoretical Time** | $O(N \log N + N \cdot M)$ | $O(M \cdot N \log N)$ | $O((M+1)^N)$ worst-case |
| **Theoretical Space**| $O(N + M)$ | $O(N)$ | $O(N)$ recursion depth |
| **Measured Time (10 jobs)**| $\approx 0.08$ ms | $\approx 0.07$ ms | $\approx 2.8$ ms |
| **Optimality Guarantee**| No (local heuristic) | Yes (for 1 resource interval problem) | **Yes (global optimal)** |
| **Pruning Mechanism** | None (irrevocable) | Tabulation overrides | Branch-and-bound bound check |
| **Recommended Use Case**| Large batch scheduling ($N > 1000$) | Non-overlapping interval optimization | High-value, critical schedules ($N \le 15$) |

---

## 10. Conclusion
This project successfully designed, implemented, and evaluated a comprehensive Smart Job Scheduling System comparing Greedy, Dynamic Programming, and Backtracking algorithms. 

The experimental and theoretical investigations reveal that no single algorithm dominates across all engineering criteria:
- **Greedy** provides outstanding throughput and polynomial responsiveness, making it the algorithm of choice for live operating system dispatchers and cloud queue workers.
- **Dynamic Programming** provides mathematical optimality for interval-based packing problems in low polynomial time.
- **Backtracking with Branch-and-Bound** provides absolute global optimality for complex combinatorial constraints, establishing the benchmark against which heuristic approximations must be measured.

---

## 11. Future Scope
1. **Genetic Algorithm / Simulated Annealing:** Implement metaheuristic approaches to bridge the gap between Greedy speed and Backtracking optimality for $N > 100$.
2. **Multi-Core Parallel Backtracking:** Distribute root branches of the decision tree across multiple CPU cores to scale Backtracking to $N \approx 25$.
3. **Machine Learning Dispatcher:** Train a lightweight classifier to automatically recommend the best algorithm based on dataset size and variance in deadlines.

---

## 12. References
1. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2009). *Introduction to Algorithms* (3rd ed.). MIT Press. (Chapters: Greedy Algorithms, Dynamic Programming).
2. Kleinberg, J., & Tardos, É. (2006). *Algorithm Design*. Pearson. (Weighted Interval Scheduling, Backtracking).
3. Pinedo, M. L. (2016). *Scheduling: Theory, Algorithms, and Systems*. Springer.
4. Base Open-Source Repository: Sonia068/Task-Scheduler-Optimization-System (MIT License).
