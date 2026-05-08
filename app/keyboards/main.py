from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


def build_main_keyboard(web_app_url: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="PUBG MOBILE")],
            [KeyboardButton(text="TG Товары")],
            [KeyboardButton(text="🎮 ВСЕ ИГРЫ", web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text="VPN Интернет без ограничений")],
            [KeyboardButton(text="👥 Пригласи друга"), KeyboardButton(text="5% Промокоды")],
            [KeyboardButton(text="Заработать денег")],
            [KeyboardButton(text="Наш сайт в Google")],
            [KeyboardButton(text="Розыгрыш 5000₽")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите раздел магазина...",
    )
