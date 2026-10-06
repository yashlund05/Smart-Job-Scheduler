"""
Task Scheduler Optimization System
====================================
src/metrics.py - KPI Calculation and Comparison
"""

from typing import List, Dict
from src.models import Task


def compute_kpis(summary: Dict) -> Dict:
    """Compute detailed KPIs from a schedule summary."""
    scheduled = summary.get("scheduled", [])
    missed = summary.get("missed", [])
    late = summary.get("late", [])
    on_time = summary.get("on_time", [])
    total = summary.get("total_tasks", 0)

    # Resource utilization
    res_util: Dict[str, int] = {}
    for t in scheduled:
        rid = t.assigned_resource or "Unassigned"
        res_util[rid] = res_util.get(rid, 0) + t.duration_h

    # Average lateness (only for late tasks)
    avg_lateness = (sum(t.lateness_h for t in late) / len(late)) if late else 0

    # Profit efficiency
    max_possible_profit = sum(t.profit for t in scheduled + missed)
    profit_achieved = sum(t.profit for t in on_time)
    profit_efficiency = (profit_achieved / max_possible_profit * 100) if max_possible_profit else 0

    return {
        **summary,
        "resource_utilization": res_util,
        "avg_lateness_h": round(avg_lateness, 1),
        "profit_efficiency_pct": round(profit_efficiency, 1),
        "max_possible_profit": max_possible_profit,
    }


def compare_algorithms(summaries: List[Dict]) -> Dict:
    """Compare multiple algorithm results side by side."""
    comparison = []
    for s in summaries:
        kpi = compute_kpis(s)
        comparison.append({
            "algorithm": kpi["algorithm"],
            "on_time_pct": kpi["on_time_pct"],
            "total_profit": kpi["total_profit"],
            "profit_efficiency_pct": kpi["profit_efficiency_pct"],
            "total_lateness_h": kpi["total_lateness_h"],
            "makespan": kpi["makespan"],
            "missed_count": kpi["missed_count"],
            "scheduled_count": kpi["scheduled_count"],
            "execution_time_ms": kpi.get("execution_time_ms", 0.0),
            "time_complexity": kpi.get("time_complexity", "N/A"),
            "space_complexity": kpi.get("space_complexity", "N/A"),
        })
    # Find best per metric
    if comparison:
        best_profit = max(comparison, key=lambda x: x["total_profit"])["algorithm"]
        best_ontime = max(comparison, key=lambda x: x["on_time_pct"])["algorithm"]
        best_lateness = min(comparison, key=lambda x: x["total_lateness_h"])["algorithm"]
        fastest_algo = min(comparison, key=lambda x: x["execution_time_ms"])["algorithm"]
    else:
        best_profit = best_ontime = best_lateness = fastest_algo = "N/A"

    return {
        "comparison": comparison,
        "best_profit_algo": best_profit,
        "best_ontime_algo": best_ontime,
        "best_lateness_algo": best_lateness,
        "fastest_algo": fastest_algo,
    }