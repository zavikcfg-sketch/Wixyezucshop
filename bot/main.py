"""
Wixyeez UC Shop — Telegram-бот. Запуск из корня проекта:
  python -m bot.main
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, FSInputFile, Message

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.keyboards import (  # noqa: E402
    inline_pay_url,
    inline_product_list,
    inline_root_menu,
    reply_cancel_only,
    reply_main_menu,
)
from shared.catalog import (  # noqa: E402
    OTHER_GAMES,
    PUBG_UC_PRODUCTS,
    TELEGRAM_GOODS,
    VPN_SERVICE,
    get_product,
)
from shared.config import get_settings  # noqa: E402
from shared.paycore import (  # noqa: E402
    PayCoreNotConfiguredError,
    PayCoreRequestError,
    create_payment_invoice,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRAND = "Wixyeez UC Shop"
BANNER_PATH = ROOT / "assets" / "banner.png"


class OrderFlow(StatesGroup):
    waiting_account = State()


def _format_product_line(p) -> tuple[str, str]:
    if p.amount <= 0:
        return p.id, f"{p.title} — скоро"
    price = int(p.amount) if p.amount == int(p.amount) else p.amount
    return p.id, f"{p.title} — {price} ₽"


async def send_welcome(bot: Bot, chat_id: int) -> None:
    text = (
        f"🟣 <b>{BRAND}</b>\n"
        f"Безопасно · Оперативно · 24/7\n\n"
        f"Добро пожаловать! Выберите категорию ниже.\n"
        f"Оплата через <b>PayCore</b> — после создания заказа откроется защищённая страница оплаты."
    )

    if BANNER_PATH.is_file():
        photo = FSInputFile(BANNER_PATH)
        await bot.send_photo(
            chat_id,
            photo,
            caption=text,
            reply_markup=inline_root_menu(),
            parse_mode="HTML",
        )
        await bot.send_message(
            chat_id,
            "Быстрые действия:",
            reply_markup=reply_main_menu(),
        )
    else:
        await bot.send_message(
            chat_id,
            text + "\n\n<i>Добавьте assets/banner.png — см. scripts/generate_banner.py</i>",
            reply_markup=reply_main_menu(),
            parse_mode="HTML",
        )
        await bot.send_message(
            chat_id,
            "Категории:",
            reply_markup=inline_root_menu(),
        )


def register_handlers(dp: Dispatcher, settings) -> None:
    @dp.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        payload = ""
        if message.text and len(message.text.split(maxsplit=1)) > 1:
            payload = message.text.split(maxsplit=1)[1].strip()
        extra = ""
        if payload.startswith("ref_"):
            extra = "\n🔗 Реферальная программа активирована."

        await send_welcome(message.bot, message.chat.id)
        if extra:
            await message.answer(extra)

    @dp.message(Command("help", "menu"))
    async def cmd_help(message: Message) -> None:
        await message.answer(
            f"Команды:\n/start — главное меню\n/help — помощь\n"
            f"Поддержка: напишите сюда же описание проблемы — мы свяжемся с вами.",
            reply_markup=inline_root_menu(),
        )

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Заказ отменён.", reply_markup=reply_main_menu())

    @dp.callback_query(F.data == "menu_root")
    async def cb_menu_root(q: CallbackQuery) -> None:
        try:
            await q.message.edit_reply_markup(reply_markup=inline_root_menu())
        except Exception:
            await q.message.answer("Главное меню:", reply_markup=inline_root_menu())
        await q.answer()

    @dp.callback_query(F.data == "cat_pubg")
    async def cb_cat_pubg(q: CallbackQuery) -> None:
        items = [_format_product_line(p) for p in PUBG_UC_PRODUCTS]
        await q.message.edit_reply_markup(
            reply_markup=inline_product_list(items),
        )
        await q.answer()

    @dp.callback_query(F.data == "cat_tg")
    async def cb_cat_tg(q: CallbackQuery) -> None:
        items = [_format_product_line(p) for p in TELEGRAM_GOODS]
        await q.message.edit_reply_markup(
            reply_markup=inline_product_list(items),
        )
        await q.answer()

    @dp.callback_query(F.data == "cat_games")
    async def cb_cat_games(q: CallbackQuery) -> None:
        items = [_format_product_line(p) for p in OTHER_GAMES]
        await q.message.edit_reply_markup(
            reply_markup=inline_product_list(items),
        )
        await q.answer()

    @dp.callback_query(F.data == "cat_vpn")
    async def cb_cat_vpn(q: CallbackQuery) -> None:
        items = [_format_product_line(p) for p in VPN_SERVICE]
        await q.message.edit_reply_markup(
            reply_markup=inline_product_list(items),
        )
        await q.answer()

    @dp.callback_query(F.data.startswith("pick_"))
    async def cb_pick(q: CallbackQuery, state: FSMContext) -> None:
        pid = q.data.removeprefix("pick_")
        product = get_product(pid)
        await q.answer()
        if not product:
            await q.message.answer("Товар не найден. Нажмите /start.")
            return
        if product.amount <= 0:
            await q.message.answer(
                f"«{product.title}» пока недоступен для автозаказа.\n"
                f"Напишите оператору сюда в чат — подключим вручную.",
            )
            return

        await state.set_state(OrderFlow.waiting_account)
        await state.update_data(product_id=pid)
        await q.message.answer(
            f"Вы выбрали: <b>{product.title}</b> — <b>{product.amount:g} ₽</b>\n"
            f"Введите <b>{product.game_id_label}</b> для пополнения.\n\n"
            f"Или отправьте /cancel или нажмите «Отменить заказ».",
            parse_mode="HTML",
            reply_markup=reply_cancel_only(),
        )

    @dp.message(OrderFlow.waiting_account, F.text == "❌ Отменить заказ")
    @dp.message(OrderFlow.waiting_account, Command("cancel"))
    async def cancel_order(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Заказ отменён.", reply_markup=reply_main_menu())

    @dp.message(OrderFlow.waiting_account, F.text)
    async def process_account(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        pid = data.get("product_id")
        product = get_product(pid) if pid else None
        if not product:
            await state.clear()
            await message.answer("Сессия сброшена. /start")
            return

        account = (message.text or "").strip()
        if len(account) < 3:
            await message.answer("Слишком короткое значение, введите ещё раз.")
            return

        await state.clear()
        await message.answer(
            "⏳ Создаю платёж в PayCore…",
            reply_markup=reply_main_menu(),
        )

        desc = (
            f"{BRAND} | {product.title} | {product.game_id_label}: {account[:120]}"
        )
        curr = settings.paycore_currency or product.currency or "RUB"

        try:
            inv = await create_payment_invoice(
                settings,
                amount=product.amount,
                currency=curr,
                description=desc,
            )
        except PayCoreNotConfiguredError as e:
            await message.answer(
                f"⚠️ PayCore пока не настроен:\n{e}\n\n"
                f"После добавления ключей в .env оплата заработает автоматически.\n\n"
                f"<b>Сводка заказа</b>\n"
                f"Товар: {product.title}\n"
                f"Сумма: {product.amount:g} {curr}\n"
                f"Реквизит: <code>{account}</code>",
                parse_mode="HTML",
            )
            return
        except PayCoreRequestError as e:
            logger.exception("PayCore error")
            await message.answer(f"❌ Ошибка PayCore: {e}")
            return

        hpp_url = inv.get("hpp_url")
        if not hpp_url or not isinstance(hpp_url, str):
            await message.answer(
                f"Ответ без ссылки оплаты: <code>{inv}</code>",
                parse_mode="HTML",
            )
            return

        ref = inv.get("reference_id", "")
        await message.answer(
            f"✅ Инвойс создан.\nРеференс: <code>{ref}</code>\n"
            f"{product.game_id_label}: <code>{account}</code>",
            reply_markup=inline_pay_url(hpp_url),
            parse_mode="HTML",
        )

    @dp.message(F.text == "👥 Пригласи друга")
    async def invite_friend(message: Message) -> None:
        me = await message.bot.me()
        if not me or not me.username:
            await message.answer("У бота нет username — рефссылку настройте через @BotFather.")
            return
        link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
        await message.answer(
            f"Ваша ссылка:\n<code>{link}</code>\n\n"
            f"Приглашённые открывают бота по ней — бонус можно настроить вручную у оператора.",
            parse_mode="HTML",
        )

    @dp.message(F.text == "🎟️ Промокоды")
    async def promos(message: Message) -> None:
        await message.answer(
            "Отправьте промокод одним сообщением в формате:\n<code>/promo ВАШ_КОД</code>",
            parse_mode="HTML",
        )

    @dp.message(Command("promo"))
    async def promo_apply(message: Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ""
        if not code:
            await message.answer("Укажите код: /promo SUMMER2026")
            return
        await message.answer(
            f"Промокод <code>{code}</code> принят (демо).\n"
            f"Подключите свою базу промокодов в коде сервера.",
            parse_mode="HTML",
        )

    @dp.message(F.text == "ℹ️ Прочая информация")
    async def other_info(message: Message) -> None:
        await message.answer(
            f"⚡ <b>{BRAND}</b>\n\n"
            f"· Работаем 24/7\n"
            f"· Автовыдача после подтверждения платежа (настройте вебхук PayCore → ваш сервер)\n"
            f"· Поддержка в этом чате\n\n"
            f"Оферта и политика — разместите ссылки под себя.",
            parse_mode="HTML",
        )

    @dp.message(F.text == "🎁 Розыгрыш 5000 ₽")
    async def giveaway(message: Message) -> None:
        ch = settings.channel_username.strip()
        if ch:
            await message.answer(f"Участвуйте в канале {ch}")
        else:
            await message.answer(
                "Розыгрыши анонсируются в нашем канале. "
                "Добавьте CHANNEL_USERNAME в .env чтобы показать @канал здесь.",
            )


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit(
            "Укажите TELEGRAM_BOT_TOKEN в .env",
        )

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, settings)

    logger.info("Бот запущен: %s", BRAND)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
