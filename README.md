# Đồ án cuối kỳ — Introduction to Artificial Intelligence

Hướng dẫn cài đặt và sử dụng mã nguồn cho ba task của đồ án. Mã nguồn được tổ chức theo từng task; các lớp và module trong mỗi task chịu trách nhiệm cho dữ liệu, thuật toán và giao diện tương ứng.

## Yêu cầu môi trường và cài đặt

- Python 3.10 trở lên.
- Các thư viện được khai báo tập trung trong [`requirement.txt`](./requirement.txt).
- Pygame cần cho giao diện Task 2 và Task 3; `python-sat` cần cho Glucose3 ở Task 1; Matplotlib cần cho notebook Task 1.

Từ thư mục gốc của source:

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Cài các dependency một lần:

```bash
python -m pip install -r requirement.txt
```

## Cấu trúc thư mục

```text
.
├── requirement.txt
├── README.md
├── main.py
├── task1/
│   ├── task1.py
│   ├── experiments.ipynb
├── task2/
│   ├── task2.py
│   ├── agents/
│   ├── assets/
│   └── experiments.ipynb
└── task3/
    ├── task3.py
    └── experiments.ipynb
```

Mỗi thư mục `taskN/` chứa source và notebook thực nghiệm của task đó. Mở notebook trong VS Code/Jupyter và chạy các cell theo thứ tự; dùng thư mục của task làm working directory nếu notebook yêu cầu import module cùng thư mục.

## Task 1 — Local Search & Propositional Logic: N-Queens

Chạy launcher `python main.py` từ thư mục gốc và chọn Task 1, hoặc chạy riêng `python task1.py` trong thư mục `task1`.

### Nội dung

- Mỗi ô bàn cờ là một biến Boolean; bộ mã hóa CNF thể hiện các điều kiện đặt hậu, không trùng hàng/cột và không tấn công trên đường chéo.
- `CNFEncoder` sinh CNF; `SATSolver` gọi Glucose3 của `python-sat`, giải mã và xác nhận nghiệm.
- `MinConflictsSolver` cung cấp Min-Conflicts chuẩn và biến thể heuristic max-conflict (ưu tiên quân hậu đang có nhiều xung đột).
- `NQueens` quản lý bài toán và kiểm tra/hiển thị nghiệm.

### Chạy chương trình và kiểm thử

Menu cho phép giải bằng Glucose3, Min-Conflicts chuẩn, Min-Conflicts max-conflict hoặc chạy benchmark. Benchmark mặc định dùng `N = 4, 8, 16, 32, 64`, 20 lượt cho mỗi cấu hình; kết quả mới được ghi vào `task1/benchmark-output/`.

Chạy unit test từ thư mục task:

```powershell
cd task1
python -m unittest discover -v
```

Notebook [`task1/experiments.ipynb`](./task1/experiments.ipynb) trình bày kết quả SAT và Min-Conflicts, bảng số liệu và biểu đồ. Dữ liệu báo cáo được lưu trong `task1/results/` (`raw.csv`, `summary.csv`, `environment.json`); nội dung báo cáo tham khảo nằm trong `task1/note/REPORT.md`.

### Thực nghiệm và quy ước

Hai biến thể Min-Conflicts dùng chung seed, ngân sách và trạng thái khởi tạo để đối chiếu công bằng. Thời gian SAT chỉ đo lời gọi `solve()`, không bao gồm sinh/nạp CNF hay giải mã; thời gian Min-Conflicts gồm khởi tạo, kiểm tra và restart. Kích thước `N=2,3` là UNSAT đối với N-Queens; benchmark yêu cầu `N >= 4`. Kết quả phụ thuộc môi trường chạy.

## Task 2 — Adversarial Search: Pixel Tank Wars

Chạy `python main.py` từ thư mục gốc và chọn Task 2, hoặc chạy riêng `python task2.py` trong thư mục `task2`.

### Mô hình trò chơi

Game theo lượt trên lưới 20×20, hai bên MAX/MIN, thông tin hoàn hảo. Xe tăng có 6 HP, căn cứ 9 HP, tường 3 HP; đạn gây 1 sát thương và di chuyển tối đa 3 ô mỗi chu kỳ. Các hành động gồm di chuyển lên/xuống/trái/phải, đứng yên và bắn. Trò chơi kết thúc khi xe tăng hoặc căn cứ bị phá hủy.

Các thành phần game được tổ chức thành các lớp trạng thái/thực thể/agent. Hàm heuristic đánh giá HP xe tăng, HP căn cứ, khoảng cách BFS có tính đến tường và nguy cơ đường đạn.

### Thuật toán và thực nghiệm

Bốn cấu hình được so sánh: Minimax, Alpha-Beta, Minimax-Heuristic và Alpha-Beta-Heuristic. Alpha-Beta cắt nhánh theo ngưỡng alpha/beta; biến thể heuristic đánh giá trạng thái tại giới hạn độ sâu; Alpha-Beta-Heuristic sắp xếp nước đi theo heuristic để tăng cơ hội cắt tỉa. Notebook [`task2/experiments.ipynb`](./task2/experiments.ipynb) và `task2/experiment.py` ghi nhận thời gian, số node, nhánh bị cắt, số bước và kết quả trận đấu. Thời gian phụ thuộc độ sâu và cấu hình máy.

### Khởi chạy

Menu cho phép mở GUI hoặc chạy benchmark. Chạy riêng các công cụ từ thư mục `task2`:

```bash
cd task2
python task2.py
python gui.py
python experiment.py
```

GUI hỗ trợ User vs AI và AI vs AI, chọn thuật toán cho mỗi bên, tạm dừng/tiếp tục, đi từng bước và bật/tắt tự động. Trong User vs AI, dùng `W`, `A`, `S`, `D` để di chuyển/quay hướng và `Space` để bắn. Sidebar hiển thị lượt, HP và thống kê tìm kiếm.

## Task 3 — Constraint Satisfaction Problems: Kakuro

Chạy `python main.py` từ thư mục gốc và chọn Task 3, hoặc chạy riêng `python task3.py` trong thư mục `task3`.

### Mô hình và bộ giải

- **Variables:** mỗi ô trắng, biểu diễn bằng tọa độ `(row, column)`.
- **Domains:** các chữ số `{1, ..., 9}` (ô cho sẵn, nếu có, được cố định).
- **Constraints:** mỗi run ngang/dọc phải có tổng bằng clue và không lặp chữ số (`AllDifferent`); các run giao nhau dùng chung biến.

`KakuroCSP` định nghĩa mô hình và constraint graph. `KakuroSolver` hỗ trợ GAC cho ràng buộc n-ary, Forward Checking, backtracking cùng MRV, Degree và LCV. GAC dùng hàng đợi revise theo ý tưởng AC-3; đây không phải AC-3 nhị phân tiêu chuẩn. Mọi nghiệm trả về được xác nhận bằng `validate_solution()`.

### Chạy và quan sát

Chọn **Play Game** để tự chơi hoặc **AI Solver** để quan sát. GUI hiển thị pencil marks/miền, propagation, gán số, mâu thuẫn và quay lui; có Start, Pause/Resume, Step, Reset và tùy chọn propagation/heuristic.

Chạy benchmark dòng lệnh:

```bash
python task3/eval_benchmark.py
```

Notebook [`task3/experiments.ipynb`](./task3/experiments.ipynb) mô tả mô hình, so sánh GAC với Forward Checking trên bảng 9×9, chạy lặp và lưu output làm dữ liệu báo cáo. Benchmark không bao gồm chế độ không propagation trên bảng lớn vì có thể rất chậm. Thời gian đo thay đổi theo CPU/Python.
