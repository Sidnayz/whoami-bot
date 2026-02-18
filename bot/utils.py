"""Utility functions."""

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner


async def is_admin(chat_id: int, user_id: int, bot: Bot = None) -> bool:
    """Check if user is admin in the chat."""
    if bot is None:
        return False

    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception:
        return False
