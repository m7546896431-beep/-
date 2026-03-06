from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_keyboard(is_premium: bool) -> ReplyKeyboardMarkup:
    """Нижнее меню бота"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔗 Отправить ссылку"),
        KeyboardButton(text="👤 Профиль"),
    )
    if is_premium:
        builder.row(
            KeyboardButton(text="⭐ Premium активен"),
            KeyboardButton(text="ℹ️ Помощь"),
        )
    else:
        builder.row(
            KeyboardButton(text="⭐ Купить Premium"),
            KeyboardButton(text="ℹ️ Помощь"),
        )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def quality_keyboard(url_key: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📺 360p",  callback_data=f"dl|360|{url_key}"),
        InlineKeyboardButton(text="📺 720p",  callback_data=f"dl|720|{url_key}"),
    )
    if is_premium:
        builder.row(
            InlineKeyboardButton(text="🎬 1080p ⭐", callback_data=f"dl|1080|{url_key}"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔒 1080p — только Premium", callback_data="premium_prompt"),
        )
    builder.row(
        InlineKeyboardButton(text="🎵 Скачать MP3", callback_data=f"dl|audio|{url_key}"),
    )
    return builder.as_markup()


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
    )
    return builder.as_markup()

