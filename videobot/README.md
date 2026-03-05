# 🎬 VideoBot — Telegram Bot для скачивания видео

Бот скачивает видео из YouTube, TikTok и Instagram прямо в Telegram.

---

## 📁 Структура проекта

```
videobot/
├── bot.py                  # Точка входа
├── config.py               # Настройки и константы
├── database.py             # SQLite — пользователи, лимиты
├── keyboards.py            # Inline-клавиатуры
├── requirements.txt
├── .env.example
├── handlers/
│   ├── common.py           # /start, /help, /premium
│   └── downloader.py       # Обработка ссылок и скачивание
├── services/
│   └── downloader.py       # yt-dlp обёртка
└── middlewares/
    └── throttle.py         # Rate limiting
```

---

## ⚙️ Установка

### 1. Клонируй репозиторий и перейди в папку

```bash
cd videobot
```

### 2. Создай виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Установи ffmpeg (нужен для yt-dlp)

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 5. Настрой переменные окружения

```bash
cp .env.example .env
nano .env   # вставь токен бота
```

Получи токен у [@BotFather](https://t.me/BotFather).

### 6. Запусти бота

```bash
python bot.py
```

---

## 🖥 Деплой на VPS (systemd)

Создай файл `/etc/systemd/system/videobot.service`:

```ini
[Unit]
Description=Telegram VideoBot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/videobot
ExecStart=/home/ubuntu/videobot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable videobot
sudo systemctl start videobot
sudo journalctl -u videobot -f   # логи
```

---

## 💳 Монетизация

### Платная подписка
- Настрой Telegram Stars или внешний платёжный шлюз
- В `keyboards.py` замени URL кнопки "Купить Premium" на свою ссылку
- В `database.py` вызови `set_premium(user_id, until_date)` после оплаты

### Донат
- Замени ссылку `https://your-donate-link.com` в `handlers/downloader.py`

---

## ⚡ Лимиты и тарификация

| Параметр          | Free     | Premium   |
|-------------------|----------|-----------|
| Загрузок в день   | 5        | ∞         |
| Макс. качество    | 720p     | 1080p     |
| Очередь           | обычная  | приоритет |

Изменить лимиты можно в `config.py`.

---

## 🔧 Минимальные требования к серверу

- **CPU:** 2 cores
- **RAM:** 2 GB
- **Диск:** 20 GB (для временных файлов)
- **OS:** Ubuntu 22.04+
- **Python:** 3.10+
