from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_upload_button() -> ReplyKeyboardMarkup:
    button = KeyboardButton(text="Отметить здоровый дух")
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
