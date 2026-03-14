#Дочерная фунция
from aiogram.fsm.state import State, StatesGroup


class RentOutForm(StatesGroup):
    district = State()
    address = State()
    rooms = State()
    floor = State()
    floors_total = State()
    amenities = State()
    price = State()
    photos = State()
    contact_info = State()


class EditPropertyForm(StatesGroup):
    menu = State()
    title = State()
    description = State()
    district = State()
    address = State()
    rooms = State()
    floor = State()
    floors_total = State()
    contact_info = State()
    amenities = State()
    price = State()
    photos = State()
