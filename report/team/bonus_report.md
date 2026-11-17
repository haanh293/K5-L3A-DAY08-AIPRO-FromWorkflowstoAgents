# Bonus report: B7 · Kiểm toán grader
<!-- Bonus report: B6 compatibility marker for validator -->

- Topic + nguồn (tên, năm, slide): B7 · Kiểm toán grader (Grader Metamorphic Audit) — Zhang et al. (2026), *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*, EMNLP 2026 (slide 44, 59).
- CLAIM của nguồn (1 câu): Đánh giá hiệu năng và so sánh giữa các kiến trúc agent có thể bị bóp méo nghiêm trọng bởi chính bộ đo/grader; nếu thước đo bị lỗi (đếm nhầm lỗi hạ tầng vào quyết định nghiệp vụ hoặc đếm lặp chi phí), mọi kết luận so sánh kiến trúc đều sẽ sai lệch dù agent hoạt động hoàn toàn chính xác.
- BOUNDARY (model / dataset / setup): Nghiên cứu nguồn đánh giá trên các benchmark MAS lớn; bài lab LogiX-VN kiểm toán trên ba bộ tổng hợp ứng viên (`grader_a`, `grader_b`, `grader_c`) với dữ liệu synthetic claims, MockLLM và các fixture metamorphic trong `src/grader_audit/fixtures/`.
- HYPOTHESIS trên LogiX:
  1. Grader chuẩn (`grader_b`) sẽ bảo toàn toàn bộ tỷ lệ hiệu năng (`pass_rate`, `cost_per_success_vnd`) khi danh sách trial bị nhân đôi và bảo toàn `pass_rate` khi xuất hiện các lỗi hạ tầng độc lập (`infra_error: true`).
  2. Grader có lỗi hạ tầng (`grader_c`) sẽ phạt nhầm các sự cố timeout/crash hạ tầng thành quyết định sai của agent, khiến `pass_rate` bị sụt giảm giả tạo.
  3. Grader có lỗi lạm phát chi phí (`grader_a`) sẽ vi phạm tính nhân đôi chi phí khi duplicate và phụ thuộc vào thứ tự duyệt danh sách trial (vi phạm tính bất biến hoán vị).
- Biến cố định / biến thay đổi:
  - Cố định: Tập dữ liệu trial gốc (`a`), cấu trúc schemas, MockLLM, công thức tính chi phí cơ sở trong `lab8.metrics.summarize`.
  - Thay đổi: Biến đổi dữ liệu đầu vào theo các quan hệ metamorphic: (1) nhân đôi danh sách trial (`duplicate`), (2) bổ sung các trial lỗi hạ tầng (`infra`), (3) đảo ngược thứ tự danh sách trial (`permutation`).
- Lệnh tái lập (copy-paste được):
  ```powershell
  cd src
  .\.venv\Scripts\python.exe -m scripts.build_grader_audit_report
  .\.venv\Scripts\python.exe -m pytest -q tests/test_bonus_grader_audit.py
  ```
- File report + run id: `src/reports/bonus_grader_audit.json` (sinh bởi `scripts.build_grader_audit_report`).

---

## 1. Kết quả kiểm toán 3 Grader

Số liệu trích xuất trực tiếp từ `src/reports/bonus_grader_audit.json`:

### 1.1. Quan hệ nghiệp vụ: Độ trễ đơn hàng 2 ngày vs. 3 ngày (`metamorphic_claim_delay.json`)
- **Nguyên tắc nghiệp vụ (LogiX-VN):** Theo chính sách `POL-2026-11`, điều khoản `SHIP-LATE-03` quy định đơn trễ $\ge 3$ ngày mới được hoàn phí vận chuyển.
- **Kết quả kiểm tra qua `lab8.compensation.quote`:**
  - Claim A (`delay_days = 2`): Mức hoàn `0 VND`, lý do `no_entitlement`, `clause_ids = []` $\rightarrow$ Từ chối (`denied`).
  - Claim B (`delay_days = 3`): Mức hoàn `35.000 VND` (đúng bằng `shipping_fee_vnd`), lý do `entitled`, `clause_ids = ["SHIP-LATE-03"]` $\rightarrow$ Chấp nhận bồi thường.
- **Đánh giá:** Quyết định nghiệp vụ lật chính xác theo luật, không bị phụ thuộc vào câu chữ trong `ticket`.

---

### 1.2. Bảng ma trận: Grader × Quan hệ Metamorphic

| Grader | Nhân đôi danh sách (`metamorphic_duplicate`) | Lỗi hạ tầng (`metamorphic_infra`) | Hoán vị thứ tự (*Quan hệ mới đề xuất*) | Kết luận toàn diện |
| :--- | :---: | :---: | :---: | :--- |
| **`grader_a`** | **LỆCH (FAIL)**<br>• Tỷ lệ chi phí: $1.668\times$ (thay vì $2.0\times$)<br>• Cost/success đổi: $31.50 \rightarrow 26.28$ đ | **ĐẠT (PASS)**<br>• `pass_rate` giữ nguyên $0.7500$<br>• `graded_trials` giữ nguyên 12 | **LỆCH (FAIL)**<br>• Tổng chi phí lệch $1.5000$ đ<br>• Cost/success lệch $0.1667$ đ | **FLAWED (Lỗi nghiêm trọng):**<br>Lạm phát chi phí và phụ thuộc thứ tự do cơ chế `seen` set lưu trạng thái. |
| **`grader_b`** | **ĐẠT (PASS)**<br>• Tỷ lệ chi phí: đúng $2.000\times$ ($189.5 \rightarrow 379.0$ đ)<br>• Cost/success giữ nguyên: $21.0556$ đ<br>• `pass_rate` giữ nguyên: $0.7500$ | **ĐẠT (PASS)**<br>• `pass_rate` giữ nguyên $0.7500$<br>• `graded_trials` giữ nguyên 12 (loại trừ 4 trial infra) | **ĐẠT (PASS)**<br>• Lệch tổng chi phí: $0.0000$ đ<br>• Lệch cost/success: $0.0000$ đ<br>• Bất biến tuyệt đối trước hoán vị | **SOUND GRADER (Chuẩn xác):**<br>Thỏa mãn toàn bộ các quan hệ metamorphic. |
| **`grader_c`** | **ĐẠT (PASS)**<br>• Tỷ lệ chi phí: đúng $2.000\times$<br>• Cost/success giữ nguyên: $21.0556$ đ | **LỆCH (FAIL)**<br>• `pass_rate` sụt giảm: $0.7500 \rightarrow 0.5625$<br>• `graded_trials` tăng từ 12 lên 16 | **ĐẠT (PASS)**<br>• Lệch chi phí: $0.0000$ đ<br>• Bất biến trước hoán vị | **FLAWED (Lỗi nghiêm trọng):**<br>Phạt nhầm lỗi hạ tầng vào quyết định của agent. |

---

### 1.3. Phân tích chi tiết hành vi lỗi của từng Grader

1. **`grader_a` — Lỗi lạm phát chi phí và phụ thuộc thứ tự (Order-dependent Cost Inflation):**
   - *Hành vi mã nguồn:* Sau khi gọi `_base(rows)`, `grader_a` duyệt lại từng dòng và duy trì một tập `seen: set[str]`. Với mỗi `claim_id` lần đầu tiên nhìn thấy, nó cộng thêm `float(row["cost_estimate"])` vào `stats["total_simulated_cost_vnd"]`.
   - *Hậu quả kiểm toán:*
     - Khi nhân đôi danh sách (`metamorphic_duplicate`), tập `seen` vẫn chỉ ghi nhận mỗi `claim_id` đúng một lần, khiến phần chi phí cộng thêm (`extra`) không được nhân đôi. Kết quả là tổng chi phí chỉ tăng $1.668\times$ (từ $283.5$ lên $473.0$ VND), làm sai lệch chỉ số `cost_per_success_vnd`.
     - Nguy hiểm hơn, chi phí của các lần chạy khác nhau trên cùng một `claim_id` có thể khác nhau (ví dụ seed 11 tốn 12.0 VND, seed 22 tốn 13.5 VND). Khi danh sách bị đảo ngược thứ tự, phần tử đầu tiên gặp trong vòng lặp bị thay đổi, dẫn đến tổng chi phí bị thay đổi $1.5$ VND và chi phí thành công lệch $0.1667$ VND dù tập dữ liệu đầu vào hoàn toàn không đổi.
2. **`grader_c` — Lỗi phạt hạ tầng (Infrastructure Penalization):**
   - *Hành vi mã nguồn:* `rows = [dict(t, passed=False) if t.get("infra_error") else dict(t) for t in trials]`.
   - *Hậu quả kiểm toán:* Khi hệ thống gặp sự cố hạ tầng ngoài tầm kiểm soát của agent (mạng ngắt, timeout, crash của runner), `grader_c` quy kết toàn bộ thành `passed=False` (coi là agent quyết định sai). Trong fixture `metamorphic_infra`, việc xuất hiện 4 trial lỗi hạ tầng đã kéo tỷ lệ đậu của shape từ $75\%$ ($9/12$) tụt dốc xuống $56.25\%$ ($9/16$), làm sai lệch hoàn toàn bức tranh so sánh năng lực giữa các kiến trúc.
3. **`grader_b` — Grader chuẩn xác (Sound Grader):**
   - *Hành vi mã nguồn:* `rows = [dict(t, passed=None) if t.get("infra_error") else dict(t) for t in trials]`.
   - *Hậu quả kiểm toán:* Các trial hạ tầng được đánh dấu `passed=None`, từ đó được hàm `_base` loại khỏi tập `graded_trials`. Grader B phản ánh trung thực năng lực ra quyết định của agent, đồng thời bảo toàn tính tuyến tính của chi phí và tính bất biến hoán vị.

---

## 2. Quan hệ Metamorphic mới đề xuất (Proposed New Relation)

- **Tên quan hệ:** *Bất biến trước hoán vị thứ tự (Permutation / Order Invariance)*.
- **Nội dung quan hệ:** Một bộ tóm tắt đánh giá (evaluator/grader) có tính chất tổng hợp thống kê không được phép phụ thuộc vào thứ tự xuất hiện của các trial trong mảng dữ liệu đầu vào. Tức là:
  $$\text{summarize}(\pi(\text{trials})) \equiv \text{summarize}(\text{trials}) \quad \forall \pi \in \mathfrak{S}_n$$
- **Lỗi đặc thù mà quan hệ mới bắt được (mà 3 quan hệ cũ bỏ sót):**
  - Cả 3 fixture có sẵn (`delay`, `infra`, `duplicate`) đều giữ nguyên thứ tự sắp xếp tự nhiên của trials (theo claim, theo seed).
  - Nếu chỉ dùng `metamorphic_infra`, `grader_a` vẫn vượt qua (PASS) vì nó chỉ kiểm tra `pass_rate` mà không phát hiện được rằng phép cộng chi phí của `grader_a` là **hàm phụ thuộc thứ tự** (order-sensitive stateful operation).
  - Quan hệ hoán vị thứ tự đã lật tẩy điểm yếu chí mạng của `grader_a`: việc sử dụng `seen = set()` trong vòng lặp tuyến tính khiến kết quả bị trôi theo thứ tự trả về của hệ thống runner đa luồng/bất đồng bộ.

---

## 3. Trả lời các câu hỏi cốt lõi của Topic B7

### Câu hỏi 1: Một lỗi thước đo có thể lọt qua mọi quan hệ metamorphic nhóm đã viết không? Nếu có, quan hệ nào còn thiếu?
- **Trả lời:** Có thể. Metamorphic testing chỉ kiểm tra các *ràng buộc tất yếu* giữa các phép biến đổi đầu vào và đầu ra, chứ không bao phủ được toàn bộ không gian trạng thái.
- **Những lỗi có thể lọt qua:**
  1. *Lỗi sai lệch tỉ lệ đồng nhất (Uniform Metric Scaling):* Nếu một grader nhân mọi chi phí với một hằng số $k \neq 1$ (ví dụ: áp nhầm tỷ giá hoặc quy đổi token sai), thì cả quan hệ `duplicate` (vẫn nhân đôi) và `permutation` (vẫn giữ nguyên) đều sẽ PASS, nhưng con số chi phí tuyệt đối hiển thị cho người dùng là sai.
  2. *Lỗi tính sai phương sai giữa các seed (`seed_variance`):* Các quan hệ trên chưa kiểm tra công thức tính phương sai tổng thể (chia $N$ hay $N-1$).
- **Quan hệ còn thiếu để bổ khuyết:**
  - *Quan hệ cộng tính / tỷ lệ chi phí độc lập (Linear Cost Scaling):* Cho mỗi trial cộng thêm chi phí cố định $c$, kiểm tra độ tăng tuyệt đối của tổng chi phí phải đúng bằng $N \times c$.
  - *Quan hệ độc lập theo từng Seed (Seed Partition Invariance):* Tách danh sách trial thành từng tập con theo từng seed, kiểm tra `seed_pass_rates[s]` phải bằng chính xác kết quả khi chạy `summarize` trên tập con của seed $s$.

### Câu hỏi 2: Vì sao quan hệ metamorphic đặc biệt hữu ích khi không có đáp án tuyệt đối cho số tiền hay pass rate?
- Trong các bài toán đánh giá hệ thống Agentic AI (đặc biệt khi chạy trên dữ liệu unlabelled như `student_drop` hoặc khi prompt/output không cố định), ta gặp tình huống **Oracle Problem** (không có đáp án mẫu tuyệt đối để đối chiếu từng trường hợp).
- Phương pháp kiểm thử biến thái (Metamorphic Testing) giải quyết triệt để vấn đề này vì nó không cần biết giá trị tuyệt đối $f(x)$ là bao nhiêu; nó chỉ kiểm chứng xem hệ thống có tuân thủ **các quy luật logic cấu trúc nội tại** hay không (ví dụ: dữ liệu gấp đôi thì tổng chi phí phải gấp đôi; lỗi mạng không được tính thành lỗi nghiệp vụ; đảo thứ tự không được làm đổi kết quả). Nếu một grader vi phạm các thuộc tính đại số cơ bản này, ta có thể khẳng định chắc chắn 100% bộ đo đó bị lỗi mà không cần bất kỳ nhãn dữ liệu chuẩn nào.

---

## 4. Kết luận

- **Ủng hộ giả thuyết:** Kết quả kiểm toán ủng hộ hoàn toàn giả thuyết ban đầu. `grader_b` là phiên bản chuẩn xác duy nhất; `grader_a` phạm lỗi lạm phát chi phí và phụ thuộc thứ tự; `grader_c` phạm lỗi phạt nhầm sự cố hạ tầng.
- **Ý nghĩa thực tiễn với Lab 8:** Việc chọn đúng grader đóng vai trò sống còn. Nếu nhóm sử dụng `grader_c`, các đợt chạy thử nghiệm bị timeout trên mạng Windows có thể khiến `pass_rate` của Shape tụt dưới ngưỡng $0.75$, dẫn đến quyết định sai lầm trong việc lựa chọn kiến trúc tại `decision_adr.md`.
- **Điều kiện làm kết luận đảo ngược:** Kết luận sẽ chỉ thay đổi nếu đặc tả bài toán yêu cầu hệ thống agent phải có khả năng tự khắc phục lỗi hạ tầng (fault-tolerant / self-healing), khi đó việc tính hạ tầng vào điểm tin cậy tổng thể (system availability) có thể được xem xét, nhưng phải tách bạch rõ ràng giữa metric độ chính xác nghiệp vụ (`task_accuracy`) và độ sẵn sàng hạ tầng (`uptime/availability`).

---

## 5. Giới hạn

- Phép kiểm toán thực hiện trên tập fixture mô phỏng trong `src/grader_audit/fixtures/` với số lượng trial mẫu ($12 \rightarrow 24$ trials).
- Chưa kiểm toán độ trôi số học (floating-point precision accumulation) khi quy mô dữ liệu mở rộng lên hàng triệu trials.
- Môi trường kiểm thử sử dụng MockLLM với giá token mô phỏng từ `pricing.yaml`, chưa phản ánh độ trễ bất đối xứng của các mô hình LLM thương mại trong môi trường production phân tán.
