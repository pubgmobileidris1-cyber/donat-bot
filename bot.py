import asyncio
import logging
import random
import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ВСТАВЬ СЮДА ТВОЙ ТОКЕН ОТ @BotFather
BOT_TOKEN = "8709792380:AAFQnlj8hIAhHdQbOKBMKgilqyi_O6lFJKw"
ADMIN_ID = 5450050924

REVIEWS_CHANNEL = "@Otziv_donatshop"
REVIEWS_CHANNEL_LINK = "https://t.me/Otziv_donatshop"

DUSHANBE_CITY_CARD = "9762 0002 2654 6264"
DUSHANBE_CITY_NAME = "K N"
ALIF_MOBI_ACC = "900163322"
WHATSAPP_NUMBER = "992900163322"

router = Router()


class OrderState(StatesGroup):
  waiting_for_id = State()
  waiting_for_receipt = State()


class ReviewState(StatesGroup):
  waiting_for_review_text = State()


class TopUpState(StatesGroup):
  waiting_for_custom_amount = State()


def get_payment_urls(amount: str):
  clean_card = DUSHANBE_CITY_CARD.replace(" ", "")
  dc_url = f"http://pay.dc.tj/?A={clean_card}&s={amount}&c=2661&f1=133"
  alif_url = f"https://alifmobi.page.link/providers?id=124&amount={amount}&account={ALIF_MOBI_ACC}"
  return dc_url, alif_url


async def get_real_free_fire_nickname(player_id: str) -> str:
  api_url = f"https://freefire-virtex.vercel.app/api/ff?id={player_id}"
  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(api_url, timeout=5) as response:
        if response.status == 200:
          data = await response.json()
          if "nickname" in data and data["nickname"]:
            return data["nickname"]
          elif "name" in data and data["name"]:
            return data["name"]
  except Exception as e:
    logging.error(f"Ошибка API проверки FF ID: {e}")
  return None


def get_main_keyboard():
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔥 Free Fire", callback_data="menu_ff"
              )
          ],
          [
              InlineKeyboardButton(
                  text="💰 Пур кардани ҳисоб", callback_data="menu_topup"
              ),
              InlineKeyboardButton(
                  text="🏆 Беҳтарин харидор", callback_data="menu_top_buyers"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="💰 Ҳисоби ман", callback_data="menu_balance"
              ),
              InlineKeyboardButton(
                  text="📦 Фармоишҳои ман", callback_data="menu_my_orders"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="💬 Отзывҳо ⭐️", url=REVIEWS_CHANNEL_LINK
              ),
              InlineKeyboardButton(
                  text="🛠 Дастгири", callback_data="menu_support"
              ),
          ],
      ]
  )


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
  await state.clear()
  text = (
      "<b>САЛОМ!</b>\n"
      "<b>DONAT SHOP 💎🇹🇯</b> — арзонтарин донат барои Free Fire!\n\n"
      "🔥 Free Fire (Алмосҳо ва Ваучерҳо)\n\n"
      "Супурдаш зуд • 100% бехатар\n"
      "Пардохт: Душанбе Сити, Alif Mobi\n\n"
      "Барои заказ тугмаҳоро пахш кунед 👇"
  )
  await message.answer(
      text, reply_markup=get_main_keyboard(), parse_mode="HTML"
  )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
  await state.clear()
  text = (
      "<b>DONAT SHOP 💎🇹🇯</b>\n\n"
      "Дар ин ҷо шумо метавонед алмосҳо ва ваучерҳои Free Fire-ро харед – зуд,"
      " арзон ва бидуни ворид шудани аккаунт.\n\n"
      "Бахшро аз поён интихоб кунед 👇"
  )
  await callback.message.edit_text(
      text, reply_markup=get_main_keyboard(), parse_mode="HTML"
  )
  await callback.answer()


@router.callback_query(F.data == "menu_ff")
async def ff_menu(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💎 Алмосҳо", callback_data="ff_diamonds"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📦 Ваучерҳо", callback_data="ff_vouchers"
              )
          ],
          [
              InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="main_menu"),
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              ),
          ],
      ]
  )
  await callback.message.edit_text(
      "🔥 <b>Free Fire</b>\n\nМаҳсулотро интихоб кунед.\n⏳ Ҳисоби шумо: 0.00"
      " с.",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


@router.callback_query(F.data == "ff_diamonds")
async def ff_diamonds_list(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💎 110 Алмаз — 8.00 с.",
                  callback_data="buy_item|110 Алмаз|8.00",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💎 341 Алмаз — 26.00 с.",
                  callback_data="buy_item|341 Алмаз|26.00",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💎 572 Алмаз — 40.00 с.",
                  callback_data="buy_item|572 Алмаз|40.00",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💎 1166 Алмаз — 80.00 с.",
                  callback_data="buy_item|1166 Алмаз|80.00",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💎 2398 Алмаз — 159.00 с.",
                  callback_data="buy_item|2398 Алмаз|159.00",
              )
          ],
          [
              InlineKeyboardButton(
                  text="💎 6160 Алмаз — 397.00 с.",
                  callback_data="buy_item|6160 Алмаз|397.00",
              )
          ],
          [
              InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="menu_ff"),
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              ),
          ],
      ]
  )
  await callback.message.edit_text(
      "🔥 <b>Free Fire — Алмосҳо</b>\n\nМаҳсулотро интихоб кунед.",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


@router.callback_query(F.data == "ff_vouchers")
async def ff_vouchers_list(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🎫 Ваучери Лайт (Weekly Lite) — 4.33 с.",
                  callback_data="buy_item|Weekly Lite|4.33",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎫 Ваучери Ҳафтаина — 15.80 с.",
                  callback_data="buy_item|Weekly Voucher|15.80",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🎫 Ваучери Моҳона — 58.50 с.",
                  callback_data="buy_item|Monthly Voucher|58.50",
              )
          ],
          [
              InlineKeyboardButton(text="⬅️ Бозгашт", callback_data="menu_ff"),
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              ),
          ],
      ]
  )
  await callback.message.edit_text(
      "🔥 <b>Free Fire — Ваучерҳо</b>\n\nМаҳсулотро интихоб кунед.",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


@router.callback_query(F.data.startswith("buy_item|"))
async def process_item_select(callback: CallbackQuery, state: FSMContext):
  _, item_name, price = callback.data.split("|")
  await state.update_data(item_name=item_name, price=price)

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              ),
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              ),
          ]
      ]
  )
  text = (
      f"🛒 <b>💎 {item_name} — {price} с.</b>\n\n"
      f"ID-и бозигари Free Fire-ро нависед — танҳо рақамҳо.\n\n"
      f"Намуна: 123456789"
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await state.set_state(OrderState.waiting_for_id)
  await callback.answer()


# 1. ШАГ ВВОДА И ПРОВЕРКИ ID
@router.message(OrderState.waiting_for_id)
async def process_player_id(message: Message, state: FSMContext):
  user_input = message.text.strip()
  if not user_input.isdigit() or len(user_input) < 5:
    await message.answer(
        "❌ Лутфан, ID-и дурустро танҳо бо рақамҳо нависед!\nНамуна:"
        " 123456789"
    )
    return

  wait_msg = await message.answer(
      "🔎 <i>Аккаунт дар базаи Free Fire тафтиш шуда истодааст...</i>",
      parse_mode="HTML",
  )

  nickname = await get_real_free_fire_nickname(user_input)
  await wait_msg.delete()

  if nickname:
    await state.update_data(player_id=user_input, nickname=nickname)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ҳа, аккаунти ман аст",
                    callback_data="confirm_acc_yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Не, ID-ро иваз мекунам", callback_data="menu_ff"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Бекор кардан", callback_data="main_menu"
                )
            ],
        ]
    )
    text = (
        f"🔍 <b>Тафтиши аккаунт</b>\n\n"
        f"🔥 Баҳш: <b>Free Fire</b>\n"
        f"🆔 ID: <b>{user_input}</b>\n"
        f"✅ Лақаб: <b>{nickname}</b>\n\n"
        f"<b>Ин аккаунти шумост?</b>"
    )
  else:
    await state.update_data(player_id=user_input, nickname="Номаълум")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ҳа, аккаунти ман аст",
                    callback_data="confirm_acc_yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Не, ID-ро иваз мекунам", callback_data="menu_ff"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Бекор кардан", callback_data="main_menu"
                )
            ],
        ]
    )
    text = (
        f"🔍 <b>Тафтиши аккаунт</b>\n\n"
        f"🔥 Баҳш: <b>Free Fire</b>\n"
        f"🆔 ID: <b>{user_input}</b>\n"
        f"⚠️ <i>Аккаунт худкор тафтиш нашуд (ID-и бозигар нодуруст аст ё"
        f" сервер банд аст). Илтимос, худатон бодиққат санҷед.</i>\n\n"
        f"<b>Ин аккаунти шумост?</b>"
    )

  await message.answer(text, reply_markup=kb, parse_mode="HTML")


# 2. ШАГ ПОДТВЕРЖДЕНИЯ АККАУНТА
@router.callback_query(F.data == "confirm_acc_yes")
async def show_payment_page(callback: CallbackQuery, state: FSMContext):
  data = await state.get_data()
  item_name = data.get("item_name", "Маҳсулот")
  price = data.get("price", "0.00")
  player_id = data.get("player_id", "---")
  nickname = data.get("nickname", "---")

  kb_confirm = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💰 Пардохт кардам", callback_data="pay_action"
              )
          ],
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              )
          ],
      ]
  )
  text_confirm = (
      f"🧾 <b>Тасдиқи фармоиш</b>\n\n"
      f"📦 Мол: 💎 <b>{item_name}</b>\n"
      f"🎯 Баҳш: Free Fire\n"
      f"🆔 Ғиранда: <b>{player_id}</b>\n"
      f"👤 Лақаб: <b>{nickname}</b>\n\n"
      f"💰 Нарх: <b>{price} с.</b>\n"
      f"💳 Ҳисоби шумо: 0.00 с.\n"
      f"💵 Пас аз харид: -{price} с.\n\n"
      f"Барои пардохт тугмаи поёнро пахш кунед."
  )
  await callback.message.edit_text(
      text_confirm, reply_markup=kb_confirm, parse_mode="HTML"
  )
  await callback.answer()


# 3. ШАГ ВЫВОДА РЕКВИЗИТОВ
@router.callback_query(F.data == "pay_action")
async def show_requisites_page(callback: CallbackQuery, state: FSMContext):
  data = await state.get_data()
  price = data.get("price", "8.00")

  confirm_code = random.randint(1000, 9999)
  order_number = random.randint(1000, 9999)

  await state.update_data(
      confirm_code=confirm_code, order_number=order_number
  )

  dc_link, alif_link = get_payment_urls(price)
  card_formatted = f"{DUSHANBE_CITY_CARD[:4]} {DUSHANBE_CITY_CARD[4:8]} {DUSHANBE_CITY_CARD[8:12]} {DUSHANBE_CITY_CARD[12:]}"

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(text="🏛 Душанбе Сити", url=dc_link),
              InlineKeyboardButton(text="📱 Alif Mobi", url=alif_link),
          ],
          [
              InlineKeyboardButton(
                  text="✅ Пардохт кардам", callback_data="ask_for_receipt"
              )
          ],
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              )
          ],
      ]
  )
  text = (
      f"💳 <b>Реквизитҳо барои пардохт</b>\n\n"
      f"🏛 <b>Душанбе Сити</b>\n"
      f"💳 Корт: <code>{card_formatted}</code>\n"
      f"👤 Ном: <b>{DUSHANBE_CITY_NAME}</b>\n\n"
      f"📱 <b>Alif Mobi</b>\n"
      f"🔢 Ҳисоб: <code>{ALIF_MOBI_ACC}</code>\n\n"
      f"💰 <b>Маблағ: {price} с.</b>\n\n"
      f"🔑 <b>Коди тасдиқ: {confirm_code}</b>\n"
      f"<i>Ин кодро ҳатман дар «Шарҳ / Комментарий»-и ҳавола нависед — бе он"
      f" пардохт зуд пайдо намешавад.</i>\n\n"
      f"📄 Рақами пардохт: #{order_number}\n\n"
      f"Пас аз ҳавола тугмаи «✅ Пардохт кардам»-ро пахш кунед ва скриншот ё"
      f" чекро фиристед."
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await callback.answer()


# 4. ШАГ ЗАПРОСА ЧЕКА (ПЕРЕХОД В СОСТОЯНИЕ WAITING_FOR_RECEIPT)
@router.callback_query(F.data == "ask_for_receipt")
async def ask_receipt_handler(callback: CallbackQuery, state: FSMContext):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              )
          ]
      ]
  )
  text = (
      "📸 <b>Лутфан, скриншот ё чеки пардохтро фиристед!</b>\n\n"
      "Расми чекро ба ҳамин ҷо ирсол кунед, то администратор онро тафтиш кунад."
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await state.set_state(OrderState.waiting_for_receipt)
  await callback.answer()


# 5. ШАГ ПОЛУЧЕНИЯ ФОТО ЧЕКА И ПЕРЕСЫЛКИ АДМИНУ
@router.message(OrderState.waiting_for_receipt, F.photo)
async def process_receipt_photo(
    message: Message, state: FSMContext, bot: Bot
):
  data = await state.get_data()
  item_name = data.get("item_name", "Маҳсулот")
  price = data.get("price", "0.00")
  player_id = data.get("player_id", "Пур кардани ҳисоб")
  nickname = data.get("nickname", "---")
  confirm_code = data.get("confirm_code", "----")
  order_number = data.get("order_number", "----")

  photo_id = message.photo[-1].file_id
  user_info = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else f"{message.from_user.full_name}"
  )

  admin_caption = (
      f"📥 <b>ФАРМОИШИ НАВ #{order_number}</b>\n\n"
      f"👤 Харидор: {user_info} (ID: <code>{message.from_user.id}</code>)\n"
      f"📦 Мол: 💎 <b>{item_name}</b>\n"
      f"🆔 ID Игрок: <code>{player_id}</code>\n"
      f"👤 Лақаб: <b>{nickname}</b>\n"
      f"💰 Маблағ: <b>{price} с.</b>\n"
      f"🔑 Коди тасдиқ: <code>{confirm_code}</code>\n"
  )

  admin_kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="✅ Алмазҳо равон карда шуданд",
                  callback_data=f"adm_done|{message.from_user.id}|{order_number}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан",
                  callback_data=f"adm_cancel|{message.from_user.id}|{order_number}",
              )
          ],
      ]
  )

  await bot.send_photo(
      chat_id=ADMIN_ID,
      photo=photo_id,
      caption=admin_caption,
      reply_markup=admin_kb,
      parse_mode="HTML",
  )

  user_kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ]
      ]
  )
  await message.answer(
      "✅ <b>Чеки шумо қабул шуд!</b>\n\n"
      "Администратор пардохтро месанҷад ва пас аз тасдиқ алмазҳо ба ҳисоби"
      " шумо ирсол мешаванд.\n\n"
      "Ташаккур барои харид! 💎",
      reply_markup=user_kb,
      parse_mode="HTML",
  )
  await state.clear()


@router.callback_query(F.data.startswith("adm_done|"))
async def admin_confirm_order(callback: CallbackQuery, bot: Bot):
  _, user_id, order_num = callback.data.split("|")

  user_kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="✍️ Гузоштани отзыв",
                  callback_data=f"leave_review|{order_num}",
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ],
      ]
  )

  user_text = (
      f"✅ <b>Алмази 💎 равон карда шуд</b>\n\n"
      f"Фармоиши шумо #{order_num} муваффақона иҷро шуд!\n\n"
      f"<b>Отзыв гузоред, хурсанд мешавем ❤️‍🩹</b>"
  )

  try:
    await bot.send_message(
        chat_id=int(user_id), text=user_text, reply_markup=user_kb, parse_mode="HTML"
    )
    await callback.message.edit_caption(
        caption=callback.message.caption
        + f"\n\n✅ <b>ИҶРО ШУД (Клиент уведомлен)!</b>",
        parse_mode="HTML",
    )
  except Exception as e:
    await callback.message.edit_caption(
        caption=callback.message.caption
        + f"\n\n⚠️ Ошибка отправки пользователю: {e}",
        parse_mode="HTML",
    )
  await callback.answer()


@router.callback_query(F.data.startswith("leave_review|"))
async def start_review_handler(callback: CallbackQuery, state: FSMContext):
  _, order_num = callback.data.split("|")
  await state.update_data(review_order_num=order_num)

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              )
          ]
      ]
  )
  text = (
      "✍️ <b>Отзиви худро нависед:</b>\n\n"
      "Мулоҳиза ё ташаккури худро нависед, он дар канали отзывҳои мо паҳн"
      " карда мешавад! ❤️‍🩹"
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await state.set_state(ReviewState.waiting_for_review_text)
  await callback.answer()


@router.message(ReviewState.waiting_for_review_text)
async def process_review_text(message: Message, state: FSMContext, bot: Bot):
  review_text = message.text.strip()

  user_display_name = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  channel_post_text = (
      f"<b>Отзыв DONAT SHOP</b>\n"
      f"⭐️ <b>Шарҳи харидор</b>\n\n"
      f"<blockquote>{review_text}</blockquote>\n\n"
      f"👤 <b>{user_display_name}</b>"
  )

  try:
    await bot.send_message(
        chat_id=REVIEWS_CHANNEL, text=channel_post_text, parse_mode="HTML"
    )
  except Exception as e:
    logging.error(f"Ошибка публикации отзыва в канал: {e}")

  admin_msg = (
      f"⭐️ <b>ОТЗЫВИ НАВ В КАНАЛЕ!</b>\n\n"
      f"👤 Харидор: {user_display_name}\n"
      f"💬 Матн: <i>«{review_text}»</i>"
  )
  await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ]
      ]
  )
  await message.answer(
      "❤️‍🩹 <b>Ташаккур барои отзиви шумо!</b>\n\n"
      "Отзиви шумо дар канали мо паҳн шуд! 💎",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await state.clear()


@router.callback_query(F.data.startswith("adm_cancel|"))
async def admin_cancel_order(callback: CallbackQuery, bot: Bot):
  _, user_id, order_num = callback.data.split("|")

  user_text = (
      f"❌ <b>Фармоиши шумо #{order_num} бекор карда шуд.</b>\n\nПардохт пайдо"
      " нашуд ё чеки нодуруст ирсол шуд. Барои маълумот ба дастгирӣ нависед."
  )

  try:
    await bot.send_message(chat_id=int(user_id), text=user_text, parse_mode="HTML")
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ <b>БЕКОР КАРДА ШУД!</b>",
        parse_mode="HTML",
    )
  except Exception as e:
    await callback.message.edit_caption(
        caption=callback.message.caption
        + f"\n\n⚠️ Ошибка отправки пользователю: {e}",
        parse_mode="HTML",
    )
  await callback.answer()


@router.callback_query(F.data == "menu_topup")
async def topup_menu(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="20.00 с.", callback_data="topup_val|20.00"
              ),
              InlineKeyboardButton(
                  text="50.00 с.", callback_data="topup_val|50.00"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="100.00 с.", callback_data="topup_val|100.00"
              ),
              InlineKeyboardButton(
                  text="200.00 с.", callback_data="topup_val|200.00"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="300.00 с.", callback_data="topup_val|300.00"
              ),
              InlineKeyboardButton(
                  text="500.00 с.", callback_data="topup_val|500.00"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="1000.00 с.", callback_data="topup_val|1000.00"
              ),
              InlineKeyboardButton(
                  text="2000.00 с.", callback_data="topup_val|2000.00"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="✏️ Маблағи дигар", callback_data="topup_custom"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ],
      ]
  )
  text = (
      "💳 <b>Пур кардани ҳисоб</b>\n\n"
      "Ҳисоби ҳозира: <b>0.00 с.</b>\n\n"
      "Маблағро интихоб кунед ё худатон нависед.\n"
      "<i>Аз 10.00 с. то 5000.00 с.</i>"
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await callback.answer()


@router.callback_query(F.data.startswith("topup_val|"))
async def topup_val_handler(callback: CallbackQuery, state: FSMContext):
  _, amount = callback.data.split("|")
  await state.update_data(
      price=amount, item_name="Пур кардани ҳисоб", nickname="Пур кардани ҳисоб"
  )
  await show_requisites_page(callback, state)


@router.callback_query(F.data == "topup_custom")
async def topup_custom_handler(callback: CallbackQuery, state: FSMContext):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              )
          ]
      ]
  )
  text = (
      "✏️ <b>Маблағи дигар</b>\n\n"
      "Илтимос, маблағи дилхоҳатонро нависед (аз 10 то 5000 сомонӣ):\n"
      "Намуна: <b>150</b>"
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await state.set_state(TopUpState.waiting_for_custom_amount)
  await callback.answer()


@router.message(TopUpState.waiting_for_custom_amount)
async def process_custom_amount(message: Message, state: FSMContext):
  val = message.text.strip().replace(",", ".")
  try:
    amount = float(val)
    if amount < 10 or amount > 5000:
      await message.answer(
          "❌ Маблағ бояд аз 10.00 с. то 5000.00 с. бошад! Дбора нависед:"
      )
      return
  except ValueError:
    await message.answer("❌ Илтимос, танҳо рақам нависед! Намуна: 150")
    return

  formatted_amount = f"{amount:.2f}"
  confirm_code = random.randint(1000, 9999)
  order_number = random.randint(1000, 9999)

  await state.update_data(
      price=formatted_amount,
      item_name="Пур кардани ҳисоб",
      nickname="Пур кардани ҳисоб",
      confirm_code=confirm_code,
      order_number=order_number,
  )

  dc_link, alif_link = get_payment_urls(formatted_amount)
  card_formatted = f"{DUSHANBE_CITY_CARD[:4]} {DUSHANBE_CITY_CARD[4:8]} {DUSHANBE_CITY_CARD[8:12]} {DUSHANBE_CITY_CARD[12:]}"

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(text="🏛 Душанбе Сити", url=dc_link),
              InlineKeyboardButton(text="📱 Alif Mobi", url=alif_link),
          ],
          [
              InlineKeyboardButton(
                  text="✅ Пардохт кардам", callback_data="ask_for_receipt"
              )
          ],
          [
              InlineKeyboardButton(
                  text="❌ Бекор кардан", callback_data="main_menu"
              )
          ],
      ]
  )
  text = (
      f"💳 <b>Реквизитҳо барои пур кардани ҳисоб</b>\n\n"
      f"🏛 <b>Душанбе Сити</b>\n"
      f"💳 Корт: <code>{card_formatted}</code>\n"
      f"👤 Ном: <b>{DUSHANBE_CITY_NAME}</b>\n\n"
      f"📱 <b>Alif Mobi</b>\n"
      f"🔢 Ҳисоб: <code>{ALIF_MOBI_ACC}</code>\n\n"
      f"💰 <b>Маблағ: {formatted_amount} с.</b>\n\n"
      f"🔑 <b>Коди тасдиқ: {confirm_code}</b>\n"
      f"<i>Ин кодро ҳатман дар «Шарҳ / Комментарий»-и ҳавола нависед.</i>\n\n"
      f"📄 Рақами пардохт: #{order_number}\n\n"
      f"Пас аз ҳавола тугмаи «✅ Пардохт кардам»-ро пахш кунед."
  )
  await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "menu_balance")
async def balance_handler(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="💰 Пур кардани ҳисоб", callback_data="menu_topup"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ],
      ]
  )
  text = (
      "💰 <b>Ҳисоби ман</b>\n\n"
      "💵 Маблағ: <b>0.00 с.</b>\n"
      "Ҳоло ҳаракат нест."
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await callback.answer()


@router.callback_query(F.data == "menu_support")
async def support_handler(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🟢 WhatsApp", url=f"https://wa.me/{WHATSAPP_NUMBER}"
              )
          ],
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ],
      ]
  )
  text = (
      "🛠 <b>Дастгири</b>\n\n"
      f"WhatsApp: <b>+{WHATSAPP_NUMBER}</b>\n\n"
      "<b>Кор мекунем:</b> ҳар рӯз, аз 08:00 то 00:00.\n"
      "Ҳангоми муроҷиат рақами фармоишро нависед — зудтар кўмак мекунем."
  )
  await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
  await callback.answer()


@router.callback_query(F.data.in_({"menu_top_buyers", "menu_my_orders"}))
async def stub_handler(callback: CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🏠 Менюи асосӣ", callback_data="main_menu"
              )
          ]
      ]
  )
  await callback.message.edit_text(
      "ℹ️ <b>Ин бахш ба наздикӣ фаъол мешавад.</b>",
      reply_markup=kb,
      parse_mode="HTML",
  )
  await callback.answer()


async def main():
  logging.basicConfig(level=logging.INFO)
  bot = Bot(token=BOT_TOKEN)
  dp = Dispatcher()
  dp.include_router(router)
  print("Бот DONAT SHOP 💎🇹🇯 запущен и работает корректно!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
