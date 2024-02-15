import config
from misc import dp, bot
from aiogram.filters import Command
from aiogram.types import Message
import requests
import text


@dp.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer(text.greet.format(name=msg.from_user.full_name))


@dp.message()
async def handle(msg: Message):
    if not msg.document:
        return
    file = await bot.get_file(msg.document.file_id)
    response = requests.get("https://api.telegram.org/file/bot" + config.BOT_TOKEN + "/" + file.file_path)
    with open("../photo.jpg", "wb") as f:
        f.write(response.content)
    #отписывать в ответ ещё список отмеченных
