from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from database import get_or_create_user, is_premium as db_is_premium, get_daily_count
from keyboards import premium_keyboard, main_menu_keyboard
from config import FREE_DAILY_LIMIT

router = Router()

FX_PARTY = "5046509860389126442"
FX_LIKE  = "5107584321108051014"
FX_FIRE  = "5104841245755180586"
FX_HEART = "5159385139981059251"
FX_POOP  = "5046589136895476101"



@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    get_or_create_user(user.id, user.username or "")
    premium = db_is_premium(user.id)
    remaining = "∞" if premium else str(max(0, FREE_DAILY_LIMIT - get_daily_count(user.id)))

    if premium:
        text = (
            f'<tg-emoji emoji-id="6041731551845159060">🎉</tg-emoji> Вас приветствует <b>SnapLoad</b>!\n\n'
            f'<tg-emoji emoji-id="6032644646587338669">🎁</tg-emoji> Привет, <b>{user.first_name}</b>! '
            f'У тебя активен <b>Premium</b> — все функции открыты!\n\n'
            f'<blockquote>'
            f'<tg-emoji emoji-id="5870528606328852614">📁</tg-emoji> YouTube · TikTok · Instagram\n'
            f'<tg-emoji emoji-id="6039802767931871481">⬇</tg-emoji> Качество до <b>1080p</b>\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Без лимитов загрузок\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Приоритетная очередь'
            f'</blockquote>\n\n'
            f'<tg-emoji emoji-id="5769289093221454192">🔗</tg-emoji> Просто отправь ссылку на видео!'
        )
    else:
        text = (
            f'👋 Вас приветствует <b>SnapLoad</b>!\n\n'
            f'Привет, <b>{user.first_name}</b>! Я скачиваю видео\n'
            f'из популярных платформ прямо в чат.\n\n'
            f'<blockquote>'
            f'📁 YouTube · TikTok · Instagram\n'
            f'⬇️ Качество до 720p\n'
            f'📥 Загрузок сегодня осталось: <b>{remaining}</b>'
            f'</blockquote>\n\n'
            f'🔗 Просто отправь ссылку на видео!'
        )

    await message.answer(
        text=text,
        parse_mode="HTML",
        message_effect_id=FX_PARTY,
        reply_markup=main_menu_keyboard(premium),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    premium = db_is_premium(message.from_user.id)

    if premium:
        text = (
            f'<tg-emoji emoji-id="6028435952299413210">ℹ</tg-emoji> <b>Как пользоваться</b>\n\n'
            f'<b>1.</b> Отправь ссылку на видео\n'
            f'<blockquote>youtube.com · tiktok.com · instagram.com</blockquote>\n\n'
            f'<b>2.</b> Выбери качество: <code>360p · 720p · 1080p</code> или <code>MP3</code>\n\n'
            f'<b>3.</b> Получи файл в чате\n\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> <b>Твой статус: Premium</b>\n'
            f'<blockquote>'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Без лимитов\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> До 1080p\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Приоритет в очереди'
            f'</blockquote>'
        )
    else:
        text = (
            f'ℹ️ <b>Как пользоваться</b>\n\n'
            f'<b>1.</b> Отправь ссылку на видео\n'
            f'<blockquote>youtube.com · tiktok.com · instagram.com</blockquote>\n\n'
            f'<b>2.</b> Выбери качество: <code>360p · 720p</code> или <code>MP3</code>\n\n'
            f'<b>3.</b> Получи файл в чате\n\n'
            f'📊 <b>Твой план: Free</b>\n'
            f'<blockquote>'
            f'• 5 загрузок в день\n'
            f'• Качество до 720p\n'
            f'• /premium — улучшить план'
            f'</blockquote>'
        )

    await message.answer(text, parse_mode="HTML", message_effect_id=FX_LIKE)


@router.message(Command("premium"))
async def cmd_premium(message: Message):
    premium = db_is_premium(message.from_user.id)
    if premium:
        await message.answer(
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> <b>Premium уже активен!</b>\n\n'
            f'<blockquote>'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Без лимита загрузок\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Качество до <code>1080p</code>\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Приоритет в очереди\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Поддержка 24/7'
            f'</blockquote>\n\n'
            f'<tg-spoiler>Ты лучший пользователь! 🔥</tg-spoiler>',
            parse_mode="HTML",
            message_effect_id=FX_HEART,
        )
        return

    await message.answer(
        f'⭐ <b>Premium подписка</b>\n\n'
        f'<blockquote>'
        f'✔️ Без лимита загрузок\n'
        f'✔️ Качество до <code>1080p</code>\n'
        f'✔️ Приоритет в очереди\n'
        f'✔️ Скачивание без водяных знаков\n'
        f'✔️ Поддержка 24/7'
        f'</blockquote>\n\n'
        f'💸 <b>Всего $3 / месяц</b>',
        parse_mode="HTML",
        message_effect_id=FX_FIRE,
        reply_markup=premium_keyboard(),
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = message.from_user
    get_or_create_user(user.id, user.username or "")
    premium = db_is_premium(user.id)
    count = get_daily_count(user.id)
    remaining = "∞" if premium else str(max(0, FREE_DAILY_LIMIT - count))

    if premium:
        text = (
            f'<tg-emoji emoji-id="5870994129244131212">👤</tg-emoji> <b>Профиль</b>\n\n'
            f'<tg-emoji emoji-id="5870676941614354370">🖋</tg-emoji> Имя: <b>{user.first_name}</b>\n'
            f'<tg-emoji emoji-id="5886285355279193209">🏷</tg-emoji> ID: <code>{user.id}</code>\n'
            f'<tg-emoji emoji-id="6032644646587338669">🎁</tg-emoji> Статус: <b>Premium ⭐</b>\n'
            f'<tg-emoji emoji-id="6039802767931871481">⬇</tg-emoji> Загрузок сегодня: <b>{count}</b>\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Лимит: <b>∞</b>'
        )
    else:
        text = (
            f'👤 <b>Профиль</b>\n\n'
            f'✏️ Имя: <b>{user.first_name}</b>\n'
            f'🏷 ID: <code>{user.id}</code>\n'
            f'📊 Статус: <b>Free</b>\n'
            f'📥 Загрузок сегодня: <b>{count}</b>\n'
            f'⏳ Осталось: <b>{remaining}</b> из <b>{FREE_DAILY_LIMIT}</b>'
        )

    await message.answer(text, parse_mode="HTML")

