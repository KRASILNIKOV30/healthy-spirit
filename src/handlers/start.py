from aiogram.filters import Command
from aiogram.fsm.state import default_state
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src import config, text
from src.misc import dp  # ← ИМПОРТИРУЕМ ТОТ САМЫЙ ГЛОБАЛЬНЫЙ dp
from .document import Uploading

@dp.message(default_state, Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    if msg.from_user.id not in config.ADMIN_LIST:
        await msg.answer("Вы не являетесь обладателем здорового духа")
        return
    await msg.answer("Привет! Отправьте групповое фото.")
    await state.set_state(Uploading.waiting_photo)