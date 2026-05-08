import asyncio
import logging
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://example.com").strip()
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/").strip()
BOT_PUBLIC_URL = os.getenv("BOT_PUBLIC_URL", "https://t.me/").strip()
BANNER_PATH = os.getenv("BANNER_PATH", "assets/telegram-preview-1.png").strip()

PAYCORE_API_URL = os.getenv("PAYCORE_API_URL", "https://api.paycore.io").strip()
PAYCORE_TOKEN = os.getenv("PAYCORE_TOKEN", "").strip()
PAYCORE_MERCHANT_ID = os.getenv("PAYCORE_MERCHANT_ID", "").strip()
PAYCORE_MODE = os.getenv("PAYCORE_MODE", "demo").strip().lower()

DB_PATH = "bot_data.db"
router = Router()


@dataclass(frozen=True)
class Product:
    code: str
    title: str
    amount_rub: Decimal
    category: str


PRODUCTS = {
    "pubg_60": Product("pubg_60", "PUBG Mobile · 60 UC", Decimal("149"), "pubg"),
    "pubg_325": Product("pubg_325", "PUBG Mobile · 325 UC", Decimal("649"), "pubg"),
    "pubg_660": Product("pubg_660", "PUBG Mobile · 660 UC", Decimal("1249"), "pubg"),
    "pubg_1800": Product("pubg_1800", "PUBG Mobile · 1800 UC", Decimal("3090"), "pubg"),
    "genshin_300": Product("genshin_300", "Genshin Impact · 300 Crystals", Decimal("399"), "genshin"),
    "genshin_980": Product("genshin_980", "Genshin Impact · 980 Crystals", Decimal("1190"), "genshin"),
    "steam_500": Product("steam_500", "Steam Wallet · 500 RUB", Decimal("539"), "steam"),
    "steam_1000": Product("steam_1000", "Steam Wallet · 1000 RUB", Decimal("1049"), "steam"),
}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                product_code TEXT NOT NULL,
                amount_rub TEXT NOT NULL,
                label TEXT NOT NULL UNIQUE,
                paycore_invoice_id TEXT,
                paycore_payment_url TEXT,
                status TEXT NOT NULL DEFAULT 'created',
                issued_code TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟩 PUBG MOBILE", callback_data="menu:pubg")],
            [InlineKeyboardButton(text="🟦 Telegram товары", callback_data="menu:telegram")],
            [InlineKeyboardButton(text="🟪 ВСЕ ИГРЫ", callback_data="menu:all_games")],
            [InlineKeyboardButton(text="🟦 ПРОЧАЯ ИНФОРМАЦИЯ", callback_data="menu:info")],
            [InlineKeyboardButton(text="🟧 Розыгрыш 5000₽", callback_data="menu:giveaway")],
            [InlineKeyboardButton(text="🟩 Профиль", callback_data="menu:profile")],
            [InlineKeyboardButton(text="🟪 Сайт Wixyeez Shop", url=WEBSITE_URL)],
        ]
    )


def products_keyboard(category: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for product in PRODUCTS.values():
        if product.category == category:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{product.title} · {product.amount_rub} RUB",
                        callback_data=f"buy:{product.code}",
                    )
                ]
            )
    rows.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def checkout_keyboard(label: str, payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить через PayCore", url=payment_url)],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check:{label}")],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="menu:main")],
        ]
    )


def create_order(user_id: int, username: str | None, product: Product) -> str:
    label = f"wix_{user_id}_{secrets.token_hex(8)}"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO orders (user_id, username, product_code, amount_rub, label, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                product.code,
                str(product.amount_rub),
                label,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    return label


def set_order_payment(label: str, invoice_id: str, payment_url: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE orders SET paycore_invoice_id = ?, paycore_payment_url = ? WHERE label = ?",
            (invoice_id, payment_url, label),
        )
        conn.commit()


def get_order(label: str):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT user_id, product_code, status, issued_code, paycore_invoice_id
            FROM orders
            WHERE label = ?
            """,
            (label,),
        ).fetchone()


def issue_code(label: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT status, issued_code FROM orders WHERE label = ?", (label,)).fetchone()
        if not row:
            return None
        status, current_code = row
        if status == "paid" and current_code:
            return current_code
        code = f"WIXYEEZ-{secrets.token_hex(4).upper()}"
        conn.execute("UPDATE orders SET status = 'paid', issued_code = ? WHERE label = ?", (code, label))
        conn.commit()
        return code


async def create_paycore_invoice(label: str, product: Product) -> tuple[bool, str, str]:
    if PAYCORE_MODE == "demo":
        return True, f"demo-{label}", f"https://paycore.example/checkout/{label}"

    if not PAYCORE_TOKEN or not PAYCORE_MERCHANT_ID:
        return False, "", "PayCore не настроен. Заполните PAYCORE_TOKEN и PAYCORE_MERCHANT_ID."

    payload = {
        "merchant_id": PAYCORE_MERCHANT_ID,
        "order_id": label,
        "amount": float(product.amount_rub),
        "currency": "RUB",
        "description": f"Wixyeez UC Shop: {product.title}",
        "success_url": WEBSITE_URL,
        "fail_url": WEBSITE_URL,
    }
    headers = {"Authorization": f"Bearer {PAYCORE_TOKEN}", "Content-Type": "application/json"}
    endpoint = f"{PAYCORE_API_URL.rstrip('/')}/v1/invoices"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers, timeout=30) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    message = data.get("message") or data.get("error") or f"HTTP {resp.status}"
                    return False, "", f"PayCore error: {message}"
    except Exception as exc:
        return False, "", f"PayCore connection error: {exc}"

    invoice_id = str(data.get("id") or data.get("invoice_id") or label)
    payment_url = data.get("payment_url") or data.get("checkout_url") or data.get("url")
    if not payment_url:
        return False, "", "PayCore не вернул ссылку на оплату."
    return True, invoice_id, payment_url


async def is_paid(invoice_id: str) -> bool:
    if PAYCORE_MODE == "demo":
        return True
    if not PAYCORE_TOKEN:
        return False

    headers = {"Authorization": f"Bearer {PAYCORE_TOKEN}"}
    endpoint = f"{PAYCORE_API_URL.rstrip('/')}/v1/invoices/{invoice_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=30) as resp:
                if resp.status >= 400:
                    return False
                data = await resp.json(content_type=None)
    except Exception:
        return False

    status = str(data.get("status", "")).lower()
    return status in {"paid", "success", "completed", "succeeded"}


@router.message(CommandStart())
async def start(message: Message):
    text = (
        "🚨 ДОБРО ПОЖАЛОВАТЬ В WIXYEEZ SHOP BOT 🧾\n\n"
        "МЫ РАБОТАЕМ НЕПРЕРЫВНО - 24/7 ✅\n"
        "Быстрая выдача после оплаты через PayCore.\n\n"
        "Выберите раздел ниже:"
    )
    if os.path.exists(BANNER_PATH):
        await message.answer_photo(
            photo=FSInputFile(BANNER_PATH),
            caption=text,
            reply_markup=main_menu_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery):
    await callback.message.edit_text("🏠 ГЛАВНОЕ МЕНЮ WIXYEEZ SHOP", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def menu_profile(callback: CallbackQuery):
    user = callback.from_user
    text = (
        "👤 Ваш профиль\n\n"
        f"ID: {user.id}\n"
        f"Username: @{user.username or 'не указан'}\n"
        f"Режим PayCore: {'DEMO' if PAYCORE_MODE == 'demo' else 'LIVE'}\n\n"
        "Для покупки выберите раздел с игрой в главном меню."
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:pubg")
async def menu_pubg(callback: CallbackQuery):
    await callback.message.edit_text("🎮 PUBG MOBILE UC", reply_markup=products_keyboard("pubg"))
    await callback.answer()


@router.callback_query(F.data == "menu:genshin")
async def menu_genshin(callback: CallbackQuery):
    await callback.message.edit_text("💎 Genshin Impact", reply_markup=products_keyboard("genshin"))
    await callback.answer()


@router.callback_query(F.data == "menu:steam")
async def menu_steam(callback: CallbackQuery):
    await callback.message.edit_text("💠 Steam Wallet", reply_markup=products_keyboard("steam"))
    await callback.answer()


@router.callback_query(F.data == "menu:telegram")
async def menu_telegram(callback: CallbackQuery):
    await callback.message.edit_text("📩 TELEGRAM ТОВАРЫ", reply_markup=products_keyboard("steam"))
    await callback.answer()


@router.callback_query(F.data == "menu:all_games")
async def menu_all_games(callback: CallbackQuery):
    await callback.message.edit_text(
        "🕹 ВСЕ ИГРЫ\n\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎮 PUBG MOBILE", callback_data="menu:pubg")],
                [InlineKeyboardButton(text="💎 Genshin Impact", callback_data="menu:genshin")],
                [InlineKeyboardButton(text="💠 Steam Wallet", callback_data="menu:steam")],
                [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu:main")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:info")
async def menu_info(callback: CallbackQuery):
    text = (
        "ℹ️ ПРОЧАЯ ИНФОРМАЦИЯ\n\n"
        "• Автовыдача 24/7\n"
        "• Безопасная оплата PayCore\n"
        "• Поддержка отвечает быстро\n\n"
        f"Поддержка: {SUPPORT_URL}\n"
        f"Сайт: {WEBSITE_URL}"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:giveaway")
async def menu_giveaway(callback: CallbackQuery):
    text = (
        "🎁 РОЗЫГРЫШ 5000₽\n\n"
        "Чтобы участвовать:\n"
        "1) Сделайте любую покупку в боте\n"
        "2) Оставьте отзыв в поддержку\n"
        "3) Дождитесь объявления победителя\n\n"
        "Победитель выбирается случайно."
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy(callback: CallbackQuery):
    product_code = callback.data.split(":", maxsplit=1)[1]
    product = PRODUCTS.get(product_code)
    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    label = create_order(callback.from_user.id, callback.from_user.username, product)
    ok, invoice_id, payment_url_or_error = await create_paycore_invoice(label, product)
    if not ok:
        await callback.message.edit_text(
            f"❌ Не удалось создать оплату.\n\n{payment_url_or_error}",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    set_order_payment(label, invoice_id, payment_url_or_error)
    text = (
        "✅ Заказ создан\n\n"
        f"Товар: {product.title}\n"
        f"Сумма: {product.amount_rub} RUB\n"
        f"Order ID: {label}\n\n"
        "Оплатите заказ и нажмите «Проверить оплату»."
    )
    await callback.message.edit_text(text, reply_markup=checkout_keyboard(label, payment_url_or_error))
    await callback.answer()


@router.callback_query(F.data.startswith("check:"))
async def check(callback: CallbackQuery):
    label = callback.data.split(":", maxsplit=1)[1]
    order = get_order(label)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    user_id, product_code, status, issued_code, invoice_id = order
    if user_id != callback.from_user.id:
        await callback.answer("Это не ваш заказ.", show_alert=True)
        return

    if status == "paid" and issued_code:
        await callback.message.edit_text(
            f"✅ Оплата уже подтверждена.\n\nВаш код: {issued_code}",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    if not invoice_id:
        await callback.answer("У заказа отсутствует invoice ID.", show_alert=True)
        return

    if not await is_paid(invoice_id):
        await callback.answer("Оплата не подтверждена. Повторите через 20-40 секунд.", show_alert=True)
        return

    code = issue_code(label)
    if not code:
        await callback.answer("Ошибка выдачи заказа.", show_alert=True)
        return

    product = PRODUCTS.get(product_code)
    title = product.title if product else product_code
    await callback.message.edit_text(
        "🎉 Оплата подтверждена\n"
        f"Товар: {title}\n"
        f"Код: {code}\n\n"
        "Спасибо за покупку в Wixyeez UC Shop!",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer("Успешно")

    if ADMIN_ID.isdigit():
        await callback.bot.send_message(
            int(ADMIN_ID),
            f"Новая оплата\nUser: {callback.from_user.id}\nOrder: {label}\nТовар: {title}\nКод: {code}",
        )


@router.message(Command("help"))
async def help_command(message: Message):
    text = (
        "🆘 Помощь\n\n"
        "1) Нажмите /start\n"
        "2) Выберите игру и товар\n"
        "3) Оплатите через PayCore\n"
        "4) Нажмите «Проверить оплату»\n\n"
        f"Поддержка: {SUPPORT_URL}\n"
        f"Сайт: {WEBSITE_URL}\n"
        f"Бот: {BOT_PUBLIC_URL}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("mark_paid"))
async def mark_paid(message: Message):
    if not ADMIN_ID.isdigit() or message.from_user.id != int(ADMIN_ID):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /mark_paid <order_label>")
        return
    label = parts[1].strip()
    code = issue_code(label)
    if not code:
        await message.answer("Заказ не найден.")
        return
    await message.answer(f"Заказ {label} помечен как оплаченный. Код: {code}")


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Fill .env file.")
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
