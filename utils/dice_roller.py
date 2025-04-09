import re
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class DiceRoller:
    DICE_PATTERN = r"\{\{roll:([\dd]+)\}\}"

    def extract_dice(self, text: str):
        """Находит бросок типа {{roll:1d20}}"""
        match = re.search(self.DICE_PATTERN, text)
        if match:
            return match.group(1)
        return None

    def clean_text(self, text: str):
        """Удаляет шаблон броска из текста"""
        return re.sub(self.DICE_PATTERN, "", text).strip()

    def build_button(self, dice: str):
        """Создаёт inline-кнопку для броска"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🎲 Бросить {dice}", callback_data=f"roll:{dice}"
                    )
                ]
            ]
        )

    @staticmethod
    def roll(dice: str):
        """Симулирует бросок (например, 2d6)"""
        match = re.match(r"(\d*)d(\d+)", dice)
        if not match:
            return [], "[ошибка броска]"
        count, sides = match.groups()
        count = int(count) if count else 1
        sides = int(sides)
        rolls = [random.randint(1, sides) for _ in range(count)]

        # Текстовый фансервис
        rolls_str = " + ".join(str(r) for r in rolls)
        result_text = f"🎲 Ты бросил {dice}: {rolls_str} = {sum(rolls)}"

        return rolls, result_text
