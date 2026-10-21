import logging
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8709792380:AAFQnlj8hIAhHdQbOKBMKgilqyi_O6lFJKw"  # Твой токен бота
ADMIN_ID = 5450050924                                        # Твой Telegram ID
REVIEWS_CHANNEL = "@Otziv_donatshop"                          # Твой канал отзывов

# Реквизиты для оплаты
DC_CARD = "9762 0002 2654 6264"
DC_NAME = "KURBONOVA N"
ALIF_PHONE = "900163322"
WHATSAPP_PHONE = "992900163322"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ТОВАРЫ И ЦЕНЫ (Алмазы Free Fire) ---
PRICES = {
    "110_diamonds": {"name": "110 Алмаз", "price": 8},
    "240_diamonds": {"name": "240 Алмаз", "price": 16},
    "580_diamonds": {"name": "580 Алмаз", "price": 38},
    "1180_diamonds": {"name": "1180 Алмаз", "price": 76},
    "2420_diamonds": {"name": "2420 Алмаз", "price": 152},
    "6040_diamonds": {"name": "6040 Алмаз", "price": 380},
    "weekly_pass": {"name": "Ваучери Ҳафтаина 🎟️", "price": 16},
    "monthly_pass": {"name": "Ваучери Моҳона 🎫", "price": 76},
}

# --- СОСТОЯНИЯ (FSM) ---
class BuyState(StatesGroup):
    waiting_for_ff_id = State()
    waiting_for_confirm = State()
    waiting_for_payment = State()
    waiting_for_receipt = State()

class ReviewState(StatesGroup):
    waiting_for_review_text = State()

# --- КЛАВИАТУРЫ ---
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 Харидани Алмазҳо"), KeyboardButton(text="🏷️ Прайс-лист")],
            [KeyboardButton(text="✍️ Гузоштани Отзыв"), KeyboardButton(text="📞 Поддержка")],
            [KeyboardButton(text="📢 Канали Мо"), KeyboardButton(text="ℹ️ ДАР БОРАИ БОТ")]
        ],
        resize_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Бекор кардан")]],
        resize_keyboard=True
    )

# --- СТАРТ И ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
@dp.message(F.text == "🏠 Менюи асосӣ")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        f"Ассалому алейкум, {message.from_user.first_name}! 🖐️\n\n"
        "Хуш омадед ба ботарии расмии **DONAT SHOP 💎🇹🇯**!\n"
        "Дар ин ҷо шумо метавонед алмазҳои Free Fire-ро бо нархҳои арзон ва зуд харидорӣ кунед. 🚀\n\n"
        "Лутфан аз менюи поён фасли дилхоҳатонро интихоб кунед 👇"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message(F.text == "🏷️ Прайс-лист")
async def show_prices(message: types.Message):
    text = "💎 **ПРАЙС-ЛИСТИ АЛМАЗҲОИ FREE FIRE** 💎\n\n"
    for item in PRICES.values():
        text += f"🔹 {item['name']} — **{item['price']} сомонӣ**\n"
    text += "\n⚡ Пардохти зуд ва амн бо Dushanbe City ва Alif Mobi!"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📢 Канали Мо")
async def show_channel(message: types.Message):
    await message.answer(f"📢 Канали отзывҳои мо: {REVIEWS_CHANNEL}\nБа канал обуна шавед ва фикри харидоронро бинед! ❤️")

@dp.message(F.text == "📞 Поддержка")
async def show_support(message: types.Message):
    text = (
        "📞 **ПАТТИШКА / АДМИНИСТРАТОР**\n\n"
        "Барои саволҳо ва мушкилот ба администратор муроҷиат кунед:\n"
        f"📱 WhatsApp: https://wa.me/{WHATSAPP_PHONE}\n"
        f"👤 Telegram: @Abdulega"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "ℹ️ ДАР БОРАИ БОТ")
async def show_about(message: types.Message):
    text = (
        "ℹ️ **ДАР БОРАИ БОТ**\n\n"
        "DONAT SHOP — боти боэътимоди донати Free Fire дар Тоҷикистон! 🇹🇯\n"
        "Ҳамаи донатҳо тавассути ID-и бозӣ дар муддати 5-15 дақиқа иҷро мешаванд."
    )
    await message.answer(text, parse_mode="Markdown")

# --- ПРОЦЕСС ПОКУПКИ ---
@dp.message(F.text == "💎 Харидани Алмазҳо")
async def start_buy(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💎 {item['name']} — {item['price']} с.", callback_data=f"buy_{key}")]
        for key, item in PRICES.items()
    ])
    await message.answer("🛒 **Пакет-и дилхоҳатонро интихоб кунед:**", parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_item(callback: types.CallbackQuery, state: FSMContext):
    item_key = callback.data.split("buy_")[1]
    item = PRICES[item_key]
    await state.update_data(item_key=item_key, item_name=item['name'], price=item['price'])
    
    await callback.message.delete()
    await callback.message.answer(
        f"📦 Шумо интихоб кардед: **{item['name']}** ({item['price']} с.)\n\n"
        "🆔 **Лутфан ID-и бозии (Free Fire ID)-и худро ворид кунед:**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(BuyState.waiting_for_ff_id)

@dp.message(BuyState.waiting_for_ff_id)
async def process_ff_id(message: types.Message, state: FSMContext):
    if message.text == "❌ Бекор кардан":
        await state.clear()
        await message.answer("❌ Харид бекор карда шуд.", reply_markup=main_menu())
        return

    ff_id = message.text.strip()
    if not ff_id.isdigit() or len(ff_id) < 5:
        await message.answer("⚠️ **ID-и нодӯруст!** Лутфан танҳо рақамҳои ID-и худро бинависед (масалан: 123456789):")
        return

    await state.update_data(ff_id=ff_id)
    data = await state.get_data()

    text = (
        f"📋 **ТАСДИҚИ МАЪЛУМОТИ ХАРИД:**\n\n"
        f"📦 Мол: **{data['item_name']}**\n"
        f"💰 Маблағ: **{data['price']} сомонӣ**\n"
        f"🆔 Free Fire ID: **{data['ff_id']}**\n\n"
        "Оё маълумот дуруст аст?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Дуруст аст (Идома)", callback_data="confirm_buy")],
        [InlineKeyboardButton(text="❌ Бекор кардан", callback_data="cancel_buy")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await state.set_state(BuyState.waiting_for_confirm)

@dp.callback_query(BuyState.waiting_for_confirm, F.data == "cancel_buy")
async def cancel_buy_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Харид бекор карда шуд.")
    await callback.message.answer("🏠 Менюи асосӣ", reply_markup=main_menu())

@dp.callback_query(BuyState.waiting_for_confirm, F.data == "confirm_buy")
async def process_payment_methods(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = data['price']

    dc_link = f"https://citypay.tj/transfer?card={DC_CARD}&amount={price}"
    alif_link = f"https://alif.tj/pay?phone={ALIF_PHONE}&amount={price}"

    text = (
        f"💳 **ИНТИХОБИ УСУЛИ ПАРДОХТ**\n\n"
        f"Суммаи пардохт: **{price} сомонӣ**\n\n"
        f"1️⃣ **Dushanbe City:** `{DC_CARD}`\n"
        f"👤 Қабулкунанда: **{DC_NAME}**\n\n"
        f"2️⃣ **Alif Mobi:** `{ALIF_PHONE}`\n\n"
        "👇 Барои пардохти худкор тугмаҳои поёнро пахш кунед ё ба реквизитҳо пардохт намоед:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Пардохт бо DC Pay", url=dc_link)],
        [InlineKeyboardButton(text="📱 Пардохт бо Alif Mobi", url=alif_link)],
        [InlineKeyboardButton(text="✅ Пардохт кардам (Ирсоли чек)", callback_data="sent_payment")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await state.set_state(BuyState.waiting_for_payment)

@dp.callback_query(BuyState.waiting_for_payment, F.data == "sent_payment")
async def request_receipt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📸 **Лутфан скроиншот ё чеки пардохтро ҳамчун расм/файл фиристонед:**",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(BuyState.waiting_for_receipt)

# --- ПРИЕМ ЧЕКА И ОТПРАВКА ЗАКАЗА АДМИНИСТРАТОРУ (В ЛИЧКУ АДМИНА!) ---
@dp.message(BuyState.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    import random
    order_id = random.randint(1000, 9999)
    confirm_code = random.randint(1000, 9999)

    # 1. Карточка заказа отправляется СТРОГО АДМИНИСТРАТОРУ В ЛИЧКУ!
    admin_caption = (
        f"📥 **ФАРМОИШИ НАВ #{order_id}**\n\n"
        f"👤 Харидор: {username} (ID: `{user.id}`)\n"
        f"📦 Мол: 💎 **{data['item_name']}**\n"
        f"🆔 ID Игрок: `{data['ff_id']}`\n"
        f"💰 Маблағ: **{data['price']} с.**\n"
        f"🔑 Коди тасдиқ: `{confirm_code}`"
    )
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Алмазҳо равон карда шуданд", callback_data=f"done_{user.id}_{data['item_name']}")],
        [InlineKeyboardButton(text="❌ Бекор кардан", callback_data=f"decline_{user.id}")]
    ])

    if message.photo:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=admin_caption, parse_mode="Markdown", reply_markup=admin_kb)
    else:
        await bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=admin_caption, parse_mode="Markdown", reply_markup=admin_kb)

    # 2. ПОКУПАТЕЛЮ отправляем только красивое сообщение-подтверждение в боте:
    await message.answer(
        "✅ **Чеки шумо қабул шуд!**\n\n"
        "Администратор пардохтро месанҷад ва пас аз тасдиқ алмазҳо ба ҳисоби шумо ирсол мешаванд.\n\n"
        "Ташаккур барои харид! 💎",
        reply_markup=main_menu()
    )
    await state.clear()

# --- КНОПКИ УПРАВЛЕНИЯ ДЛЯ АДМИНА ---
@dp.callback_query(F.data.startswith("done_"))
async def admin_approve(callback: types.CallbackQuery):
    _, user_id, item_name = callback.data.split("_")
    # Уведомляем клиента
    await bot.send_message(
        chat_id=int(user_id),
        text=f"🎉 **ФАРМОИШИ ШУМО ИҶРО ШУД!**\n\n💎 {item_name} ба ҳисоби шумо ирсол гардид.\nТашаккур барои харид! ⭐"
    )
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **ИҶРО ШУД (Клиент уведомлен)**")

@dp.callback_query(F.data.startswith("decline_"))
async def admin_decline(callback: types.CallbackQuery):
    _, user_id = callback.data.split("_")
    await bot.send_message(
        chat_id=int(user_id),
        text="❌ **Фармоиши шумо бекор карда шуд.**\nЛутфан ба поддрежка муроҷиат кунед: @Abdulega"
    )
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **БЕКОР КАРДА ШУД**")

# --- ОТПРАВКА ОТЗЫВА НАПРЯМУЮ В КАНАЛ ОТЗЫВОВ ---
@dp.message(F.text == "✍️ Гузоштани Отзыв")
async def start_review(message: types.Message, state: FSMContext):
    await message.answer(
        "✍️ **Отзиви худро нависед:**\n\nМулоҳиза ё ташаккури худро нависед, он дар канали отзывҳои мо паҳн карда мешавад! ❤️",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ReviewState.waiting_for_review_text)

@dp.message(ReviewState.waiting_for_review_text)
async def process_review_text(message: types.Message, state: FSMContext):
    if message.text == "❌ Бекор кардан":
        await state.clear()
        await message.answer("❌ Бекор карда шуд.", reply_markup=main_menu())
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    # 1. Отправляем отзыв НАПРЯМУЮ В КАНАЛ @Otziv_donatshop
    review_channel_text = (
        f"Отзывы DONAT SHOP 💎🇹🇯\n"
        f"**Отзыв DONAT SHOP**\n"
        f"⭐ **Шарҳи харидор**\n\n"
        f"«{message.text}» 💬\n\n"
        f"👤 {username}"
    )
    
    try:
        await bot.send_message(chat_id=REVIEWS_CHANNEL, text=review_channel_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить отзыв в канал: {e}")

    # 2. ПОКУПАТЕЛЮ в боте говорим спасибо
    await message.answer(
        "💖 **Ташаккур барои отзиви шумо!**\n\nОтзиви шумо дар канали мо паҳн шуд! 💎",
        reply_markup=main_menu()
    )
    await state.clear()

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (чтобы не было ошибок портов) ---
async def handle_ping(request):
    return web.Response(text="DONAT SHOP Bot is Live 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

# --- ЗАПУСК БОТА ---
async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
