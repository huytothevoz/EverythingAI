from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Tuple
import csv
import math

from sokoban_search import SokobanProblem, State, replay, solve


def benchmark(layouts: Dict[str, SokobanProblem], repeats: int = 3):
    """Compare UCS and A* using median execution time and peak traced memory."""
    rows = []
    for map_name, problem in layouts.items():
        for algorithm in ("ucs", "astar"):
            solve(problem, algorithm, measure_memory=False)  # warm-up
            runs = [solve(problem, algorithm, measure_memory=True) for _ in range(repeats)]
            first = runs[0]
            rows.append(
                {
                    "map": map_name,
                    "algorithm": algorithm.upper(),
                    "solution_cost": first.cost,
                    "nodes_expanded": first.nodes_expanded,
                    "nodes_generated": first.nodes_generated,
                    "unique_states": first.unique_states,
                    "max_frontier": first.max_frontier,
                    "median_time_ms": median(r.execution_time_s for r in runs) * 1000,
                    "median_peak_memory_mb": median(r.peak_memory_mb for r in runs),
                }
            )
    return rows


def verify_admissibility(problem: SokobanProblem):
    """
    Sample every state on an optimal UCS path. For each sampled state, run UCS again
    from that state to obtain the exact remaining optimal cost h*(s), then test h(s)<=h*(s).
    """
    optimum = solve(problem, "ucs", measure_memory=False)
    if not optimum.found:
        raise ValueError("Cannot test admissibility on an unsolved benchmark map.")

    states = replay(problem, optimum.actions)
    rows = []
    violations = 0

    for index, state in enumerate(states):
        exact = solve(problem, "ucs", start_state=state, measure_memory=False)
        h_star = math.inf if not exact.found else exact.cost
        h = problem.heuristic(state)
        ok = h <= h_star
        violations += int(not ok)
        rows.append((index, h, h_star, ok))

    return rows, violations


def reachable_states(problem: SokobanProblem, max_states: int = 50000) -> List[State]:
    """Collect reachable states by bounded graph exploration for consistency testing."""
    from collections import deque

    seen = {problem.initial_state}
    queue = deque([problem.initial_state])

    while queue and len(seen) < max_states:
        state = queue.popleft()
        for _, successor, _ in problem.successors(state):
            if successor not in seen:
                seen.add(successor)
                queue.append(successor)
                if len(seen) >= max_states:
                    break

    return list(seen)


def verify_consistency(problem: SokobanProblem, states: Iterable[State]):
    """Test h(s) <= c(s,a,s') + h(s') for every tested transition."""
    checked = 0
    violations = []

    for state in states:
        h = problem.heuristic(state)
        for action, successor, cost in problem.successors(state):
            h2 = problem.heuristic(successor)
            checked += 1

            # Extended-real convention: infinity <= infinity is accepted; an infinite
            # predecessor leading in one step to a finite successor would be a violation.
            if math.isinf(h):
                ok = math.isinf(h2)
            else:
                ok = h <= cost + h2

            if not ok:
                violations.append((state, action, successor, h, h2, cost))

    return checked, violations


def load_layouts(folder: str | Path) -> Dict[str, SokobanProblem]:
    folder = Path(folder)
    return {p.stem: SokobanProblem.from_file(p) for p in sorted(folder.glob("*.txt"))}


def save_csv(rows, path: str | Path):
    rows = list(rows)
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Sokoban search experiments.")
    parser.add_argument("layout_folder", help="Folder containing .txt benchmark maps")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    maps = load_layouts(args.layout_folder)
    benchmark_rows = benchmark(maps, repeats=args.repeats)
    save_csv(benchmark_rows, "benchmark_results.csv")

    for name, problem in maps.items():
        adm_rows, adm_violations = verify_admissibility(problem)
        states = reachable_states(problem)
        checked, cons_violations = verify_consistency(problem, states)
        print(
            name,
            f"admissibility: {len(adm_rows)} states, {adm_violations} violations;",
            f"consistency: {checked} transitions, {len(cons_violations)} violations",
        )
