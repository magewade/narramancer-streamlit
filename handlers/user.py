from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatAction
from aiogram.filters import Command
import re

from keyboards import kb
from model.model import DNDChatbot
from utils.dice_roller import DiceRoller
from keyboards.kb import get_roll_button_keyboard
from aiogram.types import FSInputFile
from aiogram.types import CallbackQuery

user = Router()
dice_roller = DiceRoller()
dnd_chatbot = DNDChatbot()
dnd_bot_interaction = DNDChatbot().interact


@user.message(CommandStart())
async def start(message: Message):
    image_url = "https://i.imgur.com/H1vGYpH.png"
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


# Пример функции для /rules
@user.message(Command("rules"))
async def show_rules(message: types.Message):
    # Текст с правилами
    rules_text = (
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

    # Отправляем правила игры пользователю
    await message.answer(rules_text, parse_mode="Markdown")


@user.callback_query(F.data == "start_game")
async def start_game(callback: CallbackQuery):
    # Сброс истории чата для текущего игрока
    dnd_chatbot.start_new_game(session_id=str(callback.from_user.id))

    await callback.message.bot.send_chat_action(
        chat_id=callback.from_user.id, action=ChatAction.TYPING
    )

    intro_text = (
        "✨ Пелена реальности расступается, и ты оказываешься на пороге великого приключения...\n\n"
        "👤 *Расскажи о своём персонаже, а Narramancer бросит кубики и подберет тебе характеристики:*\n"
        "_Кто ты, откуда, и чего ищешь в этом мире?_"
    )

    await callback.message.answer(intro_text, parse_mode="Markdown")
    await callback.answer()


@user.message(Command("start_game"))
async def start_game(message: types.Message):
    session_id = str(message.from_user.id)  # Уникальный идентификатор для пользователя

    # Логика начала новой игры
    dnd_chatbot.start_new_game(session_id)

    # Ответ пользователю
    await message.answer(
        "✨ Пелена реальности расступается, и ты оказываешься на пороге великого приключения...\n\n"
        "👤 *Расскажи о своём персонаже, а Narramancer бросит кубики и подберет тебе характеристики:*\n"
        "_Кто ты, откуда, и чего ищешь в этом мире?_",
        parse_mode="Markdown")


@user.message()
async def handle_message(message: Message):
    await message.chat.do("typing")
    user_input = message.text
    reply = dnd_bot_interaction(user_input, session_id=str(message.from_user.id))

    # Ищем все шаблоны бросков кубика вида [roll:XdY]
    roll_matches = list(re.finditer(r"\[roll:(\d+)d(\d+)\]", reply))

    if roll_matches:
        # Берем первый найденный матч
        roll_match = roll_matches[0]
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
    dice_str = callback.data[len("roll_") :]  # Получаем строку с типом кубика
    num, sides = map(int, dice_str.lower().split("d"))

    # Получаем результат броска
    rolls, result_text = DiceRoller.roll(f"{num}d{sides}")

    # Сообщение от бота о том, что игрок должен бросить кубик
    await callback.message.answer(f"🎲 Бросаю кубик...")

    # Отправка изображения кубика
    rolled_value = sum(rolls)
    image_path = f"data/dice/{rolled_value}.png"  # путь к нужной картинке

    dice_image = FSInputFile(image_path)
    await callback.message.answer_photo(dice_image)

    # Сообщение от игрока о результате броска
    result_from_player = f"🎲 На кубике выпало: {sum(rolls)}"
    await callback.message.answer(result_from_player)

    # Вставляем результат броска в ответ модели, чтобы она использовала его в следующем шаге
    continuation = dnd_bot_interaction(
        f"На кубике выпало: {sum(rolls)}", 
        session_id=str(callback.from_user.id)
    )

    # Проверяем наличие следующего броска в продолжении
    roll_matches = list(re.finditer(r"\[roll:(\d+)d(\d+)\]", continuation))

    if roll_matches:
        # Берем первый найденный матч
        roll_match = roll_matches[0]
        count, sides = map(int, roll_match.groups())

        # Убираем метку броска из текста, заменяя её на сообщение ожидания
        continuation_text = continuation.replace(roll_match.group(0), "🎲 Ждём броска кубика...")

        await callback.message.answer(
            continuation_text,
            reply_markup=get_roll_button_keyboard(count, sides),
        )
    else:
        # Если больше нет бросков, просто отправляем продолжение
        await callback.message.answer(continuation)

    await callback.answer()
