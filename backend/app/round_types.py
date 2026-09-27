"""Shared types for a round. Kept separate so build rounds can use them without a cycle."""

from __future__ import annotations

from dataclasses import dataclass

from .carbon import BUDGET_TOKENS


@dataclass(frozen=True)
class Fact:
    """One thing the model needs from the latest message.

    needs is a tuple of groups. Every group has to match somewhere in the
    message, and a group matches if any one of its regexes does. Regexes are
    case-insensitive. Most facts have a single group.
    """

    id: str
    label: str
    needs: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Samples:
    """Server-only example prompts. Tests and the rehearsal buttons use them."""

    adequate: str  # every fact, plus what you want. Should grade A+.
    bare: str  # every fact, but no ask. Should grade A.
    partial: str  # one fact left out, with an ask. Should grade C.
    vague: str  # no facts. Should grade F.
    leak: str = ""  # only for rounds with a credential. Always F.


@dataclass(frozen=True)
class Part:
    """One collaborator's piece of a turn. anchor is server-only."""

    role: str
    title: str
    body: str
    anchor: str


@dataclass(frozen=True)
class Beat:
    """One request in a thread."""

    ask: str
    fixture_title: str
    fixture: str
    facts: tuple[Fact, ...]
    simulated_reply: str
    samples: Samples
    target_tokens: int = BUDGET_TOKENS
    # Regexes that must never appear in a prompt (a credential, for example).
    forbidden: tuple[str, ...] = ()
    # Collaborate mode deals one part to each person in a pair. See Part.
    parts: tuple[Part, ...] = ()

    @property
    def anchors(self) -> tuple[str, ...]:
        """Plain-language fact list. The Grok reviewer reads this."""
        return tuple(fact.label for fact in self.facts)


@dataclass(frozen=True)
class Challenge:
    id: str
    title: str
    brief: str
    hint: str
    beats: tuple[Beat, ...]
    # Build rounds ship a few starter files, the solved copies, and a check
    # that both functions work together. Empty for the other rounds.
    files: tuple[tuple[str, str], ...] = ()
    solutions: tuple[tuple[str, str], ...] = ()
    check: str = ""
    # Offline edits only: a file is solved when the prompt names it and one of these words.
    gates: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def target_tokens(self) -> int:
        return self.beats[-1].target_tokens if self.beats else 0

    @property
    def example_efficient(self) -> tuple[str, ...]:
        return tuple(beat.samples.adequate for beat in self.beats)

    @property
    def example_vague(self) -> tuple[str, ...]:
        return tuple(beat.samples.vague for beat in self.beats)

    def example_whole_file(self, step: int) -> str:
        """What a player sends when they paste everything they have seen so far."""
        pasted = "\n\n".join(beat.fixture for beat in self.beats[: step + 1])
        return f"Fix this.\n\n{pasted}"
