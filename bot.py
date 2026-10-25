"""Telegram interface for the local Imposter word game."""

import html
import json
import logging
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatType
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from config import (
    BOT_TOKEN, MIN_PLAYERS, MAX_PLAYERS, CLUE_TIME, DISCUSSION_TIME,
    SCORE_PLAYER_WIN, SCORE_IMPOSTER_SURVIVE, SCORE_IMPOSTER_CORRECT_GUESS,
)
try:
    from config import SCORES_FILE
except ImportError:
    SCORES_FILE = Path("scores.json")
from game import initialize_game, choose_first_player

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
active_games = {}
try:
    scores = json.loads(SCORES_FILE.read_text(encoding="utf-8")) if SCORES_FILE.exists() else {}
except (OSError, json.JSONDecodeError):
    logger.exception("Could not read score file; starting with an empty score table")
    scores = {}


def award(player_id, name, points):
    record = scores.setdefault(str(player_id), {"name": name, "points": 0})
    record["name"] = name
    record["points"] += points
    try:
        SCORES_FILE.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        logger.exception("Could not persist scores")


def esc(value):
    return html.escape(str(value), quote=True)


def is_group(update):
    return update.effective_chat and update.effective_chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)


def cancel_jobs(context, chat_id):
    for job in context.job_queue.get_jobs_by_name(f"game:{chat_id}"):
        job.schedule_removal()


def host_only(update, game):
    return update.effective_user and update.effective_user.id == game["host_id"]


async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Start / welcome"), BotCommand("newgame", "Create a game"),
        BotCommand("endgame", "End the game (host)"), BotCommand("poll", "Start voting (host)"),
        BotCommand("endpoll", "Close voting (host)"), BotCommand("guess", "Imposter: guess the word in DM"),
        BotCommand("scores", "Show group scores"),
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.effective_message.reply_text("👋 Welcome to Imposter! Add me to your group, create a game with /newgame, then open this chat and press Start so I can send your secret card.")
    else:
        await new_game(update, context)


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group(update):
        await update.effective_message.reply_text("Please use /newgame in your Telegram group.")
        return
    chat_id = update.effective_chat.id
    if chat_id in active_games:
        await update.effective_message.reply_text("A game is already active. The host can use /endgame to reset it.")
        return
    user = update.effective_user
    active_games[chat_id] = {
        "host_id": user.id, "host_name": user.full_name, "players": {user.id: user.full_name},
        "alive": set(), "status": "LOBBY", "data": None, "votes": {}, "message_id": None,
    }
    await render_lobby(context, chat_id, update.effective_message)


def lobby_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Join Game", callback_data="join")],
        [InlineKeyboardButton("🚀 Start Game", callback_data="start")],
    ])


async def render_lobby(context, chat_id, message=None, query=None):
    game = active_games[chat_id]
    roster = "\n".join(f"{i}. {esc(name)}" for i, name in enumerate(game["players"].values(), 1))
    text = (f"🎭 <b>Imposter Game Lobby</b>\n\nHost: {esc(game['host_name'])}\n\n"
            f"🎮 Players: {len(game['players'])}/{MAX_PLAYERS}\n{roster}\n\n"
            f"Minimum players: {MIN_PLAYERS}\nJoin below, then the host starts the game.")
    if query:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=lobby_markup())
    elif message:
        sent = await message.reply_text(text, parse_mode="HTML", reply_markup=lobby_markup())
        game["message_id"] = sent.message_id


async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_group(update):
        await update.effective_message.reply_text("Use /endgame in the game group.")
        return
    game = active_games.get(chat_id)
    if not game:
        await update.effective_message.reply_text("There is no active game.")
    elif not host_only(update, game):
        await update.effective_message.reply_text("Only the game host can end this game.")
    else:
        cancel_jobs(context, chat_id)
        del active_games[chat_id]
        await update.effective_message.reply_text("🛑 Game ended and reset. Use /newgame to start again.")


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group(update):
        await update.effective_message.reply_text("Use /poll in the game group.")
        return
    chat_id = update.effective_chat.id
    game = active_games.get(chat_id)
    if not game or game["status"] == "LOBBY":
        await update.effective_message.reply_text("Start a game first with /newgame.")
    elif not host_only(update, game):
        await update.effective_message.reply_text("Only the host can start voting.")
    elif game["status"] == "VOTING":
        await update.effective_message.reply_text("Voting is already open.")
    else:
        await start_poll(context, chat_id)


async def start_poll(context, chat_id):
    game = active_games.get(chat_id)
    if not game:
        return
    cancel_jobs(context, chat_id)
    game["status"] = "VOTING"
    game["votes"] = {}
    buttons = [[InlineKeyboardButton(esc(game["players"][pid]), callback_data=f"vote:{pid}")]
               for pid in game["players"] if pid in game["alive"]]
    await context.bot.send_message(chat_id, "🗳 <b>Voting is open</b>\nChoose the player you suspect. Votes are private; the host can close the poll with /endpoll.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))


async def endpoll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group(update):
        await update.effective_message.reply_text("Use /endpoll in the game group.")
        return
    chat_id = update.effective_chat.id
    game = active_games.get(chat_id)
    if not game or game["status"] != "VOTING":
        await update.effective_message.reply_text("There is no active vote.")
    elif not host_only(update, game):
        await update.effective_message.reply_text("Only the host can close voting.")
    else:
        await resolve_vote(context, chat_id)


async def resolve_vote(context, chat_id):
    game = active_games.get(chat_id)
    if not game or game["status"] != "VOTING":
        return
    votes = game["votes"]
    counts = {pid: 0 for pid in game["players"] if pid in game["alive"]}
    for target in votes.values():
        if target in counts:
            counts[target] += 1
    if not votes:
        game["status"] = "IN_PROGRESS"
        await context.bot.send_message(chat_id, "📊 No votes were cast. Nobody was eliminated.")
        await schedule_discussion(context, chat_id)
        return
    high = max(counts.values(), default=0)
    leaders = [pid for pid, count in counts.items() if count == high]
    summary = "\n".join(f"{esc(game['players'][pid])} — {count}" for pid, count in sorted(counts.items(), key=lambda item: (-item[1], game['players'][item[0]].casefold())))
    if len(leaders) != 1:
        game["status"] = "IN_PROGRESS"
        game["votes"] = {}
        await context.bot.send_message(chat_id, f"📊 <b>Voting results</b>\n{summary}\n\n⚖️ Tie. Nobody was eliminated.", parse_mode="HTML")
        await schedule_discussion(context, chat_id)
        return
    eliminated = leaders[0]
    game["alive"].discard(eliminated)
    role = game["data"]["roles"][eliminated]["role"]
    details = f"📊 <b>Voting results</b>\n{summary}\n\n🚨 {esc(game['players'][eliminated])} was eliminated ({role.title()})."
    await context.bot.send_message(chat_id, details, parse_mode="HTML")
    if not game["data"]["imposter_ids"].intersection(game["alive"]):
        await finish_game(context, chat_id, "crew", "🎉 Crewmates win! All imposters were eliminated.")
    elif len(game["data"]["imposter_ids"].intersection(game["alive"])) >= len(game["alive"]) - len(game["data"]["imposter_ids"].intersection(game["alive"])):
        await finish_game(context, chat_id, "imposter", "😈 Imposters win! They now match or outnumber the crew.")
    else:
        game["status"] = "IN_PROGRESS"
        game["votes"] = {}
        await schedule_discussion(context, chat_id)


async def finish_game(context, chat_id, winner, message):
    game = active_games.get(chat_id)
    if not game:
        return
    cancel_jobs(context, chat_id)
    if winner == "crew":
        winners = [pid for pid in game["alive"] if pid not in game["data"]["imposter_ids"]]
        for pid in winners:
            award(pid, game["players"][pid], SCORE_PLAYER_WIN)
        score_text = "Crewmates who survived earn 100 points each."
    else:
        winners = list(game["data"]["imposter_ids"].intersection(game["alive"]))
        for pid in winners:
            award(pid, game["players"][pid], SCORE_IMPOSTER_SURVIVE)
        score_text = "Surviving imposters earn 150 points each."
    game["status"] = "FINISHED"
    await context.bot.send_message(chat_id, f"{message}\n\n🔑 The word was <b>{esc(game['data']['secret_word'])}</b> ({esc(game['data']['category'])}).\n{score_text}\nUse /newgame for another round.", parse_mode="HTML")
    del active_games[chat_id]


async def schedule_discussion(context, chat_id):
    game = active_games.get(chat_id)
    if not game:
        return
    game["status"] = "DISCUSSION"
    cancel_jobs(context, chat_id)
    await context.bot.send_message(chat_id, f"💬 Discuss for {DISCUSSION_TIME} seconds, then voting opens automatically.")
    context.job_queue.run_once(discussion_finished, max(1, DISCUSSION_TIME), data=chat_id, name=f"game:{chat_id}")


async def discussion_finished(context):
    chat_id = context.job.data
    game = active_games.get(chat_id)
    if game and game["status"] == "DISCUSSION":
        await start_poll(context, chat_id)


async def clue_finished(context):
    chat_id = context.job.data
    game = active_games.get(chat_id)
    if not game or game["status"] != "CLUES":
        return
    data = game["data"]
    data["clue_index"] += 1
    if data["clue_index"] >= len(data["clue_order"]):
        data["clue_index"] = 0
        data["round"] += 1
        if data["round"] > data["clue_rounds"]:
            await schedule_discussion(context, chat_id)
            return
    await prompt_clue(context, chat_id)


async def prompt_clue(context, chat_id):
    game = active_games.get(chat_id)
    if not game:
        return
    data = game["data"]
    player_id = data["clue_order"][data["clue_index"]]
    game["status"] = "CLUES"
    await context.bot.send_message(chat_id, f"🗣 Clue round {data['round']}/{data['clue_rounds']}: <b>{esc(game['players'][player_id])}</b> is up. You have {CLUE_TIME} seconds.", parse_mode="HTML")
    cancel_jobs(context, chat_id)
    context.job_queue.run_once(clue_finished, max(1, CLUE_TIME), data=chat_id, name=f"game:{chat_id}")


async def send_secret_cards(context, chat_id):
    game = active_games[chat_id]
    data = game["data"]
    for player_id, role in data["roles"].items():
        if role["role"] == "imposter":
            text = f"🔴 <b>Your secret card</b>\nYou are an <b>IMPOSTER</b>.\nCategory: <b>{esc(data['category'])}</b>. You do not know the word.\n\nBlend in. If enabled, use /guess WORD here in this private chat."
        else:
            text = f"🟢 <b>Your secret card</b>\nCategory: <b>{esc(data['category'])}</b>\nSecret word: <b>{esc(role['secret_word'])}</b>\n\nGive a clue without saying the word."
        try:
            await context.bot.send_message(player_id, text, parse_mode="HTML")
        except TelegramError as exc:
            logger.info("Could not deliver secret card to user %s: %s", player_id, exc)
            await context.bot.send_message(chat_id, f"⚠️ {esc(game['players'][player_id])}, open a private chat with me and press Start so I can send your secret card. The host can restart with /endgame if needed.", parse_mode="HTML")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat.id if query.message else None
    game = active_games.get(chat_id)
    if query.data == "join":
        if not game or game["status"] != "LOBBY":
            await query.answer("This lobby is no longer open.", show_alert=True)
        elif user.id in game["players"]:
            await query.answer("You already joined.")
        elif len(game["players"]) >= MAX_PLAYERS:
            await query.answer("The lobby is full.", show_alert=True)
        else:
            game["players"][user.id] = user.full_name
            await query.answer("You joined the game!")
            await render_lobby(context, chat_id, query=query)
        return
    if query.data == "start":
        if not game or game["status"] != "LOBBY":
            await query.answer("This lobby is no longer active.", show_alert=True)
        elif user.id != game["host_id"]:
            await query.answer("Only the host can start the game.", show_alert=True)
        elif len(game["players"]) < MIN_PLAYERS:
            await query.answer(f"Need at least {MIN_PLAYERS} players.", show_alert=True)
        else:
            try:
                data = initialize_game(game["players"])
            except (ValueError, KeyError) as exc:
                logger.exception("Game initialization failed")
                await query.answer("Could not start the game. Please try again.", show_alert=True)
                await query.message.reply_text(f"Game setup failed: {esc(exc)}", parse_mode="HTML")
                return
            game["data"] = data
            game["alive"] = set(game["players"])
            game["status"] = "CLUES"
            await query.answer("Game started!")
            await query.edit_message_text(f"🚀 <b>Game started</b>\nPlayers: {len(game['players'])}\nImposters: {len(data['imposter_ids'])}\nClue rounds: {data['clue_rounds']}\nSecret cards are being sent privately.\nFirst up: {esc(game['players'][choose_first_player(data)])}", parse_mode="HTML")
            logger.info("Game started in %s with %s imposters", chat_id, len(data["imposter_ids"]))
            await send_secret_cards(context, chat_id)
            await prompt_clue(context, chat_id)
        return
    if query.data.startswith("vote:"):
        try:
            target_id = int(query.data.split(":", 1)[1])
        except ValueError:
            await query.answer("Invalid vote button.", show_alert=True)
            return
        if not game or game["status"] != "VOTING":
            await query.answer("Voting is closed.", show_alert=True)
        elif user.id not in game["alive"]:
            await query.answer("Only active players can vote.", show_alert=True)
        elif target_id not in game["alive"]:
            await query.answer("That player is no longer in the game.", show_alert=True)
        else:
            game["votes"][user.id] = target_id
            await query.answer(f"Vote saved for {game['players'][target_id]}.")
            if len(game["votes"]) == len(game["alive"]):
                await resolve_vote(context, chat_id)
        return
    await query.answer("This button is no longer active.", show_alert=True)


async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != ChatType.PRIVATE:
        await update.effective_message.reply_text("For privacy, send /guess WORD in a private chat with the bot.")
        return
    if not context.args:
        await update.effective_message.reply_text("Use /guess WORD to make your secret guess.")
        return
    player_id = update.effective_user.id
    target_game = next(((cid, g) for cid, g in active_games.items() if g["status"] in ("CLUES", "DISCUSSION", "VOTING") and player_id in g["alive"] and player_id in g["data"]["imposter_ids"]), None)
    if not target_game:
        await update.effective_message.reply_text("You are not an active imposter in a game.")
        return
    chat_id, game = target_game
    data = game["data"]
    if player_id in data["guessed"]:
        await update.effective_message.reply_text("You have already used your guess.")
    elif " ".join(context.args).strip().casefold() == data["secret_word"].casefold():
        data["guessed"].add(player_id)
        award(player_id, game["players"][player_id], SCORE_IMPOSTER_CORRECT_GUESS)
        await update.effective_message.reply_text("✅ Correct! You earn 200 points.")
        await finish_game(context, chat_id, "imposter", f"😈 {esc(game['players'][player_id])} guessed the word correctly. Imposters win!")
    else:
        data["guessed"].add(player_id)
        await update.effective_message.reply_text("❌ Wrong guess. You cannot guess again this game.")


async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group(update):
        await update.effective_message.reply_text("Use /scores in a game group.")
        return
    game = active_games.get(update.effective_chat.id)
    ranked = sorted(((int(record.get("points", 0)), str(pid), record.get("name", str(pid))) for pid, record in scores.items()), key=lambda item: (-item[0], item[2].casefold()))
    if not ranked:
        await update.effective_message.reply_text("No scores yet. Finish a game to earn points.")
        return
    await update.effective_message.reply_text("🏆 <b>Scores</b>\n" + "\n".join(f"{esc(name)} — {points}" for points, _, name in ranked), parse_mode="HTML")


async def error_handler(update, context):
    logger.error("Unhandled update error", exc_info=context.error)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN in config.py or the BOT_TOKEN environment variable.")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    if app.job_queue is None:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("endgame", endgame))
    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(CommandHandler("endpoll", endpoll))
    app.add_handler(CommandHandler("guess", guess))
    app.add_handler(CommandHandler("scores", score_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    print("🤖 Imposter bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
