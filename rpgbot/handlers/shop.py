from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
        for item in items:
            (
                item_id,
                name,
                type_,
                power,
                max_count,
                price_gold,
                price_diamonds,
                usable_in_fight,
                usable_in_profile,
            ) = item

            text += f"\n{name} ({type_}) — {price_gold}💰 / {price_diamonds}💎"
            kb.button(text=f"Купить {name}", callback_data=f"shop:buy:{item_id}")

    kb.button(text="💎 Купить алмазы (донат)", callback_data="shop:donate")
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("shop:buy:"))
async def buy_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split(":")[2])
    player = player_repo.get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйся!", show_alert=True)
        return

    player_class = player[2]
    item = item_repo.get_item(item_id)
    if not item:
        await callback.answer("Предмет не найден!", show_alert=True)
        return

    _, name, item_type, power, max_count, price_gold, price_diamonds, _, _ = item

    if player_class == "warrior" and item_type in ("weapon_mage", "weapon_rogue"):
        await callback.answer("⚔️ Воин не может купить этот предмет!", show_alert=True)
        return
    if player_class == "mage" and item_type in ("weapon_warrior", "weapon_rogue"):
        await callback.answer("🔮 Маг не может купить этот предмет!", show_alert=True)
        return
    if player_class == "rogue" and item_type in ("weapon_warrior", "weapon_mage"):
        await callback.answer(
            "🗡️ Разбойник не может купить этот предмет!", show_alert=True
        )
        return

    if player[10] < price_gold:
        await callback.answer("Недостаточно золота!", show_alert=True)
        return

    db.execute("UPDATE players SET gold = gold - ? WHERE id=?", (price_gold, player[0]))
    inventory_repo.add_item_to_player(player[0], item_id, 1)

    await callback.answer(f"✅ Куплен предмет: {name}", show_alert=True)


# ==========================
# СИСТЕМА ДОНАТОВ REDSYS
# ==========================


@router.callback_query(F.data == "shop:donate")
async def shop_donate(callback: types.CallbackQuery):
    await callback.message.answer_invoice(
        title="💎 Алмазы",
        description="Пакет 100 алмазов",
        payload=f"diamonds:{callback.from_user.id}:100",
        provider_token=PAYMASTER_PROVIDER_TOKEN,
        currency="USD",
        prices=[types.LabeledPrice(label="100 алмазов", amount=500)],  # $5.00
    )


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(msg: types.Message):
    payload = msg.successful_payment.invoice_payload
    if payload.startswith("diamonds:"):
        _, player_id, diamonds = payload.split(":")
        player_repo.update_diamonds(int(player_id), int(diamonds))
        await msg.answer(f"✅ Оплата прошла! Зачислено {diamonds}💎")
