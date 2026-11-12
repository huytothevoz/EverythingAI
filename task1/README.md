# Task 1: Local Search & Propositional Logic

Giải bài toán N quân hậu theo hướng đối tượng. Bài làm nằm trong thư mục này; PDF đề gốc được giữ nguyên.

## Cài đặt và chạy

Yêu cầu Python 3.10 trở lên. Mở thư mục chứa `main.py`
(`task1/` trong Git, `source/task1/` trong workspace gốc).

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py cnf -n 4 --output n4.cnf
python main.py solve -n 8 --algorithm glucose3
python main.py solve -n 32 --algorithm standard --seed 2026
python main.py solve -n 32 --algorithm max_conflict --seed 2026
python main.py benchmark --sizes 4 8 16 32 64 --trials 20
python main.py benchmark --algorithms standard max_conflict --output local-results
python -m unittest discover -v
```

Gói cần cài là **python-sat**, không phải gói `pysat` có cùng tên import nhưng mục đích khác.
Các lệnh chạy độc lập trên Windows/macOS, không có đường dẫn máy cá nhân trong mã.

## Tổ chức

Chạy `python queen_app.py` để mở app minh họa hoặc mở `Task1.exe` nếu đã tải bản Windows. App dùng quay lui cho bàn chữ nhật. Các yêu cầu Glucose3 và Min-Conflicts được chạy bằng lệnh bên dưới.

Mỗi phần là một file Python có lệnh chạy trực tiếp. Từ thư mục `task1`:

```sh
python cnf.py -n 4 --output n4.cnf
python sat_solver.py -n 4
python sat_solver.py benchmark --output sat-results
python min_conflicts.py -n 4 --algorithm standard
python min_conflicts.py -n 4 --algorithm max_conflict
python min_conflicts.py -n 4 --algorithm max_conflict --initial-rows 1 3 3 2 --steps 1 --restarts 0
python min_conflicts.py benchmark --output local-results
```

Hai lệnh benchmark mặc định chạy 20 lượt cho mỗi kích thước từ N=4 đến N=64. Lệnh với `--initial-rows` tái hiện ví dụ giải tay, trả về `[1, 3, 0, 2]` sau một bước.

- `cnf.py` sinh mệnh đề từ hàng, cột và đường chéo, đếm mệnh đề và xuất DIMACS. Bàn 4×4 xuất dòng đầu `p cnf 16 80`.
- `sat_solver.py` nạp CNF vào PySAT, đo thời gian giải và đọc nghiệm.
- `min_conflicts.py` triển khai cách chọn biến chuẩn và heuristic.
- `board.py` định nghĩa bàn cờ và kết quả. `nqueens.py` cung cấp các lớp cho lệnh chạy và bộ kiểm thử.
- `main.py`: giao diện dòng lệnh và thí nghiệm.
- `test_nqueens.py`: kiểm thử độc lập, gồm duyệt toàn bộ 65.536 phép gán của N=4 để đối chiếu CNF với luật bàn cờ.
- `REPORT.md`: nội dung báo cáo có thể chèn vào Word của nhóm. `latex/main.tex` là bản IEEE hai cột tự chứa.
- `results/raw.csv`: từng lần chạy, seed, nghiệm, thời gian, số bước và số lần khởi tạo.
- `results/summary.csv`: tỷ lệ thành công, thời gian trung bình, trung vị và độ lệch chuẩn, số bước trung bình và trung vị, số lượt phải khởi động lại.
- `results/environment.json`: môi trường và tham số thí nghiệm.

Nghiệm được biểu diễn bằng danh sách `rows`, trong đó `rows[c]` là hàng của quân hậu ở cột c; chỉ số bắt đầu từ 0. `Q` là hậu, `.` là ô trống.
Glucose3 có thể chứng minh UNSAT (N=2,3); Min-Conflicts hết ngân sách chỉ báo chưa tìm được nghiệm.
Giới hạn mặc định là 10.000 bước mỗi lần khởi tạo và tối đa 4 lần khởi động lại (5 lần khởi tạo tổng cộng).

## Quy trình thực nghiệm

Hai biến thể local search dùng cùng seed, ngân sách và quy tắc chọn hàng. Bộ sinh ngẫu nhiên để khởi tạo tách khỏi bộ sinh dùng khi chọn biến và phá hòa. Với cùng seed, mỗi lần khởi tạo có cùng trạng thái ở cả hai biến thể, kể cả khi các bước sửa trước đó khác nhau.
Thời gian local search gồm khởi tạo, kiểm tra và restart. Thời gian SAT chỉ đo `solve()`, không gồm sinh CNF, nạp mệnh đề hay giải mã. Vì vậy ưu tiên so sánh standard và max_conflict với nhau; không xem thời gian SAT là thời gian đầu-cuối.

Tài liệu API tham khảo: https://pysathq.github.io/docs/html/api/solvers.html
Min-Conflicts chuẩn được đối chiếu với slide 30 của tài liệu Lecture 08 trong thư mục docs trên nhánh main.
