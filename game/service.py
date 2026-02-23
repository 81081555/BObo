from __future__ import annotations

from dataclasses import dataclass, field
from secrets import token_urlsafe
from typing import Dict, List, Optional

from game.engine import GuessNumberGame, GameRuleError, RoundResult, validate_code


@dataclass
class PlayerRoundView:
    round_no: int
    guess: str
    colors: List[str]


@dataclass
class Room:
    room_id: str
    yellow_hint_enabled: bool
    game: GuessNumberGame
    players: Dict[str, str] = field(default_factory=dict)
    player_order: List[str] = field(default_factory=list)
    history: Dict[str, List[PlayerRoundView]] = field(default_factory=dict)
    submitted_this_round: List[str] = field(default_factory=list)

    def to_state(self, player_id: str) -> Dict[str, object]:
        if player_id not in self.players:
            raise GameRuleError("unknown player")
        opponent = next((pid for pid in self.player_order if pid != player_id), None)
        return {
            "room_id": self.room_id,
            "you": {"id": player_id, "name": self.players[player_id]},
            "opponent": None
            if opponent is None
            else {"id": opponent, "name": self.players[opponent]},
            "ready": len(self.players) == 2,
            "winner": self.game.winner,
            "draw": self.game.draw,
            "rounds": [rv.__dict__ for rv in self.history.get(player_id, [])],
            "submitted": player_id in self.submitted_this_round,
            "yellow_hint_enabled": self.yellow_hint_enabled,
        }


class RoomManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, Room] = {}

    def _new_id(self, size: int = 6) -> str:
        return token_urlsafe(size).replace("-", "").replace("_", "")[:size]

    def create_room(self, name: str, secret: str, nonce: str, yellow_hint_enabled: bool = False) -> Dict[str, str]:
        validate_code(secret)
        room_id = self._new_id()
        player_id = self._new_id(8)
        game = GuessNumberGame(yellow_hint_enabled=yellow_hint_enabled)
        game.register_player(player_id, secret, nonce)

        room = Room(room_id=room_id, yellow_hint_enabled=yellow_hint_enabled, game=game)
        room.players[player_id] = name or "玩家A"
        room.player_order.append(player_id)
        room.history[player_id] = []
        self.rooms[room_id] = room
        return {"room_id": room_id, "player_id": player_id}

    def join_room(self, room_id: str, name: str, secret: str, nonce: str) -> Dict[str, str]:
        validate_code(secret)
        room = self.rooms.get(room_id)
        if room is None:
            raise GameRuleError("room not found")
        if len(room.players) >= 2:
            raise GameRuleError("room is full")

        player_id = self._new_id(8)
        room.game.register_player(player_id, secret, nonce)
        room.players[player_id] = name or "玩家B"
        room.player_order.append(player_id)
        room.history[player_id] = []
        return {"room_id": room_id, "player_id": player_id}

    def submit_guess(self, room_id: str, player_id: str, guess: str) -> Optional[Dict[str, RoundResult]]:
        room = self.rooms.get(room_id)
        if room is None:
            raise GameRuleError("room not found")
        if len(room.players) < 2:
            raise GameRuleError("waiting for second player")

        room.game.submit_guess(player_id, guess)
        if player_id not in room.submitted_this_round:
            room.submitted_this_round.append(player_id)

        if len(room.submitted_this_round) < 2:
            return None

        p1, p2 = room.player_order[0], room.player_order[1]
        results = room.game.resolve_round(p1, p2)

        submissions: Dict[str, str] = getattr(room, "_last_round_guesses")
        round_no = len(room.history[p1]) + 1
        room.history[p1].append(
            PlayerRoundView(round_no=round_no, guess=submissions[p1], colors=results[p1].colors)
        )
        room.history[p2].append(
            PlayerRoundView(round_no=round_no, guess=submissions[p2], colors=results[p2].colors)
        )
        room.submitted_this_round.clear()
        room._last_round_guesses = {}
        return results

    def stage_guess(self, room_id: str, player_id: str, guess: str) -> Optional[Dict[str, RoundResult]]:
        room = self.rooms.get(room_id)
        if room is None:
            raise GameRuleError("room not found")
        if not hasattr(room, "_last_round_guesses"):
            room._last_round_guesses = {}
        room._last_round_guesses[player_id] = guess
        return self.submit_guess(room_id, player_id, guess)

    def state(self, room_id: str, player_id: str) -> Dict[str, object]:
        room = self.rooms.get(room_id)
        if room is None:
            raise GameRuleError("room not found")
        return room.to_state(player_id)
