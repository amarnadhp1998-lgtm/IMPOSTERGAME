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

## Run continuously from GitHub

GitHub Actions is for finite jobs and stops GitHub-hosted jobs after at most six hours, so it is not an always-on bot host. This repository includes a Dockerfile for a persistent worker host such as Railway.

1. Create a Railway project and choose **Deploy from GitHub repo**, then select `amarnadhp1998-lgtm/IMPOSTERGAME` on the `master` branch.
2. Railway detects the Dockerfile and builds the bot. In the service's **Variables** tab, set `BOT_TOKEN` to the current BotFather token. Never put it in a repository file.
3. Deploy the service, then check its logs for `Imposter bot is running`.

Railway's Hobby plan currently has a $5/month minimum usage commitment. GitHub pushes to the connected branch trigger redeploys. Game sessions are in memory, so active games reset when the host restarts or deploys a new version; the local JSON scoreboard is not durable unless a persistent volume is configured.

## Temporary test with GitHub Actions

The `Temporary Telegram bot test` workflow starts only when manually dispatched and stops after six hours. Add the new token as a repository Actions secret named `BOT_TOKEN` under **Settings → Secrets and variables → Actions**. Then open **Actions**, select the workflow, choose **Run workflow**, and start it from `master`. Cancel the workflow run to stop the bot earlier. The workflow creates its runtime config from the token-free example; it does not read or publish the local `config.py`.
