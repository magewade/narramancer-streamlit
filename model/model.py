import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
import sqlalchemy
import re
from langchain_community.chat_message_histories import SQLChatMessageHistory
import random

load_dotenv()


class DNDChatbot:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")

        self.llm = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.7,
        )

        self.system_prompt = (
            "You are Narramancer — the narrator and game master in a role-playing adventure inspired by Dungeons & Dragons.\n\n"
            "Your job is to create a vivid, rich, and unpredictable world for the player, where they make decisions, act, talk, and roll dice. You are not the hero. You are the guide and the storyteller.\n\n"
            "🎭 Interaction with the player:\n"
            "- Never speak for the player. Ever.\n"
            "- Give the player time to choose an action. If a dice roll is needed, ask for it using [roll:XdY] format and wait.\n"
            "- Important: offer either a dice roll or choices — not both at the same time.\n"
            "- Always include: 'You can choose one of the options or propose your own.'\n\n"
            "🧑‍🎤 Character:\n"
            "- At the start, the player describes their character: who they are, where they're from, and what they seek.\n"
            "- Then you must create and SHOW:\n"
            "  • Name, Race, Class\n"
            "  • Attributes (1–20): Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma\n"
            "  • Total attributes ≈ 75–90\n"
            "  • Specify gear, appearance, backstory, items, and magic\n"
            "- DO NOT START THE STORY UNTIL CHARACTER CREATION IS COMPLETE\n\n"
            "🎲 Dice:\n"
            "- Use [roll:XdY] for rolls. Do not invent results.\n"
            "- Use modifiers: roll result + (attribute - 10) / 2.\n"
            "- Result > 10 is success.\n"
            "- Use for attribute checks only (not randomness).\n"
            "- No rolls needed for NPCs.\n\n"
            "🎭 Realism and consequences:\n"
            "- Let the player try anything. NPCs react realistically.\n"
            "- Use logical consequences.\n\n"
            "🌍 Story:\n"
            "- Make it deep, unique, with dilemmas and surprises.\n"
            "- Failure is allowed.\n\n"
            "📏 Max message length — 4000 characters.\n"
            "Use emojis to make the narration more lively.\n\n"
            "You are the Narramancer. Guide the game!"
        )

        self.chat_histories = {}
        os.makedirs("chat_histories", exist_ok=True)
        self.chain = self.create_chain()

    def start_new_game(self, session_id: str):
        history = self.get_session_history(session_id)
        history.clear()

    def create_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{player_input}"),
            ]
        )

        from langchain_core.runnables import RunnablePassthrough

        base_chain = (
            RunnablePassthrough.assign(roll=lambda x: x.get("roll", ""))
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return RunnableWithMessageHistory(
            base_chain,
            self.get_session_history,
            input_messages_key="player_input",
            history_messages_key="chat_history",
            additional_variables=["roll"],
        )

    def interact(
        self, player_input: str, session_id: str = "default_session", roll: str = None
    ):
        try:
            roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", player_input)
            if roll_match:
                num_dice = int(roll_match.group(1))
                dice_sides = int(roll_match.group(2))

                if roll is None:
                    self.chat_histories[session_id] = self.chat_histories.get(
                        session_id, {}
                    )
                    self.chat_histories[session_id][
                        "pending_roll_request"
                    ] = player_input
                    return {
                        "text": f"🎲 You need to roll {num_dice}d{dice_sides}. Tap the roll button!"
                    }

                original_input = self.chat_histories.get(session_id, {}).get(
                    "pending_roll_request", player_input
                )
                roll_result = int(roll)
                response = self.chain.invoke(
                    {"player_input": original_input, "roll": str(roll_result)},
                    {"configurable": {"session_id": session_id}},
                )
                self.chat_histories[session_id]["pending_roll_request"] = None
            else:
                response = self.chain.invoke(
                    {"player_input": player_input, "roll": ""},
                    {"configurable": {"session_id": session_id}},
                )

            return {"text": response}

        except Exception as e:
            return {"text": f"An error occurred: {e}"}

    @staticmethod
    def roll_dice(num: int, sides: int) -> int:
        return sum(random.randint(1, sides) for _ in range(num))

    def get_session_history(self, session_id: str):
        engine = sqlalchemy.create_engine("sqlite:///database/chat_history.db")
        return SQLChatMessageHistory(session_id=session_id, connection=engine)
