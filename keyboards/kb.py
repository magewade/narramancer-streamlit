from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🧾 О боте", callback_data="rules"),
            InlineKeyboardButton(
                text="🏔️ Начать путешествие", callback_data="start_game"
            ),
        ]
    ]
)


def get_roll_button_keyboard(count, sides):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🎲 Бросить кубик!",
                    callback_data=f"roll_{count}d{sides}",
                )
            ]
        ]
    )
