"""Travel plans and itinerary through the full HTTP stack, on a real SQLite database."""

import httpx
import pytest

PLAN = {
    "title": "Đà Lạt cuối năm",
    "destination": {"name": "Đà Lạt", "lat": 11.9404, "lon": 108.4583},
    "start_date": "2026-12-01",
    "end_date": "2026-12-03",
    "note": "  Mang áo ấm  ",
}


async def _create_plan(client: httpx.AsyncClient, **overrides: object) -> dict[str, object]:
    response = await client.post("/api/v1/travel/plans", json={**PLAN, **overrides})
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


async def test_create_and_read_a_plan(client: httpx.AsyncClient) -> None:
    plan = await _create_plan(client)

    assert plan["title"] == "Đà Lạt cuối năm"
    assert plan["destination"] == PLAN["destination"]
    assert plan["note"] == "Mang áo ấm"
    assert plan["item_count"] == 0
    assert plan["items"] == []

    fetched = await client.get(f"/api/v1/travel/plans/{plan['id']}")
    assert fetched.json()["id"] == plan["id"]


async def test_list_shows_item_counts_and_dated_plans_first(client: httpx.AsyncClient) -> None:
    undated = await _create_plan(client, title="Một ngày nào đó", start_date=None, end_date=None)
    dated = await _create_plan(client)
    await client.post(f"/api/v1/travel/plans/{dated['id']}/items", json={"title": "Chợ đêm"})

    page = (await client.get("/api/v1/travel/plans")).json()

    assert page["total"] == 2
    assert page["limit"] == 20
    assert [p["id"] for p in page["items"]] == [dated["id"], undated["id"]]
    assert page["items"][0]["item_count"] == 1

    second = (await client.get("/api/v1/travel/plans", params={"limit": 1, "offset": 1})).json()
    assert [p["id"] for p in second["items"]] == [undated["id"]]
    assert second["total"] == 2


async def test_plan_end_before_start_is_rejected(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/travel/plans", json={**PLAN, "start_date": "2026-12-05", "end_date": "2026-12-01"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_date_range"


async def test_update_checks_dates_against_the_stored_values(client: httpx.AsyncClient) -> None:
    plan = await _create_plan(client)

    bad = await client.patch(f"/api/v1/travel/plans/{plan['id']}", json={"end_date": "2026-11-01"})
    assert bad.json()["error"]["code"] == "invalid_date_range"

    good = await client.patch(
        f"/api/v1/travel/plans/{plan['id']}", json={"title": "Đà Lạt", "destination": None}
    )
    body = good.json()
    assert body["title"] == "Đà Lạt"
    assert body["destination"] is None
    assert body["start_date"] == "2026-12-01", "omitted fields keep their value"


async def test_itinerary_items_are_ordered_and_must_fall_within_the_plan(
    client: httpx.AsyncClient,
) -> None:
    plan = await _create_plan(client)
    items_url = f"/api/v1/travel/plans/{plan['id']}/items"

    late = await client.post(
        items_url, json={"title": "Đồi chè", "day": "2026-12-02", "start_time": "15:00"}
    )
    early = await client.post(
        items_url,
        json={
            "title": "Hồ Xuân Hương",
            "day": "2026-12-02",
            "start_time": "07:30",
            "place": {"name": "Hồ Xuân Hương", "lat": 11.9416, "lon": 108.4419},
        },
    )
    outside = await client.post(items_url, json={"title": "Về nhà", "day": "2026-12-09"})

    assert late.status_code == early.status_code == 201
    assert outside.status_code == 422
    assert outside.json()["error"]["code"] == "day_outside_plan"
    detail = (await client.get(f"/api/v1/travel/plans/{plan['id']}")).json()
    assert [item["title"] for item in detail["items"]] == ["Hồ Xuân Hương", "Đồi chè"]
    assert detail["items"][0]["place"]["name"] == "Hồ Xuân Hương"


async def test_update_and_delete_an_item(client: httpx.AsyncClient) -> None:
    plan = await _create_plan(client)
    item = (
        await client.post(f"/api/v1/travel/plans/{plan['id']}/items", json={"title": "Cà phê"})
    ).json()
    item_url = f"/api/v1/travel/plans/{plan['id']}/items/{item['id']}"

    patched = (await client.patch(item_url, json={"note": "Tùng", "start_time": "09:00"})).json()
    assert patched["note"] == "Tùng"
    assert patched["start_time"] == "09:00:00"

    assert (await client.delete(item_url)).status_code == 204
    missing = await client.delete(item_url)
    assert missing.json()["error"]["code"] == "itinerary_item_not_found"


async def test_deleting_a_plan_removes_its_items(client: httpx.AsyncClient) -> None:
    plan = await _create_plan(client)
    await client.post(f"/api/v1/travel/plans/{plan['id']}/items", json={"title": "Chợ"})

    assert (await client.delete(f"/api/v1/travel/plans/{plan['id']}")).status_code == 204
    missing = await client.get(f"/api/v1/travel/plans/{plan['id']}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "travel_plan_not_found"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 121},
        {"title": "A", "destination": {"name": "X", "lat": 91, "lon": 0}},
        {"title": "A", "destination": {"name": "", "lat": 1, "lon": 1}},
        {"title": "A", "start_date": "01/12/2026"},
    ],
)
async def test_invalid_plans_are_rejected(
    client: httpx.AsyncClient, payload: dict[str, object]
) -> None:
    response = await client.post("/api/v1/travel/plans", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_unknown_plan_id_is_not_found(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/travel/plans/00000000-0000-0000-0000-000000000000/items", json={"title": "A"}
    )
    assert response.status_code == 404
