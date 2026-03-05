from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from database import get_or_create_user, is_premium as db_is_premium, get_daily_count
from keyboards import premium_keyboard, main_menu_keyboard
from config import FREE_DAILY_LIMIT

router = Router()

# ─── Effect IDs ───────────────────────────────────────────────────────────────
FX_PARTY = "5046509860389126442"
FX_LIKE  = "5107584321108051014"
FX_FIRE  = "5104841245755180586"
FX_HEART = "5159385139981059251"
FX_POOP  = "5046589136895476101"


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    get_or_create_user(user.id, user.username or "")
    premium   = db_is_premium(user.id)
    status    = "⭐ <b>Premium</b>" if premium else "🆓 <b>Free</b>"
    remaining = "∞" if premium else str(max(0, FREE_DAILY_LIMIT - get_daily_count(user.id)))

    await message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃   🎬  <b>VideoLoader Bot</b>   ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👋 Привет, <b>{user.first_name}</b>! Я помогу тебе скачать видео.\n\n"
        f"<blockquote>📌 Поддерживаемые платформы:\n"
        f"  🔴 YouTube\n"
        f"  🎵 TikTok\n"
        f"  📸 Instagram</blockquote>\n\n"
        f"╭─────────────────────\n"
        f"│ 🏷  Статус: {status}\n"
        f"│ 📥 Загрузок осталось: <b>{remaining}</b>\n"
        f"╰─────────────────────\n\n"
        f"👇 Выбери действие в меню ниже:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
        message_effect_id=FX_PARTY,
    )


@router.message(F.text == "⬇️ Скачать видео")
async def btn_download(message: Message):
    await message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃   ⬇️  <b>Скачать видео</b>    ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📎 <b>Отправь ссылку на видео</b>\n\n"
        f"<blockquote>Примеры:\n"
        f"  🔴 <code>https://youtu.be/xxxxx</code>\n"
        f"  🎵 <code>https://tiktok.com/@user/video/xxx</code>\n"
        f"  📸 <code>https://instagram.com/p/xxxxx</code></blockquote>",
        parse_mode="HTML",
    )


@router.message(F.text == "👤 Мой профиль")
async def btn_profile(message: Message):
    user = message.from_user
    get_or_create_user(user.id, user.username or "")
    premium   = db_is_premium(user.id)
    count     = get_daily_count(user.id)
    status    = "⭐ Premium" if premium else "🆓 Free"
    remaining = "∞" if premium else str(max(0, FREE_DAILY_LIMIT - count))
    limit_str = "∞" if premium else str(FREE_DAILY_LIMIT)
    bar_done  = min(count, FREE_DAILY_LIMIT) if not premium else 0
    bar_total = FREE_DAILY_LIMIT if not premium else 5
    bar       = "🟩" * bar_done + "⬜" * (bar_total - bar_done) if not premium else "🟩🟩🟩🟩🟩"

    await message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃     👤  <b>Мой профиль</b>     ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"├ 👤 Имя: <b>{user.first_name}</b>\n"
        f"├ 🆔 ID: <code>{user.id}</code>\n"
        f"├ 📊 Статус: <b>{status}</b>\n\n"
        f"╭─────────────────────\n"
        f"│ 📥 Загрузок сегодня\n"
        f"│ {bar}\n"
        f"│ <b>{count}</b> / {limit_str}  •  осталось: <b>{remaining}</b>\n"
        f"╰─────────────────────",
        parse_mode="HTML",
        message_effect_id=FX_LIKE,
    )


@router.message(F.text == "⭐ Premium")
@router.message(Command("premium"))
async def cmd_premium(message: Message):
    if db_is_premium(message.from_user.id):
        await message.answer(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃   ⭐  <b>Premium активен</b>  ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"✔️ Подписка уже активна!\n\n"
            f"<blockquote>🔓 Лимиты сняты\n"
            f"🎬 Качество до 1080p\n"
            f"⚡ Приоритетная очередь</blockquote>\n\n"
            f"<tg-spoiler>💎 Ты VIP пользователь — спасибо!</tg-spoiler>",
            parse_mode="HTML",
            message_effect_id=FX_HEART,
        )
        return

    await message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃   ⭐  <b>Premium-доступ</b>   ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"<b>Что входит в Premium:</b>\n\n"
        f"├ 🔓 Безлимитные загрузки\n"
        f"├ 🎬 Качество до <code>1080p</code>\n"
        f"├ ⚡ Приоритет в очереди\n"
        f"├ 🎵 MP3 без ограничений\n\n"
        f"<blockquote>💸 Всего <b>$3 в месяц</b>\n"
        f"Отменить можно в любой момент</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_FIRE,
        reply_markup=premium_keyboard(),
    )


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃    ❓  <b>Как пользоваться</b>   ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"<b>Шаг 1.</b> Нажми <b>⬇️ Скачать видео</b>\n"
        f"<b>Шаг 2.</b> Отправь ссылку на видео\n"
        f"<b>Шаг 3.</b> Выбери качество\n"
        f"<b>Шаг 4.</b> Получи файл ✔️\n\n"
        f"╭─────────────────────\n"
        f"│ 🆓 <b>Free</b>\n"
        f"│   • 5 загрузок / день\n"
        f"│   • максимум <code>720p</code>\n"
        f"├─────────────────────\n"
        f"│ ⭐ <b>Premium</b>\n"
        f"│   • без лимитов\n"
        f"│   • до <code>1080p</code>\n"
        f"│   • быстрее очередь\n"
        f"╰─────────────────────\n\n"
        f"<blockquote expandable>🛠 <b>Технические детали</b>\n"
        f"Бот использует yt-dlp для скачивания.\n"
        f"Максимальный размер файла: 50 МБ.\n"
        f"Поддерживаются: YouTube, TikTok, Instagram.</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_LIKE,
    )
