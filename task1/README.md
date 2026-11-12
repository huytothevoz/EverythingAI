# Task 1: Local Search & Propositional Logic

Giải bài toán N quân hậu theo hướng đối tượng. Bài làm nằm trong thư mục này; PDF đề gốc được giữ nguyên.

## Cài đặt và chạy

Yêu cầu Python 3.10 trở lên. Mở thư mục chứa `main.py`.

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS: source .venv/bin/activate
python -m pip install -r requirements.txt

# Mở menu tương tác
python main.py

# Chạy unit test
python -m unittest discover -v
```

Gói cần cài là **python-sat**, không phải gói `pysat` có cùng tên import nhưng mục đích khác. Thư viện **matplotlib** cần cho notebook thực nghiệm.

## Menu tương tác

`python main.py` mở menu:

```
============================================
  N-QUEENS - TASK 1
============================================
  1. Giải bằng Glucose3 (SAT)
  2. Giải bằng Min-Conflicts (standard)
  3. Giải bằng Min-Conflicts (max-conflict)
  4. Chạy benchmark đầy đủ
  0. Thoát
--------------------------------------------
```

- Chọn **1–3**: nhập N, chương trình giải một bài và in bàn cờ ASCII cùng thời gian (và số bước với Min-Conflicts).
- Chọn **4**: chạy thí nghiệm đầy đủ (mặc định N=4,8,16,32,64 và 20 trials mỗi cấu hình), ghi `results/raw.csv` và `results/summary.csv`.
- Chọn **0**: thoát.

## Tổ chức

- **`board.py`** — `NQueens` (kiểm tra nghiệm, vẽ bàn cờ ASCII) và `Result` (kết quả thống nhất cho mọi solver: `solution`, `seconds`, `steps`, `attempts`).
- **`cnf.py`** — `CNFEncoder` sinh mệnh đề từ hàng, cột và hai họ đường chéo; `clause_count()` tính số mệnh đề theo công thức.
- **`sat_solver.py`** — `SATSolver` nạp CNF vào PySAT Glucose3, đo thời gian `solve()`, giải mã model và kiểm tra nghiệm.
- **`min_conflicts.py`** — `MinConflictsSolver` với hai cách chọn biến: chuẩn (ngẫu nhiên) và heuristic max-conflict (chọn hậu nhiều xung đột nhất).
- **`nqueens.py`** — re-export các lớp công khai để test và notebook import gọn.
- **`main.py`** — menu tương tác và hàm `benchmark()` gọi được từ notebook.
- **`test_nqueens.py`** — kiểm thử độc lập, gồm duyệt toàn bộ 65.536 phép gán của N=4 để đối chiếu CNF với luật bàn cờ.
- **`experiments.ipynb`** — notebook thực nghiệm (đã lưu output): bảng SAT, bảng Min-Conflicts 20 trials, đồ thị so sánh.
- **`REPORT.md`** — bản nháp nội dung báo cáo; bản chính thức là `report.pdf` theo template IEEE.

Sau khi chọn menu **4**, thư mục `results/` chứa:

- `raw.csv` — từng lần chạy: N, thuật toán, trial, seed, số clause, thời gian encode, success, seconds, steps, attempts.
- `summary.csv` — tổng hợp theo (N, thuật toán): success rate, mean/median/stdev thời gian, mean/median steps, số lượt phải restart.

## Quy ước

Nghiệm được biểu diễn bằng danh sách `rows`, trong đó `rows[c]` là hàng của quân hậu ở cột c; chỉ số bắt đầu từ 0. `Q` là hậu, `.` là ô trống.

Glucose3 có thể chứng minh UNSAT (N=2,3); Min-Conflicts hết ngân sách chỉ báo chưa tìm được nghiệm.

Giới hạn mặc định là 10.000 bước mỗi lần khởi tạo và tối đa 4 lần khởi động lại (5 lần khởi tạo tổng cộng).

## Quy trình thực nghiệm

Hai biến thể local search dùng cùng seed, ngân sách và quy tắc chọn hàng. Bộ sinh ngẫu nhiên để khởi tạo tách khỏi bộ sinh dùng khi chọn biến và phá hòa. Với cùng seed, mỗi lần khởi tạo có cùng trạng thái ở cả hai biến thể, kể cả khi các bước sửa trước đó khác nhau.

Thời gian local search gồm khởi tạo, kiểm tra và restart. Thời gian SAT chỉ đo `solve()`, không gồm sinh CNF, nạp mệnh đề hay giải mã. Vì vậy ưu tiên so sánh standard và max_conflict với nhau; không xem thời gian SAT là thời gian đầu-cuối.

Kết quả chi tiết nằm trong `experiments.ipynb` (đã lưu output) và trong `results/summary.csv` sau khi chọn menu 4.

Tài liệu API tham khảo: https://pysathq.github.io/docs/html/api/solvers.html
Min-Conflicts chuẩn được đối chiếu với slide 30 của tài liệu Lecture 08.