import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, JUDGES, ROUNDS, ADMIN_IDS, ADMIN_PASSWORD
from database import Database

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()

# Состояния для фидбека
class FeedbackState(StatesGroup):
    choose_judge = State()
    choose_round = State()
    enter_faction = State()
    enter_speaker = State()
    enter_score = State()
    enter_feedback = State()

# Состояния для админ-панели
class AdminState(StatesGroup):
    wait_password = State()
    main_menu = State()
    view_feedbacks = State()
    search_feedback = State()
    delete_feedback = State()

# Проверка на админа
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Клавиатуры
def main_keyboard(user_id: int = None):
    keyboard = [
        [KeyboardButton(text="📝 Жаңа фидбек"), KeyboardButton(text="ℹ️ Ақпарат")]
    ]
    
    if user_id and is_admin(user_id):
        keyboard.append([KeyboardButton(text="👑 Админ панель")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def judge_keyboard():
    keyboard = []
    for i in range(0, len(JUDGES), 2):
        row = []
        row.append(KeyboardButton(text=JUDGES[i]))
        if i + 1 < len(JUDGES):
            row.append(KeyboardButton(text=JUDGES[i + 1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(text="🏠 Басты меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def round_keyboard():
    keyboard = []
    for i in range(0, len(ROUNDS), 2):
        row = []
        row.append(KeyboardButton(text=ROUNDS[i]))
        if i + 1 < len(ROUNDS):
            row.append(KeyboardButton(text=ROUNDS[i + 1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton(text="⬅️ Артқа"), KeyboardButton(text="🏠 Басты меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def score_keyboard():
    keyboard = []
    row = []
    for i in range(1, 11):
        row.append(KeyboardButton(text=str(i)))
        if i % 5 == 0:
            keyboard.append(row)
            row = []
    keyboard.append([KeyboardButton(text="⬅️ Артқа"), KeyboardButton(text="🏠 Басты меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Артқа"), KeyboardButton(text="🏠 Басты меню")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📋 Барлық фидбектер")],
            [KeyboardButton(text="🔍 Іздеу"), KeyboardButton(text="🗑️ Фидбек жою")],
            [KeyboardButton(text="📈 Excel-ге экспорт"), KeyboardButton(text="🔄 Базаны жаңарту")],
            [KeyboardButton(text="🏠 Басты меню")]
        ],
        resize_keyboard=True
    )

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    
    welcome_text = (
        "👋 Сәлеметсіз бе! Бұл дебат турнирі төрешілеріне кері байланыс беру боты.\n\n"
        "📝 Жаңа фидбек бастау үшін 'Жаңа фидбек' басыңыз.\n"
        "ℹ️ Ақпарат алу үшін 'Ақпарат' басыңыз."
    )
    
    if is_admin(user_id):
        welcome_text += "\n\n👑 Сіз админ ретінде тіркелдіңіз. Админ панельге кіру үшін 'Админ панель' басыңыз."
    
    await message.answer(welcome_text, reply_markup=main_keyboard(user_id))

# Кнопка "Жаңа фидбек"
@dp.message(lambda message: message.text == "📝 Жаңа фидбек")
async def start_feedback(message: types.Message, state: FSMContext):
    await state.set_state(FeedbackState.choose_judge)
    await message.answer("Төрешіні таңдаңыз:", reply_markup=judge_keyboard())

# Кнопка "Ақпарат"
@dp.message(lambda message: message.text == "ℹ️ Ақпарат")
async def show_info(message: types.Message):
    info_text = (
        "ℹ️ **Бот ақпараты:**\n\n"
        "📌 Бұл бот дебат турнирінде төрешілердің кері байланысын жинау үшін жасалған.\n\n"
        "📋 **Нұсқаулық:**\n"
        "1. 'Жаңа фидбек' басыңыз\n"
        "2. Төрешіні таңдаңыз\n"
        "3. Раундты таңдаңыз\n"
        "4. Фракция атауын енгізіңіз\n"
        "5. Спикер есімін енгізіңіз\n"
        "6. Баға беріңіз (1-10)\n"
        "7. Кері байланыс жазыңыз\n\n"
        "⚠️ Фидбектер тек админдерге көрінеді.\n"
        "🏠 Басты менюге оралу үшін '🏠 Басты меню' басыңыз."
    )
    await message.answer(info_text, parse_mode="Markdown")

# Кнопка "Админ панель"
@dp.message(lambda message: message.text == "👑 Админ панель")
async def admin_panel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ Сізде админ құқықтары жоқ!")
        return
    
    await state.set_state(AdminState.main_menu)
    await message.answer(
        "👑 **Админ панеліне қош келдіңіз!**\n"
        "Төмендегі опцияларды таңдаңыз:",
        reply_markup=admin_keyboard(),
        parse_mode="Markdown"
    )

# Админ: Статистика
@dp.message(lambda message: message.text == "📊 Статистика" and is_admin(message.from_user.id))
async def admin_stats(message: types.Message):
    stats = db.get_statistics()
    
    stats_text = (
        "📊 **Статистика:**\n\n"
        f"📈 Барлық фидбектер: {stats['total']}\n"
        f"👨‍⚖️ Төрешілер саны: {stats['judges_count']}\n"
        f"⭐ Орташа баға: {stats['avg_score']}/10\n\n"
        "📋 **Раундтар бойынша:**\n"
    )
    
    for round_name, count in stats['rounds_stats']:
        stats_text += f"  • {round_name}: {count} фидбек\n"
    
    if stats['total'] > 0:
        await message.answer(stats_text, parse_mode="Markdown")
    else:
        await message.answer("📭 Әлі ешқандай фидбек жоқ.")

# Админ: Все фидбеки
@dp.message(lambda message: message.text == "📋 Барлық фидбектер" and is_admin(message.from_user.id))
async def admin_all_feedbacks(message: types.Message, state: FSMContext):
    feedbacks = db.get_all_feedback()
    
    if not feedbacks:
        await message.answer("📭 Әлі ешқандай фидбек жоқ.")
        return
    
    await state.set_state(AdminState.view_feedbacks)
    
    # Показываем по 5 фидбеков за раз
    chunk_size = 5
    for i in range(0, len(feedbacks), chunk_size):
        chunk = feedbacks[i:i + chunk_size]
        response = f"📋 **Фидбектер ({i+1}-{min(i+chunk_size, len(feedbacks))}/{len(feedbacks)}):**\n\n"
        
        for fb in chunk:
            response += (
                f"🆔 ID: {fb[0]}\n"
                f"👨‍⚖️ Төреші: {fb[1]}\n"
                f"🎯 Раунд: {fb[2]}\n"
                f"🏛️ Фракция: {fb[3]}\n"
                f"🗣️ Спикер: {fb[4]}\n"
                f"⭐ Баға: {fb[5]}/10\n"
                f"📝 Кері байланыс: {fb[6][:100]}...\n"
                f"⏰ Уақыты: {fb[7]}\n"
                f"{'-'*30}\n"
            )
        
        await message.answer(response, parse_mode="Markdown")
    
    await message.answer(
        "🔍 Фидбек іздеу үшін 'Іздеу' басыңыз немесе '🏠 Басты меню'ге оралыңыз.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Іздеу"), KeyboardButton(text="🗑️ Фидбек жою")],
                [KeyboardButton(text="🏠 Басты меню")]
            ],
            resize_keyboard=True
        )
    )

# Админ: Поиск
@dp.message(lambda message: message.text == "🔍 Іздеу" and is_admin(message.from_user.id))
async def admin_search(message: types.Message, state: FSMContext):
    await state.set_state(AdminState.search_feedback)
    await message.answer(
        "🔍 **Фидбек іздеу:**\n"
        "Төреші, фракция, спикер аты немесе кері байланыс бойынша іздеңіз.\n\n"
        "Мысалы: 'Айгерім' немесе 'финал'",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🏠 Басты меню")]],
            resize_keyboard=True
        )
    )

# Админ: Обработка поиска
@dp.message(AdminState.search_feedback)
async def process_search(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await state.set_state(AdminState.main_menu)
        await message.answer("Админ панеліне оралдыңыз.", reply_markup=admin_keyboard())
        return
    
    keyword = message.text
    results = db.search_feedback(keyword)
    
    if not results:
        await message.answer(f"❌ '{keyword}' бойынша нәтиже табылмады.")
        return
    
    response = f"🔍 **'{keyword}' бойынша нәтижелер ({len(results)} табылды):**\n\n"
    
    for fb in results[:10]:  # Показываем первые 10 результатов
        response += (
            f"🆔 ID: {fb[0]}\n"
            f"👨‍⚖️ Төреші: {fb[1]}\n"
            f"🎯 Раунд: {fb[2]}\n"
            f"⭐ Баға: {fb[5]}/10\n"
            f"📝 Кері байланыс: {fb[6][:50]}...\n"
            f"{'-'*20}\n"
        )
    
    await message.answer(response, parse_mode="Markdown")
    
    if len(results) > 10:
        await message.answer(f"ℹ️ Тағы {len(results) - 10} нәтиже бар. Нақтырақ іздеңіз.")

# Админ: Удаление фидбека
@dp.message(lambda message: message.text == "🗑️ Фидбек жою" and is_admin(message.from_user.id))
async def admin_delete_start(message: types.Message, state: FSMContext):
    await state.set_state(AdminState.delete_feedback)
    await message.answer(
        "🗑️ **Фидбек жою:**\n"
        "Жою үшін фидбек ID нөмірін енгізіңіз.\n"
        "ID нөмірін білу үшін алдымен 'Барлық фидбектерді' қараңыз.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🏠 Басты меню")]],
            resize_keyboard=True
        )
    )

# Админ: Обработка удаления
@dp.message(AdminState.delete_feedback)
async def process_delete(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await state.set_state(AdminState.main_menu)
        await message.answer("Админ панеліне оралдыңыз.", reply_markup=admin_keyboard())
        return
    
    try:
        feedback_id = int(message.text)
        feedback = db.get_feedback_by_id(feedback_id)
        
        if not feedback:
            await message.answer(f"❌ ID {feedback_id} бойынша фидбек табылмады.")
            return
        
        # Показываем информацию о фидбеке
        info_text = (
            f"🗑️ **Жоюға дайын фидбек:**\n\n"
            f"👨‍⚖️ Төреші: {feedback[1]}\n"
            f"🎯 Раунд: {feedback[2]}\n"
            f"🏛️ Фракция: {feedback[3]}\n"
            f"🗣️ Спикер: {feedback[4]}\n"
            f"⭐ Баға: {feedback[5]}/10\n"
            f"📝 Кері байланыс: {feedback[6]}\n\n"
            f"Бұл фидбекті шынымен жойғыңыз келе ме?\n"
            f"✅ Иә, жою үшін '/delete_confirm {feedback_id}' командасын жіберіңіз.\n"
            f"❌ Жоқ, болдырмау үшін '🏠 Басты меню' басыңыз."
        )
        
        await message.answer(info_text, parse_mode="Markdown")
        
    except ValueError:
        await message.answer("❌ Тура сан енгізіңіз (ID нөмірі).")

# Команда для подтверждения удаления
@dp.message(Command("delete_confirm"))
async def confirm_delete(message: types.Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Сізде админ құқықтары жоқ!")
        return
    
    try:
        feedback_id = int(message.text.split()[1])
        deleted_count = db.delete_feedback(feedback_id)
        
        if deleted_count > 0:
            await message.answer(f"✅ Фидбек ID {feedback_id} сәтті жойылды.")
        else:
            await message.answer(f"❌ Фидбек ID {feedback_id} жойылмады.")
            
    except (IndexError, ValueError):
        await message.answer("❌ Қате формат. Мынаны қолданыңыз: /delete_confirm ID")

# Админ: Экспорт в Excel
@dp.message(lambda message: message.text == "📈 Excel-ге экспорт" and is_admin(message.from_user.id))
async def export_to_excel(message: types.Message):
    import pandas as pd
    from io import BytesIO
    
    feedbacks = db.get_all_feedback()
    
    if not feedbacks:
        await message.answer("📭 Экспорттау үшін ешқандай фидбек жоқ.")
        return
    
    # Создаем DataFrame
    df = pd.DataFrame(feedbacks, columns=[
        'ID', 'Төреші', 'Раунд', 'Фракция', 'Спикер', 
        'Баға', 'Кері байланыс', 'Уақыты', 'User ID', 'Username'
    ])
    
    # Excel export
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Фидбектер', index=False)
    
    output.seek(0)
    
    # send file
    await message.answer_document(
        types.BufferedInputFile(
            output.read(),
            filename=f"feedback_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        ),
        caption="📈 Фидбектердің Excel файлы"
    )

# Админ: Обновление базы
@dp.message(lambda message: message.text == "🔄 Базаны жаңарту" and is_admin(message.from_user.id))
async def refresh_database(message: types.Message):
    # Просто пересоздаем таблицу (в реальном проекте это может быть опасно!)
    db.create_table()
    await message.answer("✅ База деректері жаңартылды.")

# Кнопка "🏠 Басты меню"
@dp.message(lambda message: message.text == "🏠 Басты меню")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)

# Оригинальные обработчики фидбека
@dp.message(FeedbackState.choose_judge)
async def process_judge(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await main_menu(message, state)
        return
    
    if message.text not in JUDGES:
        await message.answer("Төрешіні тізімнен таңдаңыз:")
        return
    
    await state.update_data(judge_name=message.text)
    await state.set_state(FeedbackState.choose_round)
    await message.answer("Қай раунд?", reply_markup=round_keyboard())

@dp.message(FeedbackState.choose_round)
async def process_round(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await main_menu(message, state)
        return
    
    if message.text == "⬅️ Артқа":
        await state.set_state(FeedbackState.choose_judge)
        await message.answer("Төрешіні таңдаңыз:", reply_markup=judge_keyboard())
        return
    
    if message.text not in ROUNDS:
        await message.answer("Раундты тізімнен таңдаңыз:")
        return
    
    await state.update_data(round_name=message.text)
    await state.set_state(FeedbackState.enter_faction)
    await message.answer("Фракция атауы:", reply_markup=back_keyboard())

@dp.message(FeedbackState.enter_faction)
async def process_faction(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await main_menu(message, state)
        return
    
    if message.text == "⬅️ Артқа":
        await state.set_state(FeedbackState.choose_round)
        await message.answer("Қай раунд?", reply_markup=round_keyboard())
        return
    
    await state.update_data(faction_name=message.text)
    await state.set_state(FeedbackState.enter_speaker)
    await message.answer("Спикер есімі:", reply_markup=back_keyboard())

@dp.message(FeedbackState.enter_speaker)
async def process_speaker(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await main_menu(message, state)
        return
    
    if message.text == "⬅️ Артқа":
        await state.set_state(FeedbackState.enter_faction)
        await message.answer("Фракция атауы:", reply_markup=back_keyboard())
        return
    
    await state.update_data(speaker_name=message.text)
    await state.set_state(FeedbackState.enter_score)
    await message.answer("Төрешілік бағалау шкаласы (1-10):", reply_markup=score_keyboard())

@dp.message(FeedbackState.enter_score)
async def process_score(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await main_menu(message, state)
        return
    
    if message.text == "⬅️ Артқа":
        await state.set_state(FeedbackState.enter_speaker)
        await message.answer("Спикер есімі:", reply_markup=back_keyboard())
        return
    
    try:
        score = int(message.text)
        if score < 1 or score > 10:
            raise ValueError
    except ValueError:
        await message.answer("1-10 аралығындағы санды енгізіңіз:")
        return
    
    await state.update_data(score=score)
    await state.set_state(FeedbackState.enter_feedback)
    await message.answer("Кері байланыс (текст):", reply_markup=back_keyboard())

@dp.message(FeedbackState.enter_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    if message.text == "🏠 Басты меню":
        await main_menu(message, state)
        return
    
    if message.text == "⬅️ Артқа":
        await state.set_state(FeedbackState.enter_score)
        await message.answer("Төрешілік бағалау шкаласы (1-10):", reply_markup=score_keyboard())
        return
    
    # Получаем все данные
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Сохраняем в БД с user_id
    feedback_id = db.add_feedback(
        judge_name=data['judge_name'],
        round_name=data['round_name'],
        faction_name=data['faction_name'],
        speaker_name=data['speaker_name'],
        score=data['score'],
        feedback_text=message.text,
        user_id=user_id,
        username=username
    )
    
    # Отправляем подтверждение пользователю
    feedback_summary = (
        "✅ **Кері байланыс сақталды!**\n\n"
        f"🆔 ID: {feedback_id}\n"
        f"👨‍⚖️ Төреші: {data['judge_name']}\n"
        f"🎯 Раунд: {data['round_name']}\n"
        f"🏛️ Фракция: {data['faction_name']}\n"
        f"🗣️ Спикер: {data['speaker_name']}\n"
        f"⭐ Баға: {data['score']}/10\n"
        f"📝 Кері байланыс: {message.text}\n\n"
        "ℹ️ Бұл фидбек тек админдерге көрінеді."
    )
    
    await message.answer(feedback_summary, parse_mode="Markdown")
    
    # Уведомляем админов
    admin_notification = (
        "🆕 **Жаңа фидбек түсті!**\n\n"
        f"🆔 ID: {feedback_id}\n"
        f"👨‍⚖️ Төреші: {data['judge_name']}\n"
        f"🎯 Раунд: {data['round_name']}\n"
        f"🏛️ Фракция: {data['faction_name']}\n"
        f"🗣️ Спикер: {data['speaker_name']}\n"
        f"⭐ Баға: {data['score']}/10\n"
        f"👤 Пайдаланушы: @{username if username else 'жоқ'} (ID: {user_id})"
    )
    
    # Отправляем уведомление всем админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_notification, parse_mode="Markdown")
        except:
            pass  # Игнорируем ошибки отправки
    
    await main_menu(message, state)

# Запуск бота
async def main():
    print("🤖 Бот іске қосылды...")
    print(f"👑 Админдер: {ADMIN_IDS}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())