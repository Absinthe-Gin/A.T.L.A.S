"""Finance endpoints through the full HTTP stack."""

import httpx
import pytest


async def _category_id(client: httpx.AsyncClient, name: str, kind: str = "expense") -> str:
    response = await client.get("/api/v1/finance/categories", params={"kind": kind})
    return str(next(c["id"] for c in response.json() if c["name"] == name))


async def test_create_list_update_delete_transaction(client: httpx.AsyncClient) -> None:
    food = await _category_id(client, "Ăn uống")

    created = await client.post(
        "/api/v1/transactions",
        json={
            "kind": "expense",
            "amount": 45000,
            "category_id": food,
            "occurred_on": "2026-11-15",
            "note": "Phở",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["amount"] == 45000
    assert body["category_name"] == "Ăn uống"
    assert body["currency"] == "VND"

    listed = await client.get("/api/v1/transactions", params={"month": "2026-11"})
    assert listed.status_code == 200
    page = listed.json()
    assert page["total"] == 1
    assert page["limit"] == 50
    assert page["items"][0]["note"] == "Phở"

    patched = await client.patch(f"/api/v1/transactions/{body['id']}", json={"amount": 50000})
    assert patched.json()["amount"] == 50000

    deleted = await client.delete(f"/api/v1/transactions/{body['id']}")
    assert deleted.status_code == 204
    missing = await client.delete(f"/api/v1/transactions/{body['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "transaction_not_found"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"kind": "expense", "amount": 1.5, "occurred_on": "2026-11-15"}, "amount"),
        ({"kind": "expense", "amount": "abc", "occurred_on": "2026-11-15"}, "amount"),
        ({"kind": "expense", "amount": 10**16, "occurred_on": "2026-11-15"}, "amount"),
        ({"kind": "gift", "amount": 1000, "occurred_on": "2026-11-15"}, "kind"),
        ({"kind": "expense", "amount": 1000, "occurred_on": "15/11/2026"}, "occurred_on"),
        ({"kind": "expense", "amount": 1000}, "occurred_on"),
    ],
)
async def test_invalid_transaction_payloads_are_rejected(
    client: httpx.AsyncClient, payload: dict[str, object], field: str
) -> None:
    response = await client.post("/api/v1/transactions", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == field


async def test_business_rule_errors_use_their_codes(client: httpx.AsyncClient) -> None:
    salary = await _category_id(client, "Lương", "income")

    negative = await client.post(
        "/api/v1/transactions", json={"kind": "expense", "amount": -1, "occurred_on": "2026-11-15"}
    )
    mismatch = await client.post(
        "/api/v1/transactions",
        json={
            "kind": "expense",
            "amount": 1000,
            "category_id": salary,
            "occurred_on": "2026-11-15",
        },
    )

    assert (negative.status_code, negative.json()["error"]["code"]) == (422, "invalid_amount")
    assert (mismatch.status_code, mismatch.json()["error"]["code"]) == (
        422,
        "category_kind_mismatch",
    )


@pytest.mark.parametrize("month", ["2026-13", "2026-1", "11-2026", "abc"])
async def test_invalid_month_is_rejected(client: httpx.AsyncClient, month: str) -> None:
    response = await client.get("/api/v1/finance/reports/monthly", params={"month": month})

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "month"


async def test_report_and_budgets(client: httpx.AsyncClient) -> None:
    food = await _category_id(client, "Ăn uống")
    for amount in (100000, 150000):
        await client.post(
            "/api/v1/transactions",
            json={
                "kind": "expense",
                "amount": amount,
                "category_id": food,
                "occurred_on": "2026-11-02",
            },
        )
    budget = await client.post(
        "/api/v1/budgets", json={"month": "2026-11", "category_id": food, "amount": 200000}
    )
    assert budget.status_code == 201
    assert budget.json()["over_budget"] is True

    duplicate = await client.post(
        "/api/v1/budgets", json={"month": "2026-11", "category_id": food, "amount": 1}
    )
    assert (duplicate.status_code, duplicate.json()["error"]["code"]) == (409, "budget_exists")

    report = (
        await client.get("/api/v1/finance/reports/monthly", params={"month": "2026-11"})
    ).json()
    assert report["expense_total"] == 250000
    assert report["net"] == -250000
    assert report["budgets"][0]["spent"] == 250000

    budgets = (await client.get("/api/v1/budgets", params={"month": "2026-11"})).json()
    assert len(budgets) == 1
    assert (await client.delete(f"/api/v1/budgets/{budgets[0]['id']}")).status_code == 204


async def test_categories_crud_and_conflicts(client: httpx.AsyncClient) -> None:
    created = await client.post(
        "/api/v1/finance/categories", json={"name": "Thú cưng", "kind": "expense"}
    )
    assert created.status_code == 201
    category_id = created.json()["id"]

    taken = await client.post(
        "/api/v1/finance/categories", json={"name": "thú cưng", "kind": "expense"}
    )
    assert (taken.status_code, taken.json()["error"]["code"]) == (409, "category_name_taken")

    await client.post(
        "/api/v1/transactions",
        json={
            "kind": "expense",
            "amount": 1000,
            "category_id": category_id,
            "occurred_on": "2026-11-02",
        },
    )
    in_use = await client.delete(f"/api/v1/finance/categories/{category_id}")
    assert (in_use.status_code, in_use.json()["error"]["code"]) == (409, "category_in_use")

    blank = await client.post("/api/v1/finance/categories", json={"name": "   ", "kind": "expense"})
    assert blank.status_code == 422
