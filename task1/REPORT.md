# Task 1 - N quân hậu

## 1. Mô hình logic mệnh đề

Cho bàn cờ N × N. Biến Boolean x(r,c) đúng khi ô hàng r, cột c có hậu. Có N² biến; ánh xạ sang số nguyên dương dùng cho PySAT là v(r,c)=rN+c+1. Literal âm biểu diễn phủ định.

Ràng buộc:

1. Mỗi hàng có ít nhất một hậu: OR theo c của x(r,c).
2. Mỗi hàng có nhiều nhất một hậu: với mỗi cặp c<d, thêm NOT x(r,c) OR NOT x(r,d).
3. Mỗi cột có nhiều nhất một hậu: với mỗi cặp r<s, thêm NOT x(r,c) OR NOT x(s,c).
4. Mỗi đường chéo có nhiều nhất một hậu: nhóm các ô theo r-c và theo r+c; với mỗi cặp ô trong nhóm, thêm mệnh đề phủ định đôi tương tự.

Lấy AND của toàn bộ mệnh đề. Các ràng buộc đã ở dạng CNF: một hội của các tuyển. Quy tắc không cùng đúng xuất phát từ NOT(a AND b), dùng De Morgan thành NOT a OR NOT b. Không cần biến phụ hay chuyển đổi Tseitin.

N hàng, mỗi hàng đúng một hậu cho đúng N hậu. N hậu nằm trên N cột, mỗi cột nhiều nhất một hậu, nên mỗi cột cũng đúng một hậu. Do đó không cần thêm tuyển dương cho cột. Mọi nghiệm CNF là một bàn cờ hợp lệ và mọi bàn cờ hợp lệ thỏa CNF.

Thuật toán phát hiện ràng buộc duyệt hàng, cột và hai họ đường chéo, rồi liệt kê các cặp không thứ tự trong mỗi nhóm. Các đường chéo cùng họ có độ dài 1,2,...,N-1,N,N-1,...,1.

Số mệnh đề chính xác:

`C(N) = N + 2N*C(N,2) + 2*[C(N,2) + 2*sum(C(k,2), k=1..N-1)]`

`     = N + N²(N-1) + N(N-1)(2N-1)/3`.

Trong biểu thức đầu, C(a,2) là tổ hợp chập hai, không phải hàm đếm mệnh đề. Dùng pairwise encoding có kích thước O(N³). Cài đặt hiện tại gom cả hai họ đường chéo trong một lượt O(N²). Thời gian sinh mệnh đề vẫn là O(N³) vì phải liệt kê tất cả cặp.

## 2. Glucose3

CNF được truyền qua `Glucose3(bootstrap_with=clauses)`. Gọi `solve()` và dùng `get_model()` để lấy literal dương, chuyển về tọa độ. Đo thời gian bằng đồng hồ đơn điệu `perf_counter`. Đếm mệnh đề từ CNF gốc, không dùng số mệnh đề nội bộ sau tiền xử lý. Mọi nghiệm đều được kiểm tra bằng quy tắc quân hậu độc lập với bộ mã hóa.

Tham khảo API chính thức: https://pysathq.github.io/docs/html/api/solvers.html

## 3. Min-Conflicts và heuristic chọn biến

Dùng một biến q[c] cho mỗi cột với miền 0..N-1. Cách biểu diễn luôn bảo đảm mỗi cột một hậu. Khởi tạo mỗi biến bằng một hàng ngẫu nhiên. Đếm số hậu trên từng hàng và hai đường chéo bằng ba mảng bộ đếm.

Ở mỗi bước, tính số hậu tấn công từng quân. Standard chọn đều ngẫu nhiên trong các quân đang xung đột. Heuristic **max-conflict** chọn quân có số xung đột lớn nhất; nếu nhiều quân bằng nhau, chọn ngẫu nhiên. Trực giác là ưu tiên quân liên quan đến nhiều vi phạm. Đây không phải bảo đảm cải thiện vì lựa chọn tham lam có thể lặp trên vùng bằng phẳng.

Sau khi chọn cột, tạm gỡ quân khỏi bộ đếm. Tính chi phí của từng hàng bằng tổng ba bộ đếm rồi chọn ngẫu nhiên một hàng có chi phí nhỏ nhất. Cho phép chọn lại hàng cũ nếu cùng tối ưu. Đặt quân lại và cập nhật bộ đếm O(1). Đánh giá N quân và N hàng làm mỗi bước O(N), bộ nhớ O(N). Tổng số cặp tấn công bằng một nửa tổng số xung đột trên các quân.

Nếu đạt giới hạn bước thì khởi tạo lại ngẫu nhiên. Không tìm thấy sau ngân sách không suy ra vô nghiệm. Cả hai biến thể có cùng giới hạn và cách restart. Có thể dừng thành công ngay ở trạng thái cuối cùng sau bước sửa cuối, tránh bỏ sót nghiệm tại biên ngân sách.

## 4. Kiểm chứng và thực nghiệm

Các kiểm thử bao gồm SAT cho N=1,2,3,4,8,16; kiểm tra công thức số mệnh đề; duyệt toàn bộ phép gán Boolean N=4 so CNF với luật bàn cờ; kiểm tra nghiệm local search và tính tái lập của seed cho N=4,8,32; kiểm tra ngân sách trên N=3.

Thực nghiệm tăng N qua 4,8,16,32,64. Mỗi cấu hình 20 lần; seed 2026..2045. SAT dùng bộ giải mới mỗi lần. Bảng đo được sinh từ `results/summary.csv`, chi tiết từng lần nằm ở `results/raw.csv`. Thời gian trung bình gồm cả lần thất bại đối với local search; tỷ lệ thành công phải đọc kèm thời gian, không chỉ so những lần thành công. Số bước tính cả bước không đổi vị trí và tất cả restart.

Môi trường thực đo được lưu trong `results/environment.json`; không phải cấu hình macOS Intel i5 nêu trong đề. Cần chạy lại trên máy chấm khi muốn so sánh trực tiếp. Các lần chạy SAT là đo lặp hiệu năng, không đại diện cho 20 bài toán ngẫu nhiên độc lập. Không có chứng minh thống kê về ưu thế tổng quát của heuristic.

## 5. Kết quả thực đo

Thời gian dưới đây tính bằng mili giây, là trung bình của 20 lần chạy. Tất cả cấu hình trong bảng đạt 20/20 nghiệm hợp lệ.

| N | Số mệnh đề | Glucose3 (ms) | Standard (ms) | Max-conflict (ms) | Bước standard | Bước heuristic |
|---|---:|---:|---:|---:|---:|---:|
| 4 | 80 | 0.0055 | 0.0457 | 0.0417 | 12.25 | 9.90 |
| 8 | 736 | 0.0415 | 3.5216 | 4.3966 | 1064.15 | 1038.10 |
| 16 | 6336 | 1.1534 | 0.3610 | 3.3604 | 62.50 | 559.25 |
| 32 | 52608 | 13.9351 | 1.1433 | 1.0277 | 103.90 | 89.15 |
| 64 | 428800 | 163.0372 | 2.3392 | 1.9028 | 122.15 | 95.35 |

Ở N=64, heuristic giảm số bước trung bình từ 122,15 xuống 95,35 (khoảng 21,94%). Tuy nhiên ở N=16, heuristic tăng số bước từ 62,50 lên 559,25: một số lần chạy dài có thể chi phối trung bình. Vì thế heuristic chỉ có lợi trên một số kích thước của bộ thử, không vượt standard một cách nhất quán. Cần xem cả trung vị và độ lệch chuẩn trong CSV.

N=100 đã được thử nhưng dừng trước khi hoàn thành toàn bộ thí nghiệm vì thời gian chạy SAT dài; không đưa số liệu chưa hoàn chỉnh vào bảng. Mã hỗ trợ chạy thêm với `--sizes 100`. Trong lúc thu bảng này có một tiến trình thử N=100 chạy đồng thời, có thể gây nhiễu phép đo thời gian; số bước và tính hợp lệ của nghiệm không bị ảnh hưởng. Muốn lấy số liệu hiệu năng sạch để nộp, chạy lại benchmark khi máy rảnh.

## 6. Mức độ hoàn thành

Đã cài đặt mô hình CNF, Glucose3, Min-Conflicts chuẩn, heuristic chọn biến, kiểm tra độc lập và thí nghiệm tăng N. Chưa xác minh trên macOS Intel i5 và chưa đối chiếu trực tiếp slide Lecture 08 do chưa được cung cấp. Báo cáo này là phần Task 1, có thể đưa nội dung vào báo cáo IEEE chung của nhóm.
