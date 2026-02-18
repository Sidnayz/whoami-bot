"""Unit tests for question and callback handlers."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.handlers.question_handlers import (
    handle_question,
    handle_answer_callback
)
from bot.services import game_manager
from bot.keyboards import get_answer_keyboard


@pytest.fixture
def reset_game_manager():
    """Reset game manager before each test."""
    game_manager.games.clear()
    yield
    game_manager.games.clear()


@pytest.fixture
def mock_group_message():
    """Create a mock Message object for group chat."""
    message = Mock()
    message.chat = Mock()
    message.chat.id = 12345
    message.chat.type = "supergroup"
    message.from_user = Mock()
    message.from_user.id = 2002
    message.from_user.username = "asker"
    message.text = "Is this a question?"
    message.caption = None
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query():
    """Create a mock CallbackQuery object."""
    callback = Mock()
    callback.from_user = Mock()
    callback.from_user.id = 1001
    callback.data = "answer:yes"
    callback.answer = AsyncMock()
    msg = Mock()
    msg.chat = Mock()
    msg.chat.id = 12345
    msg.text = "Вопрос от @asker: Is this a question?"
    msg.edit_text = AsyncMock()
    callback.message = msg
    return callback


@pytest.fixture
def mock_message_for_callback():
    """Create a mock message for callback."""
    msg = Mock()
    msg.chat = Mock()
    msg.chat.id = 12345
    msg.text = "Вопрос от @asker: Is this a question?"
    msg.edit_text = AsyncMock()
    return msg


class TestHandleQuestion:
    """Test cases for handling questions in group."""

    @pytest.mark.asyncio
    async def test_handle_question_success(self, mock_group_message, reset_game_manager):
        """Test handling a valid question."""
        # Setup active game
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")

        await handle_question(mock_group_message)

        mock_group_message.answer.assert_called_once()
        call_args = mock_group_message.answer.call_args
        assert call_args is not None

        text = call_args[0][0]
        assert "Вопрос от @asker:" in text
        assert "Is this a question?" in text

        # Check keyboard was attached
        keyboard = call_args[1].get('reply_markup')
        assert keyboard is not None

    @pytest.mark.asyncio
    async def test_handle_question_without_username(self, mock_group_message, reset_game_manager):
        """Test handling question from user without username."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")
        mock_group_message.from_user.username = None

        await handle_question(mock_group_message)

        call_text = mock_group_message.answer.call_args[0][0]
        assert "ID 2002" in call_text

    @pytest.mark.asyncio
    async def test_handle_question_no_game(self, mock_group_message, reset_game_manager):
        """Test handling question when no game exists."""
        await handle_question(mock_group_message)

        mock_group_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_question_wrong_state(self, mock_group_message, reset_game_manager):
        """Test handling question when game is not active."""
        game_manager.create_game(12345, 1001, "hostuser")
        # Don't set character - still in waiting state

        await handle_question(mock_group_message)

        mock_group_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_question_no_question_mark(self, mock_group_message, reset_game_manager):
        """Test message without question mark is ignored."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")
        mock_group_message.text = "This is not a question"

        await handle_question(mock_group_message)

        mock_group_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_question_with_command(self, mock_group_message, reset_game_manager):
        """Test that commands are not treated as questions."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")
        mock_group_message.text = "/status?"

        await handle_question(mock_group_message)

        mock_group_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_question_question_mark_at_end(self, mock_group_message, reset_game_manager):
        """Test question mark at end is detected."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")

        test_cases = [
            "Is this a question?",
            "Это вопрос?",
            "Multiple?question?marks?",  # Ends with ?
            "   trailing spaces?   ",  # Spaces before ?
        ]

        for text in test_cases:
            mock_group_message.text = text
            mock_group_message.answer.reset_mock()

            await handle_question(mock_group_message)

            mock_group_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_question_no_text(self, mock_group_message, reset_game_manager):
        """Test message without text is ignored."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")
        mock_group_message.text = None
        mock_group_message.caption = None

        await handle_question(mock_group_message)

        mock_group_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_question_with_caption(self, mock_group_message, reset_game_manager):
        """Test message with caption (photo with text)."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")
        mock_group_message.text = None
        mock_group_message.caption = "Is this a question?"

        await handle_question(mock_group_message)

        mock_group_message.answer.assert_called_once()
        call_text = mock_group_message.answer.call_args[0][0]
        assert "Is this a question?" in call_text


class TestHandleAnswerCallback:
    """Test cases for handling answer button callbacks."""

    @pytest.mark.asyncio
    async def test_handle_answer_success_yes(self, reset_game_manager):
        """Test successful answer with 'Yes'."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")

        callback = Mock()
        callback.from_user.id = 1001
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = 12345
        msg.text = "Вопрос от @asker: Is this a question?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        callback.answer.assert_called_once()

        msg.edit_text.assert_called_once()
        call_args = msg.edit_text.call_args
        updated_text = call_args[0][0]
        assert "Ответ: Да" in updated_text

    @pytest.mark.asyncio
    async def test_handle_answer_all_button_types(self, reset_game_manager):
        """Test all answer button types."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")

        test_data = [
            ("answer:yes", "Да"),
            ("answer:no", "Нет"),
            ("answer:dont_know", "Не знаю"),
            ("answer:partially", "Частично"),
        ]

        for callback_data, expected_answer in test_data:
            callback = Mock()
            callback.from_user.id = 1001
            callback.data = callback_data
            callback.answer = AsyncMock()
            msg = Mock()
            msg.chat.id = 12345
            msg.text = "Вопрос от @asker: Is this a question?"
            msg.edit_text = AsyncMock()
            callback.message = msg

            await handle_answer_callback(callback)

            call_args = msg.edit_text.call_args[0][0]
            assert f"Ответ: {expected_answer}" in call_args

    @pytest.mark.asyncio
    async def test_handle_answer_not_host(self, reset_game_manager):
        """Test that non-host cannot answer."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")

        callback = Mock()
        callback.from_user.id = 9999  # Not the host
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = 12345
        msg.text = "Вопрос от @asker: Is this a question?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        callback.answer.assert_called_once()
        call_args = callback.answer.call_args
        assert call_args is not None
        assert "Отвечать на вопросы может только загадывающий" in call_args[0][0]

        msg.edit_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_answer_no_game(self):
        """Test callback when no game exists."""
        callback = Mock()
        callback.from_user.id = 1001
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = 12345
        msg.text = "Вопрос от @asker: Is this a question?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        callback.answer.assert_called_once()
        msg.edit_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_answer_wrong_state(self, reset_game_manager):
        """Test callback when game is not active."""
        game_manager.create_game(12345, 1001, "hostuser")
        # Don't set character - still in waiting state

        callback = Mock()
        callback.from_user.id = 1001
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = 12345
        msg.text = "Вопрос от @asker: Is this a question?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        callback.answer.assert_called_once()
        msg.edit_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_answer_no_message(self):
        """Test callback without message."""
        callback = Mock()
        callback.from_user.id = 1001
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        callback.message = None

        await handle_answer_callback(callback)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_answer_unknown_callback_data(self, reset_game_manager):
        """Test callback with unknown data."""
        game_manager.create_game(12345, 1001, "hostuser")
        game_manager.set_character(12345, "Test Character")

        callback = Mock()
        callback.from_user.id = 1001
        callback.data = "answer:unknown"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = 12345
        msg.text = "Вопрос от @asker: Is this a question?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        callback.answer.assert_called_once()
        msg.edit_text.assert_not_called()


class TestKeyboardFunction:
    """Test cases for keyboard generation."""

    def test_get_answer_keyboard_structure(self):
        """Test keyboard has correct structure."""
        keyboard = get_answer_keyboard()

        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')
        buttons = keyboard.inline_keyboard

        assert len(buttons) == 4

        expected_labels = ['Да', 'Нет', 'Не знаю', 'Частично']
        expected_callbacks = [
            'answer:yes',
            'answer:no',
            'answer:dont_know',
            'answer:partially'
        ]

        for i, row in enumerate(buttons):
            assert len(row) == 1
            button = row[0]
            assert button.text == expected_labels[i]
            assert button.callback_data == expected_callbacks[i]
