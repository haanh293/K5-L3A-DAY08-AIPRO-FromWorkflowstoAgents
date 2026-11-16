# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: AIPRO
- Thành viên: xem `TEAM.md`
  1. Nguyễn Hà Anh (`2A202603605`) — Role 1: Workflow + Team Lead / Integration
  2. Nguyễn Văn Vinh (`2A202603672`) — Role 2: Single Agent (ReAct)
  3. Hoàng Đăng Kiên (`2A202603636`) — Role 3: Orchestrator + Handoff & Security
  4. Giáp Mạnh Tuyên (`2A202603648`) — Role 4: Durability (Crash/Ledger QA) + Evaluation & Research
- Commit chốt (trùng `report/team/decision_adr.md`): `(cập nhật ở CP5)`

## 2. Mục tiêu và cách tiếp cận

Bài toán của LogiX-VN yêu cầu xử lý yêu cầu hoàn phí vận chuyển / bồi thường hư hỏng hàng hóa trên cùng một giao diện hàm `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult` qua bốn kiến trúc có mức độ tự chủ tăng dần:
- **Shape A (`workflow`):** Luồng bước cố định bằng Python.
- **Shape B (`single`):** Một tác tử ReAct (tối đa 8 bước) chỉ được gọi các công cụ đọc.
- **Shape C (`orchestrator`):** Orchestrator kết hợp các investigator chỉ có quyền đọc thông qua gói `handoff.v1` đã lọc theo allowlist.
- **Shape D (`swarm`):** Kiến trúc tham chiếu có sẵn để đo chi phí và phương sai theo seed.

**Cách tiếp cận của nhóm AIPRO:**
1. **Ranh giới Code vs. Model rõ ràng:** Mọi quy tắc kiểm tra quyền sở hữu đơn (`principal_id`), lọc chính sách hiệu lực (`is_current = 1`, `effective_date <= 2026-11-15`), tính mức tiền bồi thường (`compute_compensation`) và ghi nhận hoàn tiền (`durability.issue_refund`) đều do **code** quyết định. Nội dung văn bản trong `ticket` được coi là dữ liệu người dùng không đáng tin cậy (không dùng để lấy `order_id`, số ngày trễ hay điều khoản chính sách).
2. **Làm việc song song theo nhánh độc lập:** Sau khi thiết lập môi trường ở CP1, Role 1, 2, 3 triển khai độc lập 3 file `workflow.py`, `single.py`, `orchestrator.py` kèm bộ test riêng (`test_team_*.py`), trong khi Role 4 xây dựng kịch bản kiểm thử độ bền vững (idempotency, crash suite) và khung đánh giá benchmark/ablation.

## 3. Giải pháp

### 3.1. Shape A — Deterministic Workflow (`src/lab8/shapes/workflow.py`)
- **Luồng đọc và kiểm tra điều kiện sớm:**
  1. Mở kết nối SQLite và đọc thông tin khiếu nại qua `get_claim_view(conn, claim_id)` (không truy vấn `SELECT *` để tránh chạm vào `parent_secret`). Nếu `claim_id` không tồn tại $\rightarrow$ trả về `status="failed"`, `proposal_amount=0`.
  2. Nếu thiếu `order_id` $\rightarrow$ trả về `status="needs_info"`, `proposal_amount=0` mà không ghi ledger và không trích mã đơn từ nội dung `ticket`.
  3. Gọi `lookup_order(conn, order_id, principal_id)`. Nếu đơn không tồn tại hoặc không thuộc `principal_id` của claim (`visible=False`) $\rightarrow$ trả về `status="escalated"`, `proposal_amount=0`.
- **Tính toán bồi thường và gọi cổng Host (`durability.issue_refund`):**
  4. Gọi `compute_compensation(conn, order)` trực tiếp trên dòng dữ liệu đơn hàng chuẩn xác từ DB. Nếu `proposal <= 0` $\rightarrow$ trả về `status="denied"`, `proposal_amount=0` và không gọi `issue_refund`.
  5. Nếu `proposal > 0` $\rightarrow$ gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **quote đầy đủ (full quote)** để tầng host tự kiểm tra approval của đúng claim và tự trừ phần tiền đã hoàn trước đó trên cùng đơn hàng (đáp ứng chính xác T13 và T14). Nếu xảy ra `InjectedCrash`, shape ghi sự kiện crash vào trace rồi để ngoại lệ nổi lên tự nhiên (không nuốt exception).
  6. Ánh xạ kết quả từ host: thành công $\rightarrow$ `resolved`; bị cổng policy/approval từ chối $\rightarrow$ `denied` (vẫn giữ `proposal_amount = proposal` và host đã ghi audit `policy_denied`); xung đột số tiền khi gọi lại (`conflict=True`) $\rightarrow$ `failed`.
  7. `MockLLM` (`complete(..., purpose="draft")`) chỉ được gọi 1 lần để tạo bản nháp phản hồi, không can thiệp vào số tiền hay quyết định hoàn tiền.
- **Bảo mật Trace:** Mọi nhánh thoát đều đi qua `lab8.shapes.common.finish()`, chỉ ghi các trường trong allowlist (`claim_id`, `order_id`, kết quả `lookup_order` đã lọc `ORDER_FIELDS`, và `quote`), tuyệt đối không ghi `ticket`, `parent_secret`, SĐT, địa chỉ, tên hàng hay ghi chú nội bộ.

### 3.2. Shape B — Single ReAct Agent (`src/lab8/shapes/single.py`)
- *(Role 2 — Nguyễn Văn Vinh cập nhật chi tiết khi merge)*

### 3.3. Shape C — Orchestrator + Read-only Investigators (`src/lab8/shapes/orchestrator.py`)
- *(Role 3 — Hoàng Đăng Kiên cập nhật chi tiết khi merge)*

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean/p95 steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0 | 28.79 | 3.79 / 4 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0 | 38.57 | 6.29 / 7 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0 | 56.65 | 3.71 / 4 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Mỗi shape chạy 14 claim × 5 seed; swarm sai C-002 seed 55. Crash suite host/swarm đạt 20/20; T11 và T12 qua ma trận student của cả bốn shape. Chưa có kết quả hidden chính thức.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

- **Quản lý nhiều phiên bản Python trên Windows:** Máy có sẵn cả Python 3.14 (mặc định) và Python 3.12, trong khi yêu cầu của bài lab là Python 3.11–3.13. Nhóm xử lý bằng cách chỉ định rõ `py -3.12 -m venv .venv` trong thư mục `src/` và chạy toàn bộ công cụ (`smoke`, `pytest`, `check_submission`) qua `.venv\Scripts\python.exe`.
- *(Bổ sung thêm nếu gặp sự cố ở CP3–CP5)*

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân:
- `report/team/2A202603605_NguyenHaAnh.md` (Role 1 — Workflow + Team Lead / Integration)
- `report/team/2A202603672_NguyenVanVinh.md` (Role 2 — Single Agent ReAct)
- `report/team/2A202603636_HoangDangKien.md` (Role 3 — Orchestrator + Handoff & Security)
- `report/team/2A202603648_GiapManhTuyen.md` (Role 4 — Durability + Evaluation & Research)

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

*(Cập nhật hoàn chỉnh ở CP5 cùng với `decision_adr.md`)*

## 8. Tài liệu tham khảo

- Tài liệu đặc tả Lab 8 LogiX-VN: `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
