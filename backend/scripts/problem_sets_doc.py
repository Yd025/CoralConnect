"""Generate PROBLEM-SETS.md from the challenge data, so the doc never drifts from the game.

Run from the backend folder:  python scripts/problem_sets_doc.py
"""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import app.grading as grading  # noqa: E402
from app.challenges import PROBLEM_SETS  # noqa: E402

ROLE = {
    "farm-water": "Farmer",
    "reef-alerts": "Reef scientist",
    "cafe-cooler": "Cafe owner",
    "signup-crash": "Club webmaster",
    "solar-battery": "Homeowner",
}

# The one or two lines on each card that actually matter.
KEY_LINES = {
    ("farm-water", 0): ["Z3    tomatoes   V3     02:00 for 90 min   540 min      44%", "11:00  V3 close   (closed by hand, Sam)"],
    ("farm-water", 1): ["sensor S3: last reading change Tue 14:12 (flat since then)", "hand probe check, Sat 09:00: 12% (dry)"],
    ("reef-alerts", 0): ["rule R1  water_temp > 29.0 C    check every 5 min    notify: SMS on every check", "texts sent overnight: 212 (all from R1)"],
    ("reef-alerts", 1): ['every text says: "R1: water_temp above 29.0"', "Thu   30.4 C           24"],
    ("cafe-cooler", 0): ["walk-in cooler     612    +71%            22 h (compressor)", "week 1: 24 min    week 2: 27 min    week 3: 2 h 55 min    week 4: 3 h 10 min"],
    ("cafe-cooler", 1): ['thermostat setpoint: 1.0 C  (changed Mar 3 by "staff")', "condenser coil last cleaned: 14 months ago (dusty)"],
    ("signup-crash", 0): ['KeyError: \'email\'   (app.py, line 42, in signup)', 'templates/signup_mobile.html:     name="Email"'],
    ("signup-crash", 1): ["duplicates: 31 pairs, almost all 1 second apart", "database: no unique constraint on email"],
    ("solar-battery", 0): ["EV charger      7.2 kW   schedule: 18:00-21:00 daily   source: battery first"],
    ("solar-battery", 1): ["Tue   cloudy     9           6 kWh          41%", "off-peak grid: 23:00-07:00 at $0.11 per kWh"],
}


def graded(text, beat):
    return grading.grade_prompt(text, beat)


def plugin_line(kind, result, baseline, beat):
    saved = baseline.effective_tokens - result.effective_tokens
    if kind == "vague":
        labels = " and ".join(grading.short_label(label) for label in result.missing)
        return f"Horrible. Grok has to go find {labels}: about {result.effective_tokens:,} tokens of searching and guessing."
    if kind == "partial":
        missing = grading.short_label(result.missing[0])
        return f"Okay, but it leaves out {missing}, so Grok looks that up (+1,200). Saves {saved:,} tokens vs the vague prompt."
    if kind == "bare":
        return f"Specific, but it never says what you want (+250). Saves {saved:,} tokens vs the vague prompt."
    return f"Efficient. Grok has what it needs. Saves {saved:,} tokens vs the vague prompt."


def beat_section(challenge, index, beat):
    turn = "Turn 1" if index == 0 else "Turn 2 (the twist)"
    lines = [f"### {turn}", "", f"**On the phone:** {beat.ask}", ""]
    lines.append("**The lines that matter on the card:**")
    lines.append("")
    lines.append("```")
    lines.extend(KEY_LINES[(challenge.id, index)])
    lines.append("```")
    lines.append("")
    lines.append("**Key details a good prompt names:**")
    lines.append("")
    for n, fact in enumerate(beat.facts, start=1):
        lines.append(f"{n}. {fact.label}")
    lines.append("")
    baseline = graded(beat.samples.vague, beat)
    lines.append("| Prompt | Tokens Grok handles | Grade | What the plugin says |")
    lines.append("| --- | --- | --- | --- |")
    for kind in ("vague", "partial", "bare", "adequate"):
        text = getattr(beat.samples, kind)
        result = graded(text, beat)
        prompt = text.replace("|", "\\|")
        lines.append(f"| {prompt} | {result.effective_tokens:,} | {result.grade} | {plugin_line(kind, result, baseline, beat)} |")
    lines.append("")
    lines.append(f"**Grok's stand-in answer** (used when there's no API key): {beat.simulated_reply}")
    lines.append("")
    return lines


def main():
    out = [
        "# CoralConnect problem sets",
        "",
        "Five role-play rounds for the booth. Each one gives the player a role, a real-looking dashboard or log, and a problem to fix by prompting Grok. "
        "The plugin judges each prompt: is it specific enough for Grok to act on, and how many tokens did it save or waste?",
        "",
        "This file is generated from `backend/app/challenges.py` (`PROBLEM_SETS`), so the numbers below are what the game actually scores. "
        "The four code-debugging rounds (`DEV_CHALLENGES`) are still in the game after these.",
        "",
        "## How a round works",
        "",
        "1. The player gets a role and a data card (a dashboard, a report, or a log).",
        "2. They write a prompt asking Grok to fix the problem. Grok answers.",
        "3. The plugin judges the prompt: horrible, okay, or efficient, and how many tokens it saved or wasted.",
        "4. A twist arrives (turn 2), and they prompt again. In Collaborate mode, the pair shares one draft.",
        "",
        "## How the judge scores a prompt",
        "",
        "Each turn has **2 key details**. A good prompt names both, plus what the player wants done.",
        "",
        "- **Each missing detail costs about 1,200 tokens**, because Grok has to go look for it or guess.",
        "- **No ask** (never says what they want) costs 250.",
        "- **The message's own tokens count too,** so pasting the whole card isn't free.",
        "- **Saved** = the vague prompt's total minus this prompt's total.",
        "",
        "| Tokens Grok handles | Grade |",
        "| --- | --- |",
        "| up to 200 | A+ |",
        "| up to 400 | A |",
        "| up to 800 | B |",
        "| up to 1,400 | C (one detail missing) |",
        "| up to 2,200 | D |",
        "| more | F (both details missing) |",
        "",
        "## For the plugin",
        "",
        "Until the plugin is wired in, `backend/app/grading.py` does this judging. To let the plugin judge instead, send it:",
        "",
        "- the player's prompt",
        "- the round's key details (the numbered list under each turn below; the game sends these as `beat.anchors`)",
        "",
        "and have it return: a verdict (efficient, okay, or horrible), the tokens it thinks Grok will spend, which details are missing, and a shorter version of the prompt that still names every detail. "
        "The game can then show \"This prompt saved 2,370 tokens\" or \"This prompt is horrible: Grok has to guess the zone.\"",
        "",
        "## Summary",
        "",
        "| # | Round | Role | Turn 1 problem | Turn 2 twist |",
        "| --- | --- | --- | --- | --- |",
    ]
    twists = {
        "farm-water": ("Zone 3's valve stays open 9 hours", "A dead sensor stops all watering"),
        "reef-alerts": ("Heat alert texts every 5 minutes", "A real bleaching week gets missed"),
        "cafe-cooler": ("Cooler door left open 3 hours a day", "Thermostat too cold, dirty coil"),
        "signup-crash": ("Phones crash on a KeyError", "31 people signed up twice"),
        "solar-battery": ("EV charging drains the battery at peak", "Cloudy days leave the car at 40%"),
    }
    for n, challenge in enumerate(PROBLEM_SETS, start=1):
        first, second = twists[challenge.id]
        out.append(f"| {n} | {challenge.title} (`{challenge.id}`) | {ROLE[challenge.id]} | {first} | {second} |")
    out.append("")
    for n, challenge in enumerate(PROBLEM_SETS, start=1):
        out.append(f"## {n}. {challenge.title}")
        out.append("")
        out.append(f"**Role:** {ROLE[challenge.id]}. {challenge.brief}")
        out.append("")
        out.append(f"**Hint shown to players:** {challenge.hint}")
        out.append("")
        for index, beat in enumerate(challenge.beats):
            out.extend(beat_section(challenge, index, beat))
    out.append("## Adding a new problem")
    out.append("")
    out.append(
        "Copy one of the `Challenge(...)` blocks in `PROBLEM_SETS`, write its data card, its 2 facts per turn (with several phrasings each), and its 4 sample prompts. "
        "Then run `cd backend && python -m pytest -q`. The tests check that every sample lands in its grade band. "
        "Regenerate this file with `cd backend && python scripts/problem_sets_doc.py`."
    )
    out.append("")
    (BACKEND.parent / "PROBLEM-SETS.md").write_text("\n".join(out))


if __name__ == "__main__":
    main()
