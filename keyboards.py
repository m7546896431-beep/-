from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def quality_keyboard(url_key: str, is_premium: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="360p", callback_data=f"dl|360|{url_key}",
                             icon_custom_emoji_id="6039802767931871481"),
        InlineKeyboardButton(text="720p", callback_data=f"dl|720|{url_key}",
                             icon_custom_emoji_id="6039802767931871481"),
    )
    if is_premium:
        builder.row(
            InlineKeyboardButton(text="1080p Premium", callback_data=f"dl|1080|{url_key}",
                                 icon_custom_emoji_id="6032644646587338669"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="1080p — только Premium", callback_data="premium_prompt",
                                 icon_custom_emoji_id="6037249452824072506"),
        )
    builder.row(
        InlineKeyboardButton(text="MP3 аудио", callback_data=f"dl|audio|{url_key}",
                             icon_custom_emoji_id="6039802767931871481"),
    )
    return builder.as_markup()


def premium_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Premium — $3/мес",
            url="https://t.me/your_payment_bot",
            icon_custom_emoji_id="6032644646587338669",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Поддержать донатом",
            callback_data="donate",
            icon_custom_emoji_id="5904462880941545555",
        ),
    )
    return builder.as_markup()

