from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import load_settings
from app.db import init_db
from app.handlers import register_handlers
from app.services.orders import OrderService


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    settings = load_settings()
    init_db(settings.db_path)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    order_service = OrderService(settings.db_path)

    register_handlers(dp)
    logging.info("WIXYEZ UC SHOP bot started.")
    await dp.start_polling(
        bot,
        skip_updates=True,
        settings=settings,
        order_service=order_service,
    )


def main() -> None:
    asyncio.run(run())
