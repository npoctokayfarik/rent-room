from pathlib import Path
from uuid import uuid4

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, select

from app.bot.keyboards import (
    amenities_keyboard,
    cancel_keyboard,
    district_keyboard,
    edit_amenities_keyboard,
    edit_district_keyboard,
    edit_photos_keyboard,
    edit_property_menu_keyboard,
    photos_keyboard,
    property_actions_keyboard,
    start_keyboard,
)
from app.bot.states import EditPropertyForm, RentOutForm
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.models.property import Property

router = Router()


def _to_int(value: str) -> int | None:
    try:
        result = int(value.strip())
        return result if result >= 0 else None
    except ValueError:
        return None


def _preview(item: Property) -> str:
    return (
        f"#{item.id} | {item.title}\n"
        f"{item.district}, {item.address}\n"
        f"Комнат: {item.rooms} | Этаж: {item.floor}/{item.floors_total}\n"
        f"Цена: {item.price}\n"
        f"Контакт: {item.contact_info or 'не указан'}\n"
        f"Условия: {', '.join(item.amenities) if item.amenities else 'не указаны'}\n"
        f"Фото: {len(item.images)} шт."
    )


async def _download_photo_to_uploads(bot: Bot, file_id: str) -> str:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    tg_file = await bot.get_file(file_id)
    suffix = Path(tg_file.file_path or "").suffix or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    destination = upload_dir / filename
    await bot.download_file(tg_file.file_path, destination=destination)
    return f"/uploads/{filename}"


async def _show_edit_menu(message: Message, user_id: int, property_id: int) -> None:
    async with async_session_maker() as session:
        stmt = select(Property).where(Property.id == property_id, Property.owner_tg_id == user_id)
        item = (await session.execute(stmt)).scalar_one_or_none()
    if not item:
        await message.answer("Квартира не найдена.")
        return

    await message.answer(
        "Редактирование квартиры:\n\n" + _preview(item),
        reply_markup=edit_property_menu_keyboard(),
    )


async def _update_owned_property(user_id: int, property_id: int, **updates: object) -> bool:
    async with async_session_maker() as session:
        stmt = select(Property).where(Property.id == property_id, Property.owner_tg_id == user_id)
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            return False
        for key, value in updates.items():
            setattr(item, key, value)
        await session.commit()
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    settings = get_settings()
    await message.answer("Выберите действие:", reply_markup=start_keyboard(settings.mini_app_url))


@router.message(F.text == "Сдать в аренду")
async def rent_out_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(amenities=[], images=[])
    await state.set_state(RentOutForm.district)
    await message.answer("Район?", reply_markup=district_keyboard())


@router.callback_query(F.data == "cancel")
@router.message(F.text == "Отменить")
async def cancel_flow(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    settings = get_settings()
    if isinstance(event, CallbackQuery):
        await event.answer("Отменено")
        if event.message:
            await event.message.answer("Действие отменено.", reply_markup=start_keyboard(settings.mini_app_url))
    else:
        await event.answer("Действие отменено.", reply_markup=start_keyboard(settings.mini_app_url))


@router.callback_query(RentOutForm.district, F.data.startswith("district:"))
async def choose_district(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":", 1)[1]
    await state.update_data(district=district)
    await state.set_state(RentOutForm.address)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Адрес:", reply_markup=cancel_keyboard())


@router.message(RentOutForm.address, F.text)
async def ask_rooms(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await state.set_state(RentOutForm.rooms)
    await message.answer("Сколько комнат?")


@router.message(RentOutForm.rooms, F.text)
async def ask_floor(message: Message, state: FSMContext) -> None:
    rooms = _to_int(message.text)
    if rooms is None or rooms <= 0:
        await message.answer("Введите корректное число комнат.")
        return
    await state.update_data(rooms=rooms)
    await state.set_state(RentOutForm.floor)
    await message.answer("Этаж?")


@router.message(RentOutForm.floor, F.text)
async def ask_floors_total(message: Message, state: FSMContext) -> None:
    floor = _to_int(message.text)
    if floor is None:
        await message.answer("Введите корректный этаж.")
        return
    await state.update_data(floor=floor)
    await state.set_state(RentOutForm.floors_total)
    await message.answer("Этажность всего дома?")


@router.message(RentOutForm.floors_total, F.text)
async def ask_amenities(message: Message, state: FSMContext) -> None:
    floors_total = _to_int(message.text)
    data = await state.get_data()
    floor = int(data.get("floor", 0))
    if floors_total is None or floors_total <= 0 or floor > floors_total:
        await message.answer("Введите корректную этажность (не меньше текущего этажа).")
        return
    await state.update_data(floors_total=floors_total)
    await state.set_state(RentOutForm.amenities)
    selected = data.get("amenities", [])
    await message.answer("Условия:", reply_markup=amenities_keyboard(selected))


@router.callback_query(RentOutForm.amenities, F.data.startswith("amenity:"))
async def toggle_amenity(callback: CallbackQuery, state: FSMContext) -> None:
    amenity = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected = set(data.get("amenities", []))
    if amenity in selected:
        selected.remove(amenity)
    else:
        selected.add(amenity)
    updated = sorted(selected)
    await state.update_data(amenities=updated)
    await callback.answer("Обновлено")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=amenities_keyboard(updated))


@router.callback_query(RentOutForm.amenities, F.data == "amenities:done")
async def amenities_done(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RentOutForm.price)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Цена:")


@router.message(RentOutForm.price, F.text)
async def ask_photos(message: Message, state: FSMContext) -> None:
    price = _to_int(message.text)
    if price is None or price <= 0:
        await message.answer("Введите корректную цену.")
        return
    await state.update_data(price=price)
    await state.set_state(RentOutForm.photos)
    await message.answer("ФОТО\nОтправьте фото (можно несколько) и нажмите Готово.", reply_markup=photos_keyboard())


@router.message(RentOutForm.photos, F.photo)
async def collect_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        return
    photo = message.photo[-1]
    data = await state.get_data()
    images = data.get("images", [])
    images.append(photo.file_id)
    await state.update_data(images=images)
    await message.answer(f"Фото добавлено. Сейчас: {len(images)}")


@router.callback_query(RentOutForm.photos, F.data == "photos:done")
async def ask_contact_info(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("images", []):
        await callback.answer("Добавьте хотя бы одно фото", show_alert=True)
        return

    await state.set_state(RentOutForm.contact_info)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите контактные данные (телефон или @username):")


@router.message(RentOutForm.contact_info, F.text)
async def save_property(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    contact_info = message.text.strip()
    if len(contact_info) < 4:
        await message.answer("Введите корректные контактные данные.")
        return

    file_ids = data.get("images", [])
    image_urls: list[str] = []
    for file_id in file_ids:
        image_url = await _download_photo_to_uploads(message.bot, file_id)
        image_urls.append(image_url)

    rooms = int(data["rooms"])
    district = str(data["district"])
    title = f"{rooms}-комн квартира, {district}"

    async with async_session_maker() as session:
        item = Property(
            owner_tg_id=message.from_user.id,
            title=title,
            description="",
            district=district,
            address=str(data["address"]),
            type="apartment",
            status="active",
            price=int(data["price"]),
            rooms=rooms,
            floor=int(data["floor"]),
            floors_total=int(data["floors_total"]),
            contact_info=contact_info,
            amenities=list(data.get("amenities", [])),
            images=image_urls,
        )
        session.add(item)
        await session.commit()

    await state.clear()
    settings = get_settings()
    await message.answer("Квартира опубликована.", reply_markup=start_keyboard(settings.mini_app_url))


@router.message(F.text == "Мои Квартиры")
async def my_properties(message: Message) -> None:
    async with async_session_maker() as session:
        stmt = select(Property).where(Property.owner_tg_id == message.from_user.id).order_by(Property.created_at.desc())
        items = (await session.execute(stmt)).scalars().all()

    if not items:
        await message.answer("Вы еще ничего не добавляли")
        return

    for item in items:
        await message.answer(_preview(item), reply_markup=property_actions_keyboard(item.id))


@router.callback_query(F.data.startswith("delete:"))
async def delete_property_callback(callback: CallbackQuery) -> None:
    property_id = int(callback.data.split(":", 1)[1])
    async with async_session_maker() as session:
        stmt = delete(Property).where(Property.id == property_id, Property.owner_tg_id == callback.from_user.id)
        result = await session.execute(stmt)
        await session.commit()
    if result.rowcount:
        await callback.answer("Удалено")
        if callback.message:
            await callback.message.answer("Квартира удалена.")
    else:
        await callback.answer("Не найдено", show_alert=True)


@router.callback_query(F.data.startswith("edit:"))
async def edit_property_start(callback: CallbackQuery, state: FSMContext) -> None:
    property_id = int(callback.data.split(":", 1)[1])
    await state.set_state(EditPropertyForm.menu)
    await state.update_data(edit_property_id=property_id)
    await callback.answer()
    if callback.message:
        await _show_edit_menu(callback.message, callback.from_user.id, property_id)


@router.callback_query(EditPropertyForm.menu, F.data == "edit_done")
async def edit_property_done(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Сохранено")
    if callback.message:
        settings = get_settings()
        await callback.message.answer("Редактирование завершено.", reply_markup=start_keyboard(settings.mini_app_url))


@router.callback_query(EditPropertyForm.menu, F.data.startswith("edit_field:"))
async def edit_select_field(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":", 1)[1]
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    await callback.answer()

    if not callback.message:
        return

    if field == "district":
        await state.set_state(EditPropertyForm.district)
        await callback.message.answer("Выберите район:", reply_markup=edit_district_keyboard())
    elif field == "amenities":
        async with async_session_maker() as session:
            stmt = select(Property).where(Property.id == property_id, Property.owner_tg_id == callback.from_user.id)
            item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            await state.clear()
            await callback.message.answer("Квартира не найдена.")
            return
        await state.set_state(EditPropertyForm.amenities)
        await state.update_data(edit_amenities=list(item.amenities or []))
        await callback.message.answer(
            "Выберите условия:",
            reply_markup=edit_amenities_keyboard(list(item.amenities or [])),
        )
    elif field == "photos":
        async with async_session_maker() as session:
            stmt = select(Property).where(Property.id == property_id, Property.owner_tg_id == callback.from_user.id)
            item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            await state.clear()
            await callback.message.answer("Квартира не найдена.")
            return
        await state.set_state(EditPropertyForm.photos)
        await state.update_data(edit_images=list(item.images or []))
        await callback.message.answer(
            "Отправьте новые фото. Можно добавить к текущим, очистить или завершить.",
            reply_markup=edit_photos_keyboard(),
        )
    elif field == "title":
        await state.set_state(EditPropertyForm.title)
        await callback.message.answer("Введите новый заголовок:")
    elif field == "description":
        await state.set_state(EditPropertyForm.description)
        await callback.message.answer("Введите новое описание:")
    elif field == "address":
        await state.set_state(EditPropertyForm.address)
        await callback.message.answer("Введите новый адрес:")
    elif field == "rooms":
        await state.set_state(EditPropertyForm.rooms)
        await callback.message.answer("Введите количество комнат:")
    elif field == "floor":
        await state.set_state(EditPropertyForm.floor)
        await callback.message.answer("Введите этаж:")
    elif field == "floors_total":
        await state.set_state(EditPropertyForm.floors_total)
        await callback.message.answer("Введите этажность дома:")
    elif field == "contact_info":
        await state.set_state(EditPropertyForm.contact_info)
        await callback.message.answer("Введите новые контактные данные:")
    elif field == "price":
        await state.set_state(EditPropertyForm.price)
        await callback.message.answer("Введите новую цену:")


@router.callback_query(EditPropertyForm.district, F.data.startswith("edit_district:"))
async def edit_district_finish(callback: CallbackQuery, state: FSMContext) -> None:
    district = callback.data.split(":", 1)[1]
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(callback.from_user.id, property_id, district=district)
    if not ok:
        await state.clear()
        await callback.answer("Не найдено", show_alert=True)
        return

    await state.set_state(EditPropertyForm.menu)
    await callback.answer("Район обновлен")
    if callback.message:
        await _show_edit_menu(callback.message, callback.from_user.id, property_id)


@router.callback_query(EditPropertyForm.amenities, F.data.startswith("edit_amenity:"))
async def edit_amenities_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    amenity = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected = set(data.get("edit_amenities", []))
    if amenity in selected:
        selected.remove(amenity)
    else:
        selected.add(amenity)
    updated = sorted(selected)
    await state.update_data(edit_amenities=updated)
    await callback.answer("Обновлено")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=edit_amenities_keyboard(updated))


@router.callback_query(EditPropertyForm.amenities, F.data == "edit_amenities:done")
async def edit_amenities_finish(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    updated = list(data.get("edit_amenities", []))
    ok = await _update_owned_property(callback.from_user.id, property_id, amenities=updated)
    if not ok:
        await state.clear()
        await callback.answer("Не найдено", show_alert=True)
        return

    await state.set_state(EditPropertyForm.menu)
    await callback.answer("Условия обновлены")
    if callback.message:
        await _show_edit_menu(callback.message, callback.from_user.id, property_id)


@router.message(EditPropertyForm.photos, F.photo)
async def edit_photos_collect(message: Message, state: FSMContext) -> None:
    if not message.photo:
        return

    data = await state.get_data()
    images = list(data.get("edit_images", []))
    photo = message.photo[-1]
    image_url = await _download_photo_to_uploads(message.bot, photo.file_id)
    images.append(image_url)
    await state.update_data(edit_images=images)
    await message.answer(f"Фото добавлено. Сейчас: {len(images)}")


@router.callback_query(EditPropertyForm.photos, F.data == "edit_photos:clear")
async def edit_photos_clear(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(edit_images=[])
    await callback.answer("Список фото очищен")


@router.callback_query(EditPropertyForm.photos, F.data == "edit_photos:done")
async def edit_photos_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    images = list(data.get("edit_images", []))
    ok = await _update_owned_property(callback.from_user.id, property_id, images=images)
    if not ok:
        await state.clear()
        await callback.answer("Не найдено", show_alert=True)
        return

    await state.set_state(EditPropertyForm.menu)
    await callback.answer("Фото обновлены")
    if callback.message:
        await _show_edit_menu(callback.message, callback.from_user.id, property_id)


@router.message(EditPropertyForm.title, F.text)
async def edit_title_finish(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if len(title) < 3:
        await message.answer("Минимум 3 символа.")
        return
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(message.from_user.id, property_id, title=title)
    if not ok:
        await state.clear()
        await message.answer("Квартира не найдена.")
        return
    await state.set_state(EditPropertyForm.menu)
    await message.answer("Заголовок обновлен.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.description, F.text)
async def edit_description_finish(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(message.from_user.id, property_id, description=message.text.strip())
    if not ok:
        await state.clear()
        await message.answer("Квартира не найдена.")
        return
    await state.set_state(EditPropertyForm.menu)
    await message.answer("Описание обновлено.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.address, F.text)
async def edit_address_finish(message: Message, state: FSMContext) -> None:
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("Слишком короткий адрес.")
        return
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(message.from_user.id, property_id, address=address)
    if not ok:
        await state.clear()
        await message.answer("Квартира не найдена.")
        return
    await state.set_state(EditPropertyForm.menu)
    await message.answer("Адрес обновлен.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.rooms, F.text)
async def edit_rooms_finish(message: Message, state: FSMContext) -> None:
    rooms = _to_int(message.text)
    if rooms is None or rooms <= 0:
        await message.answer("Введите корректное число комнат.")
        return
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(message.from_user.id, property_id, rooms=rooms)
    if not ok:
        await state.clear()
        await message.answer("Квартира не найдена.")
        return
    await state.set_state(EditPropertyForm.menu)
    await message.answer("Количество комнат обновлено.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.floor, F.text)
async def edit_floor_finish(message: Message, state: FSMContext) -> None:
    floor = _to_int(message.text)
    if floor is None:
        await message.answer("Введите корректный этаж.")
        return

    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    async with async_session_maker() as session:
        stmt = select(Property).where(Property.id == property_id, Property.owner_tg_id == message.from_user.id)
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            await state.clear()
            await message.answer("Квартира не найдена.")
            return
        if floor > item.floors_total:
            await message.answer("Этаж не может быть выше этажности дома.")
            return
        item.floor = floor
        await session.commit()

    await state.set_state(EditPropertyForm.menu)
    await message.answer("Этаж обновлен.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.floors_total, F.text)
async def edit_floors_total_finish(message: Message, state: FSMContext) -> None:
    floors_total = _to_int(message.text)
    if floors_total is None or floors_total <= 0:
        await message.answer("Введите корректную этажность.")
        return

    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    async with async_session_maker() as session:
        stmt = select(Property).where(Property.id == property_id, Property.owner_tg_id == message.from_user.id)
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            await state.clear()
            await message.answer("Квартира не найдена.")
            return
        if floors_total < item.floor:
            await message.answer("Этажность не может быть меньше текущего этажа.")
            return
        item.floors_total = floors_total
        await session.commit()

    await state.set_state(EditPropertyForm.menu)
    await message.answer("Этажность обновлена.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.contact_info, F.text)
async def edit_contact_info_finish(message: Message, state: FSMContext) -> None:
    contact_info = message.text.strip()
    if len(contact_info) < 4:
        await message.answer("Введите корректные контактные данные.")
        return
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(message.from_user.id, property_id, contact_info=contact_info)
    if not ok:
        await state.clear()
        await message.answer("Квартира не найдена.")
        return
    await state.set_state(EditPropertyForm.menu)
    await message.answer("Контакты обновлены.")
    await _show_edit_menu(message, message.from_user.id, property_id)


@router.message(EditPropertyForm.price, F.text)
async def edit_price_finish(message: Message, state: FSMContext) -> None:
    price = _to_int(message.text)
    if price is None or price <= 0:
        await message.answer("Введите корректную цену.")
        return
    data = await state.get_data()
    property_id = int(data["edit_property_id"])
    ok = await _update_owned_property(message.from_user.id, property_id, price=price)
    if not ok:
        await state.clear()
        await message.answer("Квартира не найдена.")
        return
    await state.set_state(EditPropertyForm.menu)
    await message.answer("Цена обновлена.")
    await _show_edit_menu(message, message.from_user.id, property_id)
