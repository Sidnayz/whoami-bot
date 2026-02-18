"""Main entry point for the bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BotConfig
from bot.handlers import group_router, private_router, question_router, callback_router


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
