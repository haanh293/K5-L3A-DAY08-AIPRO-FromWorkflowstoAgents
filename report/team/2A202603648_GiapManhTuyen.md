# Báo cáo cá nhân — Giáp Mạnh Tuyên

## 1. Thông tin thành viên

- Họ tên: Giáp Mạnh Tuyên
- MSSV: 2A202603648
- Email: 26ai.tuyengm@vinuni.edu.vn
- GitHub: Tanashi-Titus

## 2. Phần việc phụ trách

Role 4: Durability (Crash/Ledger QA), Evaluation & Research.

## 3. Đóng góp cụ thể

- Rà soát các test về idempotency, crash recovery, approval theo claim và trần hoàn tiền theo đơn; chạy demo cho thấy chỉ dựa vào checkpoint có thể tạo hai dòng refund.
- Bổ sung `test_swarm_result_and_trace_omit_secret_and_order_pii` trong `src/tests/test_role4_trace_privacy.py`: đối chiếu secret và các trường nhạy cảm của order với kết quả và artifact trace của swarm.
- Chạy crash suite, ma trận student và benchmark bốn shape; so sánh workflow–swarm theo câu hỏi R4. Đóng góp số liệu vào research card, báo cáo nhóm và đề xuất chọn workflow trong ADR.
- Commit đóng góp: [`3a9ebbc`](https://github.com/haanh293/K5-L3A-DAY08-AIPRO-FromWorkflowstoAgents/commit/3a9ebbc).

## 4. Bằng chứng

- `python -m lab8.demo.buggy_workflow`: `unsafe refund rows: 2` trong demo không an toàn.
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: 20/20; suite kiểm host và swarm. Các test T11/T12 của từng shape được kiểm riêng trong ma trận student.
- `python -m pytest -q -m student -o addopts=`: 258 passed. Cổng host: 91 passed trên bản tích hợp.
- `src/reports/benchmark.json`: 14 claim × 5 seed × 4 shape. Workflow đạt 70/70 trial, cost/success 28,79 VND mô phỏng; swarm đạt 69/70 và 49,57 VND.
- `src/reports/role4_r4_ablation.json`: kết quả so sánh workflow–swarm; trial lỗi `R-swarm-C-002-s55`.

## 5. Công cụ AI đã dùng

Dùng Codex để đọc tài liệu, hỗ trợ viết test, chạy đánh giá và soạn báo cáo. Các kết quả được đối chiếu với output pytest, crash suite và JSON do công cụ lab sinh ra; số liệu hidden chưa có. Những nhận xét cá nhân ở mục 6 cần người nộp đọc lại để bảo đảm phản ánh trải nghiệm của mình.

## 6. Tự đánh giá

Đã hoàn thành các kiểm tra và báo cáo trong phạm vi role 4 trên bộ public. Qua bài này, tôi hiểu checkpoint không đủ để chống ghi trùng khi crash sau effect; cần ledger có khóa idempotency và transaction cho refund cùng audit. Tôi cũng nhận thấy cần so sánh các shape trên cùng dữ liệu và seed, đồng thời phân biệt chi phí mô phỏng với chi phí thực tế. Giới hạn còn lại là chưa có kết quả hidden và chưa kiểm chứng trên model sản xuất.
