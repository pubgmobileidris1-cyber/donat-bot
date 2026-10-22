import logging
import asyncio
import sqlite3
import random
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8709792380:AAFQnlj8iAhHdQbQBKMgilqyi_061FJKw"
ADMIN_ID = 5450050924
REVIEWS_CHANNEL = "@Otziv_donatshop"
SUPPORT_USERNAME = "Abdulega"

# ПРАВИЛЬНЫЕ РЕКВИЗИТЫ
DC_CARD = "9762 0002 2654 6264"
DC_NAME = "KURBONOVA N"
ALIF_ACCOUNT = "900163322"

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

# --- ПРОВЕРКА FREE FIRE ID (МУЛЬТИРЕГИОН RU/CIS/SG) ---
async def check_freefire_id(uid: str):
    uid = uid.strip()
    if not uid.isdigit() or not (7 <= len(uid) <= 12):
        return False, None

    # Попытка 1: Сервер мульти-региона (включая RU)
    url_ru = f"https://free-ff-api-src-5plp.onrender.com/api/v1/account?region=RU&uid={uid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_ru, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    nickname = data.get("basicInfo", {}).get("nickname") or data.get("nickname")
                    if nickname:
                        return True, nickname

            # Попытка 2: Сервер Vyturex
            url2 = f"https://api.vyturex.com/ff?uid={uid}"
            async with session.get(url2, headers=headers, timeout=4) as response2:
                if response2.status == 200:
                    data2 = await response2.json()
                    nickname2 = data2.get("nickname") or data2.get("name")
                    if nickname2:
                        return True, nickname2

            # Попытка 3: Ищем через открытый поиск Garena
            url3 = f"https://freefireinfo-zy9l.onrender.com/api/v1/player-profile?uid={uid}"
            async with session.get(url3, headers=headers, timeout=4) as response3:
                if response3.status == 200:
                    data3 = await response3.json()
                    nickname3 = data3.get("basicInfo", {}).get("nickname")
                    if nickname3:
                        return True, nickname3
    except Exception:
        pass

    # Если API заблокирован или временно отвалился — не блокируем клиентов!
    return True, "Player Account"

# --- КЛАВИАТУРЫ ---
def main_menu_kb(user_id: int):
    bal = get_balance(user_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Free Fire", callback_data="buy_ff")],
        [InlineKeyboardButton(text=f"💳 Пур кардани ҳисоб (Ҳисоб: {bal:.2f} с.)", callback_data="deposit_start")],
        [InlineKeyboardButton(text="⭐ Шарҳҳо (Отзывҳо)", url=f"https://t.me/{REVIEWS_CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton(text="👨‍💻 Поддержка (Админ)", url=f"https://t.me/{SUPPORT_USERNAME}")]
    ])
    return keyboard

def ff_categories_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Алмосҳо", callback_data="cat_diamonds")],
        [InlineKeyboardButton(text="🎟️ Ваучерҳо", callback_data="cat_vouchers")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    return keyboard

def ff_diamonds_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 100 💎 + 10 💎 (8.80 с.)", callback_data="item_100_8.80")],
        [InlineKeyboardButton(text="🛒 310 💎 + 30 💎 (26.50 с.)", callback_data="item_310_26.50")],
        [InlineKeyboardButton(text="🛒 520 💎 + 50 💎 (44.00 с.)", callback_data="item_520_44.00")],
        [InlineKeyboardButton(text="🛒 1060 💎 + 100 💎 (88.00 с.)", callback_data="item_1060_88.00")],
        [InlineKeyboardButton(text="🔙 Бозгашт", callback_data="buy_ff")]
    ])
    return keyboard

def ff_vouchers_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Ваучери Лайт (Weekly Lite) - 5.00 с.", callback_data="item_vlite_5.00")],
        [InlineKeyboardButton(text="💳 Ваучери Ҳафтаина (Weekly) - 18.00 с.", callback_data="item_vweek_18.00")],
        [InlineKeyboardButton(text="🌟 Ваучери Моҳона (Monthly) - 88.00 с.", callback_data="item_vmonth_88.00")],
        [InlineKeyboardButton(text="🔙 Бозгашт", callback_data="buy_ff")]
    ])
    return keyboard

def deposit_amounts_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="20.00 с.", callback_data="dep_20"), InlineKeyboardButton(text="50.00 с.", callback_data="dep_50")],
        [InlineKeyboardButton(text="100.00 с.", callback_data="dep_100"), InlineKeyboardButton(text="200.00 с.", callback_data="dep_200")],
        [InlineKeyboardButton(text="✏️ Маблағи дигар", callback_data="dep_custom")],
        [InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]
    ])
    return keyboard

def back_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Менюи асосӣ", callback_data="back_to_main")]])

# --- СТАРТ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    bal = get_balance(user_id)
    
    welcome_text = (
        f"<b>САЛОМ! 👋</b>\n"
        f"<b>DONAT SHOP 💎🇹🇯</b> — арзонтарин донат барои Free Fire ⚡\n\n"
        f"💳 <b>Ҳисоби шумо: {bal:.2f} с.</b>\n\n"
        f"Барои фармоиш тугмаҳоро пахш кунед 👇"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(user_id), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    bal = get_balance(user_id)
    await callback.message.edit_text(
        f"🏠 <b>Менюи асосӣ:</b>\n\n💳 <b>Ҳисоби шумо: {bal:.2f} с.</b>",
        reply_markup=main_menu_kb(user_id),
        parse_mode="HTML"
    )
    await callback.answer()

# --- КАТАЛОГ FREE FIRE ---
@dp.callback_query(F.data == "buy_ff")
async def catalog_ff(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"🔥 <b>Free Fire</b>\n\nКатегорияро интихоб кунед:",
        reply_markup=ff_categories_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "cat_diamonds")
async def cat_diamonds(callback: types.CallbackQuery):
    await callback.message.edit_text("💎 <b>Пакетҳои алмосро интихоб кунед:</b>", reply_markup=ff_diamonds_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "cat_vouchers")
async def cat_vouchers(callback: types.CallbackQuery):
    await callback.message.edit_text("🎟️ <b>Ваучерҳоро интихоб кунед:</b>", reply_markup=ff_vouchers_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("item_"))
async def select_item(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    code = parts[1]
    price = float(parts[2])

    names = {
        "100": "🛒 100 💎 + 10 💎 бонус",
        "310": "🛒 310 💎 + 30 💎 бонус",
        "520": "🛒 520 💎 + 50 💎 бонус",
        "1060": "🛒 1060 💎 + 100 💎 бонус",
        "vlite": "🔹 Ваучери Лайт (Weekly Lite)",
        "vweek": "💳 Ваучери Ҳафтаина (Weekly)",
        "vmonth": "🌟 Ваучери Моҳона (Monthly)"
    }
    item_name = names.get(code, "Маҳсулоти Free Fire")

    await state.update_data(item_name=item_name, price=price)
    await state.set_state(BuyState.waiting_for_uid)
    
    await callback.message.edit_text(
        f"🛒 Шумо интихоб кардед: <b>{item_name}</b>\n"
        f"💰 Нарх: <b>{price:.2f} с.</b>\n\n"
        f"🆔 <b>Player ID</b>-и худро дар Free Fire фиристед (танҳо рақамҳо):",
        reply_markup=back_main_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

# ОБРАБОТКА ВВОДА ID
@dp.message(BuyState.waiting_for_uid)
async def process_buy_uid(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    uid_text = message.text.strip()
    
    wait_msg = await message.answer("🔍 <i>Player ID дар сервер тафтиш шуда истодааст...</i>", parse_mode="HTML")

    is_valid, player_name = await check_freefire_id(uid_text)
    
    try:
        await wait_msg.delete()
    except Exception:
        pass

    if not is_valid:
        await message.answer(
            "❌ <b>Player ID хато ворид карда шуд!</b>\n\n"
            "Илтимос, рақамҳои ID-ро дуруст тафтиш карда аз нав фиристед:",
            parse_mode="HTML",
            reply_markup=back_main_kb()
        )
        return

    data = await state.get_data()
    item_name = data.get("item_name")
    price = data.get("price")
    bal = get_balance(user_id)
    after_bal = bal - price

    await state.update_data(user_uid=uid_text, player_name=player_name)
    await state.set_state(BuyState.confirm_payment)

    text = (
        f"📄 <b>Тасдиқи фармоиш</b>\n\n"
        f"📦 Мол: <b>{item_name}</b>\n"
        f"🆔 ID-и бозигар: <code>{uid_text}</code>\n"
        f"👤 Никнейм дар бозӣ: <b>{player_name}</b>\n\n"
        f"💰 Нарх: <b>{price:.2f} с.</b>\n"
        f"💳 Ҳисоби шумо: <b>{bal:.2f} с.</b>\n"
        f"💵 Пас аз харид: <b>{after_bal:.2f} с.</b>\n\n"
    )

    if bal >= price:
        text += "Барои пардохт тугмаи поёнро пахш кунед 👇"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Пардохт кардан", callback_data="pay_from_balance")],
            [InlineKeyboardButton(text="❌ Бекор кардан", callback_data="back_to_main")]
        ])
    else:
        text += "⚠️ <b>Дар ҳисоби шумо маблағ кофӣ нест!</b>\nИлтимос, аввал ҳисобро пур кунед."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пур кардани ҳисоб", callback_data="deposit_start")],
            [InlineKeyboardButton(text="❌ Бекор кардан", callback_data="back_to_main")]
        ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(BuyState.confirm_payment, F.data == "pay_from_balance")
async def pay_from_balance(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    item_name = data.get("item_name")
    price = data.get("price")
    user_uid = data.get("user_uid")
    player_name = data.get("player_name")

    bal = get_balance(user_id)
    if bal < price:
        await callback.answer("⚠️ Маблағ кофӣ нест!", show_alert=True)
        return

    update_balance(user_id, -price)
    new_bal = get_balance(user_id)
    order_id = random.randint(2000, 9999)

    # Уведомление админу
    admin_order_msg = (
        f"🚀 <b>НОВЫЙ ЗАКАЗ (ОПЛАЧЕНО С БАЛАНСА)!</b>\n\n"
        f"📄 Заказ №: <b>#{order_id}</b>\n"
        f"👤 Клиент: <a href='tg://user?id={user_id}'>{callback.from_user.first_name}</a>\n"
        f"📦 Товар: <b>{item_name}</b>\n"
        f"🎮 Free Fire ID: <code>{user_uid}</code>\n"
        f"👤 Ник в игре: <b>{player_name}</b>\n"
        f"💰 Списано: <b>{price:.2f} с.</b>"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_order_msg, parse_mode="HTML")

    # Чек покупателю
    receipt_text = (
        f"📄 <b>ЧЕКИ ХАРИД</b>\n"
        f"----------------------------------------\n"
        f"✅ <b>Ҳолат: БОМУВАФФАҚИЯТ</b>\n"
        f"🔢 Фармоиш: <b>#{order_id}</b>\n"
        f"🆔 ID: <code>{user_uid}</code>\n"
        f"👤 Никнейм: <b>{player_name}</b>\n"
        f"📦 Мол: <b>{item_name}</b>\n"
        f"💰 Маблағ: <b>{price:.2f} с.</b>\n"
        f"💳 Ҳисоби нав: <b>{new_bal:.2f} с.</b>\n"
        f"----------------------------------------\n"
        f"🎉 <b>Хариди шумо иҷро шуд!</b>\n\n"
        f"Ташаккур барои харид! ❤️"
    )
    await callback.message.edit_text(receipt_text, reply_markup=main_menu_kb(user_id), parse_mode="HTML")
    await state.clear()
    await callback.answer()

# --- ПОПОЛНЕНИЕ БАЛАНСА ---
@dp.callback_query(F.data == "deposit_start")
async def deposit_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bal = get_balance(user_id)
    text = (
        f"💳 <b>Пур кардани ҳисоб</b>\n\n"
        f"Ҳисоби ҳозира: <b>{bal:.2f} с.</b>\n\n"
        f"Маблағро интихоб кунед ё худатон нависед.\n"
        f"<i>Аз 5.00 с. то 5000.00 с.</i>"
    )
    await callback.message.edit_text(text, reply_markup=deposit_amounts_kb(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("dep_"))
async def process_dep_choice(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split("_")[1]
    if choice == "custom":
        await state.set_state(DepositState.waiting_for_amount)
        await callback.message.edit_text("✏️ <b>Маблағи дилхоҳро бо рақам ворид кунед (масалан: 15):</b>", reply_markup=back_main_kb(), parse_mode="HTML")
    else:
        amount = float(choice)
        await setup_deposit_invoice(callback.message, state, amount, is_edit=True)
    await callback.answer()

@dp.message(DepositState.waiting_for_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 5 or amount > 5000:
            await message.answer("⚠️ Маблағ бояд аз 5.00 с. то 5000.00 с. бошад!")
            return
        await setup_deposit_invoice(message, state, amount, is_edit=False)
    except ValueError:
        await message.answer("⚠️ ИЛТИМОС, танҳо рақам ворид кунед!")

async def setup_deposit_invoice(message_obj, state: FSMContext, amount: float, is_edit: bool = False):
    pay_code = random.randint(1000, 9999)
    order_num = random.randint(2000, 9999)
    
    await state.update_data(deposit_amount=amount, pay_code=pay_code, order_num=order_num)
    await state.set_state(DepositState.waiting_for_receipt)
    
    text = (
        f"💳 <b>Реквизитҳо барои пардохт</b>\n\n"
        f"🏦 <b>Душанбе Сити:</b>\n"
        f"💳 Карт: <code>{DC_CARD}</code>\n"
        f"👤 Ном: <b>{DC_NAME}</b>\n\n"
        f"📲 <b>Alif Mobi:</b>\n"
        f"🔢 Ҳисоб: <code>{ALIF_ACCOUNT}</code>\n\n"
        f"💰 <b>Маблағ: {amount:.2f} с.</b>\n\n"
        f"🔑 <b>Коди тасдиқ: {pay_code}</b>\n"
        f"<i>Ин кодро ҳатман дар «Шарҳ / Комментарий»-и ҳавола нависед!</i>\n\n"
        f"📄 Рақами пардохт: <b>#{order_num}</b>\n\n"
        f"Пас аз ҳавола, чек ё скриншоти пардохтро дар ҳамин ҷо фиристед."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Бекор кардан", callback_data="back_to_main")]])
    if is_edit:
        await message_obj.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message_obj.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(DepositState.waiting_for_receipt, F.photo)
async def process_deposit_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("deposit_amount")
    order_num = data.get("order_num")
    pay_code = data.get("pay_code")
    user_id = message.from_user.id
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Тасдиқ (+{amount:.2f} с.)", callback_data=f"approve_dep_{user_id}_{amount}_{order_num}")],
        [InlineKeyboardButton(text="❌ Рaд кардан", callback_data=f"reject_dep_{user_id}_{order_num}")]
    ])
    
    admin_msg = (
        f"📥 <b>ЗАПРОС НА ПОПОЛНЕНИЕ БАЛАНСА!</b>\n\n"
        f"👤 Клиент: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"📄 Номер заявки: <b>#{order_num}</b>\n"
        f"💰 Сумма: <b>{amount:.2f} с.</b>\n"
        f"🔑 Код комментария: <b>{pay_code}</b>"
    )
    
    photo_id = message.photo[-1].file_id
    await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_msg, reply_markup=admin_kb, parse_mode="HTML")
    
    await message.answer(
        f"⏳ <b>Пардохти шумо ба тафтиш рафт.</b>\n"
        f"📄 Рақами пардохт: <b>#{order_num}</b>\n\n"
        f"Чек кабул шуд! Одатан тафтиш 5–15 дақиқа вақт мегирад.",
        reply_markup=back_main_kb(),
        parse_mode="HTML"
    )
    await state.clear()

@dp.callback_query(F.data.startswith("approve_dep_"))
async def admin_approve_dep(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    amount = float(parts[3])
    
    update_balance(target_user_id, amount)
    new_bal = get_balance(target_user_id)
    
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ <b>ПОДТВЕРЖДЕНО! Начислено {amount:.2f} с.</b>",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"✅ <b>Ҳисоб пур шуд!</b>\n\n➕ <b>+{amount:.2f} с.</b>\n💳 <b>Ҳисоби нав: {new_bal:.2f} с.</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer("Успешно начислено!")

@dp.callback_query(F.data.startswith("reject_dep_"))
async def admin_reject_dep(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ <b>ОТКЛОНЕНО АДМИНИСТРАТОРОМ.</b>",
        parse_mode="HTML"
    )
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="❌ <b>Пардохти шумо тасдиқ нашуд.</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer("Отклонено!")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
