import os
from pathlib import Path

os.environ["XAI_API_KEY"] = ""
os.environ["DATA_PATH"] = str(Path("/tmp") / "coralconnect-pytest.json")

import pytest
from fastapi.testclient import TestClient

from app.carbon import grade_for, reef_band
from app.game import _pair
from app.main import app
from app.models import Player
from app.store import store


@pytest.fixture(autouse=True)
def clean_store():
    store.sessions.clear()
    if store.path.exists():
        store.path.unlink()
    yield
    store.sessions.clear()


def test_grade_bands_and_reef_thresholds():
    assert grade_for(10, 18) == "A+"
    assert grade_for(18, 18) == "A"
    assert grade_for(28, 18) == "B"
    assert grade_for(40, 18) == "C"
    assert grade_for(70, 18) == "D"
    assert grade_for(200, 18) == "F"
    assert reef_band(75) == "thriving"
    assert reef_band(50) == "stressed"
    assert reef_band(25) == "bleaching"
    assert reef_band(24) == "dead"


def test_pairing_groups_by_language_then_mixes_leftovers():
    players = [
        Player(id="a", token="t", name="A", language="Python"),
        Player(id="b", token="t", name="B", language="Python"),
        Player(id="c", token="t", name="C", language="Python"),
        Player(id="d", token="t", name="D", language="Go"),
    ]
    squads = _pair(players)
    assert len(squads) == 2
    sizes = sorted(len(group) for group in squads)
    assert sizes == [2, 2]


def test_compete_flow_grades_and_poisons_the_reef():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "compete", "challengeId": "invoice-bug"},
    )
    assert created.status_code == 200
    body = created.json()
    code = body["session"]["code"]
    admin = body["adminToken"]
    assert "adminToken" not in body["session"]

    joined = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "language": "Python"},
    ).json()
    player_id = joined["player"]["id"]
    player_token = joined["playerToken"]
    assert "token" not in joined["session"]["players"][0]

    denied = client.post(f"/api/sessions/{code}/start", headers={"X-Admin-Token": "nope"})
    assert denied.status_code == 403

    started = client.post(f"/api/sessions/{code}/start", headers={"X-Admin-Token": admin})
    assert started.status_code == 200
    assert started.json()["session"]["status"] == "playing"

    tight = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": player_id,
            "playerToken": player_token,
            "prompt": "In total(), apply_coupon runs after tax(). Discount subtotal() first, then tax that result.",
        },
    )
    assert tight.status_code == 200
    tight_body = tight.json()["submission"]
    assert tight_body["grade"] in {"A+", "A"}
    assert tight_body["turnIndex"] == 0
    assert tight_body["followUp"] is True
    assert tight_body["simulated"] is True
    assert tight_body["reefDelta"] > 0

    bloated = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": player_id,
            "playerToken": player_token,
            "prompt": "Please explain every edge case in detail. " * 120,
        },
    )
    assert bloated.status_code == 200
    poisoned = bloated.json()
    assert poisoned["submission"]["grade"] == "F"
    assert poisoned["submission"]["reefDelta"] < 0
    assert poisoned["session"]["reefHealth"] < 100
    assert poisoned["session"]["reefBand"] in {"thriving", "stressed", "bleaching", "dead"}
    assert poisoned["session"]["events"][0]["type"] == "sludge"
    assert "adminToken" not in poisoned["session"]


def test_collaborate_pairs_on_start_and_shares_a_score():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "collaborate", "challengeId": "null-profile"},
    ).json()
    code = created["session"]["code"]
    admin = created["adminToken"]
    ada = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "language": "Python"},
    ).json()
    grace = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Grace", "language": "Python"},
    ).json()
    started = client.post(f"/api/sessions/{code}/start", headers={"X-Admin-Token": admin})
    session = started.json()["session"]
    assert len(session["squads"]) == 1
    assert set(session["squads"][0]["playerIds"]) == {ada["player"]["id"], grace["player"]["id"]}

    submitted = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": ada["player"]["id"],
            "playerToken": ada["playerToken"],
            "prompt": "AccountHeader reads profile.user.name while user is null. Return early if profile.user is missing.",
        },
    )
    assert submitted.status_code == 200
    after = submitted.json()["session"]
    scores = {player["name"]: player["score"] for player in after["players"]}
    assert scores["Ada"] == scores["Grace"]
    assert scores["Ada"] > 0


def test_follow_up_keeps_the_bloated_history_on_the_bill():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "compete", "challengeId": "invoice-bug"},
    ).json()
    code = created["session"]["code"]
    admin = created["adminToken"]
    joined = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "language": "Python"},
    ).json()
    client.post(f"/api/sessions/{code}/start", headers={"X-Admin-Token": admin})
    body = {
        "playerId": joined["player"]["id"],
        "playerToken": joined["playerToken"],
    }
    first = client.post(
        f"/api/sessions/{code}/submit",
        json={**body, "prompt": "Please restate the entire module and every caller. " * 100},
    ).json()["submission"]
    second = client.post(
        f"/api/sessions/{code}/submit",
        json={**body, "prompt": "If tax_exempt, return the amount unchanged."},
    ).json()
    assert second["submission"]["turnIndex"] == 1
    assert second["submission"]["followUp"] is False
    assert first["lookupTokens"] > 0
    assert second["submission"]["lookupTokens"] == 0
    assert second["submission"]["grade"] in {"A+", "A"}
    assert second["session"]["threads"][0]["done"] is True


def test_websocket_sends_a_snapshot():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "compete", "challengeId": "half-migration"},
    ).json()
    code = created["session"]["code"]
    with client.websocket_connect(f"/ws/{code}") as socket:
        message = socket.receive_json()
    assert message["type"] == "state"
    assert message["session"]["code"] == code
