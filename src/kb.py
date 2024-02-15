from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_today_button() -> ReplyKeyboardMarkup:
    button = KeyboardButton(text="Сегодня")
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True)


def make_upload_button() -> ReplyKeyboardMarkup:
    button = KeyboardButton(text="Отметить здоровый дух")
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
