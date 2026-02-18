"""Keyboards module."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_answer_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for answering questions."""
    buttons = [
        [InlineKeyboardButton(text='Да', callback_data='answer:yes')],
        [InlineKeyboardButton(text='Нет', callback_data='answer:no')],
        [InlineKeyboardButton(text='Не знаю', callback_data='answer:dont_know')],
        [InlineKeyboardButton(text='Частично', callback_data='answer:partially')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
