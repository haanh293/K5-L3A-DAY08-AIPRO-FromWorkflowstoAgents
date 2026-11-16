# Báo cáo cá nhân — 2A202603636_HoangDangKien

## 1. Thông tin thành viên

- Họ tên: Hoàng Đăng Kiên
- MSSV: 2A202603636
- Email: 26ai.kienhd@vinuni.edu.vn
- GitHub: https://github.com/kienHD03

## 2. Phần việc phụ trách

- **Shape C (Orchestrator)**: Chịu trách nhiệm thiết kế, triển khai logic cho kiến trúc Orchestrator phối hợp cùng read-only investigators tại `src/lab8/shapes/orchestrator.py`.
- **Unit & Integration Tests (Shape C)**: Xây dựng bộ test chuyên biệt tại `src/tests/test_team_orchestrator.py` để xác thực toàn diện các case nghiệp vụ, bảo mật handoff, idempotency và crash resilience theo đúng hợp đồng của bài lab.

## 3. Đóng góp cụ thể

- **Commit chính:** `9c53756` (`Shape C`)
- **Triển khai `src/lab8/shapes/orchestrator.py`**:
  - Đọc claim an toàn qua `get_claim_view(conn, claim_id)` (tuân thủ nguyên tắc không dùng `SELECT *` và không bao giờ rò rỉ `parent_secret` hay `raw_headers` ra bên ngoài).
  - Kiểm tra `order_id`: Xử lý phân nhánh `needs_info` sớm khi thiếu `order_id`, không ghi ledger và không gọi LLM suy diễn mã đơn từ ticket text.
  - Xây dựng sanitized handoff với `make_handoff` tuân thủ strict allowlist và bộ tool read-only (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`), tuyệt đối cấm cấp tool ghi (`issue_refund`).
  - Thực thi điều phối thông qua `run_readonly_investigators` với giới hạn phạm vi theo `principal_id`.
  - Phân nhánh nghiệp vụ chính xác: `escalated` khi đơn hàng không thuộc quyền sở hữu của principal hoặc không tìm thấy; `denied` khi quote $\le 0$ mà không gọi `issue_refund`.
  - Chuyển giao toàn quyền ghi tiền sang host: Truyền **full quote** vào `durability.issue_refund`, để host tự xử lý kiểm tra trần hoàn tiền theo đơn (per-order cap) và xác thực approval.
  - Hỗ trợ cơ chế kiểm thử chịu lỗi (fault-injection): Chuyển tiếp tham số `crash_at` vào `durability.issue_refund` và không bắt ngoại lệ `InjectedCrash` để hệ thống kiểm tra crash recovery (T12).
  - Trả kết quả thống nhất qua `lab8.shapes.common.finish()`.
- **Viết bộ kiểm thử `src/tests/test_team_orchestrator.py`**:
  - Xây dựng 10 test case bám sát bộ lọc `-k orchestrator`:
    - `test_orchestrator_resolved_c001`: Kiểm tra luồng hoàn tất chuẩn và xác minh trace không lộ secret `CANARY_SECRET_`.
    - `test_orchestrator_needs_info_missing_order_id`: Kiểm tra claim thiếu `order_id` (C-004).
    - `test_orchestrator_escalated_scope_or_not_found`: Kiểm tra đơn hàng khác principal (C-005), rà soát không rò rỉ PII (SĐT, địa chỉ, internal note).
    - `test_orchestrator_denied_zero_quote`: Kiểm tra từ chối khi quote bằng 0 mà không gọi ghi ledger (C-002).
    - `test_orchestrator_denied_policy_expired_approval`: Kiểm tra quote > 0 nhưng approval hỏng/hết hạn, xác minh audit log có ghi nhận `policy_denied` (C-007).
    - `test_orchestrator_order_already_refunded_t13`: Kiểm tra đơn đã hoàn đủ trước đó (T13).
    - `test_orchestrator_pay_difference_t14`: Kiểm tra đơn đã hoàn một phần, chỉ chi trả phần chênh lệch (T14).
    - `test_orchestrator_retry_idempotency_t11`: Kiểm tra gọi lại nhiều lần vẫn giữ nguyên tính duy nhất (idempotency) của refund (T11).
    - `test_orchestrator_crash_safety_t12`: Kiểm tra ném `InjectedCrash` và resume không gây double payment (T12).
    - `test_orchestrator_unknown_claim_fails`: Kiểm tra claim không tồn tại trả về `status="failed"`.

## 4. Bằng chứng

- **Test Suite kết quả xanh hoàn toàn:**
  - Chạy toàn bộ test student cho orchestrator:
    ```powershell
    python -m pytest -q -m student -o addopts= -k orchestrator
    ```
    *Kết quả:* **72 passed, 240 deselected in 4.86s** (Bao gồm 62 public matrix test cases và 10 unit/integration test cases mới).
  - Cổng kiểm soát host gate:
    ```powershell
    python -m pytest -q
    ```
    *Kết quả:* **54 passed, 258 deselected in 3.69s** (Bảo toàn 100% các ràng buộc của host).
- **Git status đảm bảo phạm vi thay đổi tối thiểu, tránh conflict:**
  ```text
  M src/lab8/shapes/orchestrator.py
  ?? src/tests/test_team_orchestrator.py
  ```

## 5. Công cụ AI đã dùng

- **Công cụ**: Trợ lý AI (Antigravity Agent).
- **Mục đích sử dụng**:
  - Hỗ trợ phân tích nhanh hợp đồng kiến trúc (docs/contracts.md, docs/business_rules.md).
  - Sinh mã khởi tạo khung điều phối Orchestrator bám sát `swarm_reference.py` và các nguyên tắc handoff allowlist.
  - Xây dựng khung các test case giả lập môi trường sqlite db tạm thời cho pytest.
- **Quy trình tự kiểm tra & đối soát**:
  - Kiểm tra thủ công và chạy kiểm thử tự động với pytest trên môi trường Python 3.12 của hệ thống.
  - Quét kỹ mã nguồn để đảm bảo tuyệt đối không hardcode, không bắt nuốt `InjectedCrash`, và không vi phạm việc để model can thiệp vào số tiền bồi thường.

## 6. Tự đánh giá

- **Mức độ hoàn thành**: 100% yêu cầu cho Shape C (Orchestrator) từ CP1 đến CP4.
- **Điểm mạnh**:
  - Code ngắn gọn, phân tách trách nhiệm rõ ràng: Model/Investigator chỉ đọc và lập luận; Host code là nơi duy nhất kiểm duyệt và thực thi ghi tiền vào ledger.
  - Tuân thủ nghiêm ngặt ranh giới bảo mật và trace contract: không leak thông tin nhạy cảm.
  - Test suite đầy đủ, chặt chẽ, hỗ trợ nhóm tự tin khi benchmark ở CP5 và tích hợp vào CI/CD chung.
