# Wixyeez UC Shop Bot

Готовый Telegram-бот + сайт в черно-фиолетовом стиле для продажи игровых пополнений с интеграцией PayCore.

## Что внутри

- Бот `bot.py`:
  - меню категорий (PUBG, Genshin, Steam)
  - создание заказа
  - оформление платежа через PayCore
  - проверка оплаты
  - автоматическая выдача кода
  - админ-команда `/mark_paid <order_id>`
- Сайт `web/`:
  - лендинг Wixyeez UC Shop
  - каталог и описание процесса покупки
  - стиль черно-фиолетовый

## Быстрый запуск

1. Установите Python 3.11+
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Создайте `.env`:

```bash
copy .env.example .env
```

4. Заполните `.env`:
- `BOT_TOKEN`
- `ADMIN_ID`
- `WEBSITE_URL`
- `SUPPORT_URL`
- `BOT_PUBLIC_URL`
- `PAYCORE_MODE` (`demo` или `live`)
- `PAYCORE_API_URL`
- `PAYCORE_MERCHANT_ID`
- `PAYCORE_TOKEN` (можно добавить позже)

5. Запустите бота:

```bash
python bot.py
```

## Режимы PayCore

- `PAYCORE_MODE=demo`: оплата подтверждается автоматически (для теста без токена).
- `PAYCORE_MODE=live`: реальная интеграция PayCore через API.

## Запуск сайта

```bash
python -m http.server 8080 --directory web
```

Откройте `http://localhost:8080`.
