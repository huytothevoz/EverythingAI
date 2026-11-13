"""Root launcher for the three AI course project tasks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
TASKS = {
    "1": ("Task 1 — N-Queens", ROOT_DIR / "task1", "task1.py"),
    "2": ("Task 2 — Tank Battle", ROOT_DIR / "task2", "task2.py"),
    "3": ("Task 3 — Kakuro", ROOT_DIR / "task3", "task3.py"),
}


def _run_task(choice: str) -> None:
    label, task_dir, entry_point = TASKS[choice]
    script = task_dir / entry_point
    if not script.is_file():
        raise FileNotFoundError(f"Không tìm thấy entry point {script}")

    print(f"\nĐang mở {label}...\n")
    result = subprocess.run([sys.executable, str(script)], cwd=task_dir, check=False)
    if result.returncode:
        print(f"\n{label} kết thúc với mã lỗi {result.returncode}.")


def main() -> None:
    while True:
        print("\n" + "=" * 44)
        print("  AI FINAL PROJECT — TASK LAUNCHER")
        print("=" * 44)
        for key, (label, _, _) in TASKS.items():
            print(f"  {key}. {label}")
        print("  0. Thoát")
        choice = input("Chọn task: ").strip()

        if choice == "0":
            return
        if choice not in TASKS:
            print("Lựa chọn không hợp lệ. Hãy chọn 1, 2, 3 hoặc 0.")
            continue
        _run_task(choice)


if __name__ == "__main__":
    main()
