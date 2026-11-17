# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: d6ace0b (bằng chứng benchmark: 3a9ebbc, bonus B7 & selfcheck: 15c4869)
- Run id dẫn chứng: R-workflow-C-001-s11 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0 (public, 70 trial)
- Cost per success (mô phỏng, VND): 28.79
- Crash safety: 20/20 (src/reports/crash.json; suite host và swarm); workflow T12 pass trong ma trận student
- Secret leak / approval bypass: 0 / 0 (0 leak trên 70 trial public; 0 leak_suspect và 0 error trên 200 trial hidden_selfcheck.json)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Đề xuất workflow: cả ba shape nhóm viết đạt 70/70 trial public, nhưng workflow có cost/success thấp nhất (28.79 VND mô phỏng). Swarm đạt 69/70 và 49.57 VND. Quyết định cần được cả nhóm xác nhận sau kiểm tra hidden.

## Có đáng đổi lấy multi-agent không

Public chưa cho thấy lợi ích độ chính xác từ multi-agent. Xem lại quyết định nếu dữ liệu thực tế cần điều tra độc lập hoặc xử lý mơ hồ và đo được cải thiện đủ lớn so với chi phí bổ sung.

## Trace và bằng chứng

Workflow ghi các bước quyết định, dữ liệu order đã lọc và kết quả quote/host. Không ghi secret, header, SĐT, địa chỉ, tên hàng hay ghi chú nội bộ. Trace phải nằm tại trace_path và các file phụ theo tiền tố run_id trong cùng thư mục để scanner kiểm tra; file nằm ngoài phạm vi đó không được chứng minh sạch bởi scanner.

## Giới hạn

MockLLM không phải model sản xuất, latency là `unavailable`. Bộ public chỉ có 14 claim; hidden 40 claim × 5 seed chưa được chấm chính thức.
