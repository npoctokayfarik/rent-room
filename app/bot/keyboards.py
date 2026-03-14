#aiogram keyboard docs page 43
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

DISTRICTS = [
    "Алмазарский Район",
    "Бектемирский Район",
    "Мирабадский Район",
    "Мирзо-Улугбекский Район",
    "Сергелийский Район",
    "Учтепинский Район",
    "Чиланзарский Район",
    "Шайхантахурский Район",
    "Юнусабадский Район",
    "Яккасарайский Район",
    "Янгихайотский Район",
    "Яшнабадский Район",
]

AMENITIES = [
    "Шкаф",
    "Кровать",
    "Холодильник",
    "Стиралка",
    "Wi-fi",
    "Кондиционер",
    "Микроволновка",
    "Пылесос",
    "Утюг",
]


def start_keyboard(mini_app_url: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Арендовать квартиру", web_app=WebAppInfo(url=mini_app_url))],
            [KeyboardButton(text="Сдать в аренду"), KeyboardButton(text="Мои Квартиры")],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отменить")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def district_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for district in DISTRICTS:
        builder.button(text=district, callback_data=f"district:{district}")
    builder.button(text="Отменить", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def amenities_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amenity in AMENITIES:
        marker = "✅ " if amenity in selected else ""
        builder.button(text=f"{marker}{amenity}", callback_data=f"amenity:{amenity}")
    builder.button(text="Готово", callback_data="amenities:done")
    builder.button(text="Отменить", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def photos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Готово", callback_data="photos:done")],
            [InlineKeyboardButton(text="Отменить", callback_data="cancel")],
        ]
    )


def property_actions_keyboard(property_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Редактировать", callback_data=f"edit:{property_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete:{property_id}")],
        ]
    )


def edit_property_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заголовок", callback_data="edit_field:title")],
            [InlineKeyboardButton(text="Описание", callback_data="edit_field:description")],
            [InlineKeyboardButton(text="Район", callback_data="edit_field:district")],
            [InlineKeyboardButton(text="Адрес", callback_data="edit_field:address")],
            [InlineKeyboardButton(text="Комнаты", callback_data="edit_field:rooms")],
            [InlineKeyboardButton(text="Этаж", callback_data="edit_field:floor")],
            [InlineKeyboardButton(text="Этажность", callback_data="edit_field:floors_total")],
            [InlineKeyboardButton(text="Контакты", callback_data="edit_field:contact_info")],
            [InlineKeyboardButton(text="Условия", callback_data="edit_field:amenities")],
            [InlineKeyboardButton(text="Цена", callback_data="edit_field:price")],
            [InlineKeyboardButton(text="Фото", callback_data="edit_field:photos")],
            [InlineKeyboardButton(text="Готово", callback_data="edit_done")],
        ]
    )


def edit_district_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for district in DISTRICTS:
        builder.button(text=district, callback_data=f"edit_district:{district}")
    builder.button(text="Отменить", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def edit_amenities_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amenity in AMENITIES:
        marker = "✅ " if amenity in selected else ""
        builder.button(text=f"{marker}{amenity}", callback_data=f"edit_amenity:{amenity}")
    builder.button(text="Готово", callback_data="edit_amenities:done")
    builder.button(text="Отменить", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def edit_photos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Очистить фото", callback_data="edit_photos:clear")],
            [InlineKeyboardButton(text="Готово", callback_data="edit_photos:done")],
            [InlineKeyboardButton(text="Отменить", callback_data="cancel")],
        ]
    )
