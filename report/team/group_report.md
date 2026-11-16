# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: AIPRO
- Thành viên: xem `TEAM.md`
  1. Nguyễn Hà Anh (`2A202603605`) — Role 1: Workflow + Team Lead / Integration
  2. Nguyễn Văn Vinh (`2A202603672`) — Role 2: Single Agent (ReAct)
  3. Hoàng Đăng Kiên (`2A202603636`) — Role 3: Orchestrator + Handoff & Security
  4. Giáp Mạnh Tuyên (`2A202603648`) — Role 4: Durability (Crash/Ledger QA) + Evaluation & Research
- Commit chốt (trùng `report/team/decision_adr.md`): `3a9ebbc` (merge nhánh `main`: `cb6b4b1`)

## 2. Mục tiêu và cách tiếp cận

Bài toán của LogiX-VN yêu cầu xử lý yêu cầu hoàn phí vận chuyển / bồi thường hư hỏng hàng hóa trên cùng một giao diện hàm `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult` qua bốn kiến trúc có mức độ tự chủ tăng dần:
- **Shape A (`workflow`):** Luồng bước cố định bằng Python.
- **Shape B (`single`):** Một tác tử ReAct (tối đa 8 bước) chỉ được gọi các công cụ đọc.
- **Shape C (`orchestrator`):** Orchestrator kết hợp các investigator chỉ có quyền đọc thông qua gói `handoff.v1` đã lọc theo allowlist.
- **Shape D (`swarm`):** Kiến trúc tham chiếu có sẵn để đo chi phí và phương sai theo seed.

**Cách tiếp cận của nhóm AIPRO:**
1. **Ranh giới Code vs. Model rõ ràng:** Mọi quy tắc kiểm tra quyền sở hữu đơn (`principal_id`), lọc chính sách hiệu lực (`is_current = 1`, `effective_date <= 2026-11-15`), tính mức tiền bồi thường (`compute_compensation`) và ghi nhận hoàn tiền (`durability.issue_refund`) đều do **code** quyết định. Nội dung văn bản trong `ticket` được coi là dữ liệu người dùng không đáng tin cậy (không dùng để lấy `order_id`, số ngày trễ hay điều khoản chính sách).
2. **Làm việc song song theo nhánh độc lập:** Sau khi thiết lập môi trường ở CP1, Role 1, 2, 3 triển khai độc lập 3 file `workflow.py`, `single.py`, `orchestrator.py` kèm bộ test riêng (`test_team_workflow.py`, `test_single_shape.py`, `test_team_orchestrator.py`), trong khi Role 4 xây dựng kiểm thử quyền riêng tư trace (`test_role4_trace_privacy.py`), chạy crash suite và khung đánh giá benchmark/ablation.

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
- **Vòng lặp ReAct giới hạn bước (`max_steps = 8`):**
  - Đọc claim qua `get_claim_view(conn, claim_id)`. Vòng lặp `lab8.runtime.run_react` gọi hàm `decide(obs)` tối đa 8 bước; mỗi bước thực hiện một lời gọi `complete(..., purpose="react")` được tính vào `Budget`.
  - `decide()` chỉ được phép chọn các công cụ **chỉ đọc** (`lookup_order`, `lookup_refund_history`) hoặc trả về trạng thái dừng (`needs_info` khi thiếu `order_id`, `escalated` khi `visible=False`, hoặc `propose` khi đã thu thập đủ dữ kiện). Vì `run_react` ghi đè observation sau mỗi bước, kết quả công cụ được lưu vào dict `state` phía code thay vì phụ thuộc vào trí nhớ của model.
- **Tách biệt tính tiền và ghi sổ cái sau vòng lặp:**
  - Sau khi vòng ReAct kết thúc với `propose`, code gọi `dispatch(..., "compute_compensation", {"order": order}, worker=False)` trên dòng `order` từ DB (bỏ qua hoàn toàn số ngày trễ hay câu `"ignore policy"` trong `ticket`).
  - Khi `proposal > 0`, code gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **full quote**, ghi trace nếu gặp `InjectedCrash` rồi truyền tiếp ngoại lệ, và gọi thêm 1 lần `complete(..., purpose="draft")` trước khi trả kết quả qua `finish()`.
- **Bảo mật Trace:** Chỉ ghi các sự kiện `claim` (`has_order_id`), `act` (tên công cụ), `react_stop`, `quote`, `host`, `decision`, `crash`; không ghi `ticket`, dòng claim/order thô hay `parent_secret`.

### 3.3. Shape C — Orchestrator + Read-only Investigators (`src/lab8/shapes/orchestrator.py`)
- **Kiểm tra điều kiện biên và đóng gói Handoff an toàn (`handoff.v1`):**
  - Orchestrator đọc claim qua `get_claim_view(conn, claim_id)`. Nếu không tìm thấy claim $\rightarrow$ `failed`; nếu thiếu `order_id` $\rightarrow$ `needs_info` ngay tại orchestrator mà không khởi chạy investigator.
  - Khi có `order_id`, orchestrator tạo gói bàn giao bằng `lab8.handoff.make_handoff` với `facts={}` (không truyền `parent_secret`, `raw_headers` hay dòng claim thô) và danh sách công cụ chỉ đọc: `["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"]`.
- **Thực thi Investigator và quyết định tại Orchestrator:**
  - Gọi `run_readonly_investigators(conn, budget, handoff, principal_id=claim_view["principal_id"])`. Investigator không có quyền truy cập vào registry ghi.
  - Orchestrator kiểm tra `order_view` từ kết quả investigator: nếu `not visible` $\rightarrow$ `escalated`; nếu `proposal <= 0` $\rightarrow$ `denied` (không gọi `issue_refund`); nếu `proposal > 0` $\rightarrow$ orchestrator gọi `issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **full quote** và bảo toàn `InjectedCrash`.
- **Bảo mật Trace:** Trace ghi gói `handoff` đã qua `safe_dump` (đã lọc theo allowlist), kết quả `lookup_order` đã lọc `ORDER_FIELDS`, `policy_count`, `refund_history` và `quote`; tuyệt đối không ghi ngữ cảnh gốc của parent.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean/p95 steps | Mean model / tool calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `workflow` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.79 | 3.79 / 4.0 | 1.00 / 2.79 |
| `single` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 38.57 | 6.29 / 7.0 | 3.43 / 3.64 |
| `orchestrator` | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.65 | 3.71 / 4.0 | 1.00 / 5.57 |
| `swarm` | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3.0 | 3.00 / 4.66 |

- **Độ chính xác và phương sai:** Cả ba shape nhóm cài đặt (`workflow`, `single`, `orchestrator`) đều đạt **70/70 trial pass** (`pass_rate = 1.000`, `pass^5 = 1.000`, `variance = 0`) trên 14 claim × 5 seed (`11, 22, 33, 44, 55`). `swarm` tham chiếu đạt 69/70 (`pass_rate = 0.986`, `pass^5 = 0.929`, `variance = 0.000816`) do sai `C-002` ở seed `55` khi tin số ngày trễ trong ticket thay vì cột `delay_days` của đơn hàng.
- **Chi phí mô phỏng:** `workflow` có chi phí thấp nhất (**28.79 VND/success**), rẻ hơn `single` (38.57 VND, do gọi trung bình 3.43 model calls trong vòng ReAct), `swarm` (49.57 VND, do 3 model calls + 4.66 tool calls) và `orchestrator` (56.65 VND, do investigator chạy trọn bộ 4 công cụ đọc trên các claim có `order_id`).
- **Độ bền vững và bảo mật:** Crash suite (`src/reports/crash.json`) đạt **20/20** (`crash_safety = "20/20"`). Toàn bộ 4 shape vượt qua T11 (idempotent retry) và T12 (crash & resume) trong ma trận student (`258 passed`), cổng host đạt `91 passed`, với `secret_leak_count = 0` và `approval_bypass_count = 0`.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md` (**chọn `workflow`**). Phiếu nghiên cứu và ablation (R4): xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

- **Quản lý nhiều phiên bản Python trên Windows:** Máy có sẵn cả Python 3.14 (mặc định) và Python 3.12, trong khi yêu cầu của bài lab là Python 3.11–3.13. Nhóm xử lý bằng cách chỉ định rõ `py -3.12 -m venv .venv` trong thư mục `src/` và chạy toàn bộ công cụ (`smoke`, `pytest`, `check_submission`) qua `.venv\Scripts\python.exe`.
- **Tránh xung đột Git khi 4 thành viên cùng làm việc:** Nhóm chia nhánh theo từng role (`role1-workflow-haanh`, `nguyenvinh`, `hoangkien`, `role-4-ledger-evaluation-titus`), mỗi người phụ trách một file shape riêng và một file test riêng (`test_team_workflow.py`, `test_single_shape.py`, `test_team_orchestrator.py`, `test_role4_trace_privacy.py`), sau đó mới hợp nhất về `main` để Role 4 chạy benchmark và crash suite tổng thể.
- **Lưu ý bộ lọc `-k single` của pytest:** Lệnh `-k single` khớp cả tên hàm `test_public_single_run_cases` của mọi shape; nhóm khắc phục bằng biểu thức `-k "single and not workflow and not orchestrator and not swarm"` khi cần kiểm thử riêng Shape B.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân:
- `report/team/2A202603605_NguyenHaAnh.md` (Role 1 — Workflow + Team Lead / Integration, commit `8915a3b`)
- `report/team/2A202603672_NguyenVanVinh.md` (Role 2 — Single Agent ReAct, commit `cc29c4d`)
- `report/team/2A202603636_HoangDangKien.md` (Role 3 — Orchestrator + Handoff & Security, commit `9c53756`)
- `report/team/2A202603648_GiapManhTuyen.md` (Role 4 — Durability + Evaluation & Research, commit `3a9ebbc`)

## 7. Hạn chế và hướng cải thiện

- **Giới hạn của môi trường đánh giá:** `MockLLM` là bộ sinh phản hồi tất định theo seed, không phản ánh năng lực suy luận ngôn ngữ tự nhiên hay độ trễ thực tế (`latency = "unavailable"`). Chi phí token và tool call trong `src/reports/benchmark.json` là chi phí mô phỏng từ `src/config/pricing.yaml`.
- **Phạm vi dữ liệu:** Kết luận hiện tại dựa trên 14 claim public × 5 seed (70 trial/shape). Trên bài toán mà dữ liệu đầu vào đã có cấu trúc rõ ràng trong DB (`orders`, `policies`, `approvals`) và luật tính tiền hoàn toàn xác định, `workflow` là lựa chọn tối ưu (ít tự chủ nhất, chi phí thấp nhất, phương sai bằng 0).
- **Điều kiện đảo chiều quyết định kiến trúc:** Nhóm sẽ chỉ chuyển từ `workflow` sang `single` hoặc `orchestrator` nếu ở bài toán thực tế: (1) việc chọn nguồn dữ liệu cần tra cứu phụ thuộc vào ngữ cảnh phức tạp không thể mã hóa bằng nhánh cố định, hoặc (2) cần cô lập quyền truy cập dữ liệu giữa bộ phận điều phối và các tác tử điều tra chuyên biệt (`handoff.v1`), đồng thời mức tăng `pass_rate` trên tập kiểm thử đủ lớn để bù đắp chi phí gọi model/tool tăng thêm (1.34× với `single` và 1.97× với `orchestrator`).

## 8. Tài liệu tham khảo

- Tài liệu đặc tả Lab 8 LogiX-VN: `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
- Zhang et al. (2026), *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*, EMNLP 2026 (`https://aclanthology.org/2026.emnlp-main.798/`).
