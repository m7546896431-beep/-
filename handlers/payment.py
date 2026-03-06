"""
Оплата Premium через Telegram Stars.
1 ⭐ = 30 дней Premium
"""
import logging
import datetime
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    LabeledPrice, PreCheckoutQuery,
    SuccessfulPayment,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

import database as db

router = Router()
logger = logging.getLogger(__name__)

PREMIUM_STARS  = 1
PREMIUM_DAYS   = 30
ADMIN_ID       = 5259105676

FX_PARTY = "5046509860389126442"
FX_HEART = "5159385139981059251"
FX_FIRE  = "5104841245755180586"


def buy_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"⭐ Купить Premium — {PREMIUM_STARS} звезда",
            callback_data="buy_stars",
        )
    )
    return builder.as_markup()


@router.callback_query(F.data == "buy_stars")
async def send_invoice(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer_invoice(
        title="⭐ Premium подписка",
        description=(
            f"✔️ {PREMIUM_DAYS} дней Premium\n"
            f"✔️ Без лимитов загрузок\n"
            f"✔️ Качество до 1080p\n"
            f"✔️ Приоритетная очередь"
        ),
        payload="premium_30d",
        currency="XTR",
        prices=[LabeledPrice(label="Premium 30 дней", amount=PREMIUM_STARS)],
        protect_content=False,
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment: SuccessfulPayment = message.successful_payment
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    if payment.invoice_payload == "premium_30d":
        until = str(datetime.date.today() + datetime.timedelta(days=PREMIUM_DAYS))
        db.get_or_create_user(user_id)
        db.set_premium(user_id, until)

        logger.info(f"Premium bought: user={user_id} until={until} stars={payment.total_amount}")

        # Уведомление пользователю
        await message.answer(
            f'<tg-emoji emoji-id="6041731551845159060">🎉</tg-emoji> <b>Premium активирован!</b>\n\n'
            f'<blockquote>'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Без лимитов загрузок\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Качество до <code>1080p</code>\n'
            f'<tg-emoji emoji-id="5870633910337015697">✅</tg-emoji> Приоритет в очереди\n'
            f'<tg-emoji emoji-id="5890937706803894250">📅</tg-emoji> Действует до: <code>{until}</code>'
            f'</blockquote>\n\n'
            f'Спасибо за поддержку! 🔥',
            parse_mode="HTML",
            message_effect_id=FX_PARTY,
        )

        # Уведомление админу
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f'💰 <b>Новая покупка Premium!</b>\n\n'
                f'👤 Пользователь: <a href="tg://user?id={user_id}">{username}</a>\n'
                f'🆔 ID: <code>{user_id}</code>\n'
                f'⭐ Звёзд: <b>{payment.total_amount}</b>\n'
                f'📅 До: <code>{until}</code>',
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin: {e}")

