# to run this file, run the following command in terminal:
# python -m unittest tests.test_game

import unittest
from unittest.mock import Mock

from src.board import BoardManager
from src.cell import Cell
from src.game import Game, GameStatus
from src.number_calculator import calculateNumbers


class TestGame(unittest.TestCase):

    def setUp(self):
        self.board = BoardManager()
        self.game = Game(self.board, mine_count=10)

        # Prevent random mine placement in tests.
        self.game._mine_generator = Mock()

    def test_new_game_starts_in_progress(self):
        self.assertEqual(self.game.getStatus(), GameStatus.IN_PROGRESS)

    def test_remaining_flags_starts_equal_to_mine_count(self):
        self.assertEqual(self.game.remainingFlags(), 10)

    def test_toggle_flag_marks_and_unmarks_cell(self):
        self.game.toggleFlag(2, 3)

        self.assertTrue(self.board.getCell(2, 3).isFlagged())
        self.assertEqual(self.game.remainingFlags(), 9)

        self.game.toggleFlag(2, 3)

        self.assertTrue(self.board.getCell(2, 3).isCovered())
        self.assertEqual(self.game.remainingFlags(), 10)

    def test_toggle_flag_does_not_change_uncovered_cell(self):
        cell = self.board.getCell(1, 1)
        cell.setState(Cell.UNCOVERED)

        self.game.toggleFlag(1, 1)

        self.assertTrue(cell.isUncovered())
        self.assertEqual(self.game.remainingFlags(), 10)

    def test_toggle_flag_out_of_bounds_does_nothing(self):
        self.game.toggleFlag(-1, 0)
        self.game.toggleFlag(10, 0)
        self.game.toggleFlag(0, -1)
        self.game.toggleFlag(0, 10)

        self.assertEqual(self.game.getStatus(), GameStatus.IN_PROGRESS)
        self.assertEqual(self.game.remainingFlags(), 10)

    def test_uncover_out_of_bounds_does_nothing(self):
        status = self.game.uncover(-1, 0)

        self.assertEqual(status, GameStatus.IN_PROGRESS)
        self.assertTrue(self.board.getCell(0, 0).isCovered())

    def test_uncover_flagged_cell_does_nothing(self):
        self.game.toggleFlag(4, 4)

        status = self.game.uncover(4, 4)

        self.assertEqual(status, GameStatus.IN_PROGRESS)
        self.assertTrue(self.board.getCell(4, 4).isFlagged())

    def test_first_uncover_generates_mines_once(self):
        self.game.uncover(0, 0)
        self.game.uncover(0, 1)

        self.game._mine_generator.generateMines.assert_called_once_with(
            self.board,
            10,
            (0, 0)
        )

    def test_uncover_mine_loses_game_and_reveals_all_mines(self):
        mine_one = self.board.getCell(1, 1)
        mine_two = self.board.getCell(8, 8)

        mine_one.setMine(True)
        mine_two.setMine(True)

        # Skip random generation because mines were explicitly set.
        self.game._mines_placed = True

        status = self.game.uncover(1, 1)

        self.assertEqual(status, GameStatus.LOST)
        self.assertEqual(self.game.getStatus(), GameStatus.LOST)
        self.assertTrue(mine_one.isUncovered())
        self.assertTrue(mine_two.isUncovered())

    def test_uncover_safe_cell_reveals_it(self):
        # Give the chosen cell a nonzero count so flood fill stops there.
        self.board.getCell(5, 5).setAdjacentMines(1)
        self.game._mines_placed = True

        status = self.game.uncover(5, 5)

        self.assertEqual(status, GameStatus.IN_PROGRESS)
        self.assertTrue(self.board.getCell(5, 5).isUncovered())
        self.assertEqual(self.game._revealed_count, 1)

    def test_flood_fill_reveals_zero_area(self):
        # All cells already have zero adjacent mines by default.
        self.game._mines_placed = True

        self.game.uncover(0, 0)

        for row in range(10):
            for col in range(10):
                self.assertTrue(
                    self.board.getCell(row, col).isUncovered(),
                    f"Cell ({row}, {col}) should be uncovered"
                )

    def test_game_wins_when_all_safe_cells_are_revealed(self):
        # This setup makes every cell safe, so uncovering (0, 0)
        # flood-fills the entire board.
        winning_game = Game(self.board, mine_count=0)
        winning_game._mine_generator = Mock()
        winning_game._mines_placed = True

        status = winning_game.uncover(0, 0)

        self.assertEqual(status, GameStatus.WON)
        self.assertEqual(winning_game.getStatus(), GameStatus.WON)

    def test_no_actions_allowed_after_loss(self):
        mine = self.board.getCell(0, 0)
        mine.setMine(True)
        self.game._mines_placed = True

        self.game.uncover(0, 0)
        self.assertEqual(self.game.getStatus(), GameStatus.LOST)

        self.game.toggleFlag(3, 3)
        self.game.uncover(3, 3)

        self.assertTrue(self.board.getCell(3, 3).isCovered())
        self.assertEqual(self.game.getStatus(), GameStatus.LOST)


class TestGameWithMinesOnBoard(unittest.TestCase):
    """Win, flood-fill, and flag-count cases on a board that has real mines."""

    # Ten mines down the right-hand column (column J).
    MINES = [(row, 9) for row in range(10)]

    def setUp(self):
        self.board = BoardManager()
        self.game = Game(self.board, mine_count=len(self.MINES))
        self.game._mine_generator = Mock()

        for row, col in self.MINES:
            self.board.getCell(row, col).setMine(True)

        calculateNumbers(self.board)
        self.game._mines_placed = True

    def test_win_on_board_with_mines(self):
        # Columns A-H are all zeros, so one click opens A-I (90 safe cells).
        status = self.game.uncover(0, 0)

        self.assertEqual(status, GameStatus.WON)
        self.assertEqual(self.game._revealed_count, 90)

        for row, col in self.MINES:
            self.assertTrue(self.board.getCell(row, col).isCovered())

    def test_win_does_not_require_flags(self):
        self.game.uncover(0, 0)

        self.assertEqual(self.game.getStatus(), GameStatus.WON)
        self.assertEqual(self.game.remainingFlags(), 10)

    def test_no_win_until_last_safe_cell_is_uncovered(self):
        # Uncover the numbered column I one cell at a time; none cascade.
        for row in range(9):
            self.assertEqual(self.game.uncover(row, 8), GameStatus.IN_PROGRESS)

        self.game.uncover(9, 8)
        self.assertEqual(self.game.getStatus(), GameStatus.IN_PROGRESS)

        self.assertEqual(self.game.uncover(0, 0), GameStatus.WON)

    def test_numbered_cell_does_not_cascade(self):
        self.assertEqual(self.board.getCell(4, 8).getAdjacentMines(), 3)

        self.game.uncover(4, 8)

        self.assertEqual(self.game._revealed_count, 1)
        self.assertTrue(self.board.getCell(4, 7).isCovered())
        self.assertTrue(self.board.getCell(3, 8).isCovered())

    def test_flood_fill_stops_at_numbers_and_never_opens_mines(self):
        self.game.uncover(5, 0)

        for row in range(10):
            # The numbered border (column I) is revealed...
            self.assertTrue(self.board.getCell(row, 8).isUncovered())
            self.assertGreater(self.board.getCell(row, 8).getAdjacentMines(), 0)
            # ...but the mines behind it are not.
            self.assertTrue(self.board.getCell(row, 9).isCovered())

    def test_flood_fill_skips_flagged_cells(self):
        self.game.toggleFlag(5, 5)

        status = self.game.uncover(0, 0)

        self.assertTrue(self.board.getCell(5, 5).isFlagged())
        self.assertEqual(self.game._revealed_count, 89)
        # A wrongly flagged safe cell blocks the win until it is uncovered.
        self.assertEqual(status, GameStatus.IN_PROGRESS)

        self.game.toggleFlag(5, 5)
        self.assertEqual(self.game.uncover(5, 5), GameStatus.WON)

    def test_uncovering_same_cell_twice_counts_once(self):
        self.game.uncover(4, 8)
        self.game.uncover(4, 8)

        self.assertEqual(self.game._revealed_count, 1)

    def test_losing_keeps_safe_cells_covered(self):
        status = self.game.uncover(3, 9)

        self.assertEqual(status, GameStatus.LOST)
        for row, col in self.MINES:
            self.assertTrue(self.board.getCell(row, col).isUncovered())
        self.assertTrue(self.board.getCell(0, 0).isCovered())

    def test_loss_reveals_flagged_mines_too(self):
        self.game.toggleFlag(0, 9)

        self.game.uncover(3, 9)

        self.assertTrue(self.board.getCell(0, 9).isUncovered())

    def test_no_actions_allowed_after_win(self):
        self.game.uncover(0, 0)
        self.assertEqual(self.game.getStatus(), GameStatus.WON)

        self.game.toggleFlag(0, 9)
        self.game.uncover(0, 9)

        self.assertTrue(self.board.getCell(0, 9).isCovered())
        self.assertEqual(self.game.getStatus(), GameStatus.WON)

    def test_remaining_flags_is_mines_minus_flags(self):
        for row in range(4):
            self.game.toggleFlag(row, 9)

        self.assertEqual(self.game.remainingFlags(), 6)

    def test_more_flags_than_mines_gives_negative_remaining(self):
        # Nothing stops the player from placing an 11th flag; the count is
        # still "total mines minus placed flags".
        for col in range(9):
            self.game.toggleFlag(0, col)
        self.game.toggleFlag(1, 0)
        self.game.toggleFlag(1, 1)

        self.assertEqual(self.game.remainingFlags(), -1)

        self.game.toggleFlag(1, 1)
        self.assertEqual(self.game.remainingFlags(), 0)

    def test_has_started_only_after_first_uncover(self):
        fresh = Game(BoardManager(), mine_count=10)
        self.assertFalse(fresh.hasStarted())

        fresh.toggleFlag(0, 0)
        self.assertFalse(fresh.hasStarted())

        fresh.uncover(5, 5)
        self.assertTrue(fresh.hasStarted())


if __name__ == "__main__":
    unittest.main()