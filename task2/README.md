# Task 2: Adversarial Search — Pixel Tank Wars

Báo cáo và tài liệu hướng dẫn kỹ thuật cho Task 2 thuộc môn học Nhập môn Trí tuệ nhân tạo (Introduction to Artificial Intelligence).

Đồ án xây dựng trò chơi đối kháng chiến thuật Pixel Tank Wars trên lưới tọa độ hai chiều theo cơ chế theo lượt (turn-based), đồng thời hiện thực và so sánh hiệu năng các thuật toán tìm kiếm đối kháng (Adversarial Search): Minimax, Alpha-Beta Pruning kết hợp hàm đánh giá Heuristic và tối ưu sắp xếp thứ tự nước đi (Move Ordering).

---

## Cài đặt và khởi chạy

Yêu cầu môi trường Python phiên bản 3.10 trở lên.

Từ thư mục `task2`, tiến hành cài đặt thư viện phụ thuộc và chạy ứng dụng:

```bash
# Tạo và kích hoạt môi trường ảo (tùy chọn)
python -m venv .venv
# Trên Windows PowerShell:
.venv\Scripts\Activate.ps1
# Trên Linux/macOS:
# source .venv/bin/activate

# Cài đặt thư viện phụ thuộc (Pygame)
python -m pip install -r requirements.txt

# Khởi chạy menu chính (Console Menu)
python main.py
```

### Các phương thức khởi chạy khác

- Khởi chạy trực tiếp giao diện đồ họa Pygame:
  ```bash
  python gui.py
  ```

- Chạy trực tiếp chương trình Benchmark đánh giá thuật toán từ dòng lệnh:
  ```bash
  python experiment.py
  ```

- Xem và tái hiện các thực nghiệm đồ thị trực quan:
  Mở và thực thi sổ tay `experiments.ipynb` trong VS Code hoặc Jupyter Lab.

---

## Mô hình hóa trò chơi (Game Modeling)

Pixel Tank Wars được mô hình hóa dưới dạng trò chơi đối kháng hai người chơi tổng không bằng không với thông tin hoàn hảo (Deterministic, Turn-based, Perfect Information Game).

### Bản đồ và không gian trạng thái

- Kích thước lưới: 20 hàng x 20 cột (`GRID_ROWS = 20`, `GRID_COLS = 20`), gốc tọa độ `(0, 0)` tại góc trên bên trái.
- Các thực thể trên bàn cờ:
  - Tank (Xe tăng): Mỗi người chơi điều khiển một xe tăng. Máu tối đa 6 HP (`HP_TANK = 6`). Xe tăng có thuộc tính vị trí `(row, col)` và hướng nhìn `Direction` (UP, DOWN, LEFT, RIGHT).
  - Base (Căn cứ): Mỗi người chơi sở hữu một căn cứ cố định. Máu tối đa 9 HP (`HP_BASE = 9`). Căn cứ MAX nằm ở góc dưới phải `(18, 18)`, căn cứ MIN nằm ở góc trên trái `(1, 1)`.
  - Wall (Tường chắn): Vật cản có máu tối đa 3 HP (`HP_WALL = 3`). Tường cản trở di chuyển của xe tăng và chắn đạn đạo.
  - Bullet (Đạn pháo): Được sinh ra khi xe tăng thực hiện hành động bắn. Mỗi viên đạn mang 1 điểm sát thương (`BULLET_DAMAGE = 1`), bay theo hướng của xe tăng lúc bắn với vận tốc 3 ô/lượt (`BULLET_SPEED = 3`).

### Cơ chế lượt đi và va chạm

- Hai người chơi MAX và MIN luân phiên hành động.
- Trong một lượt, người chơi có thể chọn 1 trong 6 hành động (`Action`):
  - `MOVE_UP`: Quay hướng lên trên và di chuyển 1 ô nếu không bị cản.
  - `MOVE_DOWN`: Quay hướng xuống dưới và di chuyển 1 ô nếu không bị cản.
  - `MOVE_LEFT`: Quay hướng sang trái và di chuyển 1 ô nếu không bị cản.
  - `MOVE_RIGHT`: Quay hướng sang phải và di chuyển 1 ô nếu không bị cản.
  - `FIRE`: Giữ nguyên vị trí và bắn ra 1 viên đạn theo hướng hiện tại.
  - `STAY`: Giữ nguyên vị trí và hướng hiện tại.
- Di chuyển bị cản (`is_blocked`) khi ô đích vượt ra ngoài biên bản đồ hoặc đã bị chiếm dụng bởi tường, căn cứ hoặc xe tăng khác. Nếu bị cản, xe tăng đổi hướng nhìn nhưng không thay đổi tọa độ.
- Cập nhật đạn (`_move_bullets`): Sau khi người chơi MIN hoàn thành lượt đi, toàn bộ đạn trên bản đồ sẽ di chuyển đồng thời theo từng bước nhỏ (tối đa 3 bước ứng với tốc độ đạn). Nếu đạn trúng thực thể sống (xe tăng, tường, căn cứ), thực thể đó nhận sát thương và viên đạn biến mất. Nếu hai viên đạn cùng lao vào một ô, chúng triệt tiêu lẫn nhau.

### Điều kiện kết thúc và hàm Tiện ích (Utility Function)

Trạng thái kết thúc (`is_terminal`) đạt được khi xe tăng hoặc căn cứ của ít nhất một bên bị tiêu diệt hoàn toàn (`hp <= 0`).

Giá trị tiện ích trạng thái kết thúc (`get_utility(depth_remaining)`):
- MAX thắng (tiêu diệt xe tăng hoặc căn cứ của MIN): `+10000.0 + depth_remaining` (ưu tiên đường đi dẫn đến chiến thắng sớm hơn).
- MIN thắng (tiêu diệt xe tăng hoặc căn cứ của MAX): `-10000.0 - depth_remaining` (ưu tiên phòng thủ hoặc kéo dài ván đấu).
- Hòa (cả hai bên cùng bị hủy diệt trong cùng lượt cập nhật đạn): `0.0`.

---

## Thuật toán tìm kiếm đối kháng (Adversarial Search)

Dự án cài đặt 4 biến thể thuật toán tìm kiếm trên cây trò chơi trong module `agents/search_agent.py`:

### 1. Minimax chuẩn (`Minimax`)

Duyệt vét cạn toàn bộ cây trò chơi đến độ sâu giới hạn `max_depth`. Tại các nút lá không phải là trạng thái kết thúc (cutoff), nếu không có heuristic, thuật toán trả về điểm tiện ích trung hòa `0.0`. Do không gian trạng thái lớn ($b \approx 6$), thuật toán tốn nhiều tài nguyên khi tăng độ sâu.

### 2. Cắt tỉa Alpha-Beta chuẩn (`AlphaBeta`)

Cải tiến từ Minimax bằng cách duy trì hai ngưỡng $\alpha$ (giá trị tốt nhất mà MAX đảm bảo đạt được) và $\beta$ (giá trị tốt nhất mà MIN đảm bảo đạt được). Khi $\beta \le \alpha$, thuật toán lập tức cắt tỉa các nhánh con còn lại mà không cần mở rộng, giúp giảm đáng kể số nút cần duyệt trong khi vẫn bảo toàn nước đi tối ưu tương đương Minimax.

### 3. Minimax kết hợp Heuristic (`Minimax-Heuristic`)

Áp dụng hàm đánh giá Heuristic `evaluate()` tại các nút lá bị giới hạn độ sâu (cutoff nodes). Nhờ có hàm đánh giá, thuật toán có thể định lượng được ưu thế vị trí, lượng máu và thế cờ của mỗi bên dù chưa chạm đến trạng thái kết thúc.

### 4. Alpha-Beta kết hợp Heuristic và Move Ordering (`AlphaBeta-Heuristic`)

Biến thể hoàn thiện nhất của hệ thống, kết hợp ba kỹ thuật tối ưu:
- Giới hạn độ sâu và lượng giá trạng thái lá bằng Heuristic.
- Cắt tỉa Alpha-Beta loại bỏ nhánh thừa.
- Tối ưu thứ tự duyệt nước đi (Move Ordering): Các nước đi hợp lệ được đánh giá nhanh qua hàm Heuristic và sắp xếp theo thứ tự giảm dần đối với MAX, tăng dần đối với MIN trước khi đệ quy. Nhờ duyệt nước đi hứa hẹn nhất trước, điều kiện $\beta \le \alpha$ xảy ra sớm hơn, tối đa hóa tỷ lệ cắt tỉa nhánh.

---

## Thiết kế hàm đánh giá Heuristic (`evaluation.py`)

Hàm lượng giá $f(s)$ đánh giá trạng thái $s$ theo góc nhìn của MAX thông qua 4 thành phần trọng số:

$$f(s) = S_{\text{tank\_hp}} + S_{\text{base\_hp}} + S_{\text{position}} + S_{\text{bullet}}$$

1. Điểm sinh lực xe tăng ($S_{\text{tank\_hp}}$):
   $$S_{\text{tank\_hp}} = (\text{HP}_{\text{MAX\_Tank}} - \text{HP}_{\text{MIN\_Tank}}) \times 100$$
   Phản ánh trực tiếp tương quan lực lượng sống giữa hai xe tăng.

2. Điểm sinh lực căn cứ ($S_{\text{base\_hp}}$):
   $$S_{\text{base\_hp}} = (\text{HP}_{\text{MAX\_Base}} - \text{HP}_{\text{MIN\_Base}}) \times 200$$
   Căn cứ có hệ số trọng số cao hơn xe tăng vì mất căn cứ đồng nghĩa với thua trận ngay lập tức.

3. Điểm khoảng cách chiến thuật ($S_{\text{position}}$):
   Sử dụng thuật toán tìm kiếm theo chiều rộng (BFS) có trọng số phạt xuyên tường (`bfs_distance`):
   $$S_{\text{position}} = -15 \times d_{\text{BFS}}(\text{MAX\_Tank}, \text{MIN\_Base}) + 15 \times d_{\text{BFS}}(\text{MIN\_Tank}, \text{MAX\_Base})$$
   Khoảng cách được tính toán có tính đến việc bắn phá tường chắn (mỗi bức tường chắn trên đường đi làm tăng chi phí thêm 10), khuyến khích xe tăng MAX tiếp cận căn cứ đối phương và gây áp lực phòng thủ lên MIN.

4. Điểm nguy cơ đạn đạo ($S_{\text{bullet}}$):
   Mô phỏng trước quỹ đạo các viên đạn đang bay trên lưới trong phạm vi `BULLET_SPEED = 3` ô. Nếu viên đạn của MAX có đường bay trực tiếp hướng vào xe tăng hoặc căn cứ của MIN, điểm số được cộng tương ứng $+50$ hoặc $+100$. Ngược lại, nếu đạn của MIN nhắm vào MAX, điểm số bị trừ tương ứng.

---

## Cấu trúc thư mục dự án

```text
task2/
├── agents/
│   ├── base_agent.py          # Lớp trừu tượng BaseAgent định nghĩa cấu trúc Agent
│   └── search_agent.py        # Cài đặt Minimax, AlphaBeta, và các biến thể Heuristic
├── assets/
│   ├── sounds/                # Hiệu ứng âm thanh và nhạc nền (WAV, MP3)
│   ├── base_max.png           # Sprite căn cứ MAX
│   ├── base_min.png           # Sprite căn cứ MIN
│   ├── bullet.png             # Sprite đạn pháo
│   ├── explosion.png          # Sprite hiệu ứng phát nổ
│   ├── tank_max.png           # Sprite xe tăng MAX
│   └── tank_min.png           # Sprite xe tăng MIN
├── agent_loader.py            # Hàm nạp và khởi tạo Agent theo Enum cấu hình
├── config.py                  # Các hằng số trò chơi, Enum hành động, hướng và người chơi
├── entities.py                # Lớp đối tượng thực thể: Entity, Tank, Base, Wall, Bullet
├── evaluation.py              # Hàm đánh giá Heuristic và thuật toán khoảng cách BFS
├── experiment.py              # Kịch bản mô phỏng đối đầu và đo lường benchmark
├── experiments.ipynb          # Sổ tay Jupyter trực quan hóa số liệu thực nghiệm
├── game_state.py              # Quản lý trạng thái trò chơi, tính hợp lệ và chuyển trạng thái
├── gui.py                     # Giao diện đồ họa Pygame hoàn chỉnh (chơi và trực quan hóa)
├── main.py                    # Điểm vào chương trình (Console Menu chính)
├── README.md                  # Tài liệu hướng dẫn kỹ thuật chi tiết
└── requirements.txt           # Danh mục thư viện phụ thuộc của dự án
```

---

## Hướng dẫn sử dụng các chế độ

### 1. Menu điều khiển dòng lệnh (`main.py`)

Khi chạy `python main.py`, bảng chọn hiển thị 3 tùy chọn:
- Phím `1`: Khởi động giao diện game đồ họa.
- Phím `2`: Chạy Benchmark thuật toán trên Terminal (cho phép nhập tham số `Depth` và `Max Steps`).
- Phím `0`: Thoát ứng dụng.

### 2. Giao diện đồ họa tương tác (`gui.py`)

Giao diện cung cấp màn hình Menu và màn hình thi đấu:
- Màn hình Menu:
  - Chọn chế độ chơi: `User vs AI` (Người chơi điều khiển MAX, AI điều khiển MIN) hoặc `AI vs AI` (Hai thuật toán AI tự động đấu với nhau).
  - Tùy chọn thuật toán cho từng bên: Minimax, AlphaBeta, Minimax-Heuristic, AlphaBeta-Heuristic.
  - Nhấn `START GAME` để vào trận đấu.
- Điều khiển trong chế độ `User vs AI`:
  - Phím `W`: Di chuyển / quay hướng lên trên.
  - Phím `S`: Di chuyển / quay hướng xuống dưới.
  - Phím `A`: Di chuyển / quay hướng sang trái.
  - Phím `D`: Di chuyển / quay hướng sang phải.
  - Phím `Space`: Bắn đạn.
- Bảng điều khiển bên phải (Sidebar):
  - Hiển thị lượt đi hiện tại, máu xe tăng hai bên.
  - Hành động vừa thực hiện gần nhất của MAX và MIN.
  - Thống kê thời gian thực của lượt đi AI: Số nút mở rộng (`Nodes Expanded`), số nhánh bị cắt (`Pruned Branches`), thời gian suy nghĩ (`Think Time` theo mili-giây).
  - Các nút điều khiển: `Pause / Resume` (Tạm dừng/Tiếp tục), `Step` (Thực hiện từng nước đi thủ công), `Toggle Auto Play` (Bật/Tắt tự động chạy), `Back to Menu`.

---

## Tóm tắt kết quả thực nghiệm

Kết quả trích xuất từ các kịch bản kiểm thử trong `experiments.ipynb`:

| Thuật toán | Độ sâu (Depth) | Số bước hoàn thành | Kết quả | Thời gian tb (ms/nước) | Nút duyệt/bước (Nodes) | Số nhánh cắt tỉa/bước |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Minimax | 3 | 4156 | MAX Thắng | 7.53 | 258.9 | 0.0 |
| AlphaBeta | 3 | 3160 | MAX Thắng | 2.45 | 59.0 | 10.0 |
| Minimax-Heuristic | 3 | 86 | MAX Thắng | 926.47 | 255.7 | 0.0 |
| AlphaBeta-Heuristic | 3 | 84 | MAX Thắng | 326.05 | 58.5 | 9.9 |

### Nhận xét đánh giá

1. Hiệu quả cắt tỉa của Alpha-Beta:
   Ở cùng độ sâu tìm kiếm, Alpha-Beta giúp giảm số lượng nút cần mở rộng khoảng 4 đến 5 lần so với Minimax thông thường (từ ~258 nút xuống ~59 nút ở độ sâu 3), kéo theo thời gian thực thi giảm tương ứng.
2. Vai trò định hướng của Heuristic:
   Các thuật toán không sử dụng Heuristic mất hàng nghìn bước di chuyển ngẫu nhiên mới vô tình tạo ra đột biến tiêu diệt mục tiêu. Trong khi đó, biến thể kết hợp Heuristic định hướng đường đi rõ rệt, kết thúc trận đấu chỉ sau khoảng 84 đến 86 bước.
3. Tác dụng của Move Ordering:
   Việc sắp xếp nước đi theo Heuristic sơ bộ cho phép Alpha-Beta loại bỏ sớm các nhánh bất lợi, giữ tốc độ duyệt ổn định ngay cả khi tăng độ sâu tìm kiếm.
