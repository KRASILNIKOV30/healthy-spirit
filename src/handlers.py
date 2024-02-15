import config
from misc import dp, bot
from aiogram.filters import Command
from aiogram.types import Message
import requests
import text
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
import os
from api import mark_visit
from kb import make_today_button


class Uploading(StatesGroup):
    waiting_date = State()
    waiting_photo = State()


@dp.message(default_state, Command("start"))
async def start_handler(msg: Message):
    await msg.answer(text.greet.format(name=msg.from_user.full_name))


@dp.message(Command("upload"))
async def upload_handler(msg: Message, state: FSMContext):
    await msg.answer(
        text="Отправьте дату вида 1-Jan-2024",
        reply_markup=make_today_button())
    await state.set_state(Uploading.waiting_date)


@dp.message(Uploading.waiting_date)
async def date_handler(msg: Message, state: FSMContext):
    if msg.text == "Сегодня":
        await state.update_data(date=None)
    else:
        await state.update_data(date=msg.text)
    await state.set_state(Uploading.waiting_photo)


@dp.message(Uploading.waiting_photo)
async def document_handler(msg: Message, state: FSMContext):
    file = await bot.get_file(msg.document.file_id)
    response = requests.get("https://api.telegram.org/file/bot" + config.BOT_TOKEN + "/" + file.file_path)
    with open("../photo.jpg", "wb") as f:
        f.write(response.content)
    user_data = await state.get_data()
    try:
        healthy_spirits = mark_visit(user_data['date'])
        healthy_spirits_recognized = len(healthy_spirits)
        healthy_spirits_seen = healthy_spirits_recognized - healthy_spirits.count("UNDEFINED")
        message = ("Люди, посетившие зарядку\n"
                   + healthy_spirits
                   + "\n"
                   + "Распознано: "
                   + healthy_spirits_seen
                   + "/"
                   + healthy_spirits_recognized)
        await msg.answer(message)
    except ValueError:
        await msg.answer("Возникла ошибка, попробуйте ещё раз ")
    os.remove("../photo.jpg")
