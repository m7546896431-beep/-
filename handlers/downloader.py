import asyncio
import logging
import os
import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile

import database as db
from config import FREE_DAILY_LIMIT, FREE_MAX_QUALITY, MAX_FILE_SIZE_MB
from keyboards import quality_keyboard, premium_keyboard, main_menu_keyboard
from services.downloader import detect_platform, fetch_info, download_video, cleanup

router = Router()
logger = logging.getLogger(__name__)

FX_PARTY = "5046509860389126442"
FX_LIKE  = "5107584321108051014"
FX_FIRE  = "5104841245755180586"
FX_HEART = "5159385139981059251"
FX_POOP  = "5046589136895476101"

_active_downloads: dict[int, bool] = {}

# Кэш URL: короткий ключ → полный URL
# Telegram ограничивает callback_data до 64 байт,
# поэтому URL передавать напрямую нельзя
_url_cache: dict[str, str] = {}


def _store_url(url: str) -> str:
    """Сохраняет URL в кэш и возвращает короткий ключ (8 символов)."""
    key = uuid.uuid4().hex[:8]
    _url_cache[key] = url
    return key


def _get_url(key: str) -> str | None:
    return _url_cache.get(key)


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


def _is_url(text: str) -> bool:
    return text.startswith(("http://", "https://")) and "." in text


async def _animate_status(msg: Message, base_text: str, stop_event: asyncio.Event):
    """Анимирует сообщение иконками ⏳/⌛ пока идёт ожидание."""
    frames = ["⏳", "⌛"]
    i = 0
    await asyncio.sleep(1.5)  # небольшая задержка перед стартом анимации
    while not stop_event.is_set():
        try:
            icon = frames[i % len(frames)]
            await msg.edit_text(
                f"╭─────────────────────\n"
                f"│ {icon} <b>{base_text}</b>\n"
                f"╰─────────────────────",
                parse_mode="HTML",
            )
        except Exception:
            pass
        i += 1
        await asyncio.sleep(1.5)


async def _delete_after(msg: Message, delay: float = 5.0):
    """Удаляет сообщение через delay секунд."""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


@router.message(F.text.func(_is_url))
async def handle_url(message: Message):
    user_id = message.from_user.id
    url = message.text.strip()

    platform = detect_platform(url)
    if not platform:
        err = await message.answer(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃   ✖️  <b>Ссылка не найдена</b>  ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"Эта платформа не поддерживается.\n\n"
            f"<blockquote>✔️ Поддерживаются:\n"
            f"  🔴 YouTube\n"
            f"  🎵 TikTok\n"
            f"  📸 Instagram</blockquote>",
            parse_mode="HTML",
            message_effect_id=FX_POOP,
        )
        asyncio.create_task(_delete_after(err, 8))
        return

    premium = db.is_premium(user_id)
    if not premium and db.get_daily_count(user_id) >= FREE_DAILY_LIMIT:
        await message.answer(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃    ⛔  <b>Лимит исчерпан</b>    ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"Ты использовал все <b>{FREE_DAILY_LIMIT} загрузок</b> на сегодня.\n\n"
            f"<blockquote>⭐ Оформи Premium и качай\n"
            f"без ограничений!</blockquote>",
            parse_mode="HTML",
            reply_markup=premium_keyboard(),
        )
        return

    status_msg = await message.answer(
        f"╭─────────────────────\n"
        f"│ ⏳ <b>Получаю информацию…</b>\n"
        f"╰─────────────────────",
        parse_mode="HTML",
    )

    stop_event = asyncio.Event()
    anim_task = asyncio.create_task(
        _animate_status(status_msg, "Получаю информацию…", stop_event)
    )

    try:
        info = await fetch_info(url)
    except asyncio.TimeoutError:
        stop_event.set()
        anim_task.cancel()
        await asyncio.sleep(0.1)  # дать анимации завершиться
        await status_msg.edit_text(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃     ✖️  <b>Таймаут</b>       ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"Превышено время ожидания.\n"
            f"<blockquote>Попробуй ещё раз позже.</blockquote>",
            parse_mode="HTML",
        )
        asyncio.create_task(_delete_after(status_msg, 6))
        return
    except Exception as e:
        stop_event.set()
        anim_task.cancel()
        await asyncio.sleep(0.1)
        logger.error(f"fetch_info error: {e}")
        await status_msg.edit_text(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃   ✖️  <b>Ошибка загрузки</b>   ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"Не удалось получить информацию.\n\n"
            f"<blockquote>▪️ Проверь правильность ссылки\n"
            f"▪️ Видео может быть приватным\n"
            f"▪️ Попробуй позже</blockquote>",
            parse_mode="HTML",
        )
        asyncio.create_task(_delete_after(status_msg, 8))
        return

    # Останавливаем анимацию и ждём её завершения
    stop_event.set()
    anim_task.cancel()
    await asyncio.sleep(0.1)

    # Сохраняем URL в кэш и получаем короткий ключ
    url_key = _store_url(url)

    icons = {"YouTube": "🔴", "TikTok": "🎵", "Instagram": "📸"}
    icon  = icons.get(info.platform, "🎬")

    caption = (
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃   {icon}  <b>Видео найдено!</b>    ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🎬 <b>{info.title}</b>\n\n"
        f"├ 📌 Платформа: <b>{info.platform}</b>\n"
        f"├ ⏱ Длительность: <code>{_fmt_duration(info.duration)}</code>\n\n"
        f"👇 <b>Выбери качество:</b>"
    )

    try:
        if info.thumbnail:
            await status_msg.delete()
            await message.answer_photo(
                photo=info.thumbnail,
                caption=caption,
                parse_mode="HTML",
                reply_markup=quality_keyboard(url_key, premium),
            )
        else:
            await status_msg.edit_text(
                caption,
                parse_mode="HTML",
                reply_markup=quality_keyboard(url_key, premium),
            )
    except Exception:
        try:
            await status_msg.edit_text(
                caption,
                parse_mode="HTML",
                reply_markup=quality_keyboard(url_key, premium),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("dl|"))
async def handle_download_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    if _active_downloads.get(user_id):
        warn = await callback.message.answer(
            f"╭─────────────────────\n"
            f"│ ⏳ <b>Уже скачивается…</b>\n"
            f"│ Подожди немного!\n"
            f"╰─────────────────────",
            parse_mode="HTML",
        )
        asyncio.create_task(_delete_after(warn, 4))
        return

    parts = callback.data.split("|", 2)
    if len(parts) != 3:
        return

    _, quality_raw, url_key = parts

    # Получаем полный URL из кэша
    url = _get_url(url_key)
    if not url:
        await callback.message.answer(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃   ✖️  <b>Ссылка устарела</b>   ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"<blockquote>Пришли ссылку заново.</blockquote>",
            parse_mode="HTML",
        )
        return

    audio_only = quality_raw == "audio"

    premium = db.is_premium(user_id)
    if not premium and db.get_daily_count(user_id) >= FREE_DAILY_LIMIT:
        await callback.message.answer(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃    ⛔  <b>Лимит исчерпан</b>    ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"<blockquote>⭐ Оформи Premium!</blockquote>",
            parse_mode="HTML",
            reply_markup=premium_keyboard(),
        )
        return

    if not premium and not audio_only:
        quality = str(min(int(quality_raw), int(FREE_MAX_QUALITY)))
    elif audio_only:
        quality = "audio"
    else:
        quality = quality_raw

    label = "🎵 MP3" if audio_only else f"📺 {quality}p"

    status_msg = await callback.message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃   🔥  <b>Скачиваю {label}</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"<blockquote>⏳ Пожалуйста, подожди.\n"
        f"Это займёт немного времени…</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_FIRE,
    )

    stop_event = asyncio.Event()
    anim_task = asyncio.create_task(
        _animate_status(status_msg, f"Скачиваю {label}…", stop_event)
    )

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

        stop_event.set()
        anim_task.cancel()
        await asyncio.sleep(0.1)

        if size_mb > MAX_FILE_SIZE_MB:
            await status_msg.edit_text(
                f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
                f"┃  ⚠️  <b>Файл слишком большой</b> ┃\n"
                f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                f"<blockquote>📦 Размер: <code>{size_mb:.1f} МБ</code>\n"
                f"🚫 Лимит Telegram: <code>{MAX_FILE_SIZE_MB} МБ</code></blockquote>\n\n"
                f"🔙 Попробуй выбрать качество ниже.",
                parse_mode="HTML",
            )
            asyncio.create_task(_delete_after(status_msg, 8))
            return

        await status_msg.edit_text(
            f"╭─────────────────────\n"
            f"│ 📤 <b>Отправляю файл…</b>\n"
            f"╰─────────────────────",
            parse_mode="HTML",
        )

        input_file = FSInputFile(file_path, filename=os.path.basename(file_path))

        if audio_only:
            await callback.message.answer_audio(
                audio=input_file,
                title=result.title,
                caption=(
                    f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
                    f"┃   🎵  <b>Аудио готово!</b>    ┃\n"
                    f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                    f"🎵 <b>{result.title}</b>\n"
                    f"<code>MP3 • 192 kbps</code>"
                ),
                parse_mode="HTML",
                message_effect_id=FX_LIKE,
            )
        else:
            await callback.message.answer_video(
                video=input_file,
                caption=(
                    f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
                    f"┃   🎬  <b>Видео готово!</b>    ┃\n"
                    f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                    f"🎬 <b>{result.title}</b>\n"
                    f"<code>{quality}p • MP4</code>"
                ),
                parse_mode="HTML",
                supports_streaming=True,
                message_effect_id=FX_PARTY,
            )

        db.increment_daily_count(user_id)
        remaining = "∞" if premium else str(
            max(0, FREE_DAILY_LIMIT - db.get_daily_count(user_id))
        )

        await status_msg.edit_text(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃    ✔️  <b>Готово!</b>          ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"├ 📥 Загрузок осталось: <b>{remaining}</b>\n"
            f"╰ 💬 Хочешь ещё? Просто пришли ссылку!",
            parse_mode="HTML",
        )
        asyncio.create_task(_delete_after(status_msg, 6))

    except asyncio.TimeoutError:
        stop_event.set()
        anim_task.cancel()
        await asyncio.sleep(0.1)
        await status_msg.edit_text(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃     ✖️  <b>Таймаут</b>       ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"<blockquote>Превышено время ожидания.\n"
            f"Попробуй ещё раз позже.</blockquote>",
            parse_mode="HTML",
            message_effect_id=FX_POOP,
        )
        asyncio.create_task(_delete_after(status_msg, 8))
    except Exception as e:
        stop_event.set()
        anim_task.cancel()
        await asyncio.sleep(0.1)
        logger.error(f"Download error for user {user_id}: {e}")
        await status_msg.edit_text(
            f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"┃   ✖️  <b>Ошибка скачивания</b>  ┃\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"<blockquote>▪️ Видео недоступно или приватное\n"
            f"▪️ Временные проблемы с платформой\n"
            f"▪️ Попробуй другое качество</blockquote>\n\n"
            f"🔙 Попробуй ещё раз позже.",
            parse_mode="HTML",
            message_effect_id=FX_POOP,
        )
        asyncio.create_task(_delete_after(status_msg, 8))
    finally:
        _active_downloads.pop(user_id, None)
        if file_path:
            cleanup(file_path)


@router.callback_query(F.data == "premium_prompt")
async def handle_premium_prompt(callback: CallbackQuery):
    await callback.answer("⭐ Это Premium-функция", show_alert=False)
    await callback.message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃   🔒  <b>Только Premium</b>   ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"Качество <code>1080p</code> доступно\n"
        f"только Premium-пользователям.\n\n"
        f"<blockquote>⭐ Всего $3/мес — без лимитов!</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_HEART,
        reply_markup=premium_keyboard(),
    )


@router.callback_query(F.data == "donate")
async def handle_donate(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        f"╭━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"┃     💝  <b>Донат</b>          ┃\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"Спасибо за желание поддержать!\n\n"
        f"<blockquote>👉 https://your-donate-link.com</blockquote>",
        parse_mode="HTML",
        message_effect_id=FX_HEART,
    )


@router.callback_query(F.data == "cancel")
async def handle_cancel(callback: CallbackQuery):
    await callback.answer("Отменено")
    await callback.message.delete()


@router.callback_query(F.data == "back")
async def handle_back(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

