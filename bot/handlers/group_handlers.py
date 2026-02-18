"""Group command handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services import game_manager, GameState
from bot.utils import is_admin

group_router = Router()


@group_router.message(Command('start', 'help'))
async def cmd_start_help(message: Message):
    """Handle /start and /help commands in groups."""
    help_text = (
        "🎮 <b>Игра «Угадай персонажа»</b>\n\n"
        "<b>Правила:</b>\n"
        "• Один игрок загадывает персонажа\n"
        "• Остальные задают вопросы\n"
        "• Загадывающий отвечает кнопками: Да/Нет/Не знаю/Частично\n\n"
        "<b>Команды:</b>\n"
        "/startgame — начать новую игру\n"
        "/endgame — завершить игру (для загадывающего или админа)\n"
        "/status — показать статус игры\n"
        "/help — показать эту справку"
    )
    await message.answer(help_text, parse_mode='HTML')


@group_router.message(Command('startgame'))
async def cmd_startgame(message: Message):
    """Handle /startgame command in groups."""
    chat_id = message.chat.id

    if game_manager.has_active_game(chat_id):
        await message.answer("Игра уже идёт. Сначала завершите текущую игру командой /endgame.")
        return

    user_id = message.from_user.id
    username = message.from_user.username

    game_manager.create_game(chat_id, user_id, username)

    username_text = f"@{username}" if username else f"ID {user_id}"
    await message.answer(
        f"Игрок {username_text} стал загадывающим. "
        f"Напиши мне в личку команду /mygame и отправь имя персонажа."
    )


@group_router.message(Command('endgame'))
async def cmd_endgame(message: Message):
    """Handle /endgame command in groups."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    game = game_manager.get_game(chat_id)

    if not game or game.state == GameState.IDLE:
        await message.answer("Сейчас нет активной игры.")
        return

    # Check permissions
    if game.host_id != user_id:
        is_user_admin = await is_admin(chat_id, user_id)
        if not is_user_admin:
            await message.answer("Завершить игру может только загадывающий или администратор.")
            return

    # End game and send result
    game_data = game_manager.end_game(chat_id)

    if game_data and game_data.character:
        await message.answer(f"Игра окончена. Загаданный персонаж был: <b>{game_data.character}</b>", parse_mode='HTML')
    else:
        await message.answer("Игра остановлена до ввода персонажа.")


@group_router.message(Command('status'))
async def cmd_status(message: Message):
    """Handle /status command in groups."""
    chat_id = message.chat.id

    game = game_manager.get_game(chat_id)

    if not game or game.state == GameState.IDLE:
        await message.answer("Сейчас нет активной игры.")
        return

    if game.state == GameState.WAITING_CHARACTER:
        username_text = f"@{game.host_username}" if game.host_username else f"ID {game.host_id}"
        await message.answer(
            f"Игра создаётся. Загадывающий: {username_text}. "
            "Ожидается, что он отправит имя персонажа боту в личку."
        )
    elif game.state == GameState.ACTIVE:
        username_text = f"@{game.host_username}" if game.host_username else f"ID {game.host_id}"
        await message.answer(
            f"Игра идёт. Загадывающий: {username_text}. "
            "Можно задавать вопросы в чате (со знаком вопроса в конце)."
        )
