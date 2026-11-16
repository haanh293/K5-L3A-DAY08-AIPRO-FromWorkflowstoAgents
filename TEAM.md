# Team

## Thông tin nhóm

- Tên nhóm: AIPRO
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-AIPRO-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: `https://github.com/haanh293/K5-L3A-DAY08-AIPRO-FromWorkflowstoAgents` | nhánh `main` | commit chốt: `4faad08` (code & benchmark: `3a9ebbc`)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Nguyễn Hà Anh | 2A202603605 | 26ai.anhnh7@vinuni.edu.vn | haanh293 | Role 1: Workflow + Team Lead / Integration |
|   2 | Nguyễn Văn Vinh | 2A202603672 | 26ai.vinhnv@vinuni.edu.vn | VINH1811 | Role 2: Single Agent (ReAct) |
|   3 | Hoàng Đăng Kiên | 2A202603636 | 26ai.kienhd@vinuni.edu.vn | kienHD03 | Role 3: Orchestrator + Handoff & Security |
|   4 | Giáp Mạnh Tuyên | 2A202603648 | 26ai.tuyengm@vinuni.edu.vn | Tanashi-Titus | Role 4: Durability (Crash/Ledger QA) + Evaluation & Research |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Hà Anh (2A202603605) | Role 1: Workflow + Team Lead / Integration | `8915a3b` | `src/tests/test_team_workflow.py` |
| Nguyễn Văn Vinh (2A202603672) | Role 2: Single Agent (ReAct) | `cc29c4d` | `src/tests/test_single_shape.py` |
| Hoàng Đăng Kiên (2A202603636) | Role 3: Orchestrator + Handoff & Security | `9c53756` | `src/tests/test_team_orchestrator.py` |
| Giáp Mạnh Tuyên (2A202603648) | Role 4: Durability + Evaluation & Research | `3a9ebbc` | `src/tests/test_role4_trace_privacy.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603605_NguyenHaAnh

### Phần việc phụ trách

- Thiết lập repo nhóm `K5-L3A-DAY08-AIPRO-FromWorkflowstoAgents`, kiểm soát cổng host (`pytest -q`) và tích hợp nhánh của các thành viên.
- Cài đặt Shape A (`src/lab8/shapes/workflow.py`) theo kiến trúc deterministic workflow và viết bộ unit test kiểm thử riêng cho Shape A.
- Phụ trách tổng hợp `TEAM.md` và hoàn thiện `report/team/group_report.md`.

### Đóng góp cụ thể

- Triển khai `run_claim` trong `src/lab8/shapes/workflow.py`: đọc claim qua `get_claim_view`, kiểm tra `order_id` và quyền sở hữu đơn qua `lookup_order`, tính tiền bồi thường bằng `compute_compensation` từ dữ liệu order row và policy hiện hành (`is_current = 1`), gọi `durability.issue_refund` với full quote và truyền `crash_at`, trả kết quả qua `lab8.shapes.common.finish()` đảm bảo đúng Trace contract v1.
- Thêm file test `src/tests/test_team_workflow.py` kiểm tra tính bất biến qua 5 seed trên `C-002`, các nhánh dừng sớm (`needs_info`, `unknown_claim`) không lộ `CANARY_SECRET`, và cơ chế truyền full quote cho trần hoàn tiền theo đơn (`C-013`, `C-014`).

### Bằng chứng

- File code: `src/lab8/shapes/workflow.py` (`8915a3b`, 62/62 test student cho `workflow` pass).
- File test: `src/tests/test_team_workflow.py` (3 test pass trong cổng `python -m pytest -q`).
- Báo cáo cá nhân: `report/team/2A202603605_NguyenHaAnh.md`.

## 2A202603672_NguyenVanVinh

### Phần việc phụ trách

- Cài đặt Shape B (`src/lab8/shapes/single.py`) theo kiến trúc Single ReAct Agent (`max_steps=8`) và viết unit test cho Shape B.

### Đóng góp cụ thể

- Triển khai vòng lặp ReAct trong `src/lab8/shapes/single.py` bằng `lab8.runtime.run_react` với `max_steps=8`; `decide()` chỉ chọn tool đọc (`lookup_order`, `lookup_refund_history`), lưu trạng thái trong dict `state` phía code và tính tiền sau vòng lặp bằng `compute_compensation` rồi gọi `durability.issue_refund` với full quote và `crash_at`.
- Thêm 33 kiểm thử trong `src/tests/test_single_shape.py` kiểm tra bỏ qua delay trong ticket trên 5 seed, không lộ secret/ticket trong trace trên 14 claim và giới hạn chỉ gọi read-only tools trong 8 bước.

### Bằng chứng

- File code & test: `src/lab8/shapes/single.py`, `src/tests/test_single_shape.py` (commit `cc29c4d`, `56b4bbf`).
- Báo cáo cá nhân: `report/team/2A202603672_NguyenVanVinh.md`.

## 2A202603636_HoangDangKien

### Phần việc phụ trách

- Cài đặt Shape C (`src/lab8/shapes/orchestrator.py`), kiểm soát `make_handoff` allowlist, rà soát bảo mật trace/PII/secret cho cả 3 shape và viết unit test cho Shape C.

### Đóng góp cụ thể

- Triển khai `src/lab8/shapes/orchestrator.py` dùng `make_handoff` với allowlist chỉ gồm read-only tools (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`), điều phối qua `run_readonly_investigators` theo `principal_id`, và gọi `durability.issue_refund` từ orchestrator với full quote và `crash_at`.
- Thêm 10 kiểm thử trong `src/tests/test_team_orchestrator.py` bao phủ các nhánh `resolved`, `needs_info`, `escalated`, `denied`, T11, T12, T13, T14 và kiểm tra không rò rỉ `CANARY_SECRET_` hay PII.

### Bằng chứng

- File code & test: `src/lab8/shapes/orchestrator.py`, `src/tests/test_team_orchestrator.py` (commit `9c53756`).
- Báo cáo cá nhân: `report/team/2A202603636_HoangDangKien.md`.

## 2A202603648_GiapManhTuyen

### Phần việc phụ trách

- Kiểm thử độ bền vững (idempotency T11, crash recovery T12, crash suite 20/20), chạy benchmark 4 shape × 5 seed, thực hiện ablation và hoàn thiện `decision_adr.md`, `research_card.md`.

### Đóng góp cụ thể

- Kiểm tra crash, retry và trace; bổ sung `src/tests/test_role4_trace_privacy.py`; chạy crash suite (`src/reports/crash.json`), benchmark bốn shape (`src/reports/benchmark.json`) và ablation R4 (`src/reports/role4_r4_ablation.json`); ghi số liệu và đề xuất kiến trúc.

### Bằng chứng

- File test & report: `src/tests/test_role4_trace_privacy.py`, `src/reports/benchmark.json`, `src/reports/crash.json`, `src/reports/role4_r4_ablation.json` (commit `3a9ebbc`, `5c095ab`).
- Báo cáo cá nhân: `report/team/2A202603648_GiapManhTuyen.md`.
