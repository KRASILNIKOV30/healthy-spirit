from .common import Uploading, cleanup_files, process_and_reply_with_results
from .manual_date import manual_date_handler
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import pillow_heif
from src.misc import dp
pillow_heif.register_heif_opener()


async def photo_pipeline(processing_photo_path: str, photo_date: str, msg: Message, state: FSMContext):
    new_photo_path = await process_and_reply_with_results(processing_photo_path, photo_date, msg)
    if new_photo_path:
        cleanup_files([processing_photo_path, new_photo_path])
    else:
        cleanup_files([processing_photo_path])
    await msg.answer("Обработка завершена. Можете отправить следующее фото.")
    await state.set_state(Uploading.waiting_photo)
    files_to_clean = [path for path in [processing_photo_path, new_photo_path] if path]
    cleanup_files(files_to_clean)


@dp.message(Uploading.waiting_confirmation)
async def confirmation_date_handler(msg: Message, state: FSMContext):
    data = await state.get_data()
    CONFIRM_ANSWER = data.get("confirm_answer")
    input_text = msg.text.strip().lower()
    data = await state.get_data()
    if input_text == CONFIRM_ANSWER:
        await photo_pipeline(data["photo_path"], data["photo_date"], msg, state)
    else:
        await manual_date_handler(msg, state)