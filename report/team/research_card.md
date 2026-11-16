# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4 · Evaluation confounders |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Zhang et al. (2026), [Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems](https://aclanthology.org/2026.emnlp-main.798/), EMNLP 2026; controlled benchmark study. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Báo cáo hiệu quả của các phương pháp MAS có thể phụ thuộc vào prompt và topology khởi đầu; paper đề xuất đánh giá có kiểm soát với model, agent registry và runtime dùng chung. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận nguồn dựa trên các benchmark và phương pháp MAS mà paper đánh giá; không tự động áp dụng cho xử lý claim LogiX. Lab dùng MockLLM xác định, 14 claim public, 5 seed, không đo latency sản xuất. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | So workflow với swarm: workflow sẽ đạt pass rate ít nhất bằng swarm trên public; swarm có cost/success cao hơn và variance lớn hơn do thêm lời gọi model và lỗi T02 ở seed 55. Dự đoán chênh pass tối đa khoảng 1/70 trial nếu chỉ xuất hiện lỗi seed 55 đã biết. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định MockLLM, public claims, seeds 11/22/33/44/55, giá, tool registry/quyền, as_of, SQLite mới mỗi trial và evaluator; thay đổi shape workflow ↔ swarm. Prompt cụ thể của shape không hoàn toàn đồng nhất nên kết luận là về architecture bundle, chưa cô lập topology thuần túy. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: C-002 seed 55 của swarm tin ticket thay vì order. Đo pass rate, pass^5, variance, cost/success và mean/p95 steps; đồng thời xác nhận approval bypass, secret/PII leak bằng 0 và crash safety 20/20. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/role4_r4_ablation.json`
- Run id / file report: `src/reports/role4_r4_ablation.json`; ví dụ run đối chiếu `R-workflow-C-001-s11`, `R-swarm-C-001-s11`; lỗi swarm `R-swarm-C-002-s55`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Hypothesis được ủng hộ trên public set. Workflow pass rate/pass^5 = 1.000/1.000, variance = 0, cost/success = 28.79 VND; swarm = 0.986/0.929, variance = 0.000816, cost/success = 49.57 VND. Swarm đắt hơn khoảng 1.72× và có đúng một trial fail (C-002, seed 55); pass rate chênh 1/70 trial. Mean/p95 trace steps: workflow 3.79/4, swarm 2.80/3. Steps ít hơn không đồng nghĩa chi phí thấp hơn: swarm có trung bình 3 model call so với 1 của workflow. Đây là kết quả public nhỏ, không chứng minh hiệu quả trên hidden hay model sản xuất.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
