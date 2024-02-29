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
from kb import make_today_button, make_upload_button
from draw import draw_border_on_faces
from aiogram.types import FSInputFile


class Uploading(StatesGroup):
    waiting_date = State()
    waiting_photo = State()
    waiting_upload = State()


@dp.message(default_state, Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    if msg.from_user.id not in config.ADMIN_LIST:
        return
    await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=make_upload_button())
    await state.set_state(Uploading.waiting_upload)


@dp.message(Uploading.waiting_upload)
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
    await msg.answer("Отправьте фото для распознания")
    await state.set_state(Uploading.waiting_photo)


@dp.message(Uploading.waiting_photo)
async def document_handler(msg: Message, state: FSMContext):
    file = await bot.get_file(msg.document.file_id)
    response = requests.get("https://api.telegram.org/file/bot" + config.BOT_TOKEN + "/" + file.file_path)
    with open("../photo.jpg", "wb") as f:
        f.write(response.content)
    user_data = await state.get_data()
    try:
        healthy_spirits_list = mark_visit(user_data['date'])
        healthy_spirits_string = ''
        undefined_counter = 0
        for healthy_spirit in healthy_spirits_list:
            if healthy_spirit["person"] == 'UNDEFINED':
                undefined_counter += 1
                continue
            healthy_spirits_string += healthy_spirit["person"] + "\n"
        healthy_spirits_recognized = len(healthy_spirits_list)
        healthy_spirits_seen = healthy_spirits_recognized - undefined_counter
        message = ("Люди, посетившие зарядку:\n\n"
                   + healthy_spirits_string
                   + "\n"
                   + "Распознано: "
                   + str(healthy_spirits_seen)
                   + "/"
                   + str(healthy_spirits_recognized))
        await msg.answer(message)
        draw_border_on_faces(healthy_spirits_list)
        new_photo = FSInputFile("../new_photo.jpg")
        await msg.answer_photo(new_photo)
    except ValueError:
        await msg.answer("Возникла ошибка, попробуйте ещё раз ")
    await state.set_state(Uploading.waiting_upload)
    os.remove("../new_photo.jpg")
    os.remove("../photo.jpg")
