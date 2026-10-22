import logging
import asyncio
import sqlite3
import random
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8709792380:AAEaoUeyzfnrZnqPVzMrTUygXZWwBIqm-zI"
ADMIN_ID = 5450050924
REVIEWS_CHANNEL = "@Otziv_donatshop"
SUPPORT_USERNAME = "Abdulega"

# РЕКВИЗИТЫ
DC_CARD = "9762 0002 2654 6264"
DC_NAME = "KURBONOVA N"
ALIF_ACCOUNT = "900163322"

# Картинка Аниме (Клинок рассекающий демонов)
ANIME_IMAGE = "https://i.ibb.co/vzR3X3m/demon-slayer.jpg"

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# --- БАЗА ДАННЫХ (SQLite) ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_balance(user_id: int) -> float:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        balance = row[0]
    else:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, 0.0)", (user_id,))
        conn.commit()
        balance = 0.0
    conn.close()
    return float(balance)

def update_balance(user_id: int, amount: float):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?", (user_id, amount, amount))
    conn.commit()
    conn.close()

# --- FSM (Состояния) ---
class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

class BuyState(StatesGroup):
    waiting_for_uid = State()
    confirm_payment = State()
    waiting_for_direct_receipt = State()

# --- ПРОВЕРКА ID (C НОВЫМ NFTOKEN API) ---
async def check_player_id(game: str, uid: str):
    uid = uid.strip()
    if not uid.isdigit() or not (6 <= len(uid) <= 12):
        return False, None

    headers = {"User-Agent": "Mozilla/5.0"}

    if game == "ff":
        # 1. Пробуем новые эндпоинты nftoken.info
        url_nftoken1 = f"https://api2.nftoken.info/player-info?uid={uid}"
        url_nftoken2 = f"https://api2.nftoken.info/get?uid={uid}"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Запрос к player-info
                async with session.get(url_nftoken1, headers=headers, timeout=4) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        nick = (
                            data.get("nickname") or 
                            data.get("name") or 
                            data.get("basicInfo", {}).get("nickname") or 
                            data.get("data", {}).get("nickname")
                        )
                        if nick:
                            return True, nick

                # Запрос к /get
                async with session.get(url_nftoken2, headers=headers, timeout=4) as resp2:
                    if resp2.status == 200:
                        data2 = await resp2.json()
                        nick2 = (
                            data2.get("nickname") or 
                            data2.get("name") or 
                            data2.get("basicInfo", {}).get("nickname")
                        )
                        if nick2:
                            return True, nick2

                # Запасной сервер RU-региона
                url_ru = f"https://free-ff-api-src-5plp.onrender.com/api/v1/account?region=RU&uid={uid}"
                async with session.get(url_ru, headers=headers, timeout=4) as resp3:
                    if resp3.status == 200:
                        data3 = await resp3.json()
                        nick3 = data3.get("basicInfo", {}).get("nickname") or data3.get("nickname")
                        if nick3:
                            return True, nick3
        except Exception:
            pass

        return True, "Игрок Free Fire"

    elif game == "pubg":
        return True, f"PUBG Player ({uid})"

    elif game == "codm":
        return True, f"CODM Player ({uid})"

    return True, "Игрок"

# --- КЛАВИАТУРЫ ---
def main_menu_kb(user_id: int):
    bal = get_balance(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Бозиҳо", callback_data="open_games")],
        [InlineKeyboardButton(text=f"💼 Баланси ман ({bal:.2f} смн)", callback_data="deposit_start")],
        [InlineKeyboardButton(text="⭐ Шарҳҳо (Отзывҳо)", url=f"https://t.me/{REVIEWS_CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton(text="👨‍💻 Поддержка (Админ)", url=f"https://t.me/{SUPPORT_USERNAME}")]
    ])
    return keyboard

def games_menu_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Free Fire 🔥", callback_data="game_ff")],
        [InlineKeyboardButton(text="PUBG Mobile 🎯", callback_data="game_pubg")],
        [InlineKeyboardButton(text="Call of Duty Mobile 🔫", callback_data="game_codm")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    return keyboard

def ff_categories_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Алмосҳо", callback_data="cat_ff_diamonds")],
        [InlineKeyboardButton(text="🎟️ Ваучерҳо", callback_data="cat_ff_vouchers")],
        [InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="open_games")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    return keyboard

def pubg_items_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="60 UC — 9.90 смн", callback_data="item_pubg_60_9.90")],
        [InlineKeyboardButton(text="300 + 25 UC — 48.00 смн", callback_data="item_pubg_325_48.00")],
        [InlineKeyboardButton(text="600 + 60 UC — 95.00 смн", callback_data="item_pubg_660_95.00")],
        [InlineKeyboardButton(text="1500 + 300 UC — 245.00 смн", callback_data="item_pubg_1800_245.00")],
        [InlineKeyboardButton(text="3000 + 850 UC — 489.00 смн", callback_data="item_pubg_3850_489.00")],
        [InlineKeyboardButton(text="6000 + 2100 UC — 969.00 смн", callback_data="item_pubg_8100_969.00")],
        [InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="open_games")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    return keyboard

def codm_items_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="80 CP — 12.00 смн", callback_data="item_codm_80_12.00")],
        [InlineKeyboardButton(text="420 CP — 58.00 смн", callback_data="item_codm_420_58.00")],
        [InlineKeyboardButton(text="880 CP — 115.00 смн", callback_data="item_codm_880_115.00")],
        [InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="open_games")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    return keyboard

def ff_diamonds_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 100 💎 + 10 💎 (8.80 смн)", callback_data="item_ff_100_8.80")],
        [InlineKeyboardButton(text="🛒 310 💎 + 30 💎 (26.50 смн)", callback_data="item_ff_310_26.50")],
        [InlineKeyboardButton(text="🛒 520 💎 + 50 💎 (44.00 смн)", callback_data="item_ff_520_44.00")],
        [InlineKeyboardButton(text="🛒 1060 💎 + 100 💎 (88.00 смн)", callback_data="item_ff_1060_88.00")],
        [InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="game_ff")]
    ])
    return keyboard

def ff_vouchers_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Ваучери Лайт (Weekly Lite) - 5.00 смн", callback_data="item_ff_vlite_5.00")],
        [InlineKeyboardButton(text="💳 Ваучери Ҳафтаина (Weekly) - 18.00 смн", callback_data="item_ff_vweek_18.00")],
        [InlineKeyboardButton(text="🌟 Ваучери Моҳона (Monthly) - 88.00 смн", callback_data="item_ff_vmonth_88.00")],
        [InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="game_ff")]
    ])
    return keyboard

def bank_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Dushanbe City", callback_data="bank_dc"), InlineKeyboardButton(text="📲 Alif Mobi", callback_data="bank_alif")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])

def back_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]])

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    bal = get_balance(user_id)
    
    text = (
        f"👋 <b>Ассалому алейкум!</b>\n"
        f"💙 Ба боти автодонати <b>DONAT SHOP 💎🇹🇯</b> хуш омадед!\n"
        f"----------------------------------------\n"
        f"👤 Салом, <b>{message.from_user.first_name}</b>!\n"
        f"💰 Баланси шумо: <b>{bal:.2f} смн</b>\n\n"
        f"🎮 <b>Бозии худро интихоб кунед:</b>\n"
        f"⚡ Донати зуд, осон ва боэътимод."
    )
    await message.answer(text, reply_markup=main_menu_kb(user_id), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    bal = get_balance(user_id)
    text = (
        f"👋 <b>Ассалому алейкум!</b>\n"
        f"👤 Салом, <b>{callback.from_user.first_name}</b>!\n"
        f"💰 Баланси шумо: <b>{bal:.2f} смн</b>"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, reply_markup=main_menu_kb(user_id), parse_mode="HTML")
    await callback.answer()

# --- МЕНЮ ИГР С АНИМЕ ---
@dp.callback_query(F.data == "open_games")
async def open_games(callback: types.CallbackQuery):
    caption = "🎮 <b>Бозиҳоро интихоб кунед:</b>"
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    try:
        await callback.message.answer_photo(
            photo=ANIME_IMAGE,
            caption=caption,
            reply_markup=games_menu_kb(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(caption, reply_markup=games_menu_kb(), parse_mode="HTML")
    await callback.answer()

# ИГРЫ
@dp.callback_query(F.data == "game_ff")
async def game_ff(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption="🔥 <b>Free Fire</b>\n\nКатегорияро интихоб кунед:", reply_markup=ff_categories_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "cat_ff_diamonds")
async def cat_ff_diamonds(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption="💎 <b>Пакетҳои алмосро интихоб кунед:</b>", reply_markup=ff_diamonds_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "cat_ff_vouchers")
async def cat_ff_vouchers(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption="🎟️ <b>Ваучерҳоро интихоб кунед:</b>", reply_markup=ff_vouchers_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "game_pubg")
async def game_pubg(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption="🎯 <b>PUBG Mobile</b>\n\nБастаи лозимиро интихоб кунед:", reply_markup=pubg_items_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "game_codm")
async def game_codm(callback: types.CallbackQuery):
    await callback.message.edit_caption(caption="🔫 <b>Call of Duty Mobile</b>\n\nБастаи лозимиро интихоб кунед:", reply_markup=codm_items_kb(), parse_mode="HTML")
    await callback.answer()

# ВЫБОР ТОВАРА
@dp.callback_query(F.data.startswith("item_"))
async def select_item(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    game_code = parts[1]
    item_code = parts[2]
    price = float(parts[3])

    if game_code == "ff":
        item_names = {"100": "100 💎 + 10 💎", "310": "310 💎 + 30 💎", "520": "520 💎 + 50 💎", "1060": "1060 💎 + 100 💎", "vlite": "Ваучери Лайт", "vweek": "Ваучери Ҳафтаина", "vmonth": "Ваучери Моҳона"}
    elif game_code == "pubg":
        item_names = {"60": "60 UC", "325": "300 + 25 UC", "660": "600 + 60 UC", "1800": "1500 + 300 UC", "3850": "3000 + 850 UC", "8100": "6000 + 2100 UC"}
    else:
        item_names = {"80": "80 CP", "420": "420 CP", "880": "880 CP"}

    item_name = item_names.get(item_code, "Донат")
    await state.update_data(game_code=game_code, item_name=item_name, price=price)
    await state.set_state(BuyState.waiting_for_uid)

    text = (
        f"🛒 <b>{item_name}</b>\n"
        f"----------------------------------------\n"
        f"💰 Нарх: <b>{price:.2f} смн</b>\n\n"
        f"🆔 Отправьте ваш <b>Player ID</b> (только цифры):"
    )
    await callback.message.answer(text, reply_markup=back_main_kb(), parse_mode="HTML")
    await callback.answer()

# ВВОД И ПРОВЕРКА ID
@dp.message(BuyState.waiting_for_uid)
async def process_uid(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    uid_text = message.text.strip()
    data = await state.get_data()
    game_code = data.get("game_code")
    item_name = data.get("item_name")
    price = data.get("price")

    is_valid, player_name = await check_player_id(game_code, uid_text)
    bal = get_balance(user_id)

    await state.update_data(user_uid=uid_text, player_name=player_name)
    await state.set_state(BuyState.confirm_payment)

    text = (
        f"💳 <b>Выберите способ оплаты</b>\n"
        f"----------------------------------------\n"
        f"📦 {item_name}\n"
        f"💰 Цена: <b>{price:.2f} смн</b>\n"
        f"👤 {player_name}\n"
        f"🆔 {uid_text}\n\n"
        f"💼 Ваш баланс: <b>{bal:.2f} смн</b>\n"
        f"⚡ Оплата с баланса — донат сразу."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Оплатить с баланса", callback_data="pay_bal")],
        [InlineKeyboardButton(text="💳 Оплатить картой (чек)", callback_data="pay_card")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# ОПЛАТА С БАЛАНСА
@dp.callback_query(BuyState.confirm_payment, F.data == "pay_bal")
async def pay_bal(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    price = data.get("price")
    bal = get_balance(user_id)

    if bal < price:
        await callback.answer("⚠️ Не хватает баланса!", show_alert=True)
        return

    update_balance(user_id, -price)
    order_id = random.randint(2000, 9999)

    await bot.send_message(
        ADMIN_ID,
        f"🚀 <b>НОВЫЙ ЗАКАЗ С БАЛАНСА!</b>\n\n"
        f"📄 Заказ №: <b>#{order_id}</b>\n"
        f"👤 Клиент: <a href='tg://user?id={user_id}'>{callback.from_user.first_name}</a>\n"
        f"📦 Товар: <b>{data.get('item_name')}</b>\n"
        f"🎮 Player ID: <code>{data.get('user_uid')}</code>\n"
        f"👤 Ник: <b>{data.get('player_name')}</b>\n"
        f"💰 Списано: <b>{price:.2f} смн</b>",
        parse_mode="HTML"
    )

    await callback.message.edit_text(
        f"✅ <b>Заказ #{order_id} успешно выполнен!</b>\n\n"
        f"Спасибо за покупку! ❤️",
        reply_markup=main_menu_kb(user_id),
        parse_mode="HTML"
    )
    await state.clear()

# ОПЛАТА КАРТОЙ (ЧЕК)
@dp.callback_query(BuyState.confirm_payment, F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery):
    await callback.message.edit_text("💳 <b>Выберите банк:</b>", reply_markup=bank_choice_kb(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("bank_"))
async def choose_bank(callback: types.CallbackQuery, state: FSMContext):
    bank = callback.data.split("_")[1]
    data = await state.get_data()
    price = data.get("price")

    acc = DC_CARD if bank == "dc" else ALIF_ACCOUNT
    bank_name = "Dushanbe City" if bank == "dc" else "Alif Mobi"

    text = (
        f"💳 <b>ОПЛАТА</b>\n"
        f"----------------------------------------\n"
        f"📦 {data.get('item_name')}\n"
        f"👤 {data.get('player_name')}\n"
        f"🆔 <code>{data.get('user_uid')}</code>\n\n"
        f"💰 Сумма: <b>{price:.2f} смн</b>\n"
        f"🏦 <b>{bank_name}:</b> <code>{acc}</code>\n\n"
        f"📸 Отправьте фото чека прямо здесь."
    )
    await state.set_state(BuyState.waiting_for_direct_receipt)
    await callback.message.edit_text(text, parse_mode="HTML")

@dp.message(BuyState.waiting_for_direct_receipt, F.photo)
async def process_direct_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id

    await bot.send_photo(
        ADMIN_ID,
        photo=photo_id,
        caption=f"📥 <b>ЗАКАЗ С ЧЕКОМ!</b>\n\n"
                f"👤 Клиент: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
                f"📦 Товар: <b>{data.get('item_name')}</b>\n"
                f"🎮 ID: <code>{data.get('user_uid')}</code>\n"
                f"👤 Ник: <b>{data.get('player_name')}</b>\n"
                f"💰 Сумма: <b>{data.get('price'):.2f} смн</b>",
        parse_mode="HTML"
    )
    await message.answer("⏳ Чек принят на проверку! Ожидайте 5-15 минут.", reply_markup=main_menu_kb(user_id))
    await state.clear()

# ПОПОЛНЕНИЕ БАЛАНСА
@dp.callback_query(F.data == "deposit_start")
async def deposit_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositState.waiting_for_amount)
    await callback.message.edit_text(
        "➕ <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n"
        "----------------------------------------\n"
        "Введите сумму пополнения в сомони (от 5 до 500):",
        reply_markup=back_main_kb(),
        parse_mode="HTML"
    )

@dp.message(DepositState.waiting_for_amount)
async def deposit_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(amount=amount)
        await message.answer("💳 Выберите банк для пополнения:", reply_markup=bank_choice_kb())
    except ValueError:
        await message.answer("Илтимос, танҳо рақам ворид кунед!")

# РЕНДЕР ВЕБ-СЕРВЕР
async def handle_ping(request):
    return web.Response(text="Bot Live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
