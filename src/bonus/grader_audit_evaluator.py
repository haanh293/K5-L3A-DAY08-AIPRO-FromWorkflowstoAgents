"""Bonus B7 — Grader Audit Engine.

Provides reusable evaluator logic for auditing grading candidates against
metamorphic relations and generating evaluation artifacts.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from lab8.compensation import quote

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "grader_audit" / "fixtures"


def evaluate_candidate_graders() -> dict[str, Any]:
    """Audits grader_a, grader_b, and grader_c across domain, duplicate, infra, and permutation relations."""
    dup_fix = json.loads((FIXTURES / "metamorphic_duplicate.json").read_text(encoding="utf-8"))
    infra_fix = json.loads((FIXTURES / "metamorphic_infra.json").read_text(encoding="utf-8"))

    results: dict[str, Any] = {}
    for g in ["grader_a", "grader_b", "grader_c"]:
        mod = importlib.import_module(f"grader_audit.{g}")

        # Relation 1: Duplicate
        dup_a = mod.summarize(dup_fix["a"])["workflow"]
        dup_b = mod.summarize(dup_fix["b"])["workflow"]
        dup_cost_ratio = dup_b["total_simulated_cost_vnd"] / dup_a["total_simulated_cost_vnd"]
        dup_cps_diff = abs(dup_a["cost_per_success_vnd"] - dup_b["cost_per_success_vnd"])

        # Relation 2: Infra
        inf_a = mod.summarize(infra_fix["a"])["workflow"]
        inf_b = mod.summarize(infra_fix["b"])["workflow"]
        inf_rate_diff = abs(inf_a["pass_rate"] - inf_b["pass_rate"])

        # Relation 3: Permutation
        trials_fwd = infra_fix["a"]
        trials_rev = list(reversed(trials_fwd))
        perm_fwd = mod.summarize(trials_fwd)["workflow"]
        perm_rev = mod.summarize(trials_rev)["workflow"]
        perm_cost_diff = abs(perm_fwd["total_simulated_cost_vnd"] - perm_rev["total_simulated_cost_vnd"])
        perm_cps_diff = abs(perm_fwd["cost_per_success_vnd"] - perm_rev["cost_per_success_vnd"])

        results[g] = {
            "duplicate_passed": round(dup_cost_ratio, 3) == 2.0 and round(dup_cps_diff, 4) == 0.0,
            "infra_passed": round(inf_rate_diff, 4) == 0.0 and inf_a["graded_trials"] == inf_b["graded_trials"],
            "permutation_passed": round(perm_cost_diff, 4) == 0.0 and round(perm_cps_diff, 4) == 0.0,
            "sound": (
                round(dup_cost_ratio, 3) == 2.0
                and round(dup_cps_diff, 4) == 0.0
                and round(inf_rate_diff, 4) == 0.0
                and round(perm_cost_diff, 4) == 0.0
            ),
        }
    return results
