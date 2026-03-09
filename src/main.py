import asyncio
import logging
from src.misc import dp, bot
from src.handlers import start, document, confirmation_date, manual_date

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())