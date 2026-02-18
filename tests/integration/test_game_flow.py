"""Integration tests for full game flow."""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.handlers.group_handlers import cmd_startgame, cmd_endgame, cmd_status
from bot.handlers.private_handlers import cmd_mygame, process_character_input
from bot.handlers.question_handlers import handle_question, handle_answer_callback
from bot.services import game_manager


@pytest.fixture
def reset_game_manager():
    """Reset game manager before each test."""
    game_manager.games.clear()
    yield
    game_manager.games.clear()


class TestFullGameFlow:
    """Integration tests for complete game lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_game_flow(self, reset_game_manager):
        """Test complete game from start to end."""
        chat_id = 12345
        host_id = 1001
        asker_id = 2002

        # Step 1: Start game in group
        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        await cmd_startgame(group_msg)

        # Verify game created
        game = game_manager.get_game(chat_id)
        assert game is not None
        assert game.state.value == "waiting_character"
        assert game.host_id == host_id

        # Step 2: Host starts character input
        private_msg = Mock()
        private_msg.chat.id = host_id
        private_msg.from_user.id = host_id
        private_msg.text = "/mygame"
        private_msg.answer = AsyncMock()

        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()

        await cmd_mygame(private_msg, mock_state)

        assert game.waiting_for_character is True

        # Step 3: Host inputs character
        private_msg.text = "Harry Potter"
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        await process_character_input(private_msg, mock_state, mock_bot)

        # Verify game is active
        game = game_manager.get_game(chat_id)
        assert game.character == "Harry Potter"
        assert game.state.value == "active"

        # Step 4: Other user asks question
        question_msg = Mock()
        question_msg.chat.id = chat_id
        question_msg.from_user.id = asker_id
        question_msg.from_user.username = "asker"
        question_msg.text = "Is he a wizard?"
        question_msg.answer = AsyncMock()

        await handle_question(question_msg)

        # Step 5: Host answers
        callback = Mock()
        callback.from_user.id = host_id
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = chat_id
        msg.text = "Вопрос от @asker: Is he a wizard?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        # Verify answer was recorded
        call_args = msg.edit_text.call_args[0][0]
        assert "Ответ: Да" in call_args

        # Step 6: End game
        await cmd_endgame(group_msg)

        # Verify game ended
        assert game_manager.get_game(chat_id) is None

    @pytest.mark.asyncio
    async def test_game_with_multiple_questions(self, reset_game_manager):
        """Test game with multiple questions and answers."""
        chat_id = 12345
        host_id = 1001
        asker_id = 2002

        # Start and setup game
        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        await cmd_startgame(group_msg)

        private_msg = Mock()
        private_msg.chat.id = host_id
        private_msg.from_user.id = host_id
        private_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        private_msg.text = "/mygame"
        await cmd_mygame(private_msg, mock_state)

        private_msg.text = "Sherlock Holmes"
        await process_character_input(private_msg, mock_state, mock_bot)

        # Multiple questions
        questions = [
            "Is he real?",
            "Is he a detective?",
            "Does he have a partner?",
        ]

        answers = ["answer:no", "answer:yes", "answer:yes"]

        for question_text, answer_data in zip(questions, answers):
            question_msg = Mock()
            question_msg.chat.id = chat_id
            question_msg.from_user.id = asker_id
            question_msg.from_user.username = "asker"
            question_msg.text = question_text
            question_msg.answer = AsyncMock()

            await handle_question(question_msg)

            callback = Mock()
            callback.from_user.id = host_id
            callback.data = answer_data
            callback.answer = AsyncMock()
            msg = Mock()
            msg.chat.id = chat_id
            msg.text = f"Вопрос от @asker: {question_text}"
            msg.edit_text = AsyncMock()
            callback.message = msg

            await handle_answer_callback(callback)

        # Verify game is still active
        game = game_manager.get_game(chat_id)
        assert game.state.value == "active"
        assert game.character == "Sherlock Holmes"

    @pytest.mark.asyncio
    async def test_game_stopped_before_character(self, reset_game_manager):
        """Test ending game before character is set."""
        chat_id = 12345
        host_id = 1001

        # Start game
        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        await cmd_startgame(group_msg)

        # End game without setting character
        await cmd_endgame(group_msg)

        # Verify proper message
        call_text = group_msg.answer.call_args_list[-1][0][0]
        assert "остановлена до ввода персонажа" in call_text

        assert game_manager.get_game(chat_id) is None

    @pytest.mark.asyncio
    async def test_game_status_through_stages(self, reset_game_manager):
        """Test status command at different stages."""
        chat_id = 12345
        host_id = 1001

        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        # Status before game
        await cmd_status(group_msg)
        call_text = group_msg.answer.call_args[0][0]
        assert "нет активной игры" in call_text

        # Start game
        await cmd_startgame(group_msg)

        # Status during waiting
        group_msg.answer.reset_mock()
        await cmd_status(group_msg)
        call_text = group_msg.answer.call_args[0][0]
        assert "Игра создаётся" in call_text

        # Set character
        private_msg = Mock()
        private_msg.chat.id = host_id
        private_msg.from_user.id = host_id
        private_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        private_msg.text = "/mygame"
        await cmd_mygame(private_msg, mock_state)
        private_msg.text = "Test Character"
        await process_character_input(private_msg, mock_state, mock_bot)

        # Status during active game
        group_msg.answer.reset_mock()
        await cmd_status(group_msg)
        call_text = group_msg.answer.call_args[0][0]
        assert "Игра идёт" in call_text

    @pytest.mark.asyncio
    async def test_non_cannot_answer(self, reset_game_manager):
        """Test that only host can answer questions."""
        chat_id = 12345
        host_id = 1001
        asker_id = 2002

        # Setup game
        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        await cmd_startgame(group_msg)

        private_msg = Mock()
        private_msg.chat.id = host_id
        private_msg.from_user.id = host_id
        private_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        private_msg.text = "/mygame"
        await cmd_mygame(private_msg, mock_state)
        private_msg.text = "Test Character"
        await process_character_input(private_msg, mock_state, mock_bot)

        # Ask question
        question_msg = Mock()
        question_msg.chat.id = chat_id
        question_msg.from_user.id = asker_id
        question_msg.from_user.username = "asker"
        question_msg.text = "Is this a test?"
        question_msg.answer = AsyncMock()

        await handle_question(question_msg)

        # Try to answer as non-host
        callback = Mock()
        callback.from_user.id = asker_id  # Not the host
        callback.data = "answer:yes"
        callback.answer = AsyncMock()
        msg = Mock()
        msg.chat.id = chat_id
        msg.text = "Вопрос от @asker: Is this a test?"
        msg.edit_text = AsyncMock()
        callback.message = msg

        await handle_answer_callback(callback)

        # Verify answer was rejected
        callback.answer.assert_called_once()
        call_args = callback.answer.call_args[0][0]
        assert "только загадывающий" in call_args

        # Message should not be edited
        msg.edit_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_cannot_start_duplicate_game(self, reset_game_manager):
        """Test that duplicate game cannot be started."""
        chat_id = 12345
        host_id = 1001
        other_user = 2002

        # First game
        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        await cmd_startgame(group_msg)
        game = game_manager.get_game(chat_id)
        assert game.host_id == host_id

        # Try to start another game
        group_msg.answer.reset_mock()
        group_msg.from_user.id = other_user
        group_msg.from_user.username = "otheruser"

        await cmd_startgame(group_msg)

        # Should not create new game
        game = game_manager.get_game(chat_id)
        assert game.host_id == host_id  # Should be original host

        call_text = group_msg.answer.call_args[0][0]
        assert "Игра уже идёт" in call_text

    @pytest.mark.asyncio
    async def test_admin_can_end_game(self, reset_game_manager):
        """Test that admin can end game."""
        chat_id = 12345
        host_id = 1001
        admin_id = 2002

        # Setup game
        group_msg = Mock()
        group_msg.chat.id = chat_id
        group_msg.from_user.id = host_id
        group_msg.from_user.username = "hostuser"
        group_msg.answer = AsyncMock()

        await cmd_startgame(group_msg)

        private_msg = Mock()
        private_msg.chat.id = host_id
        private_msg.from_user.id = host_id
        private_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        private_msg.text = "/mygame"
        await cmd_mygame(private_msg, mock_state)
        private_msg.text = "Test Character"
        await process_character_input(private_msg, mock_state, mock_bot)

        # Admin ends game
        group_msg.answer.reset_mock()
        group_msg.from_user.id = admin_id

        with patch('bot.handlers.group_handlers.is_admin', return_value=True):
            await cmd_endgame(group_msg)

        # Game should be ended
        assert game_manager.get_game(chat_id) is None
