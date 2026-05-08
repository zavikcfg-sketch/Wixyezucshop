from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Settings
from app.services.orders import OrderService
from app.services.orders import ALLOWED_STATUSES

router = Router(name="admin")


def _is_admin(message: Message, settings: Settings) -> bool:
    user = message.from_user
    return bool(user and settings.admin_id and user.id == settings.admin_id)


@router.message(Command("orders"))
async def cmd_orders(message: Message, settings: Settings, order_service: OrderService) -> None:
    if not _is_admin(message, settings):
        await message.answer("Команда только для администратора.")
        return
    rows = order_service.list_recent(limit=20)
    if not rows:
        await message.answer("Заказов пока нет.")
        return
    lines = ["🧾 Последние заказы:"]
    for row in rows:
        lines.append(
            f"#{row['id']} | {row['game']} | {row['status']} | user_id={row['user_id']} | {row['created_at']}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("order"))
async def cmd_order(message: Message, settings: Settings, order_service: OrderService) -> None:
    if not _is_admin(message, settings):
        await message.answer("Команда только для администратора.")
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /order <id>")
        return
    row = order_service.get_by_id(int(parts[1]))
    if not row:
        await message.answer("Заказ не найден.")
        return
    await message.answer(
        f"📦 Заказ #{row['id']}\n"
        f"Статус: {row['status']}\n"
        f"Игра: {row['game']}\n"
        f"Детали: {row['details'] or '-'}\n"
        f"Пользователь: {row['full_name'] or '-'} (@{row['username'] or '-'})\n"
        f"user_id: {row['user_id']}\n"
        f"Создан: {row['created_at']}"
    )


@router.message(Command("setstatus"))
async def cmd_setstatus(message: Message, settings: Settings, order_service: OrderService) -> None:
    if not _is_admin(message, settings):
        await message.answer("Команда только для администратора.")
        return
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit():
        await message.answer("Использование: /setstatus <id> <NEW|PAID|DONE|CANCELED>")
        return
    order_id = int(parts[1])
    status = parts[2].upper().strip()
    if status not in ALLOWED_STATUSES:
        await message.answer("Допустимые статусы: NEW, PAID, DONE, CANCELED")
        return
    if not order_service.set_status(order_id, status):
        await message.answer("Заказ не найден.")
        return
    await message.answer(f"Статус заказа #{order_id} -> {status}")
    row = order_service.get_by_id(order_id)
    if row:
        try:
            await message.bot.send_message(
                row["user_id"], f"🔔 Обновление заказа #{order_id}\nНовый статус: {status}"
            )
        except Exception:
            pass
