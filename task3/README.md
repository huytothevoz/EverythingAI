# KAKURO — CSP PUZZLE SOLVER

Đồ án Task 3 cho môn **503043 — Introduction to Artificial Intelligence**.
Ứng dụng Python/Pygame có hai chế độ độc lập: người chơi tự giải Kakuro
(Play Game) và quan sát bộ giải CSP hoạt động (AI Solver).

## Luật Kakuro

- Mỗi ô trắng nhận một chữ số từ 1 đến 9.
- Mỗi clue chỉ tổng các ô trắng trong run ngang hoặc dọc tương ứng.
- Trong cùng một run, không được lặp chữ số.
- Run chưa điền đủ vẫn có thể hợp lệ nếu các giá trị đã nhập còn có cách
  hoàn tất thỏa tổng và điều kiện không lặp.
- Run hoàn tất khi mọi ô được điền và tổng đúng clue.

Play Mode kiểm tra khả năng hỗ trợ của các bộ giá trị hợp lệ cho từng run;
không gọi bộ giải CSP để điền bảng.

## Mô hình hóa CSP

- **Variables:** mỗi ô trắng, biểu diễn bằng tọa độ `(row, column)`.
- **Domains:** ban đầu mỗi ô có các giá trị `{1, 2, ..., 9}`.
- **Constraints:** mỗi run ngang/dọc phải có tổng bằng clue và các chữ số
  trong run phải khác nhau. Mỗi run là ràng buộc nhiều biến (n-ary).

Solver liệt kê các bộ giá trị hợp lệ của mỗi run rồi dùng chúng khi lan truyền:

1. **Constraint Propagation:** GAC loại khỏi miền giá trị không có hỗ trợ
   trong bộ giá trị hợp lệ của run. Hàng đợi được cập nhật theo ý tưởng
   queue/revise của AC-3, nhưng ràng buộc Kakuro là n-ary chứ không phải AC-3
   nhị phân thông thường.
2. **Forward Checking:** sau khi gán một biến, kiểm tra các run liên quan và
   loại giá trị không còn hỗ trợ ở các ô chưa gán trong run đó.
3. **Backtracking Search:** lần lượt thử giá trị; khi phát hiện mâu thuẫn,
   quay lui và thử nhánh khác.
4. **MRV (Minimum Remaining Values):** ưu tiên biến có miền nhỏ nhất để sớm
   phát hiện nhánh khó/mâu thuẫn.
5. **Degree heuristic:** khi MRV hòa, ưu tiên biến có nhiều láng giềng chưa
   gán nhất.
6. **LCV (Least Constraining Value):** thử trước giá trị loại ít lựa chọn
   khỏi miền của các biến láng giềng nhất.

## Chạy ứng dụng

Từ thư mục `task3`:

```bash
python -m pip install -r requirements.txt
python main.py
```

Menu chính gồm **Play Game**, **AI Solver**, **How to Play**, **About Project**
và **Exit**. Từ các màn hình chơi/giải, dùng **Chọn chế độ** hoặc Escape để
quay lại menu.

### Play Game

- Click ô trắng hoặc dùng các phím mũi tên để chọn; nhấn `1`–`9` ở hàng số
  hoặc bàn phím số phụ để nhập trực tiếp từ bàn phím.
- `Backspace`/`Delete` xóa số; `N` bật/tắt ghi chú.
- Dùng **Check**, **Hint**, **Undo**, **Clear** và **Restart** trên thanh công cụ.
- Hint chỉ nêu một suy luận cục bộ dựa trên clue và ô còn thiếu; không điền số
  thay người chơi và không tiết lộ lời giải.
- Khi điền đủ ô và tất cả run hoàn tất hợp lệ, ứng dụng báo chiến thắng, thời
  gian chơi và số lần Check/Hint.

### AI Solver

- Puzzle 9×9 và clue được lấy trực tiếp từ `make_assignment_board()` trong
  `boards.py`.
- Chọn propagation: GAC, Forward Checking hoặc None; bật/tắt MRV, Degree, LCV.
- **Start**, **Pause/Resume**, **Step**, **Reset** và thanh tốc độ điều khiển
  việc phát sự kiện callback. Solver chạy trên worker thread để không khóa Pygame.
- Panel hiển thị domain, gán giá trị, mâu thuẫn, quay lui và `SolverStats` thật.
- Chế độ None có thể rất chậm trên bảng 9×9; dùng Reset để dừng và thử cấu hình
  khác.
- Cửa sổ AI Solver mở ở kích thước gọn 1280×720, tự giới hạn theo màn hình;
  chữ và bảng được bố trí để dễ đọc, giữ đúng tỉ lệ khi kéo đổi kích thước.

## Cấu trúc source

```text
task3/
├── main.py                 # Entry point, menu và điều hướng mode
├── kakuro_solver.py        # Mô hình CSP, propagation và backtracking
├── boards.py               # Puzzle đề bài 9×9 và puzzle demo 2×2
├── eval_benchmark.py       # Benchmark backend trên puzzle 9×9
├── kakuro_gui.py           # Giao diện và trực quan hóa AI Solver
├── kakuro_game.py          # Play Mode, luật chơi và trạng thái riêng
└── requirements.txt        # Pygame
```

Không cần asset hoặc đường dẫn tuyệt đối; font được chọn qua Pygame và hệ
thống thay bằng font mặc định nếu font yêu cầu không có. Mỗi giao diện tự
chọn kích thước cửa sổ khởi động theo màn hình; AI Solver dùng bố cục gọn,
chữ rõ hơn và giữ ô Kakuro vuông khi thay đổi kích thước.

## Kiểm tra và benchmark

Các bài test tự động đã được chạy trước khi xóa theo yêu cầu. Để tự chạy
benchmark CSP trên bảng 9×9:

```bash
python eval_benchmark.py
```

## Benchmark

Benchmark dùng `eval_benchmark.py` trên máy thực tế và phụ thuộc CPU/Python.
Không dùng thời gian benchmark làm tiêu chí tuyệt đối giữa các máy. Ghi lại
kết quả đã chạy:

| Cấu hình | Hợp lệ | Thời gian đo | Nodes | Assignments tried | Backtracks |
|---|---:|---:|---:|---:|---:|
| GAC + MRV + Degree + LCV | Có | 17,551.863 ms | 49 | 48 | 0 |
| Forward Checking + MRV + Degree + LCV | Có | 51,207.275 ms | 1,218 | 1,635 | 1,587 |

Đây là một lần chạy thực tế của `python eval_benchmark.py` trên Windows,
Python 3.12.10, Pygame 2.6.1; kết quả máy macOS/Intel có thể khác. Cả hai
cấu hình đều được xác nhận bằng `validate_solution()`. Benchmark lớn không chạy
chế độ None vì chế độ này không lan truyền miền và có thể tốn rất nhiều thời gian.
