from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.misc import dp
from .document import Uploading, mark_visit, cleanup_files, draw_border_on_faces, FSInputFile
from .manual_date import manual_date_handler


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