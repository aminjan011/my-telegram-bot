import os
import logging
import sqlite3
import html
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO)

# ==================== NASTROYKI ====================
BOT_TOKEN = "8646029465:AAEOJrjfnDGpDtJ6Ncx0d24JJenWBVLNI0s"      # Tokeningiz[span_2](start_span)[span_2](end_span)
PRIVATE_CHANNEL_ID = -1004324882879                    # Referal orqali kiriladigan yopiq kanal ID[span_3](start_span)[span_3](end_span)
CHANNELS_SECTION_LINK = "https://t.me/+_AxorsmPVYE2M2Ji"    # "📁 Каналы" bo'limi uchun havola[span_4](start_span)[span_4](end_span)
REQUIRED_REFERRALS = 10                               # Referal soni (10 ball)[span_5](start_span)[span_5](end_span)
ADMIN_USERNAME = "softic00"                    # Admin username (sans @)[span_6](start_span)[span_6](end_span)
ADMIN_ID = 1112793157                                  # Admin Telegram ID raqami[span_7](start_span)[span_7](end_span)

# Render dagi domen havolangiz
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://my-telegram-bot-hh51.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"
# ===================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()[span_8](start_span)[span_8](end_span)
    waiting_for_ch1 = State()[span_9](start_span)[span_9](end_span)
    waiting_for_ch2 = State()[span_10](start_span)[span_10](end_span)

def init_db():
    conn = sqlite3.connect("bot_database.db")[span_11](start_span)[span_11](end_span)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            points INTEGER DEFAULT 0,
            has_access INTEGER DEFAULT 0
        )
    ''')[span_12](start_span)[span_12](end_span)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')[span_13](start_span)[span_13](end_span)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_1', '@kinozhuldyzkz')")[span_14](start_span)[span_14](end_span)
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_2', '')")[span_15](start_span)[span_15](end_span)
    conn.commit()[span_16](start_span)[span_16](end_span)
    conn.close()[span_17](start_span)[span_17](end_span)

init_db()[span_18](start_span)[span_18](end_span)

def get_setting(key: str) -> str:
    conn = sqlite3.connect("bot_database.db")[span_19](start_span)[span_19](end_span)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))[span_20](start_span)[span_20](end_span)
    row = cursor.fetchone()[span_21](start_span)[span_21](end_span)
    conn.close()[span_22](start_span)[span_22](end_span)
    return row[0] if row else "[span_23](start_span)"[span_23](end_span)

def set_setting(key: str, value: str):
    conn = sqlite3.connect("bot_database.db")[span_24](start_span)[span_24](end_span)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))[span_25](start_span)[span_25](end_span)
    conn.commit()[span_26](start_span)[span_26](end_span)
    conn.close()[span_27](start_span)[span_27](end_span)

def get_user(user_id: int):
    conn = sqlite3.connect("bot_database.db")[span_28](start_span)[span_28](end_span)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, referrer_id, points, has_access FROM users WHERE user_id = ?", (user_id,))[span_29](start_span)[span_29](end_span)
    row = cursor.fetchone()[span_30](start_span)[span_30](end_span)
    conn.close()[span_31](start_span)[span_31](end_span)
    return row[span_32](start_span)[span_32](end_span)

def add_user(user_id: int, referrer_id: int = None):
    conn = sqlite3.connect("bot_database.db")[span_33](start_span)[span_33](end_span)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))[span_34](start_span)[span_34](end_span)
    conn.commit()[span_35](start_span)[span_35](end_span)
    conn.close()[span_36](start_span)[span_36](end_span)

def add_point(user_id: int):
    conn = sqlite3.connect("bot_database.db")[span_37](start_span)[span_37](end_span)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (user_id,))[span_38](start_span)[span_38](end_span)
    conn.commit()[span_39](start_span)[span_39](end_span)
    conn.close()[span_40](start_span)[span_40](end_span)

def get_stats():
    conn = sqlite3.connect("bot_database.db")[span_41](start_span)[span_41](end_span)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(points) FROM users")[span_42](start_span)[span_42](end_span)
    stats = cursor.fetchone()[span_43](start_span)[span_43](end_span)
    conn.close()[span_44](start_span)[span_44](end_span)
    total_users = stats[0] if stats[0] else 0[span_45](start_span)[span_45](end_span)
    total_points = stats[1] if stats[1] else 0[span_46](start_span)[span_46](end_span)
    return total_users, total_points[span_47](start_span)[span_47](end_span)

def get_all_users():
    conn = sqlite3.connect("bot_database.db")[span_48](start_span)[span_48](end_span)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")[span_49](start_span)[span_49](end_span)
    rows = cursor.fetchall()[span_50](start_span)[span_50](end_span)
    conn.close()[span_51](start_span)[span_51](end_span)
    return [r[0] for r in rows][span_52](start_span)[span_52](end_span)

async def check_subscription(user_id: int) -> bool:
    ch1 = get_setting('channel_1')[span_53](start_span)[span_53](end_span)
    ch2 = get_setting('channel_2')[span_54](start_span)[span_54](end_span)
    
    channels_to_check = [c for c in [ch1, ch2] if c.strip()][span_55](start_span)[span_55](end_span)
    
    for ch in channels_to_check:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)[span_56](start_span)[span_56](end_span)
            if member.status not in ["creator", "administrator", "member"]:[span_57](start_span)[span_57](end_span)
                return False[span_58](start_span)[span_58](end_span)
        except Exception as e:
            logging.error(f"Ошибка проверки подписки {ch}: {e}")[span_59](start_span)[span_59](end_span)
            return False[span_60](start_span)[span_60](end_span)
    return True[span_61](start_span)[span_61](end_span)

def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📁 Каналы", callback_data="channels")],[span_62](start_span)[span_62](end_span)
            [InlineKeyboardButton(text="⚡ Бесплатный канал", callback_data="free_channel")],[span_63](start_span)[span_63](end_span)
            [InlineKeyboardButton(text="🤖 Помощник", callback_data="help")],[span_64](start_span)[span_64](end_span)
            [InlineKeyboardButton(text="📝 Написать администратору", url=f"https://t.me/{ADMIN_USERNAME}")][span_65](start_span)[span_65](end_span)
        ]
    )[span_66](start_span)[span_66](end_span)

def get_sub_keyboard():
    ch1 = get_setting('channel_1')[span_67](start_span)[span_67](end_span)
    ch2 = get_setting('channel_2')[span_68](start_span)[span_68](end_span)
    
    buttons = [][span_69](start_span)[span_69](end_span)
    if ch1.strip():[span_70](start_span)[span_70](end_span)
        clean1 = ch1.replace("@", "")[span_71](start_span)[span_71](end_span)
        buttons.append([InlineKeyboardButton(text="📢 Канал 1", url=f"https://t.me/{clean1}")])[span_72](start_span)[span_72](end_span)
    if ch2.strip():[span_73](start_span)[span_73](end_span)
        clean2 = ch2.replace("@", "")[span_74](start_span)[span_74](end_span)
        buttons.append([InlineKeyboardButton(text="📢 Канал 2", url=f"https://t.me/{clean2}")])[span_75](start_span)[span_75](end_span)
        
    buttons.append([InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_sub")])[span_76](start_span)[span_76](end_span)
    return InlineKeyboardMarkup(inline_keyboard=buttons)[span_77](start_span)[span_77](end_span)

def get_admin_keyboard():
    ch1 = get_setting('channel_1') or "Не настроен[span_78](start_span)"[span_78](end_span)
    ch2 = get_setting('channel_2') or "Не настроен[span_79](start_span)"[span_79](end_span)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],[span_80](start_span)[span_80](end_span)
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],[span_81](start_span)[span_81](end_span)
            [InlineKeyboardButton(text=f"⚙️ Канал 1: {ch1}", callback_data="admin_set_ch1")],[span_82](start_span)[span_82](end_span)
            [InlineKeyboardButton(text=f"⚙️ Канал 2: {ch2}", callback_data="admin_set_ch2")],[span_83](start_span)[span_83](end_span)
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")][span_84](start_span)[span_84](end_span)
        ]
    )[span_85](start_span)[span_85](end_span)

@dp.message(CommandStart())
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id[span_86](start_span)[span_86](end_span)
    args = command.args[span_87](start_span)[span_87](end_span)
    
    referrer_id = None[span_88](start_span)[span_88](end_span)
    if args and args.isdigit():[span_89](start_span)[span_89](end_span)
        ref_candidate = int(args)[span_90](start_span)[span_90](end_span)
        if ref_candidate != user_id:[span_91](start_span)[span_91](end_span)
            referrer_id = ref_candidate[span_92](start_span)[span_92](end_span)

    user = get_user(user_id)[span_93](start_span)[span_93](end_span)
    if not user:[span_94](start_span)[span_94](end_span)
        add_user(user_id, referrer_id)[span_95](start_span)[span_95](end_span)
    
    is_sub = await check_subscription(user_id)[span_96](start_span)[span_96](end_span)
    if not is_sub:[span_97](start_span)[span_97](end_span)
        sub_text = "⚠️ <b>Для использования бота необходимо подписаться на наши каналы!</b>\n\nПосле подписки нажмите кнопку «Проверить подписку».[span_98](start_span)"[span_98](end_span)
        await message.answer(sub_text, reply_markup=get_sub_keyboard(), parse_mode=ParseMode.HTML)[span_99](start_span)[span_99](end_span)
        return[span_100](start_span)[span_100](end_span)

    first_name = html.escape(message.from_user.first_name)[span_101](start_span)[span_101](end_span)
    welcome_text = f"💥 <b>Добро пожаловать, {first_name}!</b>\n‹━━━━━━━━━━━━━━━━━━›\n\n🔥 Приватный архив 18+\n— эксклюзивный контент\n— доступ только для участников\n\n👇 <b>Выбери раздел</b> 👇[span_102](start_span)"[span_102](end_span)
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)[span_103](start_span)[span_103](end_span)

# ==================== ADMIN PANEL ====================
@dp.message(Command("admin"))
async def admin_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:[span_104](start_span)[span_104](end_span)
        return[span_105](start_span)[span_105](end_span)
    await message.answer("👑 <b>Панель администратора</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)[span_106](start_span)[span_106](end_span)

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:[span_107](start_span)[span_107](end_span)
        return[span_108](start_span)[span_108](end_span)
    total_users, total_points = get_stats()[span_109](start_span)[span_109](end_span)
    text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👤 Всего пользователей: <b>{total_users}</b>\n"
        f"⭐ Всего набрано баллов: <b>{total_points}</b>"
    )[span_110](start_span)[span_110](end_span)
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)[span_111](start_span)[span_111](end_span)

@dp.callback_query(F.data == "admin_set_ch1")
async def admin_set_ch1(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:[span_112](start_span)[span_112](end_span)
        return[span_113](start_span)[span_113](end_span)
    await state.set_state(AdminStates.waiting_for_ch1)[span_114](start_span)[span_114](end_span)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_settings")]])[span_115](start_span)[span_115](end_span)
    await callback.message.edit_text("✏️ Отправьте username первого обязательного канала (например: <code>@mychannel</code>):", reply_markup=kb, parse_mode=ParseMode.HTML)[span_116](start_span)[span_116](end_span)

@dp.message(AdminStates.waiting_for_ch1)
async def process_ch1(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:[span_117](start_span)[span_117](end_span)
        return[span_118](start_span)[span_118](end_span)
    channel_username = message.text.strip()[span_119](start_span)[span_119](end_span)
    if not channel_username.startswith("@"):[span_120](start_span)[span_120](end_span)
        channel_username = "@" + channel_username[span_121](start_span)[span_121](end_span)
    set_setting("channel_1", channel_username)[span_122](start_span)[span_122](end_span)
    await state.clear()[span_123](start_span)[span_123](end_span)
    await message.answer(f"✅ Канал 1 успешно обновлен: <b>{channel_username}</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)[span_124](start_span)[span_124](end_span)

@dp.callback_query(F.data == "admin_set_ch2")
async def admin_set_ch2(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:[span_125](start_span)[span_125](end_span)
        return[span_126](start_span)[span_126](end_span)
    await state.set_state(AdminStates.waiting_for_ch2)[span_127](start_span)[span_127](end_span)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить 2-канал", callback_data="admin_remove_ch2")],[span_128](start_span)[span_128](end_span)
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_settings")][span_129](start_span)[span_129](end_span)
        ]
    )[span_130](start_span)[span_130](end_span)
    await callback.message.edit_text("✏️ Отправьте username второго обязательного канала (например: <code>@mychannel2</code>) или нажмите «Удалить»:", reply_markup=kb, parse_mode=ParseMode.HTML)[span_131](start_span)[span_131](end_span)

@dp.callback_query(F.data == "admin_remove_ch2")
async def admin_remove_ch2(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:[span_132](start_span)[span_132](end_span)
        return[span_133](start_span)[span_133](end_span)
    set_setting("channel_2", "")[span_134](start_span)[span_134](end_span)
    await state.clear()[span_135](start_span)[span_135](end_span)
    await callback.message.edit_text("✅ Второй обязательный канал успешно удален!", reply_markup=get_admin_keyboard())[span_136](start_span)[span_136](end_span)

@dp.message(AdminStates.waiting_for_ch2)
async def process_ch2(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:[span_137](start_span)[span_137](end_span)
        return[span_138](start_span)[span_138](end_span)
    channel_username = message.text.strip()[span_139](start_span)[span_139](end_span)
    if not channel_username.startswith("@"):[span_140](start_span)[span_140](end_span)
        channel_username = "@" + channel_username[span_141](start_span)[span_141](end_span)
    set_setting("channel_2", channel_username)[span_142](start_span)[span_142](end_span)
    await state.clear()[span_143](start_span)[span_143](end_span)
    await message.answer(f"✅ Канал 2 успешно добавлен/обновлен: <b>{channel_username}</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)[span_144](start_span)[span_144](end_span)

@dp.callback_query(F.data == "admin_cancel_settings")
async def admin_cancel_settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()[span_145](start_span)[span_145](end_span)
    await callback.message.edit_text("👑 <b>Панель администратора</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)[span_146](start_span)[span_146](end_span)

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:[span_147](start_span)[span_147](end_span)
        return[span_148](start_span)[span_148](end_span)
    await state.set_state(AdminStates.waiting_for_broadcast)[span_149](start_span)[span_149](end_span)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_settings")]])[span_150](start_span)[span_150](end_span)
    await callback.message.edit_text("📢 Отправьте сообщение, которое будет разослано всем пользователям:", reply_markup=kb)[span_151](start_span)[span_151](end_span)

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:[span_152](start_span)[span_152](end_span)
        return[span_153](start_span)[span_153](end_span)
    await state.clear()[span_154](start_span)[span_154](end_span)
    
    users = get_all_users()[span_155](start_span)[span_155](end_span)
    await message.answer(f"⏳ Начинаем рассылку для {len(users)} пользователей...")[span_156](start_span)[span_156](end_span)
    
    success = 0[span_157](start_span)[span_157](end_span)
    failed = 0[span_158](start_span)[span_158](end_span)
    
    for uid in users:[span_159](start_span)[span_159](end_span)
        try:
            await message.copy_to(chat_id=uid)[span_160](start_span)[span_160](end_span)
            success += 1[span_161](start_span)[span_161](end_span)
            await asyncio.sleep(0.05)[span_162](start_span)[span_162](end_span)
        except Exception:
            failed += 1[span_163](start_span)[span_163](end_span)
            
    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"🎉 Успешно отправлено: <b>{success}</b>\n"
        f"❌ Не доставлено: <b>{failed}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_keyboard()
    )[span_164](start_span)[span_164](end_span)

@dp.callback_query(F.data == "admin_close")
async def admin_close_handler(callback: CallbackQuery):
    await callback.message.delete()[span_165](start_span)[span_165](end_span)
# ======================================================

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id[span_166](start_span)[span_166](end_span)
    is_sub = await check_subscription(user_id)[span_167](start_span)[span_167](end_span)
    
    if is_sub:[span_168](start_span)[span_168](end_span)
        user = get_user(user_id)[span_169](start_span)[span_169](end_span)
        if user and user[1]:[span_170](start_span)[span_170](end_span)
            add_point(user[1])[span_171](start_span)[span_171](end_span)
            try:
                await bot.send_message(
                    user[1], 
                    "🎉 Пользователь, которого вы пригласили, подписался на канал! Вам начислен <b>+1 балл</b>.",
                    parse_mode=ParseMode.HTML
                )[span_172](start_span)[span_172](end_span)
            except:
                pass[span_173](start_span)[span_173](end_span)
            
            conn = sqlite3.connect("bot_database.db")[span_174](start_span)[span_174](end_span)
            cursor = conn.cursor()[span_175](start_span)[span_175](end_span)
            cursor.execute("UPDATE users SET referrer_id = NULL WHERE user_id = ?", (user_id,))[span_176](start_span)[span_176](end_span)
            conn.commit()[span_177](start_span)[span_177](end_span)
            conn.close()[span_178](start_span)[span_178](end_span)

        await callback.message.delete()[span_179](start_span)[span_179](end_span)
        first_name = html.escape(callback.from_user.first_name)[span_180](start_span)[span_180](end_span)
        welcome_text = f"💥 <b>Добро пожаловать, {first_name}!</b>\n‹━━━━━━━━━━━━━━›\n\n🔥 Приватный архив 18+\n— эксклюзивный контент\n— доступ только для участников\n\n👇 <b>Выбери раздел</b> 👇[span_181](start_span)"[span_181](end_span)
        await callback.message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)[span_182](start_span)[span_182](end_span)
    else:
        await callback.answer("❌ Вы еще не подписались на все каналы!", show_alert=True)[span_183](start_span)[span_183](end_span)

@dp.callback_query(F.data == "channels")
async def channels_handler(callback: CallbackQuery):
    is_sub = await check_subscription(callback.from_user.id)[span_184](start_span)[span_184](end_span)
    if not is_sub:[span_185](start_span)[span_185](end_span)
        await callback.answer("⚠️ Сначала подпишитесь на все обязательные каналы!", show_alert=True)[span_186](start_span)[span_186](end_span)
        return[span_187](start_span)[span_187](end_span)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Перейти в канал", url=CHANNELS_SECTION_LINK)],[span_188](start_span)[span_188](end_span)
            [InlineKeyboardButton(text="👈 Назад", callback_data="back_main")][span_189](start_span)[span_189](end_span)
        ]
    )[span_190](start_span)[span_190](end_span)
    await callback.message.edit_text("👇 Вы можете перейти в наш приватный канал по кнопке ниже:", reply_markup=kb)[span_191](start_span)[span_191](end_span)

@dp.callback_query(F.data == "free_channel")
async def free_channel_handler(callback: CallbackQuery):
    user_id = callback.from_user.id[span_192](start_span)[span_192](end_span)
    is_sub = await check_subscription(user_id)[span_193](start_span)[span_193](end_span)
    if not is_sub:[span_194](start_span)[span_194](end_span)
        await callback.answer("⚠️ Сначала подпишитесь на все обязательные каналы!", show_alert=True)[span_195](start_span)[span_195](end_span)
        return[span_196](start_span)[span_196](end_span)

    bot_info = await bot.get_me()[span_197](start_span)[span_197](end_span)
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}[span_198](start_span)"[span_198](end_span)
    
    user = get_user(user_id)[span_199](start_span)[span_199](end_span)
    points = user[2] if user else 0[span_200](start_span)[span_200](end_span)

    text = (
        f"⚡ <b>Бесплатный канал (Реферальная система)</b>\n\n"
        f"Приглашайте друзей и накапливайте баллы, чтобы получить доступ к закрытому каналу!\n"
        f"💡 <i>За каждого приглашенного друга, подписавшегося на канал, вы получаете +1 балл.</i>\n\n"
        f"👤 Ваши баллы: <b>{points} / {REQUIRED_REFERRALS}</b>\n"
        f"🔗 Ваша пригласительная ссылка:\n<code>{ref_link}</code>\n\n"
    )[span_201](start_span)[span_201](end_span)

    if points >= REQUIRED_REFERRALS:[span_202](start_span)[span_202](end_span)
        try:
            expire_time = datetime.now() + timedelta(minutes=10)[span_203](start_span)[span_203](end_span)
            invite_link = await bot.create_chat_invite_link(
                chat_id=PRIVATE_CHANNEL_ID,
                member_limit=1,
                expire_date=expire_time
            )[span_204](start_span)[span_204](end_span)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔓 Войти в канал (Временная ссылка)", url=invite_link.invite_link)],[span_205](start_span)[span_205](end_span)
                    [InlineKeyboardButton(text="👈 Назад", callback_data="back_main")][span_206](start_span)[span_206](end_span)
                ]
            )[span_207](start_span)[span_207](end_span)
            text += "🎉 <b>Вы успешно собрали 10 баллов!</b>\n\n⚠️ <i>Внимание: Ссылка ниже одноразовая и действительна в течение 10 минут только для 1 человека! Не пересылайте её никому.</i>[span_208](start_span)"[span_208](end_span)
        except Exception as e:
            logging.error(f"Ошибка создания ссылки: {e}")[span_209](start_span)[span_209](end_span)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="👈 Назад", callback_data="back_main")]][span_210](start_span)[span_210](end_span)
            )
            text += "⚠️ Произошла ошибка при создании ссылки. Убедитесь, что бот является администратором закрытого канала с правом приглашения пользователей.[span_211](start_span)"[span_211](end_span)
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👈 Назад", callback_data="back_main")][span_212](start_span)[span_212](end_span)
            ]
        )
        text += f"💡 Для получения доступа вам осталось набрать ещё <b>{REQUIRED_REFERRALS - points}</b> баллов.[span_213](start_span)"[span_213](end_span)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)[span_214](start_span)[span_214](end_span)

@dp.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👈 Назад", callback_data="back_main")][span_215](start_span)[span_215](end_span)
        ]
    )
    help_text = "🤖 <b>Помощник / Информация</b>\n\n1. <b>Каналы</b> — Список наших основных ресурсов.\n2. <b>Бесплатный канал</b> — Приглашайте друзей по своей ссылке, копите баллы и получайте бесплатный доступ к закрытому каналу!\n\nЕсли у вас возникли вопросы, свяжитесь с администратором.[span_216](start_span)"[span_216](end_span)
    await callback.message.edit_text(help_text, reply_markup=kb, parse_mode=ParseMode.HTML)[span_217](start_span)[span_217](end_span)

@dp.callback_query(F.data == "back_main")
async def back_main_handler(callback: CallbackQuery):
    first_name = html.escape(callback.from_user.first_name)[span_218](start_span)[span_218](end_span)
    welcome_text = f"💥 <b>Добро пожаловать, {first_name}!</b>\n‹━━━━━━━━━━━━━━━━›\n\n🔥 Приватный архив 18+\n— эксклюзивный контент\n— доступ только для участников\n\n👇 <b>Выбери раздел</b> 👇[span_219](start_span)"[span_219](end_span)
    await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)[span_220](start_span)[span_220](end_span)

# ==================== WEBHOOK SOZLAMASI ====================
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

def main():
    dp.startup.register(on_startup)
    app = web.Application()
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
