"""Main Telegram bot for 'Guess the Character' game."""

import asyncio
import logging
import sys
import os
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest


# =============================================================================
# CONFIGURATION
# =============================================================================

class BotConfig:
    """Bot configuration."""

    BOT_TOKEN: str
    DEBUG: bool = False

    @classmethod
    def load(cls) -> None:
        """Load configuration from environment variables."""
        cls.BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        cls.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        return bool(cls.BOT_TOKEN)


BotConfig.load()


# =============================================================================
# GAME STATE
# =============================================================================

class GameState(str, Enum):
    """Game states."""
    IDLE = "idle"
    WAITING_CHARACTER = "waiting_character"
    ACTIVE = "active"


@dataclass
class GameData:
    """Game data structure."""
    state: GameState = GameState.IDLE
    host_id: Optional[int] = None
    host_username: Optional[str] = None
    character: Optional[str] = None
    waiting_for_character: bool = False
    winner_username: Optional[str] = None


class GameManager:
    """Manages game state for all groups."""

    def __init__(self):
        self.games: Dict[int, GameData] = {}

    def create_game(self, chat_id: int, host_id: int, host_username: Optional[str] = None) -> None:
        """Create a new game in waiting_character state."""
        self.games[chat_id] = GameData(
            state=GameState.WAITING_CHARACTER,
            host_id=host_id,
            host_username=host_username
        )

    def get_game(self, chat_id: int) -> Optional[GameData]:
        """Get game data for a chat."""
        return self.games.get(chat_id)

    def set_character(self, chat_id: int, character: str) -> bool:
        """Set character and transition to active state."""
        game = self.games.get(chat_id)
        if game and game.state == GameState.WAITING_CHARACTER:
            game.character = character
            game.state = GameState.ACTIVE
            game.waiting_for_character = False
            return True
        return False

    def set_waiting_for_character(self, chat_id: int, user_id: int, waiting: bool) -> bool:
        """Mark if user is waiting to input character."""
        game = self.games.get(chat_id)
        if game and game.host_id == user_id and game.state == GameState.WAITING_CHARACTER:
            game.waiting_for_character = waiting
            return True
        return False

    def set_winner(self, chat_id: int, username: str) -> None:
        """Set the winner when the character is guessed correctly."""
        game = self.games.get(chat_id)
        if game:
            game.winner_username = username

    def end_game(self, chat_id: int) -> Optional[GameData]:
        """End a game and return the game data."""
        return self.games.pop(chat_id, None)

    def get_host_game(self, user_id: int) -> Optional[tuple[int, GameData]]:
        """Find game where user is the host."""
        for chat_id, game in self.games.items():
            if game.host_id == user_id:
                return chat_id, game
        return None

    def is_waiting_for_character(self, chat_id: int, user_id: int) -> bool:
        """Check if user is waiting to input character."""
        game = self.games.get(chat_id)
        if game and game.host_id == user_id:
            return game.waiting_for_character
        return False

    def has_active_game(self, chat_id: int) -> bool:
        """Check if chat has an active game."""
        game = self.games.get(chat_id)
        return game is not None and game.state != GameState.IDLE


# Global instance
game_manager = GameManager()


# =============================================================================
# KEYBOARDS
# =============================================================================

def get_answer_keyboard():
    """Create inline keyboard for answering questions."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(text='Да', callback_data='answer:yes')],
        [InlineKeyboardButton(text='Нет', callback_data='answer:no')],
        [InlineKeyboardButton(text='Не знаю', callback_data='answer:dont_know')],
        [InlineKeyboardButton(text='Частично', callback_data='answer:partially')],
        [InlineKeyboardButton(text='✅ Угадали!', callback_data='answer:guessed')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Dictionary to map callback data to Russian answer text
ANSWER_MAP = {
    'answer:yes': 'Да',
    'answer:no': 'Нет',
    'answer:dont_know': 'Не знаю',
    'answer:partially': 'Частично',
}


# =============================================================================
# ROUTERS
# =============================================================================

group_router = Router()
private_router = Router()
question_router = Router()
callback_router = Router()


# =============================================================================
# GROUP COMMAND HANDLERS
# =============================================================================


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


async def is_admin(chat_id: int, user_id: int, bot: Bot) -> bool:
    """Check if user is admin in chat."""
    try:
        from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
        member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception:
        return False


@group_router.message(Command('endgame'))
async def cmd_endgame(message: Message, bot: Bot):
    """Handle /endgame command in groups."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    game = game_manager.get_game(chat_id)

    if not game or game.state == GameState.IDLE:
        await message.answer("Сейчас нет активной игры.")
        return

    # Check permissions
    if game.host_id != user_id:
        is_user_admin = await is_admin(chat_id, user_id, bot)
        if not is_user_admin:
            await message.answer("Завершить игру может только загадывающий или администратор.")
            return

    # End game and send result
    game_data = game_manager.end_game(chat_id)

    if game_data and game_data.character:
        if game_data.winner_username:
            await message.answer(
                f"🎉 <b>Игра окончена!</b>\nПобедитель: {game_data.winner_username}\nЗагаданный персонаж был: <b>{game_data.character}</b>",
                parse_mode='HTML'
            )
        else:
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


@group_router.message(Command('mygame'), F.chat.type.in_(["group", "supergroup"]))
async def cmd_mygame_warning(message: Message):
    """Handle /mygame command in groups - warn user to use private chat."""
    await message.answer("⚠️ Команда /mygame работает только в личных сообщениях бота. Нажмите на имя бота и напишите /mygame там.")


# =============================================================================
# PRIVATE MESSAGE HANDLERS
# =============================================================================


class CharacterInputState(StatesGroup):
    """FSM states for character input."""
    waiting_character = State()


@private_router.message(Command('start', 'help'))
async def private_cmd_start_help(message: Message):
    """Handle /start and /help commands in private chat."""
    help_text = (
        "🎮 <b>Игра «Угадай персонажа»</b>\n\n"
        "Это бот для групповой игры в угадывание персонажа.\n\n"
        "<b>Как играть:</b>\n"
        "1. Напиши /startgame в групповом чате, чтобы начать игру\n"
        "2. Ты станешь загадывающим\n"
        "3. Отправь мне в личку команду /mygame\n"
        "4. Затем напиши имя персонажа\n"
        "5. Отвечай на вопросы участников в группе кнопками\n\n"
        "<b>Команды:</b>\n"
        "/mygame — начать ввод персонажа"
    )
    await message.answer(help_text, parse_mode='HTML')


@private_router.message(Command('mygame'), F.chat.type == "private")
async def private_cmd_mygame(message: Message, state: FSMContext):
    """Handle /mygame command in private chat."""
    user_id = message.from_user.id

    host_game = game_manager.get_host_game(user_id)

    if not host_game:
        await message.answer("Сейчас нет игр, где ты должен загадать персонажа.")
        return

    chat_id, game = host_game

    game_manager.set_waiting_for_character(chat_id, user_id, True)
    await state.set_state(CharacterInputState.waiting_character)

    await message.answer("Отправь имя персонажа следующим сообщением.")


@private_router.message(StateFilter(CharacterInputState.waiting_character))
async def private_process_character_input(message: Message, state: FSMContext, bot: Bot):
    """Process character name input."""
    user_id = message.from_user.id

    host_game = game_manager.get_host_game(user_id)

    if not host_game:
        await message.answer("Ошибка: игра не найдена.")
        await state.clear()
        return

    chat_id, game = host_game

    if not game_manager.is_waiting_for_character(chat_id, user_id):
        await message.answer("Ошибка: неверное состояние игры.")
        await state.clear()
        return

    character = message.text.strip()

    if not character:
        await message.answer("Имя персонажа не может быть пустым. Попробуй ещё раз.")
        return

    success = game_manager.set_character(chat_id, character)

    if success:
        username_text = f"@{game.host_username}" if game.host_username else f"ID {game.host_id}"
        await message.answer(f"Персонаж сохранён: {character}")

        try:
            await bot.send_message(
                chat_id,
                f"Загадывающий выбрал персонажа. Можно задавать вопросы в чате (со знаком вопроса в конце)."
            )
        except Exception as e:
            await message.answer(f"Персонаж сохранён, но не удалось отправить сообщение в группу: {e}")

        await state.clear()
    else:
        await message.answer("Ошибка при сохранении персонажа. Попробуй снова.")
        await state.clear()


# =============================================================================
# QUESTION AND CALLBACK HANDLERS
# =============================================================================

@question_router.message()
async def handle_question(message: Message):
    """Handle questions in group chat."""
    chat_id = message.chat.id

    game = game_manager.get_game(chat_id)

    if not game or game.state != GameState.ACTIVE:
        return

    text = message.text or message.caption

    if not text:
        return

    # Check if message ends with '?'
    if not text.rstrip().endswith('?'):
        return

    # Check if message is a command (starts with '/')
    if text.strip().startswith('/'):
        return

    username = message.from_user.username
    username_text = f"@{username}" if username else f"ID {message.from_user.id}"

    # Store user info for callback
    question_text = text

    response_text = f"Вопрос от {username_text}: {question_text}"

    try:
        await message.answer(
            response_text,
            reply_markup=get_answer_keyboard()
        )
    except TelegramBadRequest:
        await message.answer(response_text)


@callback_router.callback_query(F.data.startswith('answer:'))
async def handle_answer_callback(callback: CallbackQuery):
    """Handle answer button clicks."""
    if not callback.message:
        await callback.answer()
        return

    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    game = game_manager.get_game(chat_id)

    if not game or game.state != GameState.ACTIVE:
        await callback.answer()
        return

    # Check if user is host
    if game.host_id != user_id:
        await callback.answer("Отвечать на вопросы может только загадывающий.")
        return

    # Check if it's "guessed" button
    if callback.data == 'answer:guessed':
        # Get username from original question message
        username_text = f"@{callback.from_user.username}" if callback.from_user.username else f"ID {callback.from_user.id}"

        # Set winner
        game_manager.set_winner(chat_id, username_text)

        # End game
        game_data = game_manager.end_game(chat_id)

        if game_data and game_data.character:
            # Edit message to show winner and character
            try:
                current_text = callback.message.text or ''
                updated_text = f"{current_text}\n\n🎉 <b>Правильно!</b>\nЗагаданный персонаж: <b>{game_data.character}</b>"

                await callback.message.edit_reply_markup(reply_markup=None)
                await callback.message.edit_text(
                    updated_text,
                    parse_mode='HTML'
                )

                # Send announcement to chat
                await callback.message.answer(
                    f"🎉 <b>Игра окончена!</b>\nУчастник {username_text} угадал персонажа: <b>{game_data.character}</b>",
                    parse_mode='HTML'
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    f"🎉 <b>Игра окончена!</b>\nУчастник {username_text} угадал персонажа: <b>{game_data.character}</b>",
                    parse_mode='HTML'
                )
        else:
            await callback.message.answer("Ошибка: персонаж не найден.")
        await callback.answer()
        return

    # Get answer text
    answer_text = ANSWER_MAP.get(callback.data, '')

    if not answer_text:
        await callback.answer()
        return

    # Edit message to show answer
    try:
        current_text = callback.message.text or ''
        updated_text = f"{current_text}\n<b>Ответ: {answer_text}</b>"

        await callback.message.edit_reply_markup(
            reply_markup=None
        )
        await callback.message.edit_text(
            updated_text,
            parse_mode='HTML'
        )

        await callback.answer()
    except TelegramBadRequest:
        await callback.answer()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main function to start the bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not BotConfig.DEBUG else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    # Validate configuration
    if not BotConfig.validate():
        logging.error("BOT_TOKEN is not set in environment variables")
        sys.exit(1)

    # Create bot and dispatcher
    bot = Bot(token=BotConfig.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(group_router)
    dp.include_router(private_router)
    dp.include_router(question_router)
    dp.include_router(callback_router)

    # Start polling
    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
