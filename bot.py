import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "8715707489:AAHRQEmB-v977wIUWtNIgrAtnnfsX0fFP0g"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Savollarni JSON’dan o‘qish
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# Foydalanuvchi holatini saqlash
user_state = {}

def subject_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for subject in questions.keys():
        keyboard.add(KeyboardButton(subject))
    keyboard.add(KeyboardButton("◀️ Ortga qaytish"))
    return keyboard

def quarter_menu(subject):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for quarter in questions[subject].keys():
        keyboard.add(KeyboardButton(quarter))
    keyboard.add(KeyboardButton("◀️ Ortga qaytish"))
    return keyboard

def start_quiz_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🚀 Testni boshlash"))
    keyboard.add(KeyboardButton("◀️ Ortga qaytish"))
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("📚 Fan tanlang:", reply_markup=subject_menu())

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    # Ortga qaytish
    if text == "◀️ Ortga qaytish":
        # Agar foydalanuvchi hali fan tanlamagan bo‘lsa
        if user_id not in user_state or "subject" not in user_state[user_id]:
            await message.answer("📚 Fan tanlang:", reply_markup=subject_menu())
        # Agar fan tanlangan bo‘lsa, chorak menyusiga qaytadi
        elif "quarter" not in user_state[user_id]:
            subject = user_state[user_id]["subject"]
            await message.answer("📖 Chorak tanlang:", reply_markup=quarter_menu(subject))
        # Agar chorak tanlangan bo‘lsa, testni boshlash menyusiga qaytadi
        else:
            await message.answer("✅ Tayyor bo‘lsang, testni boshlash tugmasini bos!", reply_markup=start_quiz_menu())
        return

    # Fan tanlash
    if text in questions.keys():
        user_state[user_id] = {"subject": text, "score": 0, "index": 0}
        await message.answer("📖 Chorak tanlang:", reply_markup=quarter_menu(text))
        return

    # Chorak tanlash
    if user_id in user_state and text in questions[user_state[user_id]["subject"]].keys():
        user_state[user_id]["quarter"] = text
        user_state[user_id]["chat_id"] = message.chat.id
        await message.answer("✅ Tayyor bo‘lsang, testni boshlash tugmasini bos!", reply_markup=start_quiz_menu())
        return

    # Testni boshlash
    if text == "🚀 Testni boshlash":
        chat_id = user_state[user_id]["chat_id"]
        await send_question(chat_id, user_id)
        return

async def send_question(chat_id, user_id):
    state = user_state[user_id]
    subject = state["subject"]
    quarter = state["quarter"]
    index = state["index"]

    q_list = questions[subject][quarter]
    if index < len(q_list):
        q = q_list[index]
        poll = await bot.send_poll(
            chat_id=chat_id,
            question=q["question"],
            options=q["options"],
            type="quiz",
            correct_option_id=q["options"].index(q["answer"]),
            is_anonymous=True
        )
        state["last_poll_id"] = poll.poll.id
    else:
        await bot.send_message(chat_id, f"🏁 Test tugadi!\nNatija: {state['score']} / {len(q_list)}")
        await bot.send_message(chat_id, "📚 Yana fan tanlang:", reply_markup=subject_menu())

@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    user_id = poll_answer.user.id
    state = user_state.get(user_id)
    if not state:
        return

    subject = state["subject"]
    quarter = state["quarter"]
    index = state["index"]
    q_list = questions[subject][quarter]
    q = q_list[index]

    chosen_index = poll_answer.option_ids[0]
    chosen = q["options"][chosen_index]

    if chosen == q["answer"]:
        state["score"] += 1

    state["index"] += 1
    chat_id = state["chat_id"]
    await send_question(chat_id, user_id)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
