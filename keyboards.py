from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def reply_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Пригласи друга"),
                KeyboardButton(text="🎟️ Промокоды"),
            ],
            [KeyboardButton(text="ℹ️ Прочая информация")],
            [KeyboardButton(text="🎁 Розыгрыш 5000 ₽")],
        ],
        resize_keyboard=True,
    )


def inline_root_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 PUBG MOBILE",
                    callback_data="cat_pubg",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Telegram товары",
                    callback_data="cat_tg",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Все игры",
                    callback_data="cat_games",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛰️ Интернет без ограничений",
                    callback_data="cat_vpn",
                ),
            ],
        ],
    )


def inline_product_list(items: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for product_id, label in items:
        cb = f"pick_{product_id}"
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="menu_root")],
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def inline_pay_url(checkout_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить в PayCore",
                    url=checkout_url,
                ),
            ],
            [InlineKeyboardButton(text="◀️ В главное меню", callback_data="menu_root")],
        ],
    )


def reply_cancel_only() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить заказ")]],
        resize_keyboard=True,
    )
