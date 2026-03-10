
from src import text
from src.kb import make_upload_button
from aiogram.filters import Command
from aiogram.fsm.state import default_state
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src import config
from src.misc import dp
from .document import Uploading



@dp.message(default_state, Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    if msg.from_user.id not in config.ADMIN_LIST:
        await msg.answer("Вы не являетесь обладателем здорового духа")
        return
    await msg.answer(
        text.greet.format(name=msg.from_user.full_name) +
        "\n\nОтправьте групповое фото (как документ), чтобы отметить посещаемость.",
        reply_markup=make_upload_button()
    )
    await state.set_state(Uploading.waiting_photo)