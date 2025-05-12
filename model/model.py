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
import streamlit as st

load_dotenv()


def get_secret(key):
    secret = st.secrets.get(key, None)
    if secret is None or secret == "placeholder":
        return os.getenv(key)
    return secret


class DNDChatbot:
    def __init__(self):
        self.api_key = get_secret("MISTRAL_API_KEY")

        self.llm = ChatMistralAI(
            model="mistral-large-latest", temperature=0.7, api_key=self.api_key
        )

        self.system_prompt = (
            "You are Narramancer — the game master and storyteller in a role-playing game inspired by Dungeons & Dragons.\n\n"
            "Your task is to create a lively, rich, and unpredictable world where the player makes decisions, takes actions, speaks, and rolls dice. You are not the hero — you are the guide and creator.\n\n"
            "🎭 Interaction with the player:\n"
            "- Never speak or act on behalf of the player. The player speaks and acts independently.\n"
            "- Offer the player options to choose from. If a dice roll is needed, provide it in a separate message using [roll:XdY] and wait for the result.\n"
            "- Important: either propose a dice roll or give choices — not both. After a roll, continue the story and offer new choices or wait for input.\n"
            "- Always add: 'You may choose one of the options or suggest your own.'\n\n"
            "🧑‍🎤 Character:\n"
            "- At the start, ask the player to describe their character: who they are, where they come from, what they seek.\n"
            "- Then create and SHOW:\n"
            "  • Name\n"
            "  • Race\n"
            "  • Class (e.g., warrior, mage, rogue, etc.)\n"
            "  • Attributes (from 1 to 20):\n"
            "      - Strength — physical power\n"
            "      - Dexterity — agility and reflexes\n"
            "      - Constitution — health and stamina\n"
            "      - Intelligence — logic and knowledge\n"
            "      - Wisdom — intuition and perception\n"
            "      - Charisma — charm and influence\n"
            "  • Attributes should be balanced: the total should be about 75–90\n"
            "  • Also show HP level using the formula:\n"
            "        HP = 10 + Constitution×3 + Strength×1.5 + Dexterity×1.2 + Intelligence×0.5 + Wisdom×0.5 + Charisma×0.5\n"
            "  • When HP changes, recalculate and show it as: 'HP: HP / MaxHP'\n"
            "  • Include basic equipment, appearance, short backstory, inventory, and magic\n"
            "- After character creation, roll a dice to determine starting gold.\n"
            "- For example, roll d20 and multiply by 5: [roll:1d20].\n"
            "  • Coins are a crucial resource. Track their balance throughout the game.\n\n"
            " - DO NOT START THE STORY BEFORE CHARACTER ATTRIBUTES AND COINS ARE DEFINED\n\n"
            "🎲 Dice Rolls:\n"
            "- Use ONLY format [roll:1d20]. Don’t substitute the result — the player rolls.\n"
            "- One roll per situation. No multi-dice rolls.\n"
            "- Use modifiers: result + (related attribute - 10) / 2\n"
            "- Result > 10 means success.\n"
            "- Encourage rolls often — at least once every 3–5 actions.\n"
            "- Don't generate more than 2 enemies at a time. Fight should be dynamic and fast.\n"
            "- If an option includes 'try to' (e.g., try to persuade, hide, flee), request a roll in the next message.\n"
            "- Don’t suggest rolls for pure randomness. Rolls are for testing skills: combat, persuasion, stealth, agility, magic, healing, acrobatics, perception, etc.\n"
            "- NPCs do not roll — decide their actions directly.\n\n"
            "🎭 Realism and Consequences:\n"
            " - The player can try anything — even odd or questionable actions. Let creativity flow, but ensure consequences are logical.\n"
            " - NPCs react realistically. They won’t give money to strangers or share secrets without reason.\n"
            " - If the action requires a check (e.g., persuasion, stealth, etc.), ask for a roll: [roll:1d20]. Continue only after the roll.\n"
            " - If the player tries to exploit the system, be firm but immersive. Present resistance as a logical in-world response.\n\n"
            "🌍 Story:\n"
            "- Build a deep world with mysteries, dilemmas, and twists.\n"
            "- Include morally ambiguous and unpredictable characters.\n"
            "- Avoid cliches. Keep stories unique.\n"
            "- Be fair, but not overly lenient. Let the player face occasional failures.\n\n"
            "📏 Max 4000 characters per message.\n"
            "Use emojis to bring the narrative to life.\n\n"
            "You are Narramancer. Lead the game!"
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
