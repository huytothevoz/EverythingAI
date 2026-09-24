from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from heapq import heappop, heappush
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple
import math
import time
import tracemalloc

Position = Tuple[int, int]

DIRECTIONS: Dict[str, Position] = {
    "North": (-1, 0),
    "East": (0, 1),
    "South": (1, 0),
    "West": (0, -1),
}


@dataclass(frozen=True)
class State:
    """Dynamic Sokoban state: player position and box positions."""

    player: Position
    boxes: FrozenSet[Position]


@dataclass
class SearchResult:
    found: bool
    actions: List[str]
    cost: Optional[int]
    execution_time_s: float
    nodes_expanded: int
    nodes_generated: int
    unique_states: int
    max_frontier: int
    peak_memory_mb: float


class SokobanProblem:
    """Sokoban model for Requirements 1-4 of the midterm project."""

    def __init__(self, lines: Sequence[str]):
        if not lines:
            raise ValueError("The layout is empty.")

        self.lines = [line.rstrip("\n") for line in lines]
        self.height = len(self.lines)
        self.width = max(len(line) for line in self.lines)

        self.walls: set[Position] = set()
        self.floor: set[Position] = set()
        self.goals: set[Position] = set()
        boxes: set[Position] = set()
        player: Optional[Position] = None

        for r, line in enumerate(self.lines):
            for c in range(self.width):
                # Missing characters in ragged lines are treated as outside/walls.
                ch = line[c] if c < len(line) else "%"
                pos = (r, c)
                if ch == "%":
                    self.walls.add(pos)
                    continue

                self.floor.add(pos)
                if ch == "A":
                    if player is not None:
                        raise ValueError("The layout contains more than one agent A.")
                    player = pos
                elif ch == "B":
                    boxes.add(pos)
                elif ch == "D":
                    self.goals.add(pos)
                elif ch == "C":
                    boxes.add(pos)
                    self.goals.add(pos)
                elif ch != " ":
                    raise ValueError(f"Unsupported map symbol {ch!r} at {(r, c)}")

        if player is None:
            raise ValueError("The layout must contain one initial agent A.")
        if len(boxes) > len(self.goals):
            raise ValueError("There are more boxes than goals; the puzzle cannot be solved.")

        self.initial_state = State(player=player, boxes=frozenset(boxes))
        self.goal_list = tuple(sorted(self.goals))

        # Reverse-push distances are computed once and reused by every A* node.
        self.push_distance = self._precompute_reverse_push_distances()
        self.dead_squares = self._compute_static_dead_squares()

    @classmethod
    def from_file(cls, path: str | Path) -> "SokobanProblem":
        text = Path(path).read_text(encoding="utf-8").splitlines()
        return cls(text)

    def is_goal(self, state: State) -> bool:
        """Goal test: every box occupies a designated position."""
        return state.boxes.issubset(self.goals)

    def successors(self, state: State, prune_static_deadlocks: bool = True):
        """Generate (action, successor, step_cost) triples."""
        boxes = set(state.boxes)

        for action, (dr, dc) in DIRECTIONS.items():
            adjacent = (state.player[0] + dr, state.player[1] + dc)
            if adjacent not in self.floor:
                continue

            if adjacent not in boxes:
                # Ordinary player move.
                yield action, State(adjacent, state.boxes), 1
                continue

            # Push: the cell behind the box in the movement direction must be free.
            box_destination = (adjacent[0] + dr, adjacent[1] + dc)
            if box_destination not in self.floor or box_destination in boxes:
                continue

            # Safe static dead-square pruning. A goal is never classified as dead.
            if prune_static_deadlocks and box_destination in self.dead_squares:
                continue

            new_boxes = set(boxes)
            new_boxes.remove(adjacent)
            new_boxes.add(box_destination)
            yield action, State(adjacent, frozenset(new_boxes)), 1

    def _precompute_reverse_push_distances(self) -> Dict[Position, Dict[Position, int]]:
        """
        For each goal, run a reverse BFS in a static box-push graph.

        A forward box push u -> v is statically possible when:
        - u and v are floor cells, and
        - the support cell behind u is also a floor cell.

        Other boxes and the player's actual route are ignored. Therefore these distances
        are optimistic lower bounds on the number of pushes in the real puzzle.
        """
        result: Dict[Position, Dict[Position, int]] = {}

        for goal in self.goals:
            dist: Dict[Position, int] = {goal: 0}
            queue = deque([goal])

            while queue:
                current = queue.popleft()
                for dr, dc in DIRECTIONS.values():
                    predecessor = (current[0] - dr, current[1] - dc)
                    support = (predecessor[0] - dr, predecessor[1] - dc)

                    if (
                        predecessor in self.floor
                        and support in self.floor
                        and predecessor not in dist
                    ):
                        dist[predecessor] = dist[current] + 1
                        queue.append(predecessor)

            result[goal] = dist

        return result

    def _compute_static_dead_squares(self) -> set[Position]:
        """Cells from which a box cannot reach any goal even in the relaxed model."""
        dead: set[Position] = set()
        for cell in self.floor:
            if cell in self.goals:
                continue
            if all(cell not in self.push_distance[g] for g in self.goals):
                dead.add(cell)
        return dead

    @lru_cache(maxsize=None)
    def _matching_cost(self, boxes: Tuple[Position, ...]) -> float:
        """
        Minimum-cost one-to-one matching between boxes and goals using reverse-push
        distances. A bitmask DP is used to avoid third-party dependencies.
        """
        if not boxes:
            return 0.0
        if len(boxes) > len(self.goal_list):
            return math.inf

        # dp[mask] = best cost after assigning the boxes processed so far.
        dp: Dict[int, float] = {0: 0.0}

        for box in boxes:
            next_dp: Dict[int, float] = {}
            for mask, current_cost in dp.items():
                for j, goal in enumerate(self.goal_list):
                    if mask & (1 << j):
                        continue
                    d = self.push_distance[goal].get(box, math.inf)
                    if math.isinf(d):
                        continue
                    new_mask = mask | (1 << j)
                    new_cost = current_cost + d
                    if new_cost < next_dp.get(new_mask, math.inf):
                        next_dp[new_mask] = new_cost

            if not next_dp:
                return math.inf
            dp = next_dp

        return min(dp.values())

    def heuristic(self, state: State) -> float:
        """
        h(s) = minimum matching cost from current boxes to distinct goals,
        where each edge cost is a static reverse-push distance.
        """
        return self._matching_cost(tuple(sorted(state.boxes)))


def _reconstruct_actions(parent: Dict[State, Tuple[Optional[State], Optional[str]]], goal: State) -> List[str]:
    actions: List[str] = []
    state = goal
    while parent[state][0] is not None:
        previous, action = parent[state]
        assert previous is not None and action is not None
        actions.append(action)
        state = previous
    actions.reverse()
    return actions


def solve(
    problem: SokobanProblem,
    algorithm: str = "astar",
    start_state: Optional[State] = None,
    measure_memory: bool = True,
) -> SearchResult:
    """Solve using UCS or A*. Every primitive action has step cost 1."""
    algorithm = algorithm.lower()
    if algorithm not in {"ucs", "astar"}:
        raise ValueError("algorithm must be 'ucs' or 'astar'")

    start = start_state or problem.initial_state
    start_h = 0.0 if algorithm == "ucs" else problem.heuristic(start)
    if math.isinf(start_h):
        return SearchResult(False, [], None, 0.0, 0, 1, 1, 1, 0.0)

    if measure_memory:
        tracemalloc.start()
    start_time = time.perf_counter()

    # Heap item: (f, g, tie_breaker, state)
    counter = 0
    frontier: List[Tuple[float, int, int, State]] = [(start_h, 0, counter, start)]
    best_g: Dict[State, int] = {start: 0}
    parent: Dict[State, Tuple[Optional[State], Optional[str]]] = {start: (None, None)}

    nodes_expanded = 0
    nodes_generated = 1
    max_frontier = 1
    goal_state: Optional[State] = None

    while frontier:
        _, g, _, state = heappop(frontier)
        if g != best_g.get(state):
            continue  # stale heap entry

        if problem.is_goal(state):
            goal_state = state
            break

        nodes_expanded += 1

        for action, successor, step_cost in problem.successors(state):
            new_g = g + step_cost
            if new_g >= best_g.get(successor, math.inf):
                continue

            h = 0.0 if algorithm == "ucs" else problem.heuristic(successor)
            if math.isinf(h):
                continue

            best_g[successor] = new_g
            parent[successor] = (state, action)
            counter += 1
            heappush(frontier, (new_g + h, new_g, counter, successor))
            nodes_generated += 1

        max_frontier = max(max_frontier, len(frontier))

    elapsed = time.perf_counter() - start_time
    peak_mb = 0.0
    if measure_memory:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb = peak / (1024 * 1024)

    if goal_state is None:
        return SearchResult(
            found=False,
            actions=[],
            cost=None,
            execution_time_s=elapsed,
            nodes_expanded=nodes_expanded,
            nodes_generated=nodes_generated,
            unique_states=len(best_g),
            max_frontier=max_frontier,
            peak_memory_mb=peak_mb,
        )

    actions = _reconstruct_actions(parent, goal_state)
    return SearchResult(
        found=True,
        actions=actions,
        cost=len(actions),
        execution_time_s=elapsed,
        nodes_expanded=nodes_expanded,
        nodes_generated=nodes_generated,
        unique_states=len(best_g),
        max_frontier=max_frontier,
        peak_memory_mb=peak_mb,
    )


def replay(problem: SokobanProblem, actions: Iterable[str], start: Optional[State] = None) -> List[State]:
    """Return all states visited while replaying an action sequence."""
    state = start or problem.initial_state
    states = [state]

    for action in actions:
        candidates = {a: s2 for a, s2, _ in problem.successors(state)}
        if action not in candidates:
            raise ValueError(f"Action {action!r} is invalid at state {state}")
        state = candidates[action]
        states.append(state)

    return states


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Solve a Sokoban layout with UCS or A*.")
    parser.add_argument("layout", help="Path to a map text file")
    parser.add_argument("--algorithm", choices=["ucs", "astar"], default="astar")
    args = parser.parse_args()

    p = SokobanProblem.from_file(args.layout)
    result = solve(p, args.algorithm)
    print(result)
    if result.found:
        print("Actions:", result.actions)
