from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from database import get_or_create_user, is_premium as db_is_premium, get_daily_count
from keyboards import premium_keyboard
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
        status = '<tg-emoji emoji-id="5873147866364514353">🏘</tg-emoji> <b>Premium</b>'
    else:
        status = '<tg-emoji emoji-id="5870994129244131212">👤</tg-emoji> <b>Free</b>'

    await message.answer(
        f'<tg-emoji emoji-id="6041731551845159060">🎉</tg-emoji> <b>Привет, {user.first_name}!</b>\n\n'
        f'Я скачиваю видео из популярных платформ и отправляю файл прямо сюда.\n\n'
        f'<blockquote>'
        f'<tg-emoji emoji-id="5870528606328852614">📁</tg-emoji> YouTube\n'
        f'<tg-emoji emoji-id="5870528606328852614">📁</tg-emoji> TikTok\n'
        f'<tg-emoji emoji-id="5870528606328852614">📁</tg-emoji> Instagram'
        f'</blockquote>\n\n'
        f'<tg-emoji emoji-id="5870994129244131212">👤</tg-emoji> Статус: {status}\n'
        f'<tg-emoji emoji-id="6039802767931871481">⬇</tg-emoji> Загрузок сегодня: <b>{remaining}</b>\n\n'
        f'<blockquote expandable>'
        f'<tg-emoji emoji-id="6028435952299413210">ℹ</tg-emoji> <b>Команды</b>\n'
        f'/premium — Premium подписка\n'
        f'/help — как пользоваться'
        f'</blockquote>\n\n'
        f'<tg-emoji emoji-id="5769289093221454192">🔗</tg-emoji> Просто отправь ссылку на видео!',
        parse_mode="HTML",
        message_effect_id=FX_PARTY,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        f'<tg-emoji emoji-id="6028435952299413210">ℹ</tg-emoji> <b>Как пользоваться</b>\n\n'
        f'<b>1.</b> Отправь ссылку на видео\n'
        f'<blockquote>youtube.com · tiktok.com · instagram.com</blockquote>\n\n'
        f'<b>2.</b> Выбери качество или <code>MP3</code>\n\n'
        f'<b>3.</b> Получи файл в чате\n\n'
        f'<tg-emoji emoji-id="5870930636742595124">📊</tg-emoji> <b>Планы</b>\n'
        f'<blockquote>'
        f'<tg-emoji emoji-id="5870994129244131212">👤</tg-emoji> Free — 5 загрузок/день · до 720p\n'
        f'<tg-emoji emoji-id="5873147866364514353">🏘</tg-emoji> Premium — без лимитов · 1080p · приоритет'
        f'</blockquote>',
        parse_mode="HTML",
        message_effect_id=FX_LIKE,
    )


@router.message(Command("premium"))
async def cmd_premium(message: Message):
    premium = db_is_premium(message.from_user.id)
    if premium:
        await message.answer(
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> <b>Premium активен!</b>\n\n'
            f'Все функции уже открыты для тебя.\n'
            f'<tg-spoiler>Ты лучший 🔥</tg-spoiler>',
            parse_mode="HTML",
            message_effect_id=FX_HEART,
        )
        return

    await message.answer(
        f'<tg-emoji emoji-id="6032644646587338669">🎁</tg-emoji> <b>Premium подписка</b>\n\n'
        f'<blockquote>'
        f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Без лимита загрузок\n'
        f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Качество до <code>1080p</code>\n'
        f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Приоритет в очереди\n'
        f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Поддержка 24/7'
        f'</blockquote>\n\n'
        f'<tg-emoji emoji-id="5904462880941545555">🪙</tg-emoji> <b>$3 / месяц</b>',
        parse_mode="HTML",
        message_effect_id=FX_FIRE,
        reply_markup=premium_keyboard(),
    )

