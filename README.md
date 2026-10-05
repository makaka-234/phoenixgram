# PhoenixGram 🐦‍🔥

Полноценный мессенджер-клон Telegram с внутренней валютой **Звёзды Феникс**, магазином подарков, Premium-подпиской, Telegram-ботом-магазином, веб-админ-панелью владельца и мобильным приложением на Flutter.

> **Звёзды Феникс — внутренняя валюта**. Вывод средств невозможен ни в каком виде. Покупка звёзд, Premium, красивых юзернеймов и верификации осуществляется только за Telegram Stars (XTR). Обмен звёзд Феникс на деньги или криптовалюту не предусмотрен.

---

## 1. Состав проекта

```
phoenixgram/
├── backend/          # FastAPI + PostgreSQL + Redis + WebSocket
├── bot/              # Telegram-бот-магазин (aiogram 3.x)
├── admin/            # Админ-панель владельца (React + TypeScript + Vite)
├── mobile/           # Мобильное приложение (Flutter, Android + iOS)
├── scripts/          # Вспомогательные скрипты
├── docker-compose.yml
├── .env.example
└── README.md
```

## 2. Требования

* Docker ≥ 24 и Docker Compose v2 (для полного стека)
* Python 3.11+ (для локального запуска backend/bot без Docker)
* Node.js 20+ (для админки без Docker)
* Flutter 3.19+ (для мобильного приложения)
* Токен Telegram-бота от [@BotFather](https://t.me/BotFather)
* Telegram ID владельца — узнать у [@userinfobot](https://t.me/userinfobot)

## 3. Быстрый старт (Docker, весь стек)

```bash
# 1. Перейти в папку проекта
cd phoenixgram

# 2. Создать .env и заполнить
cp .env.example .env
#   обязательно укажите SECRET_KEY, BOT_TOKEN, OWNER_TG_ID, ADMIN_PASSWORD

# 3. Сгенерировать секрет (если нужно)
openssl rand -hex 32

# 4. Собрать и запустить
docker compose up -d --build

# 5. Проверить статус
docker compose ps
docker compose logs -f backend bot
```

После запуска доступны:

| Сервис        | Адрес                          |
|---------------|--------------------------------|
| Backend API   | http://localhost:8000          |
| Swagger UI    | http://localhost:8000/docs     |
| Админ-панель  | http://localhost:8080          |
| PostgreSQL    | localhost:5432                 |
| Redis         | localhost:6379                 |

Бот запускается автоматически (long polling) — откройте его в Telegram.

## 4. Запуск для разработки (без Docker)

### 4.1. Инфраструктура
```bash
docker compose up -d postgres redis
```

### 4.2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env           # и заполнить
python -m app.init_db                # создать таблицы + сиды
uvicorn app.main:app --reload --port 8000
```

### 4.3. Bot
```bash
cd bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

### 4.4. Admin
```bash
cd admin
npm install
npm run dev        # http://localhost:5173
```

### 4.5. Mobile
```bash
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000   # Android-эмулятор
# или
flutter run --dart-define=API_URL=http://localhost:8000  # iOS-симулятор
```

## 5. Как пользоваться

1. Откройте бота в Telegram, отправьте `/start`.
2. **📝 Регистрация** — введите желаемый ID (латиница, 3–20 символов). Бот проверит уникальность, создаст аккаунт, начислит **1000 звёзд** бонусом и выдаст **8-значный код**.
3. Откройте мобильное приложение, введите ID и код — вы внутри.
4. **🛒 Магазин** в боте: покупка Звёзд Феникс, Premium, красивых юзернеймов и верификации за Telegram Stars.
5. **🔐 Админ-панель бота** доступна владельцу и админам (`/addadmin <tg_id>`).
6. Веб-админка (`http://localhost:8080`) — вход по `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

## 6. Внутренняя валюта и оплата

* **Звёзды Феникс** — внутренняя валюта приложения. Покупаются пакетами за Telegram Stars (XTR) в боте. Вывод невозможен.
* Оплата выполняется штатным механизмом Telegram (`sendInvoice` с `currency="XTR"`). Реальные деньги в приложение не поступают минуя Telegram.
* Товары за звёзды Феникс: Premium, красивые юзернеймы, верификация, подарки.

## 7. Архитектура

* **Backend** — FastAPI, SQLAlchemy 2 (async, asyncpg), Redis (pub/sub для WebSocket и кэш), JWT (access + refresh).
* **WebSocket** — `/api/v1/ws?token=...`, доставка через Redis pub/sub (масштабируется горизонтально).
* **Bot** — aiogram 3.x, FSM, приём платежей Telegram Stars (`pre_checkout_query`, `successful_payment`).
* **Admin** — React 18 + TS + Vite, Zustand, TanStack Query, Tailwind.
* **Mobile** — Flutter, Riverpod, Dio, `web_socket_channel`.

## 8. Безопасность и логирование

* Пароли админов — bcrypt.
* Все админ-действия пишутся в таблицу `admin_logs` (кто, что, когда, над кем).
* Бан/разбан пользователей с указанием причины.
* JWT access и refresh токены; refresh-токен можно отозвать.

## 9. Остановка

```bash
docker compose down          # остановить
docker compose down -v       # остановить и удалить данные БД
```

## 10. Лицензия

Проект предоставляется как есть для личного использования владельцем.
