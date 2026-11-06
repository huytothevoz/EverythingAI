# Ôn tập và giải thích Task 1

## 1. Nắm ý chính trước khi đọc code

Bài toán yêu cầu đặt N quân hậu trên bàn N×N sao cho không có hai quân cùng hàng, cùng cột hoặc cùng đường chéo. Ta chỉ cần tìm **một nghiệm**, không phải đếm tất cả nghiệm.

Bài làm có hai hướng:

- **SAT:** biến từng ô thành một biến đúng/sai, viết luật bàn cờ thành CNF, rồi nhờ Glucose3 tìm phép gán thỏa mãn.
- **Min-Conflicts:** đặt sẵn một hậu mỗi cột, chấp nhận bàn cờ ban đầu có xung đột, rồi liên tục sửa vị trí hậu để giảm vi phạm.

Heuristic đề xuất thay đổi cách chọn quân cần sửa: chọn quân đang bị nhiều quân khác tấn công nhất. Phần chọn hàng mới vẫn dùng quy tắc ít xung đột nhất.

## 2. Biểu diễn nghiệm: phải hiểu thật chắc

Code dùng `rows[c] = r`: hậu ở **cột c, hàng r**. Chỉ số bắt đầu từ 0.

Ví dụ `rows = [1, 3, 0, 2]` nghĩa là bốn tọa độ (hàng, cột): `(1,0), (3,1), (0,2), (2,3)`.

```text
. . Q .
Q . . .
. . . Q
. Q . .
```

Mỗi phần tử ứng với một cột nên biểu diễn này luôn có đúng một hậu mỗi cột. Hai hậu cùng hàng khi hai giá trị `rows` bằng nhau.

Hai ô `(r1,c1)` và `(r2,c2)` cùng đường chéo khi `abs(r1-r2) == abs(c1-c2)`. Tương đương chúng có cùng `r-c` hoặc cùng `r+c`. Đây là lý do code kiểm tra hai tập hiệu và tổng.

## 3. Logic mệnh đề và CNF

**Biến mệnh đề:** nhận True hoặc False. `x(r,c)=True` nghĩa là ô đó có hậu.

**Literal:** một biến hoặc phủ định của biến đó. **Clause:** một tuyển (OR) các literal. **CNF:** một hội (AND) các clause.

Ví dụ `(a OR b) AND (NOT a OR NOT c)` là CNF. Với PySAT, `[1,2]` là một clause; `[-1,-3]` là một clause khác; cả CNF là `[[1,2],[-1,-3]]`. Số âm là **phủ định**, không phải số lượng hậu âm.

### Ít nhất một và nhiều nhất một

Hàng r có ít nhất một hậu:

`x(r,0) OR x(r,1) OR ... OR x(r,N-1)`.

Hai ô a,b không được cùng có hậu: `NOT(a AND b)`. Theo De Morgan, viết thành `NOT a OR NOT b`. Áp dụng cho mọi cặp ô trong cùng hàng, cột hoặc đường chéo.

“Đúng một” = “ít nhất một” AND “nhiều nhất một”. Chỉ viết các mệnh đề cấm đôi thì bàn cờ trống cũng thỏa, nên bắt buộc có điều kiện ít nhất một hậu mỗi hàng.

Không cần clause “ít nhất một” cho từng cột: N hàng đúng một hậu tạo N hậu; N cột chứa nhiều nhất một hậu mỗi cột buộc tất cả cột đều có hậu.

### Đánh số biến

`v(r,c) = r*N + c + 1`. Cộng 1 vì biến PySAT bắt đầu từ 1. Với N=4:

```text
 1  2  3  4
 5  6  7  8
 9 10 11 12
13 14 15 16
```

Hàng đầu có clause `[1,2,3,4]`. Cấm hai ô đầu cùng hàng: `[-1,-2]`. Cấm hai ô đầu cột đầu: `[-1,-5]`. Cấm hai ô trên đường chéo chính: `[-1,-6]`.

Nghiệm `[1,3,0,2]` tương ứng biến dương `5,14,3,12`; các ô còn lại là biến âm trong model đầy đủ.

### Đếm clause

- Ít nhất một mỗi hàng: N clause.
- Cấm đôi theo hàng và cột: `2*N*choose(N,2) = N²(N-1)`.
- Cấm đôi theo hai họ đường chéo: `N(N-1)(2N-1)/3`.

Tổng `N + N²(N-1) + N(N-1)(2N-1)/3`. Với N=4: `4+48+28=80`. Số biến là 16, không phải 80.

Một họ đường chéo có độ dài `1,2,...,N-1,N,N-1,...,1`; đường dài k tạo `choose(k,2)` clause. Cộng hai họ thu được công thức trên. Pairwise encoding dễ giải thích nhưng kích thước tăng O(N³).

## 4. Giải thích từng lớp và hàm trong nqueens.py

### Result

`@dataclass` tự tạo hàm khởi tạo và cách biểu diễn đối tượng chứa kết quả. `solution` là danh sách hàng hoặc `None`; `seconds` là thời gian; `steps` là tổng bước sửa của local search; `attempts` là số lần khởi tạo đã dùng. SAT giữ giá trị mặc định steps=0, attempts=1: **không có nghĩa SAT không thực hiện tính toán**.

### NQueens.__init__(n)

Kiểm tra N là số nguyên dương, rồi lưu `self.n`. Đối tượng này mô tả bài toán, không gắn với thuật toán cụ thể.

### NQueens.valid(rows)

Kiểm tra danh sách tồn tại, đủ N phần tử, hàng nằm trong miền, N hàng khác nhau và N giá trị khác nhau ở mỗi họ đường chéo. `set` bỏ phần tử trùng; nếu kích thước tập nhỏ hơn N thì có vi phạm. Cột khác nhau đã được bảo đảm bởi chỉ số danh sách. Hàm dùng để kiểm tra đầu ra độc lập với solver.

### NQueens.board(rows)

Duyệt từng hàng r và cột c; in Q nếu `rows[c]==r`, ngược lại in dấu chấm. `join` ghép các ô thành dòng và các dòng thành bàn cờ. Hàm trình bày nghiệm, không tìm nghiệm.

### CNFEncoder.__init__(problem) và variable(r,c)

Hàm khởi tạo lưu N từ bài toán. `variable` đổi tọa độ thành mã biến nguyên dương theo công thức ở trên.

### CNFEncoder.encode()

`clauses` chứa CNF cuối cùng. `groups` chứa các nhóm ô không được có hai hậu đồng thời.

1. Mỗi hàng: đưa danh sách biến vào `clauses` để bảo đảm ít nhất một; đồng thời đưa vào `groups` để cấm đôi.
2. Đưa mỗi cột vào `groups`.
3. Gom các ô có cùng `r-c`, với offset từ `-N+1` đến `N-1`.
4. Gom các ô có cùng `r+c`, từ 0 đến `2N-2`.
5. `combinations(group,2)` liệt kê các cặp khác nhau, không phân biệt thứ tự. Với mỗi cặp a,b thêm `[-a,-b]`.

Đường chéo dài 1 không tạo cặp nên không tạo clause. Python `range` không lấy cận phải. Code hiện tại duyệt toàn bàn cho từng đường chéo, vì vậy thời gian tạo nhóm cũng O(N³).

### CNFEncoder.clause_count()

Tính số clause bằng công thức, không chạy SAT. `//3` là chia nguyên; biểu thức luôn chia hết cho 3. Thí nghiệm so số này với `len(clauses)` để phát hiện sai sót đếm.

### SATSolver.solve(problem, clauses=None)

Nếu chưa truyền CNF thì tự sinh. Khối `with Glucose3(...)` tạo solver và tự giải phóng tài nguyên khi kết thúc. `bootstrap_with` nạp CNF. `solver.solve()` trả kết quả khả thỏa; nếu có nghiệm, `get_model()` trả phép gán.

Đồng hồ bắt đầu **sau khi nạp CNF**, kết thúc ngay sau `solve()`. Do đó thời gian này không gồm tạo CNF, nạp solver, lấy model và kiểm tra nghiệm.

Với literal dương l, `divmod(l-1,N)` trả thương và dư tương ứng hàng và cột. Gán `rows[c]=r`, kiểm tra bằng `problem.valid`, rồi trả `Result`. Với literal âm, ô trống nên bỏ qua. UNSAT trả `solution=None`.

### MinConflictsSolver.__init__()

Lưu cờ chọn heuristic, số bước tối đa mỗi lần khởi tạo và số restart tối đa. `restarts=4` nghĩa là có tối đa **5 lần khởi tạo**, gồm lần đầu và 4 lần làm lại.

### MinConflictsSolver.solve(problem, seed)

`Random(seed)` tạo bộ sinh ngẫu nhiên riêng. Cùng seed và cùng thuật toán cho cùng chuỗi quyết định và nghiệm; thời gian chạy vẫn dao động.

Mỗi lần khởi tạo, sinh N hàng ngẫu nhiên, một hàng cho mỗi cột. Ba mảng lưu số hậu:

| Mảng | Ý nghĩa | Độ dài |
|---|---|---:|
| rc | số hậu từng hàng | N |
| down | số hậu trên đường có cùng r-c | 2N-1 |
| up | số hậu trên đường có cùng r+c | 2N-1 |

`r-c` có thể âm; cộng `N-1` để chỉ số nằm trong 0..2N-2. Đây là dịch chỉ số, không thay đổi đường chéo.

### Hàm lồng update(c,r,delta)

Cộng delta vào ba bộ đếm chứa ô `(r,c)`. Delta=1 khi đặt hậu, delta=-1 khi gỡ hậu. Cập nhật O(1). Đây là hàm lồng trong solve, dùng trực tiếp các mảng của lần khởi tạo hiện tại.

### Hàm lồng conflicts(c,r)

Trả tổng ba bộ đếm tại ô cần xét. Khi hậu vẫn nằm tại ô đó, chính nó xuất hiện trong cả ba bộ đếm nên `scores=conflicts-3`. Mỗi hậu khác tấn công quân đang xét chỉ được đếm một lần vì hai ô khác nhau không thể vừa cùng hàng vừa cùng đường chéo.

Khi đã gỡ quân được chọn ra, tính chi phí các ô ứng viên bằng `conflicts` trực tiếp; **không trừ 3 nữa**.

### Vòng lặp sửa xung đột

1. Tính scores, lập danh sách `bad` gồm các cột có hậu xung đột.
2. Nếu bad rỗng: kiểm tra và trả nghiệm.
3. Nếu hết ngân sách: chuyển sang lần khởi tạo tiếp theo.
4. Nếu bật heuristic: lọc bad chỉ còn các quân có score lớn nhất.
5. Chọn ngẫu nhiên một cột trong bad.
6. Gỡ hậu cũ, tính chi phí N hàng, chọn ngẫu nhiên trong các hàng ít xung đột nhất, đặt hậu lại.
7. Tăng tổng số bước, kể cả khi hậu được đặt lại hàng cũ.

Vòng `range(max_steps+1)` có thêm lượt **kiểm tra nghiệm**, không có thêm bước sửa. Nếu bước cuối tìm được nghiệm, lượt kiểm tra cuối sẽ nhận ra.

Mỗi bước O(N), bộ nhớ O(N). Tổng thời gian có thể đến O((restarts+1)*max_steps*N), ngoài phần khởi tạo. Không bảo đảm tìm được nghiệm trong ngân sách hữu hạn.

## 5. Ví dụ một bước Min-Conflicts với N=4

Giả sử `rows=[0,0,0,0]`: cả bốn hậu cùng hàng, mỗi quân có score=3. Chọn cột 0, gỡ hậu tại `(0,0)`.

Các hậu còn lại ở `(0,1),(0,2),(0,3)`. Chi phí đặt lại tại cột 0:

| Hàng thử | Số hậu tấn công | Giải thích |
|---:|---:|---|
| 0 | 3 | cùng hàng với ba hậu |
| 1 | 1 | chéo với hậu cột 1 |
| 2 | 1 | chéo với hậu cột 2 |
| 3 | 1 | chéo với hậu cột 3 |

Chọn ngẫu nhiên hàng 1,2 hoặc 3. Nếu chọn 1, trạng thái thành `[1,0,0,0]`. Đây mới là bước sửa, chưa phải nghiệm. Thuật toán tiếp tục đến khi không có xung đột. Ví dụ này minh họa quy tắc, không phải trace được ghi từ seed cụ thể.

## 6. Giải thích main.py và kiểm thử

`main()` đọc tham số bằng argparse. Lệnh `solve` tìm một nghiệm; `benchmark` thực hiện nhiều lần chạy. Các tham số quan trọng là N, tên thuật toán, seed, số bước và số restart. `if __name__ == '__main__'` chỉ gọi main khi chạy file trực tiếp, không tự chạy khi import.

`experiment(args)` tạo CNF một lần cho mỗi N, kiểm tra số clause, rồi chạy cả ba cấu hình cho mỗi trial. Seed là `seed_gốc + trial`. Mỗi lượt SAT tạo solver mới. `asdict(result)` đổi dataclass thành dictionary để ghi dữ liệu.

`raw.csv` lưu từng lần chạy; `summary.csv` tổng hợp; `environment.json` lưu môi trường và tham số. `mean` là trung bình; `median` là trung vị, ít nhạy với một số lần quá chậm; `stdev` là độ lệch chuẩn mẫu, mô tả mức dao động. Thời gian được lưu theo giây; nhân 1000 thành mili giây.

Hai biến thể local search dùng cùng seed và trạng thái đầu tiên, cùng ngân sách và cùng cách chọn hàng. Sau khi chọn biến khác nhau, chuỗi tiêu thụ số ngẫu nhiên có thể khác; không nên nói mọi trạng thái khởi tạo lại đều giống nhau.

Trong test, N=4 có 16 biến Boolean nên có `2^16=65.536` phép gán. Duyệt tất cả để kiểm tra “CNF đúng khi và chỉ khi bàn cờ hợp lệ”. Các test còn kiểm tra trường hợp vô nghiệm, nghiệm SAT, nghiệm local search và khả năng tái lập theo seed. Test hữu hạn không chứng minh code đúng với mọi N; chứng minh mô hình và kiểm thử bổ trợ nhau.

## 7. Cách đọc kết quả của chính bài làm

Với N=64, standard trung bình 122,15 bước, heuristic 95,35 bước, giảm khoảng 21,94%. Với N=16, standard 62,50 bước nhưng heuristic 559,25 bước. Vì vậy không được kết luận heuristic luôn tốt hơn.

Tất cả cấu hình đã đo có tỷ lệ thành công 20/20, nhưng điều đó không chứng minh xác suất thành công tuyệt đối là 100%. Ở N=8 và N=16 có các lần local search dài làm trung bình tăng mạnh; phải đọc cả trung vị và độ lệch chuẩn.

Thời gian SAT chỉ gồm solve; local search gồm khởi tạo và restart nên hai thời gian khác phạm vi. Bảng hiện tại đo trên Windows, chưa xác minh trên macOS Intel i5. Một tiến trình thử N=100 chạy đồng thời trong lúc thu bảng có thể gây nhiễu thời gian; muốn kết luận hiệu năng cần đo lại khi máy rảnh. Không có kết quả hoàn chỉnh cho N=100.

## 8. Câu hỏi vấn đáp kèm gợi ý trả lời

**1. Vì sao dùng N² biến trong SAT nhưng chỉ N biến trong local search?** SAT biểu diễn từng ô có/không có hậu. Local search dùng biến đa trị biểu diễn hàng của hậu từng cột. Hai mô hình mô tả cùng bài toán bằng cách khác nhau.

**2. Vì sao không chỉ cấm hai hậu tấn công nhau?** Vì bàn cờ không có hậu cũng thỏa tất cả điều kiện cấm đôi. Cần buộc mỗi hàng có ít nhất một hậu.

**3. CNF có phải danh sách các nghiệm không?** Không. Nó là danh sách các luật mà một phép gán phải đồng thời thỏa.

**4. Clause `[-1,-6]` nghĩa là gì?** Không được đồng thời chọn cả biến 1 và biến 6. Nó không buộc cả hai đều sai.

**5. Glucose3 là phần em tự cài đặt không?** Không. Bài làm tự mô hình hóa, sinh CNF, gọi thư viện, giải mã và kiểm tra nghiệm; thuật toán SAT nằm trong thư viện.

**6. Glucose3 làm gì về mặt ý tưởng?** Đây là SAT solver thuộc họ CDCL: lan truyền giá trị bị bắt buộc, quyết định giá trị khi cần, phân tích xung đột và học clause để tránh lặp lại nhánh mâu thuẫn. Code này sử dụng API, không hiện thực các cơ chế nội bộ ấy.

**7. Standard và heuristic khác ở đâu?** Standard chọn ngẫu nhiên một quân đang xung đột; heuristic chọn quân có nhiều xung đột nhất và phá hòa ngẫu nhiên. Cả hai chọn hàng mới có ít xung đột nhất.

**8. Có phải heuristic là chọn hàng ít xung đột?** Trong bài này không: chọn hàng ít xung đột là quy tắc chung của Min-Conflicts. Điểm đề xuất là cách chọn biến cần sửa.

**9. Vì sao phải gỡ hậu trước khi đánh giá hàng mới?** Để chi phí chỉ đếm các hậu khác. Nếu không gỡ, hậu cũ làm sai lệch các bộ đếm khi thử vị trí.

**10. Vì sao trừ 3 mà không trừ 1?** Vì chính quân đó hiện diện trong bộ đếm hàng và cả hai đường chéo, tổng cộng ba lần.

**11. Sao cho phép giữ nguyên hàng?** Hàng cũ có thể cùng đạt chi phí nhỏ nhất. Đây là bước bằng phẳng; phá hòa ngẫu nhiên hoặc restart giúp thay đổi đường đi, nhưng không bảo đảm thoát ngay.

**12. Có phải số xung đột luôn giảm sau mỗi bước?** Không tăng đối với số cặp tấn công trong một bước sửa theo quy tắc hiện tại, vì hàng cũ nằm trong tập ứng viên nên chi phí nhỏ nhất không lớn hơn chi phí cũ. Nó có thể giữ nguyên. Restart có thể làm số xung đột tăng.

**13. Vì sao cần restart?** Vì tìm kiếm có thể mắc ở vùng bằng phẳng hoặc cực tiểu cục bộ. Khởi tạo lại thử vùng khác; ngân sách hữu hạn vẫn có thể thất bại.

**14. Thất bại của Min-Conflicts có chứng minh UNSAT không?** Không. Chỉ biết chưa tìm được trong ngân sách. Glucose3 trả UNSAT mới là kết luận vô nghiệm của công thức được mã hóa.

**15. `restarts=4, max_steps=10000` có tối đa bao nhiêu bước?** 5 lần khởi tạo × 10.000 = 50.000 bước sửa.

**16. Heuristic có độ phức tạp cao hơn không?** Cả hai mỗi bước O(N). Heuristic có thêm lượt tìm score lớn nhất và lọc hòa, tăng hằng số thực hiện.

**17. Bộ nhớ CNF và local search khác nhau thế nào?** Pairwise CNF O(N³) vì lưu các clause cấm đôi. Local search chỉ lưu N vị trí và các mảng bộ đếm O(N).

**18. Tại sao phải chạy nhiều seed?** Vì local search phụ thuộc khởi tạo và phá hòa. Một lần chạy có thể không đại diện. Hai mươi seed vẫn chỉ là mẫu hữu hạn.

**19. Có phải cùng seed thì mọi thuật toán có cùng nghiệm?** Không. Seed giúp lặp lại một thuật toán với cùng tham số; hai thuật toán có các quyết định khác nhau.

**20. OOP thể hiện ở đâu?** Dữ liệu bài toán và kiểm tra nằm trong NQueens; mã hóa nằm trong CNFEncoder; từng phương pháp giải có lớp riêng; Result thống nhất đầu ra. Không nên tuyên bố có kế thừa vì code hiện tại không dùng kế thừa.

**21. Vì sao có cả công thức đếm và len(clauses)?** Một bên là tính toán lý thuyết, một bên là số dữ liệu thực tạo. Đối chiếu giúp phát hiện lỗi triển khai.

**22. Kết quả nào cho thấy hạn chế của heuristic?** N=16 có số bước trung bình lớn hơn standard đáng kể. Không được chỉ chọn N=64 để nói heuristic thắng.

**23. N=1,2,3 có gì đặc biệt?** N=1 có nghiệm; N=2,3 vô nghiệm. Benchmark theo đề dùng N≥4, nhưng test vẫn dùng các N nhỏ để kiểm tra biên.

**24. Có thể cải tiến gì?** Gom đường chéo trong một lượt O(N²) thay vì quét lại toàn bàn; thử encoding cardinality tiết kiệm clause; thử heuristic pha ngẫu nhiên. Đây là ý tưởng mở rộng, chưa phải tính năng đang có.

## 9. Lịch ôn bốn ngày

**Ngày 1:** học biểu diễn nghiệm, đường chéo, literal/clause/CNF. Tự viết 80 clause theo nhóm cho N=4 và giải thích vì sao không cần tuyển dương từng cột. Không cần chép tay toàn bộ 80 clause; cần tính đúng số lượng và viết được ví dụ mỗi loại.

**Ngày 2:** đọc NQueens, CNFEncoder và SATSolver. Tự đổi tọa độ sang số biến và đổi literal dương về tọa độ. Chạy N=4 và N=3; giải thích SAT/UNSAT.

**Ngày 3:** đọc MinConflictsSolver. Tự tính ba bộ đếm của một bàn N=4, tính score, gỡ một hậu và tính chi phí từng hàng. Giải thích trừ 3, restart và heuristic.

**Ngày 4:** đọc bảng kết quả, tập trả lời 24 câu không nhìn tài liệu. Demo cả ba thuật toán và benchmark nhỏ; nói rõ giới hạn phép đo và những phần chưa kiểm chứng.

## 10. Bài nói mở đầu khoảng một phút

“Task 1 của nhóm giải bài toán N quân hậu theo hai hướng. Với SAT, mỗi ô là một biến Boolean. Nhóm tạo CNF để mỗi hàng đúng một hậu, mỗi cột và mỗi đường chéo nhiều nhất một hậu, sau đó gọi Glucose3 và kiểm tra lại nghiệm. Với Min-Conflicts, nhóm dùng một biến cho mỗi cột để biểu diễn hàng của hậu. Mỗi bước chọn một quân đang xung đột và đưa nó đến hàng ít xung đột nhất. Heuristic đề xuất ưu tiên quân có số xung đột lớn nhất. Nhóm so sánh hai biến thể với cùng ngân sách và seed. Kết quả cho thấy heuristic giảm số bước ở một số kích thước nhưng không tốt hơn một cách nhất quán, chẳng hạn N=16 có kết quả kém hơn standard.”

Học để tự giải thích được các quyết định trong code. Khi chưa kiểm chứng một nhận định, nói rõ giới hạn thay vì đoán.
