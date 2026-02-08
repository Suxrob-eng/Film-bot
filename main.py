import asyncio
import logging
import sqlite3
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError

from config import TOKEN, ADMIN_ID, CHANNEL_USERNAME
from buttons.default import phone_btn, stats_btn
from buttons.inline import sub_keyboard
from database import init_db, add_user, get_user, add_movie, get_movie_by_code, get_all_movies, get_total_movies_count, get_movies_by_page
from state import AdminMovie, ReklamaState
from movie_code import generate_move_code
from movie_stats import MovieStats
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_subscription(user_id):
        await message.answer(
            "❗ Botdan foydalanish uchun kanalga obuna bo'ling",
            reply_markup=sub_keyboard(CHANNEL_USERNAME)
        )
        return
    
    user = get_user(user_id)
    full_name = message.from_user.full_name
    
    if user:
        await message.answer(
            f"🎬 <b>Kino botga xush kelibsiz, {full_name}!</b>\n\n"
            "Film kodini yuboring yoki statistikani ko'ring:",
            reply_markup=stats_btn
        )
    else:
        await message.answer(
            f"Assalomu Alaykum Xush Kelibsiz Hurmatli <b>{full_name}</b>\n"
            "Ro'yxatdan o'ting👇", 
            reply_markup=phone_btn
        )

@dp.callback_query(F.data == "check_sub")
async def check_subscription_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    if await check_subscription(user_id):
        await call.message.delete()
        await call.message.answer(
            "✅ Obuna tasdiqlandi!\n"
            "Endi botdan foydalanishingiz mumkin",
            reply_markup=phone_btn
        )
    else:
        await call.answer(
            "❌ Hali kanalga obuna bo'lmadingiz",
            show_alert=True
        )

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramForbiddenError:
        logging.error(f"Bot kanalda admin emas yoki kanal topilmadi: {CHANNEL_USERNAME}")
        return False
    except Exception as e:
        logging.error(f"Obunani tekshirishda xato: {e}")
        return False

@dp.message(F.contact)
async def get_user_contact(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    phone_number = message.contact.phone_number
    
    if not phone_number:
        await message.answer("❌ Telefon raqami noto'g'ri formatda")
        return
    
    try:
        existing_user = get_user(user_id)
        
        if existing_user:
            add_user(user_id, full_name, username, phone_number)
            await message.answer(
                "✅ Ma'lumotlaringiz yangilandi!\n\n"
                "Film kodini yuboring yoki statistikani ko'ring:",
                reply_markup=stats_btn,
                parse_mode="HTML"
            )
        else:
            success = add_user(user_id, full_name, username, phone_number)
            
            if success:
                await message.answer(
                    "<b><i>Ro'yxatdan o'tdingiz 🥳</i></b>\n\n"
                    "Film kodini yuboring yoki statistikani ko'ring:",
                    reply_markup=stats_btn,
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "❌ Ro'yxatdan o'tishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
                )
    except Exception as e:
        logging.error(f"Error in get_user_contact: {e}")
        await message.answer(
            "❌ Texnik xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
        )

@dp.message(Command("admin"))
async def admin_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        await message.answer(
            "👨‍💻 Assalomu alaykum admin, xush kelibsiz!\n\n"
            "📤 Film videosini yuboring"
        )
        await state.set_state(AdminMovie.movie_file)
    else:
        await message.answer("❌ Bu buyruq faqat admin uchun!")

@dp.message(AdminMovie.movie_file, F.video)
async def get_movie_file(message: types.Message, state: FSMContext):
    movie_file = message.video.file_id
    await state.update_data(movie_file=movie_file)
    await message.answer(
        "✅ Film qabul qilindi\n\n"
        "📝 Tavsifini yuboring"
    )
    await state.set_state(AdminMovie.movie_desc)

@dp.message(AdminMovie.movie_desc)
async def get_movie_desc(message: types.Message, state: FSMContext):
    movie_desc = message.text
    await state.update_data(movie_desc=movie_desc)

    data = await state.get_data()
    movie_file = data.get('movie_file')
    movie_desc = data.get('movie_desc')

    if not movie_file or not movie_desc:
        await message.answer("❌ Ma'lumotlar to'liq emas")
        await state.clear()
        return

    code = generate_move_code()
    
    print(f"🎬 YANGI FILM YUKLANMOQDA:")
    print(f"📁 File ID: {movie_file}")
    print(f"📝 Description: {movie_desc}")
    print(f"🔢 Generated Code: {code}")

    lines = movie_desc.split('\n')
    new_lines = []
    
    for line in lines:
        new_lines.append(line)
        if line.startswith("⚡️ Janri:") or line.startswith("Janri:"):
            new_lines.append(f"\n🔢 KINO KODI: {code}\n")

    final_desc = '\n'.join(new_lines)
    
    success = add_movie(movie_file, final_desc, code)
    
    if success:
        await message.answer_video(movie_file, caption=final_desc)
        await message.answer(f"✅ Film muvaffaqiyatli yuklandi!\n🎬 Kodi: {code}")
        print(f"✅ FILM BAZAGA SAQLANDI: {code}")
    else:
        await message.answer("❌ Film bazaga saqlanmadi!")
        print(f"❌ FILM BAZAGA SAQLANMADI: {code}")
    
    await state.clear()

@dp.message(Command("all"))
async def all_movies_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    movies = get_all_movies()
    
    if not movies:
        await message.answer("📭 Hozircha filmlar mavjud emas")
        return
    
    response = "🎬 BARCHA FILMLAR RO'YXATI:\n\n"
    
    for i, (code, desc) in enumerate(movies, 1):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response += f"{i}. {title}\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    await message.answer(response)

@dp.message(Command("allpage"))
async def all_movies_paginated_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    total_movies = get_total_movies_count()
    page = 1
    limit = 10
    
    movies = get_movies_by_page(page, limit)
    
    if not movies:
        await message.answer("📭 Hozircha filmlar mavjud emas")
        return
    
    response = f"🎬 FILMLAR (1-sahifa) - Jami: {total_movies} ta\n\n"
    
    for i, (code, desc) in enumerate(movies, 1):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response += f"{i}. {title}\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    keyboard = []
    if total_movies > limit:
        keyboard.append([InlineKeyboardButton(
            text="Keyingi sahifa →", 
            callback_data=f"next_page_{page+1}"
        )])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(response, reply_markup=reply_markup)

@dp.callback_query(F.data.startswith("next_page_"))
async def next_page_handler(callback: types.CallbackQuery):
    try:
        page = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        page = 1
    
    user_id = callback.from_user.id

    if user_id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    limit = 10
    movies = get_movies_by_page(page, limit)
    total_movies = get_total_movies_count()
    
    if not movies:
        await callback.answer("✅ Boshqa film yo'q", show_alert=True)
        return
    
    start_num = (page - 1) * limit + 1
    response = f"🎬 FILMLAR ({page}-sahifa) - Jami: {total_movies} ta\n\n"
    
    for i, (code, desc) in enumerate(movies, start_num):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response += f"{i}. {title}\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    keyboard_buttons = []
    
    if page > 1:
        keyboard_buttons.append([InlineKeyboardButton(
            text="← Oldingi sahifa", 
            callback_data=f"prev_page_{page-1}"
        )])
    
    if total_movies > page * limit:
        keyboard_buttons.append([InlineKeyboardButton(
            text="Keyingi sahifa →", 
            callback_data=f"next_page_{page+1}"
        )])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(response, reply_markup=reply_markup)
    await callback.answer()

@dp.callback_query(F.data.startswith("prev_page_"))
async def prev_page_handler(callback: types.CallbackQuery):
    try:
        page = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        page = 1
    
    user_id = callback.from_user.id

    if user_id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    limit = 10
    movies = get_movies_by_page(page, limit)
    total_movies = get_total_movies_count()
    
    if not movies:
        await callback.answer("❌ Sahifa topilmadi", show_alert=True)
        return
    
    start_num = (page - 1) * limit + 1
    response = f"🎬 FILMLAR ({page}-sahifa) - Jami: {total_movies} ta\n\n"
    
    for i, (code, desc) in enumerate(movies, start_num):
        desc_lines = desc.split('\n')
        title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response += f"{i}. {title}\n"
        response += f"   🔢 Kodi: <code>{code}</code>\n\n"
    
    keyboard_buttons = []
    
    if page > 1:
        keyboard_buttons.append([InlineKeyboardButton(
            text="← Oldingi sahifa", 
            callback_data=f"prev_page_{page-1}"
        )])
    
    if total_movies > page * limit:
        keyboard_buttons.append([InlineKeyboardButton(
            text="Keyingi sahifa →", 
            callback_data=f"next_page_{page+1}"
        )])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(response, reply_markup=reply_markup)
    await callback.answer()

@dp.message(Command("random"))
async def random_movies_handler(message: types.Message):
    random_movies = MovieStats.get_random_top_movies(5)
    response = MovieStats.format_movie_stats(random_movies, "🎲 Tasodifiy Top 5 Film")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Yangi tasodifiy filmlar",
                callback_data="refresh_random"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Bugungi top",
                callback_data="today_top"
            ),
            InlineKeyboardButton(
                text="📊 Haftalik top",
                callback_data="weekly_top"
            )
        ]
    ])
    
    await message.answer(response, reply_markup=keyboard)

@dp.message(Command("today"))
async def today_top_handler(message: types.Message):
    today_movies = MovieStats.get_today_top_movies(3)
    response = MovieStats.format_movie_stats(today_movies, "🌟 Bugungi Top Filmlar")
    
    await message.answer(response)

@dp.message(Command("weekly"))
async def weekly_top_handler(message: types.Message):
    weekly_movies = MovieStats.get_weekly_top_movies(5)
    response = MovieStats.format_movie_stats(weekly_movies, "📅 Haftalik Top 5 Film")
    
    await message.answer(response)

@dp.message(Command("genres"))
async def genres_handler(message: types.Message):
    genre_movies = MovieStats.get_popular_by_genre()
    response = MovieStats.format_genre_stats(genre_movies)
    
    await message.answer(response)

@dp.message(Command("recommend"))
async def recommend_handler(message: types.Message):
    user_id = message.from_user.id
    recommended = MovieStats.get_recommended_movie(user_id)
    
    if recommended:
        code, desc = recommended
        desc_lines = desc.split('\n')
        film_title = desc_lines[0] if desc_lines else "Nomsiz film"
        
        response = f"🎯 <b>Siz uchun tavsiya:</b>\n\n"
        response += f"<b>{film_title}</b>\n"
        response += f"\n🔢 Kino kodi: <code>{code}</code>\n\n"
        response += f"❓ Bu filmni ko'rish uchun shu kodni yuboring"
        
        await message.answer(response)
    else:
        await message.answer("📭 Tavsiya qilish uchun filmlar mavjud emas")

@dp.message(F.text == "🎲 Tasodifiy filmlar")
async def random_movies_button_handler(message: types.Message):
    await random_movies_handler(message)

@dp.message(F.text == "🌟 Bugungi top")
async def today_top_button_handler(message: types.Message):
    await today_top_handler(message)

@dp.message(F.text == "📊 Haftalik top")
async def weekly_top_button_handler(message: types.Message):
    await weekly_top_handler(message)

@dp.message(F.text == "🎭 Janrlar bo'yicha")
async def genres_button_handler(message: types.Message):
    await genres_handler(message)

@dp.message(F.text == "🎯 Menga tavsiya")
async def recommend_button_handler(message: types.Message):
    await recommend_handler(message)

@dp.message(F.text == "🔙 Asosiy menyu")
async def back_button_handler(message: types.Message):
    await message.answer(
        "Asosiy menyuga qaytdingiz. Film kodini yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.callback_query(F.data == "refresh_random")
async def refresh_random_handler(callback: types.CallbackQuery):
    random_movies = MovieStats.get_random_top_movies(5)
    response = MovieStats.format_movie_stats(random_movies, "🎲 Tasodifiy Top 5 Film")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Yangi tasodifiy filmlar",
                callback_data="refresh_random"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Bugungi top",
                callback_data="today_top"
            ),
            InlineKeyboardButton(
                text="📊 Haftalik top",
                callback_data="weekly_top"
            )
        ]
    ])
    
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer("🔄 Yangi tasodifiy filmlar yuklandi!")

@dp.callback_query(F.data == "today_top")
async def today_top_callback_handler(callback: types.CallbackQuery):
    today_movies = MovieStats.get_today_top_movies(3)
    response = MovieStats.format_movie_stats(today_movies, "🌟 Bugungi Top Filmlar")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎲 Tasodifiy filmlar",
                callback_data="refresh_random"
            )
        ]
    ])
    
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "weekly_top")
async def weekly_top_callback_handler(callback: types.CallbackQuery):
    weekly_movies = MovieStats.get_weekly_top_movies(5)
    response = MovieStats.format_movie_stats(weekly_movies, "📅 Haftalik Top 5 Film")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎲 Tasodifiy filmlar",
                callback_data="refresh_random"
            )
        ]
    ])
    
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()

# REKLAMA FUNKSIYALARI
@dp.message(Command("reklama"))
async def reklama_command_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    await message.answer(
        "📢 <b>Reklama yuborish</b>\n\n"
        "Reklama matnini yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(ReklamaState.reklama_text)

@dp.message(ReklamaState.reklama_text)
async def get_reklama_text(message: types.Message, state: FSMContext):
    reklama_text = message.text
    
    if not reklama_text:
        await message.answer("❌ Matn bo'sh bo'lishi mumkin emas!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="send_reklama"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_reklama")
        ]
    ])
    
    await state.update_data(reklama_text=reklama_text)
    await message.answer(
        f"📝 <b>Reklama matni:</b>\n\n{reklama_text}\n\n"
        f"Barcha foydalanuvchilarga yuborilsinmi?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ReklamaState.reklama_confirm)

@dp.callback_query(F.data == "send_reklama")
async def send_reklama_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    reklama_text = data.get('reklama_text', '')
    
    await callback.message.edit_text("📤 Reklama yuborilmoqda...")
    
    conn = sqlite3.connect('movie_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    success_count = 0
    error_count = 0
    
    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>E'lon:</b>\n\n{reklama_text}",
                parse_mode="HTML"
            )
            success_count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            error_count += 1
            logging.error(f"Reklama {user_id} ga yuborilmadi: {e}")
    
    await callback.message.edit_text(
        f"✅ Reklama yuborish tugadi!\n\n"
        f"✅ Muvaffaqiyatli: {success_count}\n"
        f"❌ Xatolik: {error_count}\n"
        f"👥 Jami: {len(users)}"
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel_reklama")
async def cancel_reklama_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Reklama bekor qilindi")
    await state.clear()
    await callback.answer()

@dp.message(F.text)
async def send_movie_by_code(message: types.Message):
    print(f"🔍 USER KOD KIRITDI: {message.text}")
    
    if not message.text.isdigit():
        await message.answer("❌ Iltimos faqat film kodini yuboring")
        return

    movie_code = message.text
    
    print(f"🔍 KOD TEKSHIRILMOQDA: {movie_code}")
    
    movie = get_movie_by_code(movie_code)

    if movie:
        movie_file, movie_desc = movie
        await message.answer_video(
            video=movie_file,
            caption=movie_desc
        )
        print(f"✅ FILM TOPILDI VA YUBORILDI: {movie_code}")
    else:
        await message.answer("❌ Bunday film kodi topilmadi")
        print(f"❌ FILM TOPILMADI: {movie_code}")

async def main():
    if os.path.exists('movie_bot.db'):
        print("✅ Database fayli mavjud")
    else:
        print("📂 Database fayli mavjud emas, yangisi yaratiladi...")
    

    init_db()
    

    conn = sqlite3.connect('movie_bot.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📊 Database jadvallari: {tables}")
    
    if ('movies',) in tables:
        cursor.execute("PRAGMA table_info(movies);")
        columns = cursor.fetchall()
        print(f"📋 Movies jadvali ustunlari:")
        for col in columns:
            print(f"  {col}")
        
        cursor.execute('SELECT COUNT(*) FROM movies')
        movie_count = cursor.fetchone()[0]
        print(f"🎬 Bazadagi filmlar soni: {movie_count}")
    
    if ('users',) in tables:
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        print(f"👥 Bazadagi foydalanuvchilar soni: {user_count}")
    
    conn.close()
    
    print("🤖 Bot ishga tushmoqda...")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        print(f"❌ Bot ishlashda xato: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Dastur to'xtatildi")