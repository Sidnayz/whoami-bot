"""Question and callback handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.services.game_state import game_manager, GameState
from bot.keyboards import get_answer_keyboard


question_router = Router()


# Dictionary to map callback data to Russian answer text
ANSWER_MAP = {
    'answer:yes': 'Да',
    'answer:no': 'Нет',
    'answer:dont_know': 'Не знаю',
    'answer:partially': 'Частично',
}


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


callback_router = Router()


@callback_router.callback_query(lambda c: c.data.startswith('answer:'))
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

    # Check if it's the "guessed" button
    if callback.data == 'answer:guessed':
        # Get the username from the original question message
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
