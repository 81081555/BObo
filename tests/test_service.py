import unittest

from game.engine import GameRuleError
from game.service import RoomManager


class RoomManagerTests(unittest.TestCase):
    def test_create_join_and_round(self):
        m = RoomManager()
        a = m.create_room("A", "1234", "n1", yellow_hint_enabled=True)
        b = m.join_room(a["room_id"], "B", "5678", "n2")

        m.stage_guess(a["room_id"], a["player_id"], "5678")
        m.stage_guess(a["room_id"], b["player_id"], "1234")

        state_a = m.state(a["room_id"], a["player_id"])
        self.assertTrue(state_a["draw"])
        self.assertEqual(len(state_a["rounds"]), 1)

    def test_full_room(self):
        m = RoomManager()
        a = m.create_room("A", "1234", "n1")
        m.join_room(a["room_id"], "B", "5678", "n2")
        with self.assertRaises(GameRuleError):
            m.join_room(a["room_id"], "C", "9999", "n3")


if __name__ == '__main__':
    unittest.main()
