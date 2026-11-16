"""Role 4 QA: public shape artifacts must not expose raw claim/order PII."""

from lab8.db import connect
from lab8.metrics import artifact_blob
from lab8.shapes.swarm_reference import run_claim


def test_swarm_result_and_trace_omit_secret_and_order_pii(public_db):
    conn = connect(public_db)
    claim = conn.execute(
        "SELECT parent_secret FROM claims WHERE claim_id = 'C-001'"
    ).fetchone()
    order = conn.execute(
        "SELECT phone, address, internal_note, item_name FROM orders WHERE order_id = 'O-107'"
    ).fetchone()
    forbidden = [str(value) for value in (*claim, *order) if value]
    conn.close()

    result = run_claim("C-001", seed=11, store_path=str(public_db)).as_dict()
    artifacts = artifact_blob(result)

    for value in forbidden:
        assert value not in artifacts
