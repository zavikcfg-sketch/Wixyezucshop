from __future__ import annotations

import json
import logging

from aiogram import F, Router
from aiogram.types import Message

from app.config import Settings
from app.services.orders import OrderCreateDTO
from app.services.orders import OrderService

router = Router(name="webapp")


@router.message(F.web_app_data)
async def webapp_order_handler(
    message: Message, settings: Settings, order_service: OrderService
) -> None:
    if not message.from_user or not message.web_app_data:
        await message.answer("Ошибка обработки WebApp данных.")
        return

    try:
        payload = json.loads(message.web_app_data.data)
    except json.JSONDecodeError:
        await message.answer("Неверный формат данных заказа.")
        return

    if payload.get("action") != "create_order":
        await message.answer("Неизвестное действие WebApp.")
        return

    game = str(payload.get("game", "")).strip()
    details = str(payload.get("details", "")).strip()
    if not game:
        await message.answer("Игра не указана.")
        return

    full_name = " ".join(
        part for part in [message.from_user.first_name, message.from_user.last_name] if part
    ).strip()
    dto = OrderCreateDTO(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=full_name,
        game=game,
        details=details,
    )
    order_id = order_service.create(dto)

    await message.answer(
        f"✅ Заказ #{order_id} создан!\n"
        f"Игра: {game}\n"
        f"Комментарий: {details or '-'}\n\n"
        "Менеджер свяжется с вами в ближайшее время."
    )

    admin_id = settings.admin_id
    if admin_id:
        try:
            await message.bot.send_message(
                admin_id,
                f"🆕 Новый заказ #{order_id}\n"
                f"Игра: {game}\n"
                f"Детали: {details or '-'}\n"
                f"Пользователь: {full_name or '-'} (@{message.from_user.username or '-'})\n"
                f"user_id: {message.from_user.id}",
            )
        except Exception as exc:
            logging.warning("Ошибка уведомления админа: %s", exc)
