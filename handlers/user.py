from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatAction
import re

from keyboards import kb
from model.model import DNDChatbot
from utils.dice_roller import DiceRoller
from keyboards.kb import get_roll_button_keyboard

user = Router()
dice_roller = DiceRoller()
dnd_bot_interaction = DNDChatbot().interact


@user.message(CommandStart())
async def start(message: Message):
    image_url = "https://i.imgur.com/j7mxtyf.png"
    text = """Здравствуй, путник!
Опасное это дело — выходить за порог. Стоит ступить на дорогу и, если дашь волю ногам, неизвестно, куда тебя занесёт.
Ты выбираешь, куда идти, а я буду строить мир вокруг твоих шагов.
Готов начать путешествие?
    """

    await message.bot.send_chat_action(
        chat_id=message.from_user.id, action=ChatAction.TYPING
    )
    await message.answer_photo(
        photo=image_url,
        caption=text,
        message_effect_id="5104841245755180586",
        reply_markup=kb.main,
    )


@user.callback_query(F.data == "rules")
async def show_about_bot(callback: CallbackQuery):
    await callback.message.bot.send_chat_action(
        chat_id=callback.from_user.id, action=ChatAction.TYPING
    )

    text = (
        "🧙 *Narramancer* — твой персональный мастер приключений!\n\n"
        "Погрузись в мир фантазии, где история рождается на лету. "
        "Narramancer ведёт тебя по захватывающим сюжетам в стиле настольных RPG — "
        "но *без сложных правил*. Просто играй — он позаботится обо всём.\n\n"
        "Бот будет предлагать варианты действий, но ты волен идти куда угодно, "
        "делать что угодно и быть кем захочешь.\n\n"
        "*Что умеет Narramancer:*\n"
        "• Придумывать миры, квесты и персонажей\n"
        "• Реагировать на ваши действия в реальном времени\n"
        "• Помогать развивать героя по ходу истории\n"
        "• Бросать кубики и создавать атмосферу\n\n"
        "_Никаких правил — только история._"
    )

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer() 


@user.callback_query(F.data == "start_game")
async def start_game(callback: CallbackQuery):
    await callback.message.bot.send_chat_action(
        chat_id=callback.from_user.id, action=ChatAction.TYPING
    )

    intro_text = (
        "✨ Пелена реальности расступается, и ты оказываешься на пороге великого приключения...\n\n"
        "👤 *Расскажи о своём персонаже:*\n"
        "_Кто ты, откуда, и чего ищешь в этом мире?_"
    )

    await callback.message.answer(intro_text, parse_mode="Markdown")
    await callback.answer()


@user.message()
async def handle_message(message: Message):
    await message.chat.do("typing")
    user_input = message.text
    reply = dnd_bot_interaction(user_input, session_id=str(message.from_user.id))

    # Ищем шаблон броска кубика вида [roll:1d20]
    roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", reply)

    if roll_match:
        count, sides = map(int, roll_match.groups())

        # Убираем метку броска из текста, заменяя её на сообщение ожидания
        reply_text = reply.replace(roll_match.group(0), "🎲 Ждём броска кубика...")

        await message.reply(
            reply_text,
            reply_markup=get_roll_button_keyboard(count, sides),
        )
    else:
        await message.reply(reply)


@user.callback_query(F.data.startswith("roll_"))
async def handle_roll(callback: CallbackQuery):
    # Получаем строку с данными для броска
    dice_str = callback.data[len("roll_") :]
    num, sides = map(int, dice_str.lower().split("d"))

    # Получаем результат броска
    _, result_text = DiceRoller.roll(f"{num}d{sides}")

    # Берём последнее сообщение Narramancer'а
    prev_message = callback.message.reply_to_message
    if not prev_message:
        await callback.answer("Произошла ошибка: не найдено предыдущее сообщение.")
        return

    # Обновляем текст с результатами в original_prompt
    original_prompt = prev_message.text.replace("🎲 Ждём броска кубика...", result_text)

    # Передаем обновленный prompt в модель
    continuation = dnd_bot_interaction(
        original_prompt, session_id=str(callback.from_user.id), roll=result_text
    )

    # Отправляем продолжение от модели
    await callback.message.answer(continuation)

    # Завершаем callback
    await callback.answer()
