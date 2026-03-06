from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ─── Главное меню (Reply-кнопки внизу) ───────────────────────────────────────
def main_menu_keyboard(is_premium: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⬇️ Скачать видео"),
        KeyboardButton(text="👤 Мой профиль"),
    )
    builder.row(
        KeyboardButton(text="⭐ Premium"),
        KeyboardButton(text="❓ Помощь"),
    )
    return builder.as_markup(resize_keyboard=True)

# ─── Выбор качества (Inline) ─────────────────────────────────────────────────
# url_key — короткий 8-символьный ключ из _url_cache (не полный URL!)
def quality_keyboard(url_key: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 360p",  callback_data=f"dl|360|{url_key}"),
        InlineKeyboardButton(text="💻 720p",  callback_data=f"dl|720|{url_key}"),
    )
    if is_premium:
        builder.row(
            InlineKeyboardButton(text="🖥 1080p ⭐", callback_data=f"dl|1080|{url_key}"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔒 1080p — только Premium", callback_data="premium_prompt"),
        )
    builder.row(
        InlineKeyboardButton(text="🎵 Скачать MP3", callback_data=f"dl|audio|{url_key}"),
    )
    builder.row(
        InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel"),
    )
    return builder.as_markup()

# ─── Premium ──────────────────────────────────────────────────────────────────
def premium_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⭐ Купить Premium — $3/мес",
            url="https://t.me/your_payment_bot",
        )
    )
    builder.row(
        InlineKeyboardButton(text="💝 Поддержать донатом", callback_data="donate"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
    )
    return builder.as_markup()

def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back"),
    )
    return builder.as_markup()

# Алиас для совместимости
main_keyboard = main_menu_keyboard

