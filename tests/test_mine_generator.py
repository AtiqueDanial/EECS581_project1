# to run this file, run the following command in terminal:
# python -m unittest tests.test_mine_generator

import random
import unittest

from src.board import BoardManager
from src.game import Game, GameStatus, MIN_MINES, MAX_MINES
from src.mine_generator import MineGenerator


def mine_coords(board):
    return {
        (row, col)
        for row in range(board.ROWS)
        for col in range(board.COLS)
        if board.getCell(row, col).hasMine()
    }


class TestMineGenerator(unittest.TestCase):

    def setUp(self):
        self.board = BoardManager()
        self.generator = MineGenerator()

    def test_allowed_range_is_10_to_20(self):
        self.assertEqual(MIN_MINES, 10)
        self.assertEqual(MAX_MINES, 20)

    def test_places_exact_mine_count_for_every_allowed_value(self):
        for count in range(MIN_MINES, MAX_MINES + 1):
            with self.subTest(mine_count=count):
                board = BoardManager()
                self.generator.generateMines(board, count, (0, 0))

                self.assertEqual(len(mine_coords(board)), count)

    def test_returned_set_matches_mines_on_board(self):
        mines = self.generator.generateMines(self.board, 15, (4, 4))

        self.assertEqual(len(mines), 15)
        self.assertEqual(mines, mine_coords(self.board))

    def test_mines_are_inside_the_board(self):
        mines = self.generator.generateMines(self.board, MAX_MINES, (9, 9))

        for row, col in mines:
            self.assertTrue(0 <= row < BoardManager.ROWS)
            self.assertTrue(0 <= col < BoardManager.COLS)

    def test_safe_cell_never_gets_a_mine(self):
        # Use the largest mine count so a mistake is most likely to show up.
        for trial in range(300):
            board = BoardManager()
            safe = (trial % 10, (trial // 10) % 10)

            mines = self.generator.generateMines(board, MAX_MINES, safe)

            self.assertNotIn(safe, mines)
            self.assertFalse(board.getCell(*safe).hasMine())

    def test_safe_cell_can_be_given_as_a_list(self):
        for _ in range(100):
            board = BoardManager()
            mines = self.generator.generateMines(board, MAX_MINES, [3, 7])

            self.assertNotIn((3, 7), mines)

    def test_placement_is_random(self):
        layouts = set()

        for seed in range(20):
            random.seed(seed)
            board = BoardManager()
            mines = self.generator.generateMines(board, MIN_MINES, (0, 0))
            layouts.add(frozenset(mines))

        self.assertGreater(len(layouts), 1)

    def test_same_seed_gives_same_layout(self):
        random.seed(581)
        first = self.generator.generateMines(BoardManager(), 12, (5, 5))

        random.seed(581)
        second = self.generator.generateMines(BoardManager(), 12, (5, 5))

        self.assertEqual(first, second)


class TestGameWithRealMineGenerator(unittest.TestCase):
    """Game + MineGenerator together, without mocking the generator."""

    def test_first_click_never_loses(self):
        for count in (MIN_MINES, MAX_MINES):
            for trial in range(200):
                with self.subTest(mine_count=count, trial=trial):
                    board = BoardManager()
                    game = Game(board, count)
                    row, col = trial % 10, (trial // 10) % 10

                    status = game.uncover(row, col)

                    self.assertNotEqual(status, GameStatus.LOST)
                    self.assertTrue(board.getCell(row, col).isUncovered())
                    self.assertFalse(board.getCell(row, col).hasMine())

    def test_no_mines_exist_before_first_click(self):
        board = BoardManager()
        game = Game(board, 15)

        self.assertFalse(game.hasStarted())
        self.assertEqual(mine_coords(board), set())

    def test_first_click_places_the_requested_number_of_mines(self):
        for count in range(MIN_MINES, MAX_MINES + 1):
            with self.subTest(mine_count=count):
                board = BoardManager()
                game = Game(board, count)

                game.uncover(5, 5)

                self.assertTrue(game.hasStarted())
                self.assertEqual(len(mine_coords(board)), count)

    def test_mines_are_not_regenerated_on_later_clicks(self):
        board = BoardManager()
        game = Game(board, 10)

        game.uncover(0, 0)
        before = mine_coords(board)

        for row in range(10):
            for col in range(10):
                if not board.getCell(row, col).hasMine():
                    game.uncover(row, col)

        self.assertEqual(mine_coords(board), before)

    def test_numbers_match_generated_mines(self):
        board = BoardManager()
        game = Game(board, MAX_MINES)
        game.uncover(5, 5)
        mines = mine_coords(board)

        for row in range(10):
            for col in range(10):
                if (row, col) in mines:
                    continue

                expected = sum(
                    (row + dr, col + dc) in mines
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if (dr, dc) != (0, 0)
                )
                self.assertEqual(
                    board.getCell(row, col).getAdjacentMines(), expected
                )


if __name__ == "__main__":
    unittest.main()