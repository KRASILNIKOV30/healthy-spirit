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
from kb import make_upload_button
from draw import draw_border_on_faces
from aiogram.types import FSInputFile

from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
import pillow_heif


class Uploading(StatesGroup):
    waiting_photo = State()


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


@dp.message(Uploading.waiting_photo)
async def document_handler(msg: Message, state: FSMContext):
    if not msg.document:
        await msg.answer("Пожалуйста, отправьте фото именно как документ (файл), чтобы сохранились метаданные.")
        return
    
    file = await bot.get_file(msg.document.file_id)
    ext = file.file_path.split('.')[-1].lower()
    
    original_photo_path = f"./photo.{ext}"
    response = requests.get("https://api.telegram.org/file/bot" + config.BOT_TOKEN + "/" + file.file_path)
    with open(original_photo_path, "wb") as f:
        f.write(response.content)

    processing_photo_path = original_photo_path
    
    if ext in ('heic', 'heif'):
        await msg.answer("Обнаружен формат HEIC. Конвертирую в JPEG...")
        
        jpeg_path = "./photo.jpg"
        
        heif_file = pillow_heif.read_heif(original_photo_path)
        
        image = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
        )

        exif_data = heif_file.info.get('exif', None)
        image.save(jpeg_path, "JPEG", quality=95, exif=exif_data)
        processing_photo_path = jpeg_path     
        os.remove(original_photo_path)

    photo_date = None
    try:
        image = Image.open(processing_photo_path)
        exif_data = image.getexif()

        if exif_data:
            date_str = None
            possible_date_tags = [36867, 36868, 306]

            for tag_code in possible_date_tags:
                if tag_code in exif_data:
                    date_str = exif_data[tag_code]
                    break 

            if date_str:
                if isinstance(date_str, bytes):
                    date_str = date_str.decode('utf-8', 'ignore').strip()
                
                dt_object = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

                if os.name == 'nt':
                    photo_date = dt_object.strftime('%#d-%b-%Y')
                else:
                    photo_date = dt_object.strftime('%-d-%b-%Y')

                await msg.answer(f"Дата определена из фото: {photo_date}")
            else:
                await msg.answer("Не удалось найти дату в метаданных фото. Использую сегодняшнюю дату.")
        else:
            await msg.answer("Метаданные (EXIF) в фото отсутствуют. Использую сегодняшнюю дату.")

    except Exception as e:
        print(f"Ошибка при чтении EXIF: {e}")
        await msg.answer(f"Ошибка при чтении метаданных фото. Использую сегодняшнюю дату.")

    await msg.answer("Фото получено, начинаю распознавание...")

    healthy_spirits_list = mark_visit(processing_photo_path, photo_date)
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

    new_photo_path = draw_border_on_faces(healthy_spirits_list, processing_photo_path)
    new_photo = FSInputFile(new_photo_path)
    await msg.answer_photo(new_photo)

    os.remove(new_photo_path)
    os.remove(processing_photo_path)

    await msg.answer("Обработка завершена. Можете отправить следующее фото.")
    await state.set_state(Uploading.waiting_photo)
