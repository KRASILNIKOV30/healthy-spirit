from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_today_button() -> ReplyKeyboardMarkup:
    button = KeyboardButton(text="Сегодня")
    return ReplyKeyboardMarkup(keyboard=[button], resize_keyboard=True)
