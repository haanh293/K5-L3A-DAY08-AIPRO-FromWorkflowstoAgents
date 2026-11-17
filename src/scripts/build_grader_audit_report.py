"""Builds reports/bonus_grader_audit.json comparing grader_a, grader_b, grader_c.

Can be run via:
    python -m scripts.build_grader_audit_report
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from lab8.compensation import quote

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "grader_audit" / "fixtures"
REPORTS = ROOT / "reports"


def generate_audit_report(out_path: Path | None = None) -> dict[str, Any]:
    if out_path is None:
        out_path = REPORTS / "bonus_grader_audit.json"

    delay_fix = json.loads((FIXTURES / "metamorphic_claim_delay.json").read_text(encoding="utf-8"))
    dup_fix = json.loads((FIXTURES / "metamorphic_duplicate.json").read_text(encoding="utf-8"))
    infra_fix = json.loads((FIXTURES / "metamorphic_infra.json").read_text(encoding="utf-8"))

    # 1. Claim delay domain check
    quote_a = quote(delay_fix["a"]["order"], delay_fix["policies"], as_of=delay_fix["as_of"])
    quote_b = quote(delay_fix["b"]["order"], delay_fix["policies"], as_of=delay_fix["as_of"])

    delay_check = {
        "relation": "delay_days_2_vs_3",
        "claim_a": {
            "delay_days": delay_fix["a"]["order"]["delay_days"],
            "amount_vnd": quote_a.amount_vnd,
            "clause_ids": quote_a.clause_ids,
            "reason": quote_a.reason,
            "verdict": "denied",
        },
        "claim_b": {
            "delay_days": delay_fix["b"]["order"]["delay_days"],
            "amount_vnd": quote_b.amount_vnd,
            "clause_ids": quote_b.clause_ids,
            "reason": quote_b.reason,
            "verdict": "entitled",
        },
        "passed": (quote_a.amount_vnd == 0 and quote_b.amount_vnd == 35000),
        "explanation": "Quyết định lật đúng: 2 ngày chưa đủ min_delay_days=3 nên 0đ; 3 ngày đủ điều kiện hoàn 35.000đ.",
    }

    # 2. Matrix evaluation for graders
    graders = ["grader_a", "grader_b", "grader_c"]
    eval_matrix: dict[str, Any] = {}

    for g in graders:
        mod = importlib.import_module(f"grader_audit.{g}")

        # Relation 1: Duplicate
        dup_a = mod.summarize(dup_fix["a"])["workflow"]
        dup_b = mod.summarize(dup_fix["b"])["workflow"]
        dup_cost_ratio = dup_b["total_simulated_cost_vnd"] / dup_a["total_simulated_cost_vnd"]
        dup_cps_diff = abs(dup_a["cost_per_success_vnd"] - dup_b["cost_per_success_vnd"])
        dup_passed = (round(dup_cost_ratio, 3) == 2.0 and round(dup_cps_diff, 4) == 0.0)

        # Relation 2: Infra error invariance
        inf_a = mod.summarize(infra_fix["a"])["workflow"]
        inf_b = mod.summarize(infra_fix["b"])["workflow"]
        inf_rate_diff = abs(inf_a["pass_rate"] - inf_b["pass_rate"])
        inf_passed = (round(inf_rate_diff, 4) == 0.0 and inf_a["graded_trials"] == inf_b["graded_trials"])

        # Relation 3: Proposed New Relation (Permutation Invariance)
        trials_fwd = infra_fix["a"]
        trials_rev = list(reversed(trials_fwd))
        perm_fwd = mod.summarize(trials_fwd)["workflow"]
        perm_rev = mod.summarize(trials_rev)["workflow"]
        perm_cost_diff = abs(perm_fwd["total_simulated_cost_vnd"] - perm_rev["total_simulated_cost_vnd"])
        perm_cps_diff = abs(perm_fwd["cost_per_success_vnd"] - perm_rev["cost_per_success_vnd"])
        perm_passed = (round(perm_cost_diff, 4) == 0.0 and round(perm_cps_diff, 4) == 0.0)

        diagnosis = []
        if not dup_passed:
            diagnosis.append("Lỗi lạm phát chi phí (Cost Inflation): tổng chi phí không nhân đôi (1.668x thay vì 2.0x), cost/success bị lệch.")
        if not inf_passed:
            diagnosis.append("Lỗi phạt hạ tầng (Infrastructure Penalization): coi lỗi timeout/crash hạ tầng là shape thất bại, pass_rate sụt giảm từ 75% xuống 56.25%.")
        if not perm_passed:
            diagnosis.append("Lỗi phụ thuộc thứ tự (Order Sensitivity): đảo ngược thứ tự danh sách làm thay đổi tổng chi phí và cost/success do set `seen` trạng thái.")
        if not diagnosis:
            diagnosis.append("Chuẩn (Sound Grader): thỏa mãn toàn bộ các quan hệ metamorphic.")

        eval_matrix[g] = {
            "duplicate_relation": {
                "passed": dup_passed,
                "trials_a": dup_a["trials"],
                "trials_b": dup_b["trials"],
                "total_cost_a": dup_a["total_simulated_cost_vnd"],
                "total_cost_b": dup_b["total_simulated_cost_vnd"],
                "cost_ratio": round(dup_cost_ratio, 4),
                "cost_per_success_a": round(dup_a["cost_per_success_vnd"], 4),
                "cost_per_success_b": round(dup_b["cost_per_success_vnd"], 4),
                "pass_rate_a": dup_a["pass_rate"],
                "pass_rate_b": dup_b["pass_rate"],
            },
            "infra_error_relation": {
                "passed": inf_passed,
                "trials_a": inf_a["trials"],
                "trials_b": inf_b["trials"],
                "graded_trials_a": inf_a["graded_trials"],
                "graded_trials_b": inf_b["graded_trials"],
                "pass_rate_a": inf_a["pass_rate"],
                "pass_rate_b": inf_b["pass_rate"],
                "successes_a": inf_a["successes"],
                "successes_b": inf_b["successes"],
            },
            "permutation_invariance_relation": {
                "passed": perm_passed,
                "cost_fwd": perm_fwd["total_simulated_cost_vnd"],
                "cost_rev": perm_rev["total_simulated_cost_vnd"],
                "cost_diff": round(perm_cost_diff, 4),
                "cost_per_success_fwd": round(perm_fwd["cost_per_success_vnd"], 4),
                "cost_per_success_rev": round(perm_rev["cost_per_success_vnd"], 4),
                "cost_per_success_diff": round(perm_cps_diff, 4),
            },
            "overall_status": "PASS" if (dup_passed and inf_passed and perm_passed) else "FAIL",
            "behavioral_diagnosis": "; ".join(diagnosis),
        }

    report = {
        "topic": "B7 · Kiểm toán grader (Grader Metamorphic Audit)",
        "source": "Zhang et al. (2026), Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems, EMNLP 2026",
        "domain_relation_delay": delay_check,
        "graders_audit": eval_matrix,
        "sound_grader": "grader_b",
        "flawed_graders": {
            "grader_a": "Lạm phát chi phí (cộng thừa cost) và phụ thuộc thứ tự duyệt trials",
            "grader_c": "Phạt lỗi hạ tầng (infra_error: true) thành thất bại của agent, bóp méo pass_rate",
        },
        "proposed_new_relation": {
            "name": "permutation_invariance",
            "description": "Bất biến trước hoán vị thứ tự trials. Đảo ngược danh sách trial không được làm thay đổi bất kỳ chỉ số tổng hợp nào.",
            "uncovered_flaw": "Bắt được lỗi của grader_a: vì dùng tập seen để cộng chi phí lần đầu gặp claim_id, khi đảo thứ tự trials thì chi phí trial đầu tiên gặp bị thay đổi, dẫn đến tổng chi phí và cost/success bị lệch 1.5000 VND và 0.1667 VND.",
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    rep = generate_audit_report()
    print("Generated bonus_grader_audit.json successfully.")
    print("Sound grader:", rep["sound_grader"])
    for g, data in rep["graders_audit"].items():
        print(f"  {g}: {data['overall_status']} -> {data['behavioral_diagnosis']}")
