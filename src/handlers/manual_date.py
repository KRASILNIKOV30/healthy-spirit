from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.misc import dp
from datetime import datetime
import os
from .common import process_and_reply_with_results, Uploading, cleanup_files


@dp.message(Uploading.waiting_date)
async def manual_date_handler(msg: Message, state: FSMContext):
    """Обрабатывает введенную вручную дату."""
    input_date = msg.text.strip()

    try:
        datetime.strptime(input_date, "%d-%b-%Y")
    except ValueError:
        await msg.answer("Неверный формат даты.\nПожалуйста, используйте формат <b>1-Jan-2025</b>:", parse_mode="HTML")
        await state.set_state(Uploading.waiting_confirmation)
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
        await state.set_state(Uploading.waiting_photo)
    except Exception as e:
        print(f"Ошибка при обработке с ручной датой: {e}")
        await msg.answer("Произошла ошибка при обработке. Попробуйте загрузить фото заново.")
        await state.set_state(Uploading.waiting_photo)
    finally:
        files_to_clean = [path for path in [photo_path, new_photo_path] if path]
        cleanup_files(files_to_clean)