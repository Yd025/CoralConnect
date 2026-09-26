import os
from pathlib import Path

os.environ["XAI_API_KEY"] = ""
os.environ["DATA_PATH"] = str(Path("/tmp") / "coralconnect-pytest.json")

import pytest
from fastapi.testclient import TestClient

from app.carbon import grade_for, reef_band
from app.game import _pair
from app.grok import call_trace, finalize_verdict, parse_verdict
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


def test_open_collaborate_reuses_the_room_until_it_is_full():
    client = TestClient(app)
    first = client.get("/api/collaborate")
    assert first.status_code == 200
    code = first.json()["session"]["code"]
    assert first.json()["session"]["mode"] == "collaborate"
    again = client.get("/api/collaborate")
    assert again.json()["session"]["code"] == code
    for index in range(8):
        joined = client.post(
            f"/api/sessions/{code}/join",
            json={"name": f"P{index}", "builds": "Apps", "cares": "Planet"},
        )
        assert joined.status_code == 200
    fresh = client.get("/api/collaborate")
    assert fresh.json()["session"]["code"] != code
    assert fresh.json()["session"]["mode"] == "collaborate"


def test_pairing_follows_join_order():
    players = [
        Player(id="a", token="t", name="A", language="Python", joined_at=1, builds="apis", cares="trust"),
        Player(id="b", token="t", name="B", language="Python", joined_at=2, builds="sensors", cares="energy"),
        Player(id="c", token="t", name="C", language="Go", joined_at=3, builds="models", cares="trust"),
        Player(id="d", token="t", name="D", language="Rust", joined_at=4, builds="compilers", cares="speed"),
    ]
    squads = _pair(players)
    assert [[player.name for player in group] for group in squads] == [["A", "B"], ["C", "D"]]


def test_compete_caps_at_ten_players():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "compete", "challengeId": "invoice-bug"},
    )
    assert created.status_code == 200
    code = created.json()["session"]["code"]
    assert created.json()["session"]["playerMin"] == 1
    assert created.json()["session"]["playerMax"] == 10
    for index in range(10):
        joined = client.post(
            f"/api/sessions/{code}/join",
            json={"name": f"P{index}", "language": "Python"},
        )
        assert joined.status_code == 200
    extra = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Extra", "language": "Python"},
    )
    assert extra.status_code == 409
    assert "10" in extra.json()["error"]


def test_collaborate_requires_two_to_four_players():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "collaborate", "challengeId": "null-profile"},
    ).json()
    code = created["session"]["code"]
    admin = created["adminToken"]
    assert created["session"]["playerMin"] == 2
    assert created["session"]["playerMax"] == 8

    alone = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "language": "Python"},
    )
    assert alone.status_code == 200
    no_shared_start = client.post(f"/api/sessions/{code}/start", headers={"X-Admin-Token": admin})
    assert no_shared_start.status_code == 409
    assert "same animal" in no_shared_start.json()["error"]

    full = client.post(
        "/api/sessions",
        json={"mode": "collaborate", "challengeId": "null-profile"},
    ).json()
    full_code = full["session"]["code"]
    for name in ("Ada", "Grace", "Lin", "Kay", "Nia", "Owen", "Bea", "Cy"):
        joined = client.post(
            f"/api/sessions/{full_code}/join",
            json={"name": name, "language": "Python"},
        )
        assert joined.status_code == 200
    ninth = client.post(
        f"/api/sessions/{full_code}/join",
        json={"name": "Jin", "language": "Python"},
    )
    assert ninth.status_code == 409
    assert "8" in ninth.json()["error"]


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
    assert tight_body["reasonable"] is True
    assert tight_body["judgedByModel"] is False
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
    assert poisoned["submission"]["reasonable"] is False
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
    ada = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "language": "Python"},
    ).json()
    grace = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Grace", "language": "Python"},
    ).json()
    session = grace["session"]
    assert len(session["squads"]) == 1
    assert set(session["squads"][0]["playerIds"]) == {ada["player"]["id"], grace["player"]["id"]}
    assert "Ada" in session["squads"][0]["shared"] or "Ada" in session["squads"][0]["name"]
    assert session["players"][0]["piece"]["role"]
    assert session["players"][0]["piece"]["body"] != session["players"][1]["piece"]["body"]

    submitted = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": ada["player"]["id"],
            "playerToken": ada["playerToken"],
            "prompt": (
                "AccountHeader reads profile.user.name while user is null. "
                "The crash happens while the account request is still in flight."
            ),
        },
    )
    assert submitted.status_code == 200
    after = submitted.json()["session"]
    scores = {player["name"]: player["score"] for player in after["players"]}
    assert scores["Ada"] == scores["Grace"]
    assert scores["Ada"] > 0


def test_two_people_share_one_animal_and_a_third_waits():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "collaborate", "challengeId": "null-profile"},
    ).json()
    code = created["session"]["code"]
    first_join = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Maya", "builds": "Apps", "cares": "Planet"},
    ).json()
    assert first_join["session"]["squads"][0]["creature"] == ""
    second_join = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Jordan", "builds": "Systems", "cares": "Planet"},
    ).json()
    assert second_join["session"]["squads"][0]["creature"] == "Seagull"
    assert len(second_join["session"]["squads"][0]["playerIds"]) == 2
    third_join = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "builds": "Data", "cares": "Trust"},
    ).json()
    waiting = client.get(f"/api/sessions/{code}").json()["session"]
    assert sorted(squad.get("creature") for squad in waiting["squads"]) == ["", "Seagull"]
    seagull = next(squad for squad in waiting["squads"] if squad["creature"] == "Seagull")
    maya = next(player for player in waiting["players"] if player["name"] == "Maya")
    ada = next(player for player in waiting["players"] if player["name"] == "Ada")
    playing = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": seagull["playerIds"][0],
            "playerToken": next(
                item["playerToken"]
                for item in (first_join, second_join)
                if item["player"]["id"] == seagull["playerIds"][0]
            ),
            "prompt": "AccountHeader reads profile.user.name while the request is still in flight.",
        },
    )
    assert playing.status_code == 200
    waiting_submit = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": ada["id"],
            "playerToken": third_join["playerToken"],
            "prompt": "AccountHeader reads profile.user.name while the request is still in flight.",
        },
    )
    assert waiting_submit.status_code == 409
    assert maya["id"] in seagull["playerIds"]
    client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Grace", "builds": "Design", "cares": "People"},
    )
    paired = client.get(f"/api/sessions/{code}").json()["session"]
    assert sorted(squad["creature"] for squad in paired["squads"]) == ["Seagull", "Turtle"]


def test_questionnaire_shows_up_in_the_match():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "collaborate", "challengeId": "null-profile"},
    ).json()
    code = created["session"]["code"]
    client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Maya", "builds": "reef sensors", "cares": "the coast"},
    )
    second = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Jordan", "builds": "payment APIs", "cares": "customer trust"},
    )
    squad = second.json()["session"]["squads"][0]
    text = f"{squad['shared']} {squad['distinct']}"
    assert "reef sensors" in text
    assert "payment APIs" in text
    assert "the coast" in text
    assert "customer trust" in text


def test_collaborate_needs_both_pieces():
    client = TestClient(app)
    created = client.post(
        "/api/sessions",
        json={"mode": "collaborate", "challengeId": "null-profile"},
    ).json()
    code = created["session"]["code"]
    ada = client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Ada", "builds": "headers", "cares": "the crash"},
    ).json()
    client.post(
        f"/api/sessions/{code}/join",
        json={"name": "Grace", "builds": "support", "cares": "the reporter"},
    )
    submitted = client.post(
        f"/api/sessions/{code}/submit",
        json={
            "playerId": ada["player"]["id"],
            "playerToken": ada["playerToken"],
            "prompt": "AccountHeader reads profile.user.name while user is null.",
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["submission"]["reasonable"] is False


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


def test_judge_reads_a_web_search_even_if_it_calls_the_prompt_reasonable():
    verdict = parse_verdict('Sure. {"reasonable": true, "reason": "The message names the function."}')
    assert verdict == {"reasonable": True, "reason": "The message names the function."}
    assert parse_verdict("no json here") is None
    trace = call_trace(
        {
            "output": [{"type": "web_search_call"}, {"type": "message", "content": "done"}],
            "usage": {"input_tokens": 40, "output_tokens": 12, "num_server_side_tools_used": 1},
        }
    )
    assert trace["serverSideTools"] == 1
    assert trace["inputTokens"] == 40
    reasonable, reason, judged = finalize_verdict(
        verdict,
        trace,
        local_reasonable=True,
        local_reason="local",
    )
    assert reasonable is False
    assert judged is True
    assert "searched the web" in reason


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
