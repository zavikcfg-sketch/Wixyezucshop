# WIXYEZ UC SHOP

Полноценный Telegram-бот на `Aiogram 3` + Telegram Mini App для игрового магазина.

## Архитектура (профессиональная структура)

- `bot.py` - тонкая точка входа
- `app/main.py` - инициализация бота и DI
- `app/config.py` - загрузка и валидация конфигурации
- `app/db.py` - подключение и миграция SQLite
- `app/services/orders.py` - бизнес-логика заказов
- `app/handlers/user.py` - пользовательские сценарии
- `app/handlers/admin.py` - админ-команды
- `app/handlers/webapp.py` - прием данных из Mini App
- `app/keyboards/main.py` - клавиатура бота

## Что умеет

- Главное меню с фиксированной Reply Keyboard.
- WebApp-кнопка `🎮 ВСЕ ИГРЫ`.
- Создание заказа из Mini App и отправка в бот.
- SQLite база заказов.
- Уведомления админу о новых заказах.
- Админ-команды для просмотра и изменения статуса.
- Команда пользователя `/myorders` для проверки своих заказов.

## Установка

```powershell
cd C:\Users\zavik\WIXYEZ-UC-SHOP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Настройка .env

1. Скопируйте пример:

```powershell
Copy-Item .env.example .env
```

2. Откройте `.env` и заполните:

- `BOT_TOKEN` - токен из BotFather
- `ADMIN_ID` - ваш Telegram user id
- `WEB_APP_URL` - HTTPS ссылка ngrok на `index.html`
- `SITE_URL` - ссылка сайта
- `DB_PATH` - путь к базе (обычно `shop.db`)

## Запуск Mini App локально

В первом терминале:

```powershell
cd C:\Users\zavik\WIXYEZ-UC-SHOP
python -m http.server 8080
```

Во втором терминале:

```powershell
ngrok http 8080
```

Берем HTTPS URL из ngrok и ставим в `.env`:

`WEB_APP_URL=https://<ваш-ngrok>.ngrok-free.app/index.html`

## Запуск бота

```powershell
cd C:\Users\zavik\WIXYEZ-UC-SHOP
.\.venv\Scripts\Activate.ps1
python bot.py
```

## Команды

### Пользователь

- `/start`
- `/menu`
- `/help`
- `/myorders`

### Админ

- `/orders` - последние заказы
- `/order <id>` - детали заказа
- `/setstatus <id> <NEW|PAID|DONE|CANCELED>`

## Как работает заказ из Mini App

1. Пользователь открывает кнопку `🎮 ВСЕ ИГРЫ`.
2. Выбирает игру и пишет детали.
3. Нажимает `Отправить заказ в бот`.
4. WebApp отправляет `sendData(JSON)`.
5. Бот сохраняет заказ в SQLite, отвечает пользователю и отправляет уведомление админу.
