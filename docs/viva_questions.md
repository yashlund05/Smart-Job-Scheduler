# DAA Viva Preparation: Questions & Answers

**Project Title:** Smart Job Scheduling Using Greedy, Dynamic Programming and Backtracking Techniques  
**Course:** Design and Analysis of Algorithms (DAA)

---

### Q1. What is Job Scheduling?
**Answer:**  
Job scheduling is the process of allocating shared resources (such as CPU cores, machines, or human workers) to a collection of tasks over time, while satisfying constraints like deadlines, execution duration, precedence dependencies, and required skills to optimize an objective (such as maximizing earned profit or minimizing makespan).

---

### Q2. What is a Greedy Algorithm?
**Answer:**  
A Greedy algorithm is an algorithmic paradigm that builds a solution step-by-step, always choosing the option that offers the most immediate, locally optimal benefit without ever reconsidering past decisions or looking ahead to future consequences.

---

### Q3. Why is a Greedy Algorithm used in this project?
**Answer:**  
Greedy is used because it runs extremely fast in polynomial time ($O(N \log N + N \cdot M)$). For large-scale systems with thousands of incoming jobs, it produces a very good, feasible schedule almost instantaneously, even though it does not guarantee the global maximum profit.

---

### Q4. What is Dynamic Programming (DP)?
**Answer:**  
Dynamic Programming is an algorithmic technique for solving optimization problems by breaking them down into smaller subproblems, solving each subproblem only once, and storing their solutions in a table (memoization or tabulation) to avoid redundant computations.

---

### Q5. What is an Overlapping Subproblem?
**Answer:**  
A problem has overlapping subproblems when the same smaller subproblems are solved repeatedly during recursive evaluation. For instance, in our Weighted Job Scheduling DP, finding the optimal profit for a prefix of jobs up to time $t$ is reused by multiple later candidate jobs. DP caches these results in an array so each state is computed once.

---

### Q6. What is Optimal Substructure?
**Answer:**  
A problem exhibits optimal substructure if an optimal solution to the overall problem contains within it optimal solutions to its subproblems. In our DP formulation:
$$\text{OptimalProfit}(i) = \max\Big(\text{OptimalProfit}(i-1),\; \text{profit}_i + \text{OptimalProfit}(p(i))\Big)$$
where the optimal answer for $i$ directly uses the optimal answer of subproblems $i-1$ and $p(i)$.

---

### Q7. What is Backtracking?
**Answer:**  
Backtracking is a systematic, depth-first search of a problem's state-space decision tree. At each decision point, it explores an assignment branch. If a branch violates constraints or cannot possibly beat the best-known solution, it prunes the search and "backtracks" (undoes the previous choice) to explore alternative choices.

---

### Q8. What is the fundamental difference between Dynamic Programming and Backtracking?
**Answer:**  
- **Dynamic Programming** solves problems with overlapping subproblems and optimal substructure by building solutions bottom-up and storing them in polynomial time ($O(N \log N)$).
- **Backtracking** traverses an exponential decision tree top-down ($O(2^N)$ or $O((M+1)^N)$) through trial and error, undoing choices when branches fail or prove suboptimal. It does not require subproblems to overlap.

---

### Q9. Why is Backtracking computationally expensive?
**Answer:**  
Because its decision tree grows exponentially with the number of jobs. For $N$ jobs across $M$ resources, each job has $(M+1)$ potential branches (assigned to resource $1..M$ or skipped), leading to a worst-case state space of $O((M+1)^N)$ nodes.

---

### Q10. What is the time complexity of the three algorithms in this project?
**Answer:**  
- **Greedy:** $O(N \log N + N \cdot M)$ — sorting ready jobs by EDF/priority takes $O(N \log N)$, and slot checking takes $O(N \cdot M)$.
- **Dynamic Programming:** $O(M \cdot N \log N)$ — sorting intervals and performing binary search (`bisect`) for non-overlapping predecessors across $M$ resources.
- **Backtracking:** $O((M + 1)^N)$ in the worst case, but pruned heavily in practice by Branch & Bound.

---

### Q11. What is the space complexity of each algorithm?
**Answer:**  
- **Greedy:** $O(N + M)$ to store graph adjacency lists, in-degree counts, and resource cursors.
- **Dynamic Programming:** $O(N)$ for the 1D DP table and choice tracking array.
- **Backtracking:** $O(N)$ for the recursion call stack depth and state tracking arrays.

---

### Q12. What is the difference between a Greedy Algorithm and Dynamic Programming?
**Answer:**  
A Greedy algorithm makes an irreversible choice based purely on local criteria (e.g., picking the earliest deadline first) without looking back. Dynamic Programming evaluates all possible subproblem choices, records intermediate states, and guarantees an optimal solution by combining optimal sub-solutions.

---

### Q13. What is a Job Deadline?
**Answer:**  
A deadline is the specific point in time (in hours from $t=0$) before which a job must complete execution. If a job finishes after its deadline, it is considered **late** and incurs a lateness penalty (and 0 profit in strict weighted scheduling).

---

### Q14. What is Profit in this scheduling context?
**Answer:**  
Profit represents the business or utility value gained by completing a job on time. The objective function of our system is to maximize the sum of profits earned from all successfully completed on-time tasks.

---

### Q15. How does the Gantt Chart work in this system?
**Answer:**  
The Gantt chart is a horizontal bar chart displaying time along the X-axis and resources along the Y-axis. Each scheduled job appears as a colored block spanning from its start time to its end time:
- **Green bars:** Jobs completed on or before their deadline.
- **Yellow/Orange bars:** Jobs that completed after their deadline (late).
- **Red vertical lines:** Exact deadline positions.

---

### Q16. What happens when two jobs have the same deadline?
**Answer:**  
A tie-breaking rule is applied:
- In our **Greedy and Priority Queue** schedulers, ties are broken by **higher priority (1–5)**, and then by **higher profit**.
- In **Dynamic Programming**, intervals with equal finish times are sequenced consistently so binary search handles boundary conditions correctly.
- In **Backtracking**, both branch sequences are explored to determine which one yields the highest overall schedule profit.

---

### Q17. Why do we limit the Backtracking input size?
**Answer:**  
Because of the combinatorial explosion ($O((M+1)^N)$). While Backtracking runs in less than 3 ms for 10 jobs, 30 jobs would require exploring over $4^{30} \approx 10^{18}$ states, which would take centuries and freeze the computer. Limiting input to $\le 15$ jobs ensures responsive execution while demonstrating the algorithm.

---

### Q18. What is Big-O notation, and how does it differ from measured execution time?
**Answer:**  
- **Big-O notation** measures the theoretical asymptotic growth rate of an algorithm's running time as input size $N \to \infty$, independent of specific hardware.
- **Measured execution time** is the real wall-clock time in milliseconds taken on an actual CPU, measured using high-precision timers (`time.perf_counter()`). It is influenced by constant factors, CPU cache, and system load.

---

### Q19. What is the purpose of comparing algorithms side-by-side?
**Answer:**  
To understand real-world engineering trade-offs. The comparison matrix proves that while Backtracking achieves the highest profit (100% optimal), its execution time grows exponentially. Meanwhile, Greedy and DP run in fractions of a millisecond, making them the right choice when speed is paramount.

---

### Q20. Which algorithm produces the best result in your tests?
**Answer:**  
**Backtracking** produces the highest profit and lowest lateness because it exhaustively explores the solution space and guarantees global optimality. However, **Dynamic Programming** produces the fastest optimal subset for single-resource packing, and **Greedy** provides the fastest overall schedule with high on-time percentage.

---

### Q21. How do you handle precedence constraints (dependencies) between tasks?
**Answer:**  
We construct a Directed Acyclic Graph (DAG) of tasks and apply **Kahn's algorithm for Topological Sorting**. A task can only be scheduled once all tasks in its dependency list have completed, ensuring:
$$\text{start}_{\text{child}} \ge \max(\text{end}_{\text{parents}})$$

---

### Q22. How does Branch & Bound pruning work in your Backtracking scheduler?
**Answer:**  
Before expanding a node at job $k$, we calculate an upper bound:
$$\text{PotentialProfit} = \text{CurrentProfit} + \sum_{j=k}^N \text{Profit}_j$$
If $\text{PotentialProfit} \le \text{BestProfitFoundSoFar}$, we prune the entire subtree immediately because no decision downstream can possibly beat the solution we already have.

---

### Q23. What are the limitations of this project?
**Answer:**  
1. Backtracking is restricted to small job counts ($\le 15$) due to exponential time complexity.
2. The Dynamic Programming scheduler optimizes resources individually and greedily reconciles overlaps across multiple machines.
3. Task durations are deterministic and assumed to remain constant without stochastic delays.

---

### Q24. How can this system be expanded in the future?
**Answer:**  
1. Incorporating **Genetic Algorithms** or **Simulated Annealing** to achieve near-optimal schedules for large datasets ($N > 100$).
2. Parallelizing the Backtracking tree across multiple CPU cores.
3. Supporting dynamic real-time job arrivals (online scheduling).
