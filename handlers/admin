"""
Скрытая админ панель. Вход: /admin 1507
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import database as db

router = Router()
logger = logging.getLogger(__name__)

ADMIN_PASSWORD = "1507"

# Храним авторизованных админов в памяти
_admins: set[int] = set()


class AdminStates(StatesGroup):
    waiting_password     = State()
    waiting_premium_id   = State()
    waiting_premium_days = State()
    waiting_revoke_id    = State()
    waiting_broadcast    = State()


# ─── Клавиатуры ───────────────────────────────────────────────────────────────
def admin_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭐ Выдать Premium",    callback_data="adm_give_premium"),
        InlineKeyboardButton(text="✖️ Забрать Premium",  callback_data="adm_revoke_premium"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика",        callback_data="adm_stats"),
        InlineKeyboardButton(text="📣 Рассылка",          callback_data="adm_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Выйти",             callback_data="adm_logout"),
    )
    return builder.as_markup()


def admin_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="adm_back"))
    return builder.as_markup()


# ─── Вход ─────────────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    # /admin 1507 — сразу с паролем
    if len(args) == 2 and args[1] == ADMIN_PASSWORD:
        _admins.add(message.from_user.id)
        await message.answer(
            "🔐 <b>Админ панель</b>\n\n"
            "Добро пожаловать! Выбери действие:",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard(),
        )
        return
    # /admin без пароля — просим ввести
    await message.answer(
        "🔒 Введи пароль для входа в админ панель:",
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.waiting_password)


@router.message(AdminStates.waiting_password)
async def process_password(message: Message, state: FSMContext):
    await state.clear()
    if message.text.strip() == ADMIN_PASSWORD:
        _admins.add(message.from_user.id)
        await message.answer(
            "🔐 <b>Админ панель</b>\n\n"
            "Добро пожаловать! Выбери действие:",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard(),
        )
    else:
        await message.answer("✖️ Неверный пароль.", parse_mode="HTML")


def _check_admin(user_id: int) -> bool:
    return user_id in _admins


# ─── Главное меню ──────────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_back")
async def adm_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not _check_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "🔐 <b>Админ панель</b>\n\nВыбери действие:",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "adm_logout")
async def adm_logout(callback: CallbackQuery):
    _admins.discard(callback.from_user.id)
    await callback.message.edit_text("🔒 Вышел из админ панели.")


# ─── Статистика ───────────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_stats")
async def adm_stats(callback: CallbackQuery):
    if not _check_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    import sqlite3
    from pathlib import Path
    try:
        conn = sqlite3.connect(Path("data/users.db"))
        conn.row_factory = sqlite3.Row
        total      = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        premium    = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_premium=1").fetchone()["c"]
        active_today = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE dl_date=date('now') AND dl_count>0"
        ).fetchone()["c"]
        conn.close()
    except Exception as e:
        await callback.answer(f"Ошибка БД: {e}", show_alert=True)
        return

    await callback.message.edit_text(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"⭐ Premium пользователей: <b>{premium}</b>\n"
        f"📥 Активных сегодня: <b>{active_today}</b>",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )


# ─── Выдать Premium ───────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_give_premium")
async def adm_give_premium(callback: CallbackQuery, state: FSMContext):
    if not _check_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "⭐ <b>Выдать Premium</b>\n\n"
        "Введи <b>Telegram ID</b> пользователя:\n"
        "<blockquote>Узнать ID можно через @userinfobot</blockquote>",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await state.set_state(AdminStates.waiting_premium_id)


@router.message(AdminStates.waiting_premium_id)
async def process_premium_id(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id):
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        await state.update_data(target_id=uid)
        await message.answer(
            f"👤 ID: <code>{uid}</code>\n\n"
            f"На сколько дней выдать Premium?\n"
            f"<blockquote>Введи число, например: <code>30</code></blockquote>",
            parse_mode="HTML",
            reply_markup=admin_back_keyboard(),
        )
        await state.set_state(AdminStates.waiting_premium_days)
    except ValueError:
        await message.answer("✖️ Неверный ID. Введи только цифры.", parse_mode="HTML")


@router.message(AdminStates.waiting_premium_days)
async def process_premium_days(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id):
        await state.clear()
        return
    try:
        days = int(message.text.strip())
        data = await state.get_data()
        uid  = data["target_id"]
        await state.clear()

        import datetime
        until = str(datetime.date.today() + datetime.timedelta(days=days))
        db.get_or_create_user(uid)
        db.set_premium(uid, until)

        await message.answer(
            f"✔️ <b>Premium выдан!</b>\n\n"
            f"👤 ID: <code>{uid}</code>\n"
            f"📅 До: <code>{until}</code> ({days} дней)",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard(),
        )
        logger.info(f"Admin gave premium to {uid} until {until}")
    except ValueError:
        await message.answer("✖️ Неверное число дней.", parse_mode="HTML")


# ─── Забрать Premium ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_revoke_premium")
async def adm_revoke_premium(callback: CallbackQuery, state: FSMContext):
    if not _check_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "✖️ <b>Забрать Premium</b>\n\n"
        "Введи <b>Telegram ID</b> пользователя:",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await state.set_state(AdminStates.waiting_revoke_id)


@router.message(AdminStates.waiting_revoke_id)
async def process_revoke_id(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id):
        await state.clear()
        return
    try:
        uid = int(message.text.strip())
        await state.clear()

        import sqlite3
        from pathlib import Path
        conn = sqlite3.connect(Path("data/users.db"))
        conn.execute("UPDATE users SET is_premium=0, premium_until='' WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()

        await message.answer(
            f"✔️ <b>Premium забран</b>\n\n"
            f"👤 ID: <code>{uid}</code>",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard(),
        )
    except ValueError:
        await message.answer("✖️ Неверный ID.", parse_mode="HTML")


# ─── Рассылка ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast(callback: CallbackQuery, state: FSMContext):
    if not _check_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "📣 <b>Рассылка</b>\n\n"
        "Отправь сообщение которое хочешь разослать всем пользователям:\n"
        "<blockquote>Поддерживается HTML форматирование</blockquote>",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not _check_admin(message.from_user.id):
        await state.clear()
        return
    await state.clear()

    import sqlite3
    from pathlib import Path
    conn = sqlite3.connect(Path("data/users.db"))
    users = [r[0] for r in conn.execute("SELECT user_id FROM users").fetchall()]
    conn.close()

    bot = message.bot
    ok = 0
    fail = 0
    for uid in users:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=message.chat.id,
                                   message_id=message.message_id)
            ok += 1
        except Exception:
            fail += 1

    await message.answer(
        f"📣 <b>Рассылка завершена!</b>\n\n"
        f"✔️ Доставлено: <b>{ok}</b>\n"
        f"✖️ Не доставлено: <b>{fail}</b>",
        parse_mode="HTML",
        reply_markup=admin_main_keyboard(),
    )

