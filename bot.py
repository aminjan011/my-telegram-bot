import asyncio
import logging
from datetime import datetime, timedelta
import sqlite3

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8646029465:AAHDm5rvMgp53-Hnut5DTgy5fgFsTlyga5U"
ADMIN_IDS = [1112793157]  # Введите ваш Telegram ID
CHANNEL_ID = -1004324882879  # ID канала (начинается с -100)
CHANNEL_INVITE_LINK = "https://t.me/+_AxorsmPVYE2M2Ji"
REQUIRED_REFERRALS = 10
SUB_DAYS = 10

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM СОСТОЯНИЯ ДЛЯ АДМИНКИ ---
class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_user_id = State()

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER,
    ref_count INTEGER DEFAULT 0,
    expire_date TEXT,
    created_at TEXT
)
""")
conn.commit()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, referrer_id=None):
    if not get_user(user_id):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO users (user_id, referrer_id, created_at) VALUES (?, ?, ?)", (user_id, referrer_id, now_str))
        conn.commit()

        if referrer_id and referrer_id != user_id and get_user(referrer_id):
            cursor.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# --- ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    add_user(user_id, referrer_id)
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    userData = get_user(user_id)
    ref_count = userData[2]
    
    text = (
        f"👋 **Добро пожаловать!**\n\n"
        f"🎁 Чтобы получить бесплатный доступ к закрытому каналу на **{SUB_DAYS} дней**, "
        f"вам необходимо пригласить минимум **{REQUIRED_REFERRALS} друзей**.\n\n"
        f"📊 Вы пригласили: **{ref_count}/{REQUIRED_REFERRALS}**\n\n"
        f"🔗 **Ваша пригласительная ссылка:**\n`{ref_link}`\n\n"
        f"⚠️ **Внимание:** После приглашения {REQUIRED_REFERRALS} человек вам откроется доступ к каналу. "
        f"Срок пребывания в канале составляет **{SUB_DAYS} дней**. По истечении этого срока система автоматически удалит вас из канала."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить и войти в канал 🔓", callback_data="check_access")]
    ])
    
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "check_access")
async def check_access(call: types.CallbackQuery):
    user_id = call.from_user.id
    userData = get_user(user_id)
    ref_count = userData[2]
    expire_date_str = userData[3]

    if expire_date_str:
        await call.message.answer(f"Вам уже предоставлен доступ! Ссылка на канал: {CHANNEL_INVITE_LINK}")
        await call.answer()
        return

    if ref_count >= REQUIRED_REFERRALS:
        expire_date = datetime.now() + timedelta(days=SUB_DAYS)
        cursor.execute("UPDATE users SET expire_date = ? WHERE user_id = ?", (expire_date.strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()

        try:
            await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        except Exception:
            pass

        msg = (
            f"🎉 **Поздравляем!** Вы успешно пригласили {REQUIRED_REFERRALS} друзей.\n\n"
            f"Вам предоставлен доступ к каналу на **{SUB_DAYS} дней**.\n"
            f"⏳ Доступ действителен до: **{expire_date.strftime('%Y-%m-%d %H:%M')}**.\n\n"
            f"👉 Ссылка для входа: {CHANNEL_INVITE_LINK}"
        )
        await call.message.answer(msg, parse_mode="Markdown")
    else:
        left = REQUIRED_REFERRALS - ref_count
        await call.answer(f"У вас недостаточно приглашений! Нужно пригласить еще {left} человек.", show_alert=True)

# --- АДМИН ПАНЕЛЬ ---
def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Выдать доступ вручную", callback_data="admin_give_access")]
    ])

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🛠 **Панель администратора**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE expire_date IS NOT NULL")
    active_subs = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(ref_count) FROM users")
    total_refs = cursor.fetchone()[0] or 0

    stats_msg = (
        f"📊 **Статистика бота:**\n\n"
        f"👤 Всего пользователей: **{total_users}**\n"
        f"⚡ Активных подписок (в канале): **{active_subs}**\n"
        f"🔗 Всего приглашено рефералов: **{total_refs}**"
    )
    await call.message.answer(stats_msg, parse_mode="Markdown", reply_markup=get_admin_keyboard())
    await call.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.waiting_for_broadcast)
    await call.message.answer("✏️ Отправьте сообщение (текст, фото или документ), которое нужно разослать всем пользователям:")
    await call.answer()

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    users = get_all_users()
    success = 0
    failed = 0

    await message.answer(f"🚀 Рассылка началась на {len(users)} пользователей...")

    for uid in users:
        try:
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.answer(f"✅ **Рассылка завершена!**\n\nУспешно отправлено: **{success}**\nОшибок: **{failed}**", parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "admin_give_access")
async def admin_give_access_callback(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(AdminStates.waiting_for_user_id)
    await call.message.answer("👤 Введите Telegram **ID пользователя**, которому нужно выдать доступ на 10 дней:")
    await call.answer()

@dp.message(AdminStates.waiting_for_user_id)
async def process_give_access(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Ошибка: Telegram ID должен состоять только из цифр. Попробуйте снова.")
        return

    target_id = int(message.text)
    add_user(target_id)

    expire_date = datetime.now() + timedelta(days=SUB_DAYS)
    cursor.execute("UPDATE users SET expire_date = ? WHERE user_id = ?", (expire_date.strftime("%Y-%m-%d %H:%M:%S"), target_id))
    conn.commit()

    try:
        await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=target_id)
    except Exception:
        pass

    try:
        await bot.send_message(
            target_id,
            f"🎉 **Администратор выдал вам доступ!**\n\n"
            f"Вам доступен вход в канал на **{SUB_DAYS} дней**.\n"
            f"👉 Ссылка для входа: {CHANNEL_INVITE_LINK}",
            parse_mode="Markdown"
        )
        await message.answer(f"✅ Пользователю `{target_id}` успешно выдан доступ!", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"⚠️ Доступ выдан в базе, но не удалось отправить сообщение пользователю: {e}")

    await state.clear()

# --- АВТОМАЧЕСКОЕ ИСКЛЮЧЕНИЕ ПО ИСТЕЧЕНИИ СРОКА ---
async def auto_kick_expired_users():
    while True:
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT user_id FROM users WHERE expire_date IS NOT NULL AND expire_date <= ?", (now_str,))
            expired_users = cursor.fetchall()

            for (u_id,) in expired_users:
                try:
                    await bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=u_id)
                    await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=u_id)
                    
                    await bot.send_message(
                        u_id, 
                        f"⏰ **Срок подписки истек!**\n\n"
                        f"Ваш срок пребывания в канале ({SUB_DAYS} дней) окончен, поэтому вы были исключены. "
                        f"Чтобы войти снова, вам необходимо пригласить еще {REQUIRED_REFERRALS} друзей.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.error(f"Ошибка при исключении пользователя: {e}")

                cursor.execute("UPDATE users SET expire_date = NULL, ref_count = 0 WHERE user_id = ?", (u_id,))
                conn.commit()

        except Exception as e:
            logging.error(f"Ошибка при проверке пользователей: {e}")

        await asyncio.sleep(3600)

async def main():
    asyncio.create_task(auto_kick_expired_users())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
