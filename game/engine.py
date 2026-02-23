from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Dict, List, Literal, Optional


Color = Literal["green", "yellow", "red"]


class GameRuleError(ValueError):
    """Raised when an input violates game rules."""


@dataclass(frozen=True)
class CommitProof:
    """Commit-reveal proof for anti-cheat verification."""

    digest: str

    @staticmethod
    def build(secret: str, nonce: str) -> "CommitProof":
        validate_code(secret)
        return CommitProof(digest=sha256(f"{secret}:{nonce}".encode("utf-8")).hexdigest())

    def verify(self, secret: str, nonce: str) -> bool:
        validate_code(secret)
        return self.digest == sha256(f"{secret}:{nonce}".encode("utf-8")).hexdigest()


def validate_code(code: str) -> None:
    if len(code) != 4 or not code.isdigit():
        raise GameRuleError("code must be exactly 4 digits")


@dataclass
class RoundResult:
    colors: List[Color]

    @property
    def is_all_green(self) -> bool:
        return all(c == "green" for c in self.colors)


@dataclass
class GuessNumberGame:
    """Two-player turn-based guessing game engine."""

    yellow_hint_enabled: bool = False
    round_timeout_sec: int = 45
    secrets: Dict[str, str] = field(default_factory=dict)
    commits: Dict[str, CommitProof] = field(default_factory=dict)
    round_submissions: Dict[str, str] = field(default_factory=dict)
    winner: Optional[str] = None
    draw: bool = False

    def register_player(self, player_id: str, secret: str, nonce: str) -> None:
        if player_id in self.secrets:
            raise GameRuleError("player already registered")
        validate_code(secret)
        self.secrets[player_id] = secret
        self.commits[player_id] = CommitProof.build(secret, nonce)

    def submit_guess(self, player_id: str, guess: str) -> None:
        if self.winner or self.draw:
            raise GameRuleError("game already finished")
        if player_id not in self.secrets:
            raise GameRuleError("unknown player")
        validate_code(guess)
        self.round_submissions[player_id] = guess

    def force_timeout_submission(self, player_id: str) -> None:
        """Timeout strategy: submit a guaranteed non-winning dummy guess."""
        if player_id not in self.secrets:
            raise GameRuleError("unknown player")
        self.round_submissions[player_id] = "9999"

    def resolve_round(self, player_a: str, player_b: str) -> Dict[str, RoundResult]:
        if player_a not in self.round_submissions or player_b not in self.round_submissions:
            raise GameRuleError("both players must submit before round resolution")

        guess_a = self.round_submissions[player_a]
        guess_b = self.round_submissions[player_b]
        secret_a = self.secrets[player_a]
        secret_b = self.secrets[player_b]

        result_for_a = RoundResult(colors=self._score_guess(guess_a, secret_b))
        result_for_b = RoundResult(colors=self._score_guess(guess_b, secret_a))

        a_win = result_for_a.is_all_green
        b_win = result_for_b.is_all_green
        if a_win and b_win:
            self.draw = True
        elif a_win:
            self.winner = player_a
        elif b_win:
            self.winner = player_b

        self.round_submissions.clear()
        return {player_a: result_for_a, player_b: result_for_b}

    def _score_guess(self, guess: str, secret: str) -> List[Color]:
        if not self.yellow_hint_enabled:
            return ["green" if g == s else "red" for g, s in zip(guess, secret)]

        colors: List[Color] = ["red"] * 4
        secret_pool: Dict[str, int] = {}

        for i, (g, s) in enumerate(zip(guess, secret)):
            if g == s:
                colors[i] = "green"
            else:
                secret_pool[s] = secret_pool.get(s, 0) + 1

        for i, g in enumerate(guess):
            if colors[i] == "green":
                continue
            remain = secret_pool.get(g, 0)
            if remain > 0:
                colors[i] = "yellow"
                secret_pool[g] = remain - 1

        return colors

    def verify_reveal(self, player_id: str, secret: str, nonce: str) -> bool:
        proof = self.commits.get(player_id)
        if proof is None:
            raise GameRuleError("unknown player")
        return proof.verify(secret, nonce)
