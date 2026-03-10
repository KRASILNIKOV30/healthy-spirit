from src.draw import draw_border_on_faces
from aiogram.types import FSInputFile
import pillow_heif
pillow_heif.register_heif_opener()
from src.api import mark_visit
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from typing import List
import os
import pillow_heif
pillow_heif.register_heif_opener()

class Uploading(StatesGroup):
    waiting_photo = State()
    waiting_date = State()
    waiting_confirmation = State()


def cleanup_files(files_to_delete: List[str]):
    """Удаляет список временных файлов."""
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"Ошибка при удалении файла {file_path}: {e}")


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