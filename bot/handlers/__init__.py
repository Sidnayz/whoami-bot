"""Handlers module."""

from .group_handlers import group_router
from .private_handlers import private_router
from .question_handlers import question_router, callback_router

__all__ = ['group_router', 'private_router', 'question_router', 'callback_router']
