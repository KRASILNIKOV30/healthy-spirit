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
from aiogram.types import FSInputFile, Document

from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from datetime import datetime
from typing import Optional, Tuple, List
import pillow_heif

pillow_heif.register_heif_opener()

class Uploading(StatesGroup):
    waiting_photo = State()
    waiting_date = State()

async def download_photo(document: Document) -> Tuple[str, str]:
    """Скачивает фото из сообщения и возвращает путь и расширение."""
    file = await bot.get_file(document.file_id)
    ext = file.file_path.split('.')[-1].lower()
    
    photo_path = f"./photo.{ext}"
    response = requests.get(f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file.file_path}")
    response.raise_for_status() 
    
    with open(photo_path, "wb") as f:
        f.write(response.content)
        
    return photo_path, ext

async def convert_heic_to_jpeg_if_needed(original_path: str, ext: str, msg: Message) -> str:
    """Конвертирует HEIC в JPEG с учетом поворота."""
    if ext not in ('heic', 'heif'):
        return original_path

    await msg.answer("Обнаружен формат HEIC. Конвертирую в JPEG...")
    jpeg_path = "./photo.jpg"
    
    try:
        image = Image.open(original_path)
        image = ImageOps.exif_transpose(image)
        exif_obj = image.getexif()
        if exif_obj:
            image.save(jpeg_path, "JPEG", quality=95, exif=exif_obj.tobytes())
        else:
            image.save(jpeg_path, "JPEG", quality=95)
            
    except Exception as e:
        await msg.answer(f"Ошибка при конвертации: {e}")
        return original_path
    
    os.remove(original_path)
    return jpeg_path


async def extract_and_report_date(photo_path: str, msg: Message) -> Optional[str]:
    """Извлекает дату из EXIF. Возвращает None, если дата не найдена."""
    try:
        image = Image.open(photo_path)
        exif_data = image.getexif()

        if not exif_data:
            return None

        possible_date_tags = [36867, 36868, 306]
        date_str = next((exif_data.get(tag) for tag in possible_date_tags if exif_data.get(tag)), None)

        if not date_str:
            return None
        
        if isinstance(date_str, bytes):
            date_str = date_str.decode('utf-8', 'ignore').strip()
            
        dt_object = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        date_format = '%#d-%b-%Y' if os.name == 'nt' else '%-d-%b-%Y'
        photo_date = dt_object.strftime(date_format)

        await msg.answer(f"Дата определена из фото: {photo_date}")
        return photo_date

    except Exception as e:
        print(f"Ошибка при чтении EXIF: {e}")
        return None


async def process_and_reply_with_results(photo_path: str, photo_date: str, msg: Message):
    """Распознает лица, форматирует результат, отправляет текст и фото с рамками."""
    await msg.answer(f"Обрабатываю фото за дату: {photo_date}\nНачинаю распознавание...")

    try:
        healthy_spirits_list = mark_visit(photo_path, photo_date)
    except Exception as e:
        await msg.answer(f"Ошибка при отметке в таблице (проверьте формат даты или наличие колонки): {e}")
        return None
    
    recognized_names = [p["person"] for p in healthy_spirits_list if p["person"] != 'UNDEFINED']
    total_recognized = len(healthy_spirits_list)
    found_count = len(recognized_names)
    
    message_text = (
        "Люди, посетившие зарядку:\n\n"
        + "\n".join(recognized_names)
        + f"\n\nРаспознано: {found_count}/{total_recognized}"
    )
    await msg.answer(message_text)

    new_photo_path = draw_border_on_faces(healthy_spirits_list, photo_path)
    new_photo = FSInputFile(new_photo_path)
    await msg.answer_photo(new_photo)
    return new_photo_path


def cleanup_files(files_to_delete: List[str]):
    """Удаляет список временных файлов."""
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")

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
    """Принимает фото, пытается найти дату."""
    if not msg.document:
        await msg.answer("Пожалуйста, отправьте фото именно как документ (файл).")
        return
    
    processing_photo_path = None
    try:
        original_photo_path, ext = await download_photo(msg.document)
        processing_photo_path = await convert_heic_to_jpeg_if_needed(original_photo_path, ext, msg)

        photo_date = await extract_and_report_date(processing_photo_path, msg)

        if photo_date:
            new_photo_path = await process_and_reply_with_results(processing_photo_path, photo_date, msg)
            if new_photo_path:
                cleanup_files([processing_photo_path, new_photo_path])
            else:
                cleanup_files([processing_photo_path])
            
            await msg.answer("Обработка завершена. Можете отправить следующее фото.")
            await state.set_state(Uploading.waiting_photo)
        
        else:
            await msg.answer("Не удалось найти дату в метаданных.\n"
                             "Пожалуйста, введите дату вручную в формате <b>1-Jan-2025</b>:", parse_mode="HTML")
            await state.update_data(photo_path=processing_photo_path)
            await state.set_state(Uploading.waiting_date)

    except Exception as e:
        print(f"Произошла ошибка в document_handler: {e}")
        await msg.answer("Произошла ошибка при обработке фото. Попробуйте еще раз.")
        if processing_photo_path:
            cleanup_files([processing_photo_path])
        await state.set_state(Uploading.waiting_photo)


@dp.message(Uploading.waiting_date)
async def manual_date_handler(msg: Message, state: FSMContext):
    """Обрабатывает введенную вручную дату."""
    input_date = msg.text.strip()
    
    try:
        datetime.strptime(input_date, "%d-%b-%Y")
    except ValueError:
        await msg.answer("Неверный формат даты.\nПожалуйста, используйте формат <b>1-Jan-2025</b> (например: 1-Dec-2024):", parse_mode="HTML")
        return

    data = await state.get_data()
    photo_path = data.get('photo_path')

    if not photo_path or not os.path.exists(photo_path):
        await msg.answer("Файл фото потерян. Пожалуйста, загрузите фото заново.")
        await state.clear()
        await state.set_state(Uploading.waiting_photo)
        return

    new_photo_path = None
    try:
        new_photo_path = await process_and_reply_with_results(photo_path, input_date, msg)
        await msg.answer("Обработка завершена. Можете отправить следующее фото.")
    except Exception as e:
        print(f"Ошибка при обработке с ручной датой: {e}")
        await msg.answer("Произошла ошибка при обработке. Попробуйте загрузить фото заново.")
    finally:
        files_to_clean = [path for path in [photo_path, new_photo_path] if path]
        cleanup_files(files_to_clean)
        
        await state.clear()
        await state.set_state(Uploading.waiting_photo)