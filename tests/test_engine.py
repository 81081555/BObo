import unittest

from game.engine import GuessNumberGame, GameRuleError


class GuessNumberGameTests(unittest.TestCase):
    def test_red_green_only_mode(self):
        game = GuessNumberGame(yellow_hint_enabled=False)
        game.register_player("A", "1234", "nA")
        game.register_player("B", "5678", "nB")

        game.submit_guess("A", "1456")
        game.submit_guess("B", "9999")
        result = game.resolve_round("A", "B")

        self.assertEqual(result["A"].colors, ["red", "red", "red", "red"])

    def test_yellow_hint_mode(self):
        game = GuessNumberGame(yellow_hint_enabled=True)
        game.register_player("A", "1234", "nA")
        game.register_player("B", "4411", "nB")

        game.submit_guess("A", "1444")
        game.submit_guess("B", "9999")
        result = game.resolve_round("A", "B")

        self.assertEqual(result["A"].colors, ["yellow", "green", "yellow", "red"])

    def test_draw_when_both_hit_in_same_round(self):
        game = GuessNumberGame()
        game.register_player("A", "1234", "nA")
        game.register_player("B", "5678", "nB")

        game.submit_guess("A", "5678")
        game.submit_guess("B", "1234")
        game.resolve_round("A", "B")

        self.assertTrue(game.draw)
        self.assertIsNone(game.winner)

    def test_reveal_verification(self):
        game = GuessNumberGame()
        game.register_player("A", "0123", "nonce")

        self.assertTrue(game.verify_reveal("A", "0123", "nonce"))
        self.assertFalse(game.verify_reveal("A", "0123", "other"))

    def test_invalid_code(self):
        game = GuessNumberGame()
        with self.assertRaises(GameRuleError):
            game.register_player("A", "12A4", "x")


if __name__ == "__main__":
    unittest.main()
