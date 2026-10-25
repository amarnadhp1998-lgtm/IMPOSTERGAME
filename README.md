# Telegram Imposter

A group word game with private role cards, timed clue rounds, host-controlled voting, player elimination, imposters' private word guesses, and a persistent local scoreboard.

## Run locally

Keep your existing local `config.py` with `BOT_TOKEN` set, or copy `config.example.py` to `config.py` in a fresh checkout and set `BOT_TOKEN` in the environment. The private local `config.py` is ignored by Git. The launch command is unchanged:

```powershell
python bot.py
```

Install dependencies once:

```powershell
python -m pip install -r requirements.txt
```

The bot needs a private chat initiated by each player to deliver secret cards. If a player has not pressed Start in the bot's private chat, the bot warns the group. Game state is held in memory and resets on restart; the scoreboard is stored in the ignored local `scores.json` file.

## Commands

- `/newgame` — open a group lobby; the creator becomes host.
- `/endgame` — host ends and resets the game.
- `/poll` — host opens voting early.
- `/endpoll` — host closes voting; voting also resolves when every active player votes.
- `/guess WORD` — imposters can make one guess in private chat. A correct guess wins the game.
- `/scores` — show persisted overall scores.

After configured clue rounds, a discussion timer runs and voting opens automatically. Tied votes eliminate nobody. Eliminated players cannot vote again. The game ends when all imposters are eliminated or imposters equal/outnumber the remaining crew.

## Settings

`config.py` values remain supported. Environment variables can override `MIN_PLAYERS`, `MAX_PLAYERS`, `NUMBER_OF_IMPOSTERS`, `CLUE_ROUNDS`, `DISCUSSION_TIME`, and `CLUE_TIME`. There must be at least three players and at least two crewmates; the configured imposter count is capped accordingly.

For a public repository, never commit a BotFather token. Use the token-free `config.example.py` as `config.py` in a fresh checkout and provide `BOT_TOKEN` through the environment.
