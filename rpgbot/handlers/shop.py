from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from utils.db import Database, ItemRepo, InventoryRepo, PlayerRepo
from config import DB_PATH, PAYMASTER_PROVIDER_TOKEN

router = Router()
db = Database(DB_PATH)
item_repo = ItemRepo(db)
inventory_repo = InventoryRepo(db)
player_repo = PlayerRepo(db)


@router.callback_query(F.data == "shop:menu")
async def shop_menu(callback: types.CallbackQuery):
    items = item_repo.list_items()
    kb = InlineKeyboardBuilder()
    text = "🛒 Магазин:\n"

    if items:
        for item_id, name, type_, power, max_count, price_gold, price_diamonds in items:
            text += f"\n{name} ({type_}) — {price_gold}💰 / {price_diamonds}💎"
            kb.button(text=f"Купить {name}", callback_data=f"shop:buy:{item_id}")

    # кнопка доната
    kb.button(text="💎 Купить алмазы (донат)", callback_data="shop:donate")
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("shop:buy:"))
async def shop_buy(callback: types.CallbackQuery):
    item_id = int(callback.data.split(":")[2])
    player = player_repo.get_player(callback.from_user.id)
    item = item_repo.get_item(item_id)

    if not item:
        await callback.answer("Такого предмета нет!", show_alert=True)
        return

    _, name, type_, power, max_count, price_gold, price_diamonds = item

    if player[10] < price_gold:  # gold
        await callback.answer("Недостаточно золота!", show_alert=True)
        return

    # списываем золото
    player_repo.update_gold(player[0], -price_gold)
    # добавляем предмет
    inventory_repo.add_item_to_player(player[0], item_id, 1)

    await callback.message.edit_text(f"✅ Ты купил {name} за {price_gold}💰!")


# ==========================
# СИСТЕМА ДОНАТОВ PAYMASTER
# ==========================


@router.callback_query(F.data == "shop:donate")
async def shop_donate(callback: types.CallbackQuery):
    # Пример: продаём 100 алмазов за 5$
    await callback.message.answer_invoice(
        title="💎 Алмазы",
        description="Пакет 100 алмазов",
        payload=f"diamonds:{callback.from_user.id}:100",  # payload для идентификации
        provider_token=PAYMASTER_PROVIDER_TOKEN,
        currency="USD",
        prices=[types.LabeledPrice(label="100 алмазов", amount=500)],  # 500 = $5.00
    )


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    # подтверждаем оплату
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(msg: types.Message):
    payload = msg.successful_payment.invoice_payload
    if payload.startswith("diamonds:"):
        _, player_id, diamonds = payload.split(":")
        player_repo.update_diamonds(int(player_id), int(diamonds))
        await msg.answer(f"✅ Оплата прошла! Зачислено {diamonds}💎")
