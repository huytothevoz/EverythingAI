# I. Bài toán N quân hậu bằng logic mệnh đề và tìm kiếm cục bộ

## A. Phát biểu bài toán

Bài toán yêu cầu đặt đúng N quân hậu trên bàn N×N sao cho mọi cặp hậu nằm khác hàng, khác cột và khác đường chéo. Chỉ số hàng r và cột c bắt đầu từ 0. Hai ô khác nhau cùng đường chéo nếu chúng có cùng hiệu r−c hoặc cùng tổng r+c.

Xét N=4. Đặt hậu đầu tiên tại (0,2). Trên hàng 1, cột 2 đã có hậu và cột 1, 3 bị chiếu chéo, nên chọn (1,0). Trên hàng 2, cột 0, 2 đã có hậu và ô (2,1) bị hậu (1,0) chiếu chéo, nên chọn (2,3). Hàng cuối còn cột 1. Ô (3,1) khác đường chéo với ba hậu trước. Các giá trị r−c là (−2, 1, −1, 2) và r+c là (2, 1, 5, 4). Mỗi dãy có bốn giá trị phân biệt, xác nhận nghiệm dưới đây.

| Hàng / cột | 0 | 1 | 2 | 3 |
|---:|:---:|:---:|:---:|:---:|
| 0 | · | · | Q | · |
| 1 | Q | · | · | · |
| 2 | · | · | · | Q |
| 3 | · | Q | · | · |

*Hình 1. Vị trí bốn quân hậu trong nghiệm giải tay.*

## B. Cài đặt và tối ưu hóa

**Mô hình logic mệnh đề.** Chương trình dùng hai nhóm mệnh đề. Nhóm thứ nhất yêu cầu mỗi hàng có hậu. Nhóm thứ hai cấm mỗi cặp ô có thể tấn công nhau cùng chứa hậu.

Biến Boolean x(r,c) đúng khi ô (r,c) chứa hậu. Chương trình nhóm các ô theo hàng r, cột c và hai họ đường chéo r−c, r+c. Mỗi hàng có một mệnh đề tuyển tất cả biến trong hàng để buộc đặt ít nhất một hậu. Với mỗi cặp ô a,b trong cùng nhóm, điều kiện ¬(xₐ ∧ xᵦ) được chuyển theo De Morgan thành ¬xₐ ∨ ¬xᵦ. Hội của các mệnh đề tạo thành CNF. Ràng buộc hàng buộc có đúng N hậu. Ràng buộc cột và đường chéo loại mọi cặp tấn công còn lại. Theo chiều ngược lại, mọi bàn cờ hợp lệ thỏa toàn bộ mệnh đề.

PySAT đánh số biến bằng v(r,c)=rN+c+1. Với N=4, hàng đầu sinh [1,2,3,4]. Ví dụ cặp cùng hàng, cùng cột và cùng chéo lần lượt sinh [−1,−2], [−1,−5] và [−1,−6]. Mỗi hàng hoặc cột có C(4,2)=6 cặp. Một họ đường chéo có các độ dài 1,2,3,4,3,2,1 nên sinh 0+1+3+6+3+1+0=14 mệnh đề. Tổng cộng có 4+24+24+14+14=80 mệnh đề.

Với N bất kỳ, hai nhóm hàng và cột đóng góp 2N·C(N,2) mệnh đề cấm đôi. Mỗi họ đường chéo có một đường dài N và hai đường cho mỗi độ dài từ 1 đến N−1. Do đó, mỗi họ có C(N,2)+2·C(N,3) mệnh đề cấm đôi. Cộng thêm N mệnh đề yêu cầu mỗi hàng có hậu, ta được C(N)=N+N²(N−1)+N(N−1)(2N−1)/3. Gom nhóm tốn O(N²) thời gian. Liệt kê và lưu các mệnh đề cấm đôi tốn O(N³).

**Giải bằng Glucose3.** Lớp NQueens biểu diễn bàn cờ và kiểm tra nghiệm. CNFEncoder sinh mệnh đề và xuất DIMACS. SATSolver nạp CNF vào Glucose3 của PySAT, gọi solve() và lấy model khi công thức khả thỏa. Với literal dương ℓ, thương và dư của phép chia ℓ−1 cho N xác định hàng và cột. Chẳng hạn 12−1=2×4+3 xác định ô (2,3). Nghiệm giải tay ứng với các literal dương 3,5,12,14 và khớp kết quả Glucose3 ở lượt đầu với N=4.

**Min-Conflicts.** MinConflictsSolver biểu diễn biến q[c] là hàng của hậu ở cột c. Gọi g(c,t) là số hậu ở các cột khác tấn công ô hàng t, cột c. Tổng số cặp xung đột bằng một nửa tổng g(c,q[c]) trên tất cả các cột, vì mỗi cặp được đếm hai lần. Nghiệm đạt được khi tổng này bằng 0.

Theo Lecture 08, bản chuẩn chọn đều một cột có g(c,q[c])>0. Bản đề xuất chọn cột có g(c,q[c]) lớn nhất và phá hòa ngẫu nhiên. Sau khi chọn cột, cả hai gỡ hậu và chọn ngẫu nhiên một hàng t làm nhỏ nhất g(c,t). Vì hàng cũ cũng là một ứng viên, số cặp xung đột không tăng trong một bước sửa, nhưng có thể giữ nguyên. Chương trình dùng ba mảng đếm theo hàng và đường chéo để tính chi phí một ô trong O(1). Khi hậu vẫn còn trên bàn, phải trừ 3 để loại hậu đó khỏi cả ba bộ đếm. Mỗi bước quét N hậu và N hàng ứng viên, tốn O(N) thời gian và O(N) bộ nhớ. Khi hết ngân sách mà chưa tìm được nghiệm, chương trình trả về trạng thái tìm kiếm thất bại.

**Mô phỏng bằng tay.** Từ q=(1,3,3,2), điểm xung đột theo cột là (1,1,3,1). Hậu cột 2 cùng hàng với hậu cột 1, cùng đường chéo với hậu cột 0 và 3. Heuristic chọn cột 2. Sau khi gỡ hậu đó, chi phí theo hàng là (0,2,2,3). Chuyển đến hàng 0 cho nghiệm q=(1,3,0,2) sau một bước.

Bản chuẩn có thể chọn cột 0 trước, với chi phí (0,1,2,2), để tới (0,3,3,2). Tiếp theo, chọn cột 2, tính chi phí (1,1,3,2) và phá hòa bằng hàng 0 để tới (0,3,0,2). Cuối cùng, chọn cột 0, tính chi phí (1,0,3,1) và chuyển đến hàng 1 để đạt nghiệm. Nếu chọn cột 2 ngay đầu, bản chuẩn cũng có thể kết thúc sau một bước.

## C. Thí nghiệm và kết quả

Thực nghiệm chạy trên Windows 11, Python 3.12.6 và python-sat 1.9.dev17. Mỗi cấu hình chạy 20 lượt ở N=4, 8, 16, 32, 64. Mỗi lượt SAT tạo mới Glucose3 và chỉ đo thời gian solve() sau khi nạp CNF. Hai biến thể Min-Conflicts dùng các seed 2026–2045 và cùng chuỗi bàn khởi tạo, kể cả sau restart. Mỗi lần khởi tạo có tối đa 10.000 bước và mỗi lượt có tối đa 4 lần khởi động lại. Thời gian Min-Conflicts bao gồm khởi tạo và restart. Cả ba cấu hình tìm được nghiệm hợp lệ ở 20/20 lượt cho mỗi kích thước.

**Bảng I. Số mệnh đề và thời gian Glucose3**

| N | Số biến | Số mệnh đề | Thời gian trung bình (ms) |
|---:|---:|---:|---:|
| 4 | 16 | 80 | 0,0062 |
| 8 | 64 | 736 | 0,0344 |
| 16 | 256 | 6.336 | 1,0878 |
| 32 | 1.024 | 52.608 | 12,9204 |
| 64 | 4.096 | 428.800 | 152,6832 |

**Bảng II. Kết quả trung bình của Min-Conflicts chuẩn và max-conflict**

| N | Chuẩn (ms) | Max (ms) | Chuẩn (bước) | Max (bước) |
|---:|---:|---:|---:|---:|
| 4 | 0,0416 | 0,0447 | 7,40 | 7,55 |
| 8 | 3,5220 | 5,8855 | 1.103,15 | 1.575,45 |
| 16 | 0,5442 | 6,1647 | 95,60 | 1.084,65 |
| 32 | 0,9424 | 0,8170 | 97,15 | 77,40 |
| 64 | 2,2594 | 2,0700 | 127,25 | 112,00 |

**Kiểm chứng.** Số mệnh đề trong Bảng I khớp công thức C(N). Với N=4, nhóm duyệt toàn bộ 65.536 phép gán Boolean và đối chiếu giá trị CNF với luật bàn cờ. Kiểm thử Min-Conflicts tái hiện đúng bước chuyển của heuristic với ngân sách một bước. Các nghiệm từ cả 300 lượt thực nghiệm đều được kiểm tra theo hàng, cột và đường chéo.

**Phân tích.** Bảng II cho thấy heuristic giảm khoảng 20,3% số bước trung bình ở N=32 và 12,0% ở N=64. So theo từng cặp cùng seed, heuristic dùng ít bước hơn ở 13/20 và 11/20 lượt tương ứng. Ở N=16, trung vị giảm từ 84 xuống 61 bước, nhưng hai lượt heuristic phải khởi động lại, làm trung bình tăng từ 95,60 lên 1.084,65 bước. Chênh lệch giữa trung vị và trung bình cho thấy các lượt chậm có ảnh hưởng lớn tới kết quả. Thời gian SAT và Min-Conflicts đo các giai đoạn khác nhau, nên hai bảng lần lượt dùng để quan sát Glucose3 khi tăng N và so sánh hai quy tắc chọn biến. Số đo hiện tại áp dụng cho cấu hình Windows đã thử.

**Tài liệu tham khảo cho mục này**

- N. T. An, “Constraint Satisfaction,” Lecture 08, Introduction to Artificial Intelligence, Trường Đại học Tôn Đức Thắng, 2026, slide 29–31.
- N. T. An, “Logical Agents,” Lecture 09, Introduction to Artificial Intelligence, Trường Đại học Tôn Đức Thắng, 2026, slide 27.
