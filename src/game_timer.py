"""
File: game_timer.py
Module: GameTimer

Description:
    Tracks how long the current round of Minesweeper has been running.
    The timer starts on the first uncovered cell, stops when the game is
    won or lost, and resets when a new game begins. It only measures
    time; the UI decides when to start, stop, and draw it.

Inputs:
    An optional clock function that returns the current time in seconds.

Outputs:
    Elapsed time in whole seconds and as MM:SS text.

Created:
    Wen H. Tan
    2026-10-09

Course:
    EECS 581 - Project 2 (Minesweeper)
"""

import time

# The display has two digits for minutes, so stop counting at 99:59.
MAX_SECONDS = 99 * 60 + 59

def format_time(seconds):
    """Return a number of seconds as MM:SS."""
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    return f"{minutes:02d}:{seconds:02d}"

class GameTimer:
    """Stopwatch for one round of Minesweeper."""

    def __init__(self, clock=time.monotonic):
        """
        Create a stopped timer at zero.

        Args:
            clock: Function returning the current time in seconds.
                Tests pass a fake clock here so they do not have to wait.
        """
        self._clock = clock
        self._start_time = None
        self._elapsed = 0.0

    def start(self):
        """Start timing. Does nothing if already running or already stopped
        after a run, so the first uncover is the only thing that starts it."""
        if self._start_time is None and self._elapsed == 0.0:
            self._start_time = self._clock()

    def stop(self):
        """Stop timing and keep the elapsed time on display."""
        if self._start_time is not None:
            self._elapsed = self._clock() - self._start_time
            self._start_time = None

    def reset(self):
        """Stop the timer and set it back to zero for a new game."""
        self._start_time = None
        self._elapsed = 0.0

    def is_running(self):
        """Return True while the timer is counting."""
        return self._start_time is not None

    def get_elapsed_seconds(self):
        """Return the elapsed time in whole seconds, capped at 99:59."""
        if self._start_time is not None:
            elapsed = self._clock() - self._start_time
        else:
            elapsed = self._elapsed

        return max(0, min(int(elapsed), MAX_SECONDS))

    def get_text(self):
        """Return the elapsed time as MM:SS."""
        minutes, seconds = divmod(self.get_elapsed_seconds(), 60)
        return f"{minutes:02d}:{seconds:02d}"