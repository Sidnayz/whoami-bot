"""Private message handlers."""

from aiogram import Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services import game_manager
from bot.keyboards import get_answer_keyboard

private_router = Router()


class CharacterInputState(StatesGroup):
    """FSM states for character input."""
    waiting_character = State()


@private_router.message(Command('start', 'help'))
async def cmd_start_help(message: Message):
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


@private_router.message(Command('mygame'))
async def cmd_mygame(message: Message, state: FSMContext):
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
async def process_character_input(message: Message, state: FSMContext, bot: Bot):
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
