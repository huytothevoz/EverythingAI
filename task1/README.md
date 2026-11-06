# Task 1: Local Search & Propositional Logic

Giải bài toán N quân hậu theo hướng đối tượng. Bài làm nằm trong thư mục này; PDF đề gốc được giữ nguyên.

## Cài đặt và chạy

Yêu cầu Python 3.10 trở lên. Từ thư mục `source/task1`:

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py solve -n 8 --algorithm glucose3
python main.py solve -n 32 --algorithm standard --seed 2026
python main.py solve -n 32 --algorithm max_conflict --seed 2026
python main.py benchmark --sizes 4 8 16 32 64 --trials 20
python -m unittest discover -v
```

Gói cần cài là **python-sat**, không phải gói `pysat` có cùng tên import nhưng mục đích khác.
Các lệnh chạy độc lập trên Windows/macOS, không có đường dẫn máy cá nhân trong mã.

## Tổ chức

- `nqueens.py`: `NQueens` kiểm tra/vẽ bàn cờ; `CNFEncoder` sinh CNF; `SATSolver` gọi Glucose3; `MinConflictsSolver` tìm kiếm cục bộ.
- `main.py`: giao diện dòng lệnh và thí nghiệm.
- `test_nqueens.py`: kiểm thử độc lập, gồm duyệt toàn bộ 65.536 phép gán của N=4 để đối chiếu CNF với luật bàn cờ.
- `REPORT.md`: mô hình, thuật toán và phân tích số liệu thực đo.
- `results/raw.csv`: từng lần chạy, seed, nghiệm, thời gian, số bước và số lần khởi tạo.
- `results/summary.csv`: tỷ lệ thành công, trung bình, trung vị, độ lệch chuẩn và số bước trung bình.
- `results/environment.json`: môi trường và tham số thí nghiệm.

Nghiệm được biểu diễn bằng danh sách `rows`, trong đó `rows[c]` là hàng của quân hậu ở cột c; chỉ số bắt đầu từ 0. `Q` là hậu, `.` là ô trống.
Glucose3 có thể chứng minh UNSAT (N=2,3); Min-Conflicts hết ngân sách chỉ báo chưa tìm được nghiệm.
Giới hạn mặc định là 10.000 bước mỗi lần khởi tạo và tối đa 4 lần khởi động lại (5 lần khởi tạo tổng cộng).

## Quy trình thực nghiệm

Hai biến thể local search có cùng seed, khởi tạo ngẫu nhiên, ngân sách, cách chọn giá trị và quy tắc phá hòa. Chỉ cách chọn biến khác nhau. Với cùng seed, trạng thái khởi tạo đầu tiên giống nhau; sau khi hai thuật toán đi khác hướng, chuỗi lựa chọn cũng có thể khác nhau. Không bảo đảm heuristic thắng trên mọi N.
Thời gian local search gồm khởi tạo, kiểm tra và restart. Thời gian SAT chỉ đo `solve()`, không gồm sinh CNF, nạp mệnh đề hay giải mã. Vì vậy ưu tiên so sánh standard và max_conflict với nhau; không xem thời gian SAT là thời gian đầu-cuối.

Tài liệu API tham khảo: https://pysathq.github.io/docs/html/api/solvers.html
Chưa có tài liệu Lecture 08 trong thư mục nên cài đặt dùng Min-Conflicts chuẩn: chọn ngẫu nhiên một biến đang xung đột, rồi chọn giá trị gây ít xung đột nhất; phá hòa ngẫu nhiên.
