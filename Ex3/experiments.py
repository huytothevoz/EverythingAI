import csv
import os
import sys
import time
import tracemalloc

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from Ex1.game_logic import SokobanGame
from Ex2.search_algorithms import a_star_search, ucs_search


def measure_time(search_fn, map_path, repeats=5):
    """Chạy nhiều lần và lấy thời gian trung bình."""
    times = []
    last_result = None

    for _ in range(repeats):
        game = SokobanGame(map_path)
        start = time.perf_counter()
        last_result = search_fn(game, return_stats=True)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # milliseconds

    return sum(times) / len(times), last_result


def measure_peak_memory(search_fn, map_path):
    """Đo peak memory bằng tracemalloc."""
    game = SokobanGame(map_path)
    tracemalloc.start()
    result = search_fn(game, return_stats=True)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024.0, result  # KB


def benchmark_algorithm(name, search_fn, map_path, repeats=5):
    """Thu thập time, memory, frontier và số state đã duyệt."""
    avg_time_ms, result = measure_time(search_fn, map_path, repeats)
    peak_memory_kb, _ = measure_peak_memory(search_fn, map_path)

    path, cost, expanded, stats = result

    return {
        "algorithm": name,
        "cost": cost,
        "expanded_nodes": expanded,
        "visited_states": stats["visited_states"],
        "max_frontier_size": stats["max_frontier_size"],
        "avg_time_ms": avg_time_ms,
        "peak_memory_kb": peak_memory_kb,
        "solution_found": path is not None,
    }


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)

    # Benchmark trên nhiều map để kết quả dễ so sánh.
    maps = [
        ("testmap", os.path.join(root_dir, "Ex1", "testmap.txt")),
        ("benchmark_1box", os.path.join(current_dir, "maps", "benchmark_1box.txt")),
        ("benchmark_2box", os.path.join(current_dir, "maps", "benchmark_2box.txt")),
        ("example_map", os.path.join(root_dir, "Ex1", "example_map.txt")),
    ]
    algorithms = [("A*", a_star_search), ("UCS", ucs_search)]

    rows = []
    for map_name, map_path in maps:
        for algorithm_name, search_fn in algorithms:
            result = benchmark_algorithm(algorithm_name, search_fn, map_path)
            result["map"] = map_name
            rows.append(result)

            print(
                f"{map_name:16} | {algorithm_name:3} | "
                f"cost={result['cost']:3} | expanded={result['expanded_nodes']:7} | "
                f"visited={result['visited_states']:7} | frontier={result['max_frontier_size']:7} | "
                f"time={result['avg_time_ms']:.3f} ms | peak={result['peak_memory_kb']:.1f} KB"
            )

    output_path = os.path.join(current_dir, "benchmark_results.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "map",
                "algorithm",
                "cost",
                "expanded_nodes",
                "visited_states",
                "max_frontier_size",
                "avg_time_ms",
                "peak_memory_kb",
                "solution_found",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nĐã lưu kết quả: {output_path}")
    return rows


if __name__ == "__main__":
    main()
