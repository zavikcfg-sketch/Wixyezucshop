from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.config import Settings
from app.keyboards.main import build_main_keyboard
from app.services.orders import OrderService

router = Router(name="user")

WELCOME_TEXT = (
    "⚡ ДОБРО ПОЖАЛОВАТЬ В WIXYEZ UC SHOP 🖱\n\n"
    "Мы работаем непрерывно - 24/7 ✅"
)


@router.message(CommandStart())
async def cmd_start(message: Message, settings: Settings) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=build_main_keyboard(settings.web_app_url))


@router.message(Command("menu"))
async def cmd_menu(message: Message, settings: Settings) -> None:
    await message.answer("Главное меню 👇", reply_markup=build_main_keyboard(settings.web_app_url))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "🧭 Команды:\n"
        "/start - запуск\n"
        "/menu - меню\n"
        "/help - помощь\n"
        "/myorders - мои заказы"
    )


@router.message(Command("myorders"))
async def cmd_myorders(message: Message, order_service: OrderService) -> None:
    if not message.from_user:
        return
    rows = order_service.list_by_user(message.from_user.id, limit=10)
    if not rows:
        await message.answer("У вас пока нет заказов.")
        return
    lines = ["📋 Ваши последние заказы:"]
    for row in rows:
        lines.append(f"#{row['id']} | {row['game']} | {row['status']} | {row['created_at']}")
    await message.answer("\n".join(lines))


@router.message(F.text == "PUBG MOBILE")
async def pubg_mobile_handler(message: Message) -> None:
    await message.answer(
        "🎯 PUBG MOBILE\n\n"
        "Пакеты UC доступны 24/7.\n"
        "Откройте '🎮 ВСЕ ИГРЫ' для оформления заявки."
    )


@router.message(F.text == "TG Товары")
async def tg_goods_handler(message: Message) -> None:
    await message.answer("📦 TG Товары\n\nНапишите, что именно нужно, и менеджер ответит.")


@router.message(F.text == "🎮 ВСЕ ИГРЫ")
async def all_games_hint(message: Message) -> None:
    await message.answer("Открываю каталог игр через Mini App 👾")


@router.message(F.text == "VPN Интернет без ограничений")
async def vpn_handler(message: Message) -> None:
    await message.answer("🌐 VPN: 1/3/12 месяцев. Напишите: ХОЧУ VPN.")


@router.message(F.text == "👥 Пригласи друга")
async def invite_friend_handler(message: Message) -> None:
    if not message.from_user:
        return
    me = await message.bot.get_me()
    referral = (
        f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
        if me.username
        else "Ссылка недоступна"
    )
    await message.answer(f"👥 Ваша реферальная ссылка:\n{referral}")


@router.message(F.text == "5% Промокоды")
async def promo_codes_handler(message: Message) -> None:
    await message.answer("🏷 Промокоды:\n• WIXYEZ5\n• BONUS5")


@router.message(F.text == "Заработать денег")
async def earn_money_handler(message: Message) -> None:
    await message.answer("💸 Партнерка: напишите 'ХОЧУ В ПАРТНЕРКУ'.")


@router.message(F.text == "Наш сайт в Google")
async def website_handler(message: Message, settings: Settings) -> None:
    await message.answer(f"🔎 Наш сайт:\n{settings.site_url}")


@router.message(F.text == "Розыгрыш 5000₽")
async def giveaway_handler(message: Message) -> None:
    await message.answer("🎁 Розыгрыш 5000₽: следите за анонсами и делайте заказы.")


@router.message(F.text)
async def fallback_handler(message: Message, settings: Settings) -> None:
    await message.answer(
        "Не понял запрос. Используйте меню или /help.",
        reply_markup=build_main_keyboard(settings.web_app_url),
    )
