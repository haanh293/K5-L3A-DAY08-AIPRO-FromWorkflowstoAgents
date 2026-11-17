"""Bonus B7 — Metamorphic testing and audit of evaluation graders.

Audits three grader candidates (grader_a, grader_b, grader_c) against:
1. Domain rule relation: delay_days 2 vs 3 (compensation.quote)
2. Metamorphic relation 1: duplicate trials list (ratios preserved, totals double)
3. Metamorphic relation 2: infra errors do not move pass_rate
4. Metamorphic relation 3 (Proposed New Relation): Permutation invariance (reversing
   or reordering trials list must not alter any summary metric)

Identifies:
- grader_b: SOUND grader (passes all relations).
- grader_a: FLAWED (violates duplicate total scaling and permutation invariance due
  to first-seen claim_id cost inflation).
- grader_c: FLAWED (violates infra invariance by penalizing infrastructure crashes
  as agent decision failures, dropping pass rate from 75% to 56.25%).
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from lab8.compensation import quote

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "grader_audit" / "fixtures"
REPORTS = ROOT / "reports"


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_metamorphic_claim_delay():
    """Claim delay: changing delay_days from 2 to 3 must flip entitlement from 0 to shipping fee."""
    fixture = _load_fixture("metamorphic_claim_delay.json")
    quote_a = quote(fixture["a"]["order"], fixture["policies"], as_of=fixture["as_of"])
    quote_b = quote(fixture["b"]["order"], fixture["policies"], as_of=fixture["as_of"])

    assert quote_a.amount_vnd == 0
    assert quote_a.clause_ids == []
    assert quote_a.reason == "no_entitlement"

    expected_shipping = int(fixture["b"]["order"]["shipping_fee_vnd"])
    assert quote_b.amount_vnd == expected_shipping
    assert quote_b.clause_ids == ["SHIP-LATE-03"]
    assert quote_b.reason == "entitled"


@pytest.mark.parametrize("grader_name", ["grader_a", "grader_b", "grader_c"])
def test_metamorphic_duplicate(grader_name: str):
    """Duplicating trial list must double totals and keep all rates identical."""
    mod = importlib.import_module(f"grader_audit.{grader_name}")
    fixture = _load_fixture("metamorphic_duplicate.json")
    res_a = mod.summarize(fixture["a"])["workflow"]
    res_b = mod.summarize(fixture["b"])["workflow"]

    # In all graders, pass_rate, trials, and successes follow expected duplicate behavior
    assert res_a["pass_rate"] == res_b["pass_rate"] == 0.75
    assert res_b["trials"] == res_a["trials"] * 2 == 24
    assert res_b["successes"] == res_a["successes"] * 2 == 18

    if grader_name == "grader_b":
        # Sound grader: cost_per_success is invariant, total cost exactly doubles
        assert round(res_a["cost_per_success_vnd"], 4) == round(res_b["cost_per_success_vnd"], 4) == 21.0556
        assert res_b["total_simulated_cost_vnd"] == res_a["total_simulated_cost_vnd"] * 2 == 379.0
    elif grader_name == "grader_a":
        # Flawed grader_a: fails to double total cost (ratio is 1.668 instead of 2.0)
        cost_ratio = res_b["total_simulated_cost_vnd"] / res_a["total_simulated_cost_vnd"]
        assert round(cost_ratio, 3) == 1.668
        assert res_a["cost_per_success_vnd"] != res_b["cost_per_success_vnd"]
        assert round(res_a["cost_per_success_vnd"], 4) == 31.5000
        assert round(res_b["cost_per_success_vnd"], 4) == 26.2778
    elif grader_name == "grader_c":
        # grader_c passes duplicate test because it doesn't inflate cost
        assert round(res_a["cost_per_success_vnd"], 4) == round(res_b["cost_per_success_vnd"], 4) == 21.0556
        assert res_b["total_simulated_cost_vnd"] == res_a["total_simulated_cost_vnd"] * 2 == 379.0


@pytest.mark.parametrize("grader_name", ["grader_a", "grader_b", "grader_c"])
def test_metamorphic_infra(grader_name: str):
    """Infra errors must not be counted as shape decision failures."""
    mod = importlib.import_module(f"grader_audit.{grader_name}")
    fixture = _load_fixture("metamorphic_infra.json")
    res_a = mod.summarize(fixture["a"])["workflow"]
    res_b = mod.summarize(fixture["b"])["workflow"]

    if grader_name in ("grader_a", "grader_b"):
        # Sound behavior on infra: pass_rate remains unchanged across graded trials
        assert res_a["pass_rate"] == res_b["pass_rate"] == 0.75
        assert res_a["graded_trials"] == res_b["graded_trials"] == 12
        assert res_a["successes"] == res_b["successes"] == 9
    else:
        # Flawed grader_c: penalizes infra errors as shape failures (drops pass_rate from 0.75 to 0.5625)
        assert res_a["pass_rate"] == 0.75
        assert res_b["pass_rate"] == 0.5625
        assert res_b["graded_trials"] == 16
        assert res_b["successes"] == 9


@pytest.mark.parametrize("grader_name", ["grader_a", "grader_b", "grader_c"])
def test_metamorphic_new_relation_permutation_invariance(grader_name: str):
    """Proposed New Relation: Reversing trial order must preserve all summary metrics."""
    mod = importlib.import_module(f"grader_audit.{grader_name}")
    fixture = _load_fixture("metamorphic_infra.json")
    trials_fwd = fixture["a"]
    trials_rev = list(reversed(trials_fwd))

    res_fwd = mod.summarize(trials_fwd)["workflow"]
    res_rev = mod.summarize(trials_rev)["workflow"]

    diff_total = abs(res_fwd["total_simulated_cost_vnd"] - res_rev["total_simulated_cost_vnd"])
    diff_cps = abs(res_fwd["cost_per_success_vnd"] - res_rev["cost_per_success_vnd"])

    if grader_name == "grader_a":
        # Flawed grader_a: order-dependent cost calculation alters summary results
        assert diff_total == 1.5
        assert round(diff_cps, 4) == 0.1667
    else:
        # grader_b and grader_c are permutation invariant
        assert diff_total == 0.0
        assert diff_cps == 0.0
        assert res_fwd["pass_rate"] == res_rev["pass_rate"]


def test_grader_audit_generate_report():
    """Generates and asserts the comprehensive audit matrix report in reports/bonus_grader_audit.json."""
    from scripts.build_grader_audit_report import generate_audit_report

    report_path = REPORTS / "bonus_grader_audit.json"
    data = generate_audit_report(out_path=report_path)

    assert data["sound_grader"] == "grader_b"
    assert "grader_a" in data["flawed_graders"]
    assert "grader_c" in data["flawed_graders"]
    assert report_path.is_file()
