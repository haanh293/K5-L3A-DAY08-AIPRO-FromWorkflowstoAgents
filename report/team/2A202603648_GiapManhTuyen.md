# Báo cáo cá nhân — Giáp Mạnh Tuyên

## 1. Thông tin thành viên

- Họ tên: Giáp Mạnh Tuyên
- MSSV: 2A202603648
- Email: 26ai.tuyengm@vinuni.edu.vn
- GitHub: Tanashi-Titus

## 2. Phần việc phụ trách

Role 4: Durability (Crash/Ledger QA), Evaluation & Research.

## 3. Đóng góp cụ thể

Rà soát kiểm tra idempotency, crash và approval; bổ sung test kiểm tra secret và PII trong trace/kết quả swarm. Chạy crash suite, ma trận student, benchmark bốn shape và ablation workflow–swarm; điền research card, số liệu báo cáo và đề xuất ADR. Commit đóng góp: `3a9ebbc`.

## 4. Bằng chứng

- `src/tests/test_role4_trace_privacy.py`.
- `src/reports/crash.json`: 20/20; `src/reports/benchmark.json`: 14 claim × 5 seed × 4 shape.
- `src/reports/role4_r4_ablation.json`; ví dụ `R-swarm-C-002-s55`.
- Ma trận student: 258 passed; cổng host: 91 passed.

## 5. Công cụ AI đã dùng

Dùng Codex để đọc tài liệu, hỗ trợ viết test, chạy đánh giá và soạn báo cáo. Kiểm tra bằng output lệnh, file JSON do công cụ sinh ra và test; số liệu hidden chưa có.

## 6. Tự đánh giá

Đã hoàn thành các kiểm tra và báo cáo trong phạm vi role 4 trên bộ public. Qua bài này, tôi hiểu checkpoint không đủ để chống ghi trùng khi crash sau effect; cần ledger có khóa idempotency và transaction cho refund cùng audit. Tôi cũng nhận thấy cần so sánh các shape trên cùng dữ liệu và seed, đồng thời phân biệt chi phí mô phỏng với chi phí thực tế. Giới hạn còn lại là chưa có kết quả hidden và chưa kiểm chứng trên model sản xuất.
