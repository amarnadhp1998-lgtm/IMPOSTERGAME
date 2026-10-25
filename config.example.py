"""Copy this file to config.py for a clean checkout, then set BOT_TOKEN."""

import os
from pathlib import Path

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MIN_PLAYERS = int(os.getenv("MIN_PLAYERS", "4"))
MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", "12"))
NUMBER_OF_IMPOSTERS = int(os.getenv("NUMBER_OF_IMPOSTERS", "1"))
CLUE_ROUNDS = int(os.getenv("CLUE_ROUNDS", "2"))
DISCUSSION_TIME = int(os.getenv("DISCUSSION_TIME", "90"))
CLUE_TIME = int(os.getenv("CLUE_TIME", "60"))
SCORE_PLAYER_WIN = 100
SCORE_IMPOSTER_SURVIVE = 150
SCORE_IMPOSTER_CORRECT_GUESS = 200
SCORES_FILE = Path("scores.json")
