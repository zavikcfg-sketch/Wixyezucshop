from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    description: str
    amount: float
    currency: str
    game_id_label: str = "Player ID"


# Типовые пакеты UC (цены примерные — замените на свои)
PUBG_UC_PRODUCTS: list[Product] = [
    Product(
        id="pubg_uc_60",
        title="60 UC",
        description="PUBG Mobile — 60 UC",
        amount=99.0,
        currency="RUB",
    ),
    Product(
        id="pubg_uc_325",
        title="325 UC",
        description="PUBG Mobile — 325 UC",
        amount=449.0,
        currency="RUB",
    ),
    Product(
        id="pubg_uc_660",
        title="660 UC",
        description="PUBG Mobile — 660 UC",
        amount=899.0,
        currency="RUB",
    ),
    Product(
        id="pubg_uc_1800",
        title="1800 UC",
        description="PUBG Mobile — 1800 UC",
        amount=2299.0,
        currency="RUB",
    ),
    Product(
        id="pubg_uc_3850",
        title="3850 UC",
        description="PUBG Mobile — 3850 UC",
        amount=4599.0,
        currency="RUB",
    ),
]

TELEGRAM_GOODS: list[Product] = [
    Product(
        id="tg_stars_100",
        title="100 Stars",
        description="Telegram Stars — пакет 100",
        amount=179.0,
        currency="RUB",
        game_id_label="Username / ссылка",
    ),
    Product(
        id="tg_premium_1m",
        title="Premium 1 мес.",
        description="Telegram Premium — 1 месяц (оформление по API кабинета)",
        amount=299.0,
        currency="RUB",
        game_id_label="Username",
    ),
]

OTHER_GAMES: list[Product] = [
    Product(
        id="steam_wallet_500",
        title="Steam 500 ₽",
        description="Пополнение Steam (по логину / инструкция после оплаты)",
        amount=500.0,
        currency="RUB",
        game_id_label="Логин Steam",
    ),
    Product(
        id="brawl_pass_stub",
        title="Brawl Stars — Brawl Pass",
        description="Скоро в ассортименте — оставьте заявку у оператора",
        amount=0.0,
        currency="RUB",
        game_id_label="Player tag",
    ),
    Product(
        id="coc_gems_stub",
        title="Clash of Clans — гемы",
        description="Скоро в ассортименте — оставьте заявку у оператора",
        amount=0.0,
        currency="RUB",
        game_id_label="Supercell ID",
    ),
    Product(
        id="genshin_stub",
        title="Genshin Impact",
        description="Скоро в ассортименте — оставьте заявку у оператора",
        amount=0.0,
        currency="RUB",
        game_id_label="UID",
    ),
]

VPN_SERVICE: list[Product] = [
    Product(
        id="vpn_month",
        title="VPN — 30 дней",
        description="Доступ без ограничений — данные выдаются после оплаты",
        amount=199.0,
        currency="RUB",
        game_id_label="Email для выдачи доступа",
    ),
]

_BY_ID: dict[str, Product] = {}
for _plist in (PUBG_UC_PRODUCTS, TELEGRAM_GOODS, OTHER_GAMES, VPN_SERVICE):
    for _p in _plist:
        _BY_ID[_p.id] = _p


def get_product(product_id: str) -> Optional[Product]:
    return _BY_ID.get(product_id)
