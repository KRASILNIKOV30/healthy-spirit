from aiogram.types import Message, Document
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from src.misc import dp, bot
from aiogram.types import FSInputFile
from src import config
from src.api import mark_visit
from src.draw import draw_border_on_faces
from PIL import Image, ImageOps
from datetime import datetime
from typing import Optional, Tuple, List
import requests
import os
import pillow_heif
pillow_heif.register_heif_opener()

class Uploading(StatesGroup):
    waiting_photo = State()
    waiting_date = State()
    waiting_confirmation = State()

async def download_photo(document: Document) -> Tuple[str, str, str]:
    """Скачивает фото из сообщения и возвращает путь, расширение и оригинальное имя."""
    file = await bot.get_file(document.file_id)
    ext = file.file_path.split('.')[-1].lower()
    original_filename = document.file_name
    photo_path = f"./photo.{ext}"
    response = requests.get(f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file.file_path}")
    response.raise_for_status()
    with open(photo_path, "wb") as f:
        f.write(response.content)
    return photo_path, ext, original_filename

async def convert_heic_to_jpeg_if_needed(original_path: str, ext: str, msg: Message) -> Optional[str]:
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

def extract_date_from_filename(filename: str) -> Optional[str]:
    """Из photo_2026-03-04_08-05-23.jpg делает 4-Mar-2026"""
    MONTHS = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
    }
    try:
        DATE_PLACE_AFTER_SPLIT = 1
        date_part = (filename.split('_'))[DATE_PLACE_AFTER_SPLIT]
        year, month, day = date_part.split('-')
        day_int = int(day)
        if month not in MONTHS:
            return None
        return f"{day_int}-{MONTHS[month]}-{year}"
    except (IndexError, ValueError, KeyError):
        return None

async def extract_and_report_date(photo_path: str, filename: str, msg: Message) -> Optional[str]:
    """Извлекает дату из названия, если не нашла в названии, то из EXIF."""
    try:
        photo_date = extract_date_from_filename(filename)
        if photo_date != None:
            return photo_date
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


def cleanup_files(files_to_delete: List[str]):
    """Удаляет список временных файлов."""
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")


@dp.message(Uploading.waiting_photo)
async def document_handler(msg: Message, state: FSMContext):
    """Принимает фото, пытается найти дату."""
    if not msg.document:
        await msg.answer("Пожалуйста, отправьте фото именно как документ (файл).")
        return
    processing_photo_path = None
    try:
        original_photo_path, ext, original_filename = await download_photo(msg.document)
        processing_photo_path = await convert_heic_to_jpeg_if_needed(original_photo_path, ext, msg)
        photo_date = await extract_and_report_date(processing_photo_path, original_filename, msg)
        CONFIRM_ANSWER = "ok"
        if photo_date:
            await state.update_data(
                photo_path=processing_photo_path,
                photo_date=photo_date,
                confirm_answer=CONFIRM_ANSWER
            )
            await msg.answer(f"Обнаружена дата фото: <b>{photo_date}</b>.\n"
                             f"Введите <b>\"{CONFIRM_ANSWER}\"</b>, чтобы подтвердить дату или отправьте другую в формате: <b>1-Jan-2025</b>", parse_mode="HTML")
            await state.set_state(Uploading.waiting_confirmation)
        else:
            await msg.answer("Не удалось найти дату в метаданных.\n"
                             "Пожалуйста, введите дату вручную в формате <b>1-Jan-2025</b>", parse_mode="HTML")
            await state.update_data(photo_path=processing_photo_path)
            await state.set_state(Uploading.waiting_date)
    except Exception as e:
        print(f"Произошла ошибка в document_handler: {e}")
        await msg.answer("Произошла ошибка при обработке фото. Попробуйте еще раз.")
        if processing_photo_path:
            cleanup_files([processing_photo_path])
        await state.set_state(Uploading.waiting_photo)