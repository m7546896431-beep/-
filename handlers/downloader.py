"""
Handler flow:
  1. User sends a URL  → bot extracts info, shows preview + quality buttons
  2. User taps quality → bot downloads, sends file, cleans up
"""
import asyncio
import logging
import os
import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile

import database as db
from config import FREE_DAILY_LIMIT, FREE_MAX_QUALITY, MAX_FILE_SIZE_MB
from keyboards import quality_keyboard, premium_keyboard, main_menu_keyboard
from services.downloader import (
    detect_platform,
    fetch_info,
    download_video,
    cleanup,
)

router = Router()
logger = logging.getLogger(__name__)

FX_PARTY = "5046509860389126442"
FX_LIKE  = "5107584321108051014"
FX_FIRE  = "5104841245755180586"
FX_HEART = "5159385139981059251"
FX_POOP  = "5046589136895476101"

_active_downloads: dict[int, bool] = {}
_url_store: dict[str, str] = {}


def _save_url(url: str) -> str:
    key = uuid.uuid4().hex[:8]
    _url_store[key] = url
    return key


def _get_url(key: str):
    return _url_store.get(key)


def _fmt_duration(seconds) -> str:
    try:
        seconds = int(seconds or 0)
        if not seconds:
            return "неизвестно"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    except Exception:
        return "неизвестно"


def _is_url(text) -> bool:
    if not text:
        return False
    return text.startswith(("http://", "https://")) and "." in text


async def _safe_edit(msg: Message, text: str, **kwargs) -> None:
    try:
        await msg.edit_text(text, **kwargs)
    except Exception:
        try:
            await msg.answer(text, **kwargs)
        except Exception as e:
            logger.warning(f"_safe_edit failed: {e}")


# ─── Кнопки нижнего меню ────────────────────────────────────────────────────
@router.message(F.text == "👤 Профиль")
async def menu_profile(message: Message):
    from handlers.common import cmd_profile
    await cmd_profile(message)


@router.message(F.text == "ℹ️ Помощь")
async def menu_help(message: Message):
    from handlers.common import cmd_help
    await cmd_help(message)


@router.message(F.text == "⭐ Купить Premium")
async def menu_premium(message: Message):
    from handlers.common import cmd_premium
    await cmd_premium(message)


@router.message(F.text == "⭐ Premium активен")
async def menu_premium_active(message: Message):
    from handlers.common import cmd_premium
    await cmd_premium(message)


@router.message(F.text == "🔗 Отправить ссылку")
async def menu_link_hint(message: Message):
    await message.answer(
        "📎 Просто отправь ссылку на видео в чат!\n\n"
        "<blockquote>youtube.com · tiktok.com · instagram.com</blockquote>",
        parse_mode="HTML",
    )


# ─── Step 1: receive link ───────────────────────────────────────────────────
@router.message(F.text.func(_is_url))
async def handle_url(message: Message):
    user_id = message.from_user.id
    url = message.text.strip()

    platform = detect_platform(url)
    if not platform:
        await message.answer(
            "✖️ <b>Ссылка не поддерживается</b>\n\n"
            "<blockquote>Поддерживаются:\n"
            "📁 YouTube\n📁 TikTok\n📁 Instagram</blockquote>",
            parse_mode="HTML",
            message_effect_id=FX_POOP,
        )
        return

    premium = db.is_premium(user_id)
    if not premium and db.get_daily_count(user_id) >= FREE_DAILY_LIMIT:
        await message.answer(
            f"🔒 <b>Лимит исчерпан</b>\n\n"
            f"Ты достиг лимита <b>{FREE_DAILY_LIMIT} загрузок</b> в день.\n\n"
            f"<blockquote>⭐ Оформи Premium для безлимитных загрузок</blockquote>",
            parse_mode="HTML",
            reply_markup=premium_keyboard(),
        )
        return

    status_msg = await message.answer(
        "⏳ <b>Получаю информацию о видео…</b>",
        parse_mode="HTML",
    )

    try:
        info = await fetch_info(url)
    except asyncio.TimeoutError:
        await _safe_edit(status_msg,
            "✖️ <b>Таймаут</b>\n\nПревышено время ожидания. Попробуй позже.",
            parse_mode="HTML")
        return
    except Exception as e:
        logger.error(f"fetch_info error: {e}")
        await _safe_edit(status_msg,
            "✖️ <b>Ошибка</b>\n\nНе удалось получить информацию.\n"
            "<blockquote>Проверь ссылку или попробуй позже.</blockquote>",
            parse_mode="HTML")
        return

    url_key = _save_url(url)

    if premium:
        caption = (
            f'<tg-emoji emoji-id="6035128606563241721">🖼</tg-emoji> <b>{info.title}</b>\n\n'
            f'<tg-emoji emoji-id="5886285355279193209">🏷</tg-emoji> Платформа: <b>{info.platform}</b>\n'
            f'<tg-emoji emoji-id="5983150113483134607">⏰</tg-emoji> Длительность: <code>{_fmt_duration(info.duration)}</code>\n\n'
            f'<tg-emoji emoji-id="6039802767931871481">⬇</tg-emoji> <b>Выбери качество:</b>'
        )
    else:
        caption = (
            f"🎬 <b>{info.title}</b>\n\n"
            f"📌 Платформа: <b>{info.platform}</b>\n"
            f"⏱ Длительность: <code>{_fmt_duration(info.duration)}</code>\n\n"
            f"👇 <b>Выбери качество:</b>"
        )

    kb = quality_keyboard(url_key, premium)

    try:
        if info.thumbnail:
            await status_msg.delete()
            await message.answer_photo(photo=info.thumbnail, caption=caption,
                                       parse_mode="HTML", reply_markup=kb)
        else:
            await _safe_edit(status_msg, caption, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await _safe_edit(status_msg, caption, parse_mode="HTML", reply_markup=kb)


# ─── Step 2: quality callback ───────────────────────────────────────────────
@router.callback_query(F.data.startswith("dl|"))
async def handle_download_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    if _active_downloads.get(user_id):
        await callback.message.answer(
            "⏳ <b>Подожди</b> — твоё предыдущее видео ещё загружается.",
            parse_mode="HTML")
        return

    parts = callback.data.split("|", 2)
    if len(parts) != 3:
        return

    _, quality_raw, url_key = parts
    audio_only = quality_raw == "audio"

    url = _get_url(url_key)
    if not url:
        await callback.message.answer(
            "✖️ <b>Ссылка устарела.</b> Отправь видео заново.",
            parse_mode="HTML")
        return

    premium = db.is_premium(user_id)
    if not premium and db.get_daily_count(user_id) >= FREE_DAILY_LIMIT:
        await callback.message.answer(
            "🔒 <b>Лимит исчерпан</b>\n\nОформи Premium:",
            parse_mode="HTML", reply_markup=premium_keyboard())
        return

    if not premium and not audio_only:
        quality = str(min(int(quality_raw), int(FREE_MAX_QUALITY)))
    elif audio_only:
        quality = "audio"
    else:
        quality = quality_raw

    label = "MP3 аудио" if audio_only else f"{quality}p видео"

    if premium:
        status_msg = await callback.message.answer(
            f'<tg-emoji emoji-id="5345906554510012647">🔄</tg-emoji> <b>Скачиваю {label}…</b>\n'
            f'<blockquote>Приоритетная загрузка ⭐</blockquote>',
            parse_mode="HTML", message_effect_id=FX_FIRE)
    else:
        status_msg = await callback.message.answer(
            f"🔄 <b>Скачиваю {label}…</b>\n"
            f"<blockquote>Это может занять немного времени ⏳</blockquote>",
            parse_mode="HTML", message_effect_id=FX_FIRE)

    _active_downloads[user_id] = True
    file_path = None
    try:
        result = await download_video(
            url=url,
            quality=quality if not audio_only else "720",
            audio_only=audio_only,
            user_id=user_id,
        )
        file_path = result.file_path

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            await _safe_edit(status_msg,
                f"⚠️ <b>Файл слишком большой</b>\n\n"
                f"<blockquote>Размер: <code>{size_mb:.1f} МБ</code>\n"
                f"Лимит Telegram: <code>{MAX_FILE_SIZE_MB} МБ</code></blockquote>\n\n"
                f"Попробуй выбрать качество ниже.",
                parse_mode="HTML")
            return

        await _safe_edit(status_msg, "📤 <b>Отправляю файл…</b>", parse_mode="HTML")
        input_file = FSInputFile(file_path, filename=os.path.basename(file_path))

        if audio_only:
            if premium:
                cap = (f'<tg-emoji emoji-id="5870528606328852614">📁</tg-emoji> <b>{result.title}</b>\n\n'
                       f'<tg-emoji emoji-id="6028435952299413210">ℹ</tg-emoji> Формат: <code>MP3 · 192kbps</code>')
            else:
                cap = f"🎵 <b>{result.title}</b>\n\nФормат: <code>MP3 · 192kbps</code>"
            await callback.message.answer_audio(
                audio=input_file, title=result.title,
                caption=cap, parse_mode="HTML",
                message_effect_id=FX_LIKE)
        else:
            if premium:
                cap = (f'<tg-emoji emoji-id="6035128606563241721">🖼</tg-emoji> <b>{result.title}</b>\n\n'
                       f'<tg-emoji emoji-id="6028435952299413210">ℹ</tg-emoji> Качество: <code>{quality}p</code>')
            else:
                cap = f"🎬 <b>{result.title}</b>\n\nКачество: <code>{quality}p</code>"
            await callback.message.answer_video(
                video=input_file, caption=cap,
                parse_mode="HTML", supports_streaming=True,
                message_effect_id=FX_PARTY)

        db.increment_daily_count(user_id)
        remaining = "∞" if premium else str(max(0, FREE_DAILY_LIMIT - db.get_daily_count(user_id)))

        if premium:
            done_text = (
                f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> <b>Готово!</b>\n\n'
                f'<tg-emoji emoji-id="6039802767931871481">⬇</tg-emoji> Загрузок сегодня: <b>{db.get_daily_count(user_id)}</b>'
            )
        else:
            done_text = (
                f"✔️ <b>Готово!</b>\n\n"
                f"📥 Загрузок осталось сегодня: <b>{remaining}</b>"
            )
        await _safe_edit(status_msg, done_text, parse_mode="HTML")

    except asyncio.TimeoutError:
        await _safe_edit(status_msg,
            "✖️ <b>Таймаут</b>\n\nПревышено время ожидания. Попробуй позже.",
            parse_mode="HTML")
    except Exception as e:
        logger.error(f"Download error for user {user_id}: {e}")
        await _safe_edit(status_msg,
            "✖️ <b>Ошибка скачивания</b>\n\n"
            "<blockquote>▪️ Видео недоступно или приватное\n"
            "▪️ Временные проблемы с платформой</blockquote>\n\nПопробуй позже.",
            parse_mode="HTML")
    finally:
        _active_downloads.pop(user_id, None)
        if file_path:
            cleanup(file_path)


@router.callback_query(F.data == "premium_prompt")
async def handle_premium_prompt(callback: CallbackQuery):
    await callback.answer("⭐ Это Premium-функция", show_alert=False)
    await callback.message.answer(
        "🔒 <b>Только для Premium</b>\n\n"
        "Качество <code>1080p</code> доступно только Premium-пользователям.\n\n"
        "<blockquote>⭐ Оформи подписку ниже 👇</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_HEART,
        reply_markup=premium_keyboard(),
    )


@router.callback_query(F.data == "donate")
async def handle_donate(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "💝 <b>Поддержать проект</b>\n\n"
        "Спасибо за желание помочь развитию бота!\n\n"
        "<blockquote>👉 https://your-donate-link.com</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_HEART,
    )

