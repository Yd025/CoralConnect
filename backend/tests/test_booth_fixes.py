"""Fixes from the live booth test on 2026-09-27 (claude/live-site-test.md)."""

import asyncio
import os
import re
import time
from dataclasses import replace
from pathlib import Path

os.environ["XAI_API_KEY"] = ""
os.environ["DATA_PATH"] = str(Path("/tmp") / "coralconnect-pytest.json")

import pytest
from fastapi.testclient import TestClient

import app.game as game
import app.grok as grok
import app.main as main
import app.store as store_module
from app.builds import BUILD_CHALLENGES
from app.main import app
from app.models import Player, Session, Squad
from app.store import store


@pytest.fixture(autouse=True)
def clean_store():
    store.sessions.clear()
    store.cards.clear()
    grok.reset_limits()
    main.reset_limits()
    yield
    store.sessions.clear()
    store.cards.clear()
    grok.reset_limits()
    main.reset_limits()


def _compete(client, names=("Ada", "Ben")):
    created = client.post("/api/sessions", json={"mode": "compete", "challengeId": "farm-water"}).json()
    code = created["session"]["code"]
    players = [
        client.post(f"/api/sessions/{code}/join", json={"name": name, "builds": "Apps", "cares": "Planet"}).json()
        for name in names
    ]
    client.post(f"/api/sessions/{code}/start", headers={"X-Admin-Token": created["adminToken"]})
    return code, created["adminToken"], players


def _body(joined):
    return {"playerId": joined["player"]["id"], "playerToken": joined["playerToken"]}


# --- builds.py runs on Python 3.11 --------------------------------------------


def test_build_file_facts_escape_the_dot():
    file_facts = [fact for challenge in BUILD_CHALLENGES for beat in challenge.beats for fact in beat.facts if fact.id == "file"]
    assert file_facts
    for fact in file_facts:
        for pattern in fact.needs[0]:
            assert r"\." in pattern
            name = pattern.replace("\\", "")
            assert re.search(pattern, f"please edit {name} now", re.IGNORECASE)
            assert not re.search(pattern, "please edit " + name.replace(".", "X"), re.IGNORECASE)


# --- Grok: capped retry, spending caps, clipped replies ------------------------


def test_the_retry_keeps_the_reply_cap_and_drops_only_search(monkeypatch):
    monkeypatch.setattr(grok, "settings", replace(grok.settings, xai_api_key="test-key", grok_timeout=15.0))
    sent = []

    async def fake_post(body, *, timeout):
        sent.append((dict(body), timeout))
        if len(sent) == 1:
            return None
        return {"output_text": "Close V3 after 90 minutes.", "usage": {"input_tokens": 10, "output_tokens": 8}}

    monkeypatch.setattr(grok, "_post_responses", fake_post)
    answer, simulated, request, _trace = asyncio.run(grok.complete([{"role": "user", "content": "hi"}], "fallback"))
    assert answer == "Close V3 after 90 minutes."
    assert simulated is False
    first, second = sent
    assert "tools" in first[0] and first[0]["max_output_tokens"] == grok.REPLY_TOKENS
    assert "tools" not in second[0]
    assert second[0]["max_output_tokens"] == grok.REPLY_TOKENS
    assert first[1] == 15.0 and second[1] <= 10.0
    assert "tools" not in request


def test_the_spending_cap_turns_grok_calls_into_written_answers(monkeypatch):
    monkeypatch.setattr(grok, "settings", replace(grok.settings, xai_api_key="test-key", grok_calls_per_minute=2))
    assert grok._spend() and grok._spend()
    assert grok._spend() is False
    # A capped solver call falls back to the round's written answer without any network call.
    answer, simulated, _request, _trace = asyncio.run(grok.complete([{"role": "user", "content": "hi"}], "written"))
    assert (answer, simulated) == ("written", True)


def test_image_rewards_have_an_hourly_cap(monkeypatch):
    monkeypatch.setattr(grok, "settings", replace(grok.settings, xai_api_key="test-key", grok_images=True, grok_images_per_hour=1))
    assert grok._images.take(1) is True
    assert asyncio.run(grok.imagine("turtle", "Team Crab")) is None


def test_a_clipped_reply_keeps_line_breaks_and_closes_its_code_fence():
    reply = "Fix V3 like this.\n```python\n" + "valve.close()\n" * 120 + "```\nDone."
    clipped = grok._clip_reply(reply)
    assert len(clipped) <= 710
    assert "\n" in clipped
    assert clipped.count("```") % 2 == 0
    assert grok._clip_reply("One.\n\n\n\nTwo.") == "One.\n\nTwo."


def test_the_reviewer_runs_alongside_the_solver(monkeypatch):
    live = replace(grok.settings, xai_api_key="test-key", grok_images=False)
    monkeypatch.setattr(grok, "settings", live)
    monkeypatch.setattr(game, "settings", replace(game.settings, xai_api_key="", grok_images=False))

    log = []

    async def slow_complete(messages, fallback):
        log.append(("solver starts", time.monotonic()))
        await asyncio.sleep(0.2)
        log.append(("solver ends", time.monotonic()))
        return "Close V3 after 90 minutes.", False, {}, grok.empty_trace()

    async def slow_review(packet):
        log.append(("review starts", time.monotonic()))
        await asyncio.sleep(0.2)
        log.append(("review ends", time.monotonic()))
        return None

    monkeypatch.setattr(grok, "complete", slow_complete)
    monkeypatch.setattr(grok, "review_prompt", slow_review)
    client = TestClient(app)
    code, _admin, (ada, _ben) = _compete(client)
    sent = client.post(
        f"/api/sessions/{code}/submit",
        json={**_body(ada), "prompt": "Zone 3 valve V3 runs 540 min a day instead of 90. Make it close after 90 minutes."},
    )
    assert sent.status_code == 200
    when = dict(log)
    # The review started before the solver finished, so the two waits overlap.
    assert when["review starts"] < when["solver ends"]
    assert when["solver starts"] < when["review ends"]


# --- Presence: a phone that walks away doesn't hold the room open --------------


def test_compete_ends_when_the_only_unfinished_phone_has_walked_away():
    client = TestClient(app)
    code, _admin, (ada, ben) = _compete(client)
    for prompt in ("Zone 3 valve V3 is stuck open. Close it after 90 minutes.", "Sensor S3 is stuck at 44%. Ignore it."):
        client.post(f"/api/sessions/{code}/submit", json={**_body(ada), "prompt": prompt})
    assert client.get(f"/api/sessions/{code}").json()["session"]["status"] == "playing"

    session = store.get(code)
    ben_player = next(player for player in session.players if player.id == ben["player"]["id"])
    ben_player.connected = False
    ben_player.left_at = time.time() - 5
    assert client.get(f"/api/sessions/{code}").json()["session"]["status"] == "playing"

    ben_player.left_at = time.time() - game.AWAY_GRACE_SECONDS - 1
    assert client.get(f"/api/sessions/{code}").json()["session"]["status"] == "ended"


def test_a_room_where_everyone_walked_away_is_left_for_the_host():
    client = TestClient(app)
    code, _admin, _players = _compete(client)
    for player in store.get(code).players:
        player.connected = False
        player.left_at = time.time() - 600
    assert client.get(f"/api/sessions/{code}").json()["session"]["status"] == "playing"


def test_a_waiting_seat_whose_phone_left_is_not_paired():
    session = Session(
        code="ROOM", admin_token="a", mode="collaborate", status="lobby", challenge_id="team-chat",
        reef_health=100, players=[], squads=[], submissions=[], events=[], created_at=time.time(),
    )
    gone_player = Player(id="gone", token="t", name="Gone", language="Python", builds="Apps", cares="Planet",
                         joined_at=1, connected=False, left_at=time.time() - 600)
    here = Player(id="here", token="t", name="Here", language="Python", builds="Data", cares="Cost", joined_at=2)
    session.players = [gone_player, here]
    session.squads = [
        Squad(id="s1", name="Looking", player_ids=["gone"], icebreaker=""),
        Squad(id="s2", name="Looking", player_ids=["here"], icebreaker=""),
    ]
    newcomer = Player(id="new", token="t", name="New", language="Python", builds="Apps", cares="Planet", joined_at=3)
    chosen = game._pick_waiter(session, newcomer)
    assert chosen is not None and chosen.player_ids == ["here"]


def test_a_phone_socket_marks_its_player_here_then_gone():
    client = TestClient(app)
    code, _admin, (ada, _ben) = _compete(client)
    player = next(item for item in store.get(code).players if item.id == ada["player"]["id"])
    player.connected = False  # as if an earlier socket had closed
    player.left_at = time.time() - 5
    with client.websocket_connect(f"/ws/{code}") as socket:
        socket.receive_json()
        socket.send_json({"type": "hello", "playerId": ada["player"]["id"], "playerToken": "wrong"})
        socket.send_json({"type": "hello", **_body(ada)})
        message = socket.receive_json()
        shown = next(item for item in message["session"]["players"] if item["id"] == ada["player"]["id"])
        assert shown["connected"] is True
        assert player.connected is True and player.left_at == 0
    deadline = time.time() + 2
    while player.connected and time.time() < deadline:
        time.sleep(0.02)
    assert player.connected is False
    assert player.left_at > 0


# --- Save file ------------------------------------------------------------------


def test_idle_games_are_dropped_from_the_save_file_but_cards_stay():
    now = time.time()
    fresh = Session(code="NEW1", admin_token="a", mode="compete", status="playing", challenge_id="farm-water",
                    reef_health=100, players=[], squads=[], submissions=[], events=[], created_at=now - 20 * 3600,
                    updated_at=now - 60)
    stale = replace(fresh, code="OLD1", updated_at=now - 7 * 3600)
    legacy = replace(fresh, code="OLD2", updated_at=0, created_at=now - 9 * 3600)
    store.sessions.update({"NEW1": fresh, "OLD1": stale, "OLD2": legacy})
    store.cards["C1"] = {"id": "C1", "kind": "compete", "room": "OLD1"}
    assert store.prune(now) == 2
    assert set(store.sessions) == {"NEW1"}
    assert "C1" in store.cards


def test_changes_share_one_delayed_write(tmp_path, monkeypatch):
    target = store_module.Store(tmp_path / "games.json")
    monkeypatch.setattr(store_module, "SAVE_DELAY", 0.05)
    writes = []
    real_write = target._write
    monkeypatch.setattr(target, "_write", lambda text: (writes.append(text), real_write(text)))

    async def burst():
        for _ in range(20):
            target.request_save()
        await asyncio.sleep(0.3)

    asyncio.run(burst())
    assert len(writes) == 1
    assert (tmp_path / "games.json").exists()


def test_shared_draft_keystrokes_do_not_touch_the_save_file():
    client = TestClient(app)
    created = client.post("/api/sessions", json={"mode": "collaborate", "challengeId": "team-chat"}).json()
    code = created["session"]["code"]
    ada = client.post(f"/api/sessions/{code}/join", json={"name": "Ada", "builds": "Apps", "cares": "Planet"}).json()
    client.post(f"/api/sessions/{code}/join", json={"name": "Ben", "builds": "Data", "cares": "Cost"})
    session = store.get(code)
    before = session.revision
    store._dirty = False
    asyncio.run(game.update_draft(code, ada["player"]["id"], ada["playerToken"], "In messages.py ..."))
    assert session.squads[0].prompt == "In messages.py ..."
    assert session.revision == before + 1
    assert store._dirty is False


# --- Abuse: new games per address ----------------------------------------------


def test_new_games_are_capped_per_address(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, sessions_per_ip=2))
    client = TestClient(app)
    body = {"mode": "compete", "challengeId": "farm-water"}
    headers = {"X-Forwarded-For": "203.0.113.9"}
    assert client.post("/api/sessions", json=body, headers=headers).status_code == 200
    assert client.post("/api/sessions", json=body, headers=headers).status_code == 200
    third = client.post("/api/sessions", json=body, headers=headers)
    assert third.status_code == 429
    assert client.post("/api/sessions", json=body, headers={"X-Forwarded-For": "198.51.100.4"}).status_code == 200


# --- Pair introductions ------------------------------------------------------------


def test_grok_cannot_invent_a_difference_between_the_same_answers():
    members = [
        Player(id="a", token="t", name="Claude A", language="Python", builds="Apps", cares="Planet"),
        Player(id="b", token="t", name="Claude B", language="Python", builds="Apps", cares="Planet"),
    ]
    squad = Squad(id="s", name="", player_ids=["a", "b"], icebreaker="", creature="Octopus")
    game._apply_connection(
        squad,
        members,
        {"shared": "Claude A wants Planet.", "distinct": "Only Claude A builds Apps. Only Claude B builds Apps.",
         "closing": "What would you change?"},
    )
    assert squad.distinct == "Claude A and Claude B both build Apps."
    assert squad.shared == "Claude A and Claude B both want the work to care about Planet."
    assert squad.closing == "What would you change?"


def test_grok_still_writes_the_lines_when_answers_differ():
    members = [
        Player(id="a", token="t", name="Ada", language="Python", builds="Apps", cares="Planet"),
        Player(id="b", token="t", name="Ben", language="Python", builds="Data", cares="Cost"),
    ]
    squad = Squad(id="s", name="", player_ids=["a", "b"], icebreaker="", creature="Crab")
    game._apply_connection(squad, members, {"shared": "Both ship things people use.", "distinct": "Ada builds apps; Ben reads the data."})
    assert squad.shared == "Both ship things people use."
    assert squad.distinct == "Ada builds apps; Ben reads the data."
