import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from config import TOKEN, ADMIN_ID
from buttons.default import phone_btn
from database import init_db, add_user, get_user, add_movie
from state import AdminMovie
from movie_code import generate_move_code
from database import get_movie_by_code



logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))


dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    user = get_user(user_id)
    if user:
        await message.answer("Film kodini yuboring")
    else:
        await message.answer(f"Assalomu Alaykum Xush Kelibsiz Hurmatli <b>{full_name}</b>\nRo'yxatdan o'ting👇", reply_markup=phone_btn)



@dp.message(F.contact)
async def get_user_conatct(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    phone_number = message.contact.phone_number
    add_user(user_id, full_name, username, phone_number)
    await message.answer("<b><i>Ro'yxatdan o'tdingiz🥳</i>\nFilm kodini yuboring</b>", reply_markup=ReplyKeyboardRemove())

@dp.message(F.text)
async def send_movie_by_code(message: types.Message):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos faqat film kodini yuboring")
        return

    movie_code = int(message.text)
    movie = get_movie_by_code(movie_code)

    if movie:
        movie_file, movie_desc = movie
        await message.answer_video(
            video=movie_file,
            caption=movie_desc
        )
    else:
        await message.answer("❌ Bunday film kodi topilmadi")


@dp.message(Command("admin"))
async def admin_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        await message.answer("Assalomu alaykum admin xush kelibsiz")
        await message.answer("Film videosini yuboring")
        await state.set_state(AdminMovie.movie_file)
    else:
        print("xato")


@dp.message(AdminMovie.movie_file, F.video)
async def get_movie_file(message: types.Message, state: FSMContext):
    movie_file = message.video.file_id
    await state.update_data(movie_file=movie_file)
    await message.answer("Film qabul qilindi\nTavsifini yuboring")
    await state.set_state(AdminMovie.movie_desc)



@dp.message(AdminMovie.movie_desc)
async def get_movie_desc(message: types.Message, state: FSMContext):
    movie_desc = message.text
    await state.update_data(movie_desc=movie_desc)

    data = await state.get_data()

    movie_file = data.get('movie_file')
    movie_desc = data.get('movie_desc')

    code = generate_move_code()

    lines = movie_desc.split('\n')
    new_lines = []

    for line in lines:
        new_lines.append(line)
        if line.startswith("⚡️ Janri:"):
            new_lines.append(f"\n🔢 KINO KODI: {code}\n")

    final_desc = '\n'.join(new_lines)
    add_movie(movie_file, final_desc, code)
    await message.answer_video(movie_file, caption=final_desc)
    await message.answer("film yuklandi")
    await state.clear()



async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())