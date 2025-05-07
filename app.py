import streamlit as st
from model.model import DNDChatbot
import random
import re

# Настройки
st.set_page_config(page_title="Narramancer", page_icon="🎲")
st.title("🧙‍♂️🏔️ Narramancer — Your Story Begins")


# 📈 Обновление HP/Gold из текста
def update_stats_from_response(response_data):
    if st.session_state.get("stats_parsed", False):
        return

    text = response_data.get("text", "")

    # 🩸 Ищем HP (например: "HP: 72 / 72")
    hp_match = re.search(r"HP:\s*(\d+)\s*/\s*(\d+)", text)
    if hp_match:
        st.session_state.hp = int(hp_match.group(1))
        st.session_state.max_hp = int(hp_match.group(2))

    # 🪙 Ищем золото (например: "Gold Coins: 75")
    gold_match = re.search(r"Gold Coins:\s*(\d+)", text)
    if gold_match:
        st.session_state.gold = int(gold_match.group(1))

    st.session_state.stats_parsed = True


# Инициализация сессии
if "chatbot" not in st.session_state:
    st.session_state.chatbot = DNDChatbot()
    st.session_state.session_id = "streamlit_session"
    st.session_state.messages = []
    st.session_state.character_created = False
    st.session_state.initial_story_shown = False
    st.session_state.hp = 100
    st.session_state.max_hp = 100
    st.session_state.gold = 50
    st.session_state.pending_roll = None
    st.session_state.stats_parsed = False

# Сайдбар — лист персонажа
with st.sidebar:
    st.header("📜 Character Sheet")
    if st.session_state.character_created:
        st.text_input("Name", st.session_state.char_name, disabled=True)
        st.text_input("Class", st.session_state.char_class, disabled=True)
        st.text(f"🪙 Gold: {st.session_state.gold}")
        st.text(f"💖 HP: {st.session_state.hp} / {st.session_state.max_hp}")
        st.progress(st.session_state.hp / st.session_state.max_hp)

# 🔧 Этап создания персонажа
if not st.session_state.character_created:
    st.subheader("🎭 Create Your Character")

    char_name = st.text_input("Name", value="John", key="name_input")
    char_class = st.text_input("Class", value="Warrior", key="class_input")
    char_backstory = st.text_area(
        "Backstory",
        value=(
            "I awoke on a desolate shore, the taste of salt on my lips and sand clinging to my skin. "
            "It seems the sea has cast me here, a broken tide-borne soul. In the distance, a ship "
            "flounders against the rocks, its silhouette splintered by storm and flame. I remember nothing, "
            "only the roar of the waves and the whisper of something lost."
        ),
        height=120,
        key="backstory_input",
    )

    if st.button("Start Adventure"):
        if char_name and char_class and char_backstory:
            st.session_state.char_name = char_name
            st.session_state.char_class = char_class
            st.session_state.char_backstory = char_backstory
            st.session_state.character_created = True

            first_prompt = (
                f"My name is {char_name}, I am a {char_class}. {char_backstory}"
            )

            with st.spinner("Narramancer is preparing your journey..."):
                response_data = st.session_state.chatbot.interact(
                    player_input=first_prompt,
                    session_id=st.session_state.session_id,
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": response_data["text"]}
                )
                update_stats_from_response(response_data)

                # Проверим наличие броска
                roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", response_data["text"])
                if roll_match:
                    st.session_state.pending_roll = (
                        int(roll_match.group(1)),
                        int(roll_match.group(2)),
                    )
                else:
                    st.session_state.pending_roll = None

                st.session_state.initial_story_shown = True
                st.rerun()
        else:
            st.warning("Please fill in all character details.")

# 🧙 Основной чат
else:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    # 🎲 Если ожидается бросок кубика — покажем кнопку
    if st.session_state.pending_roll:
        num_dice, dice_sides = st.session_state.pending_roll
        if st.button(f"🎲 Roll {num_dice}d{dice_sides}"):
            roll_result = sum(random.randint(1, dice_sides) for _ in range(num_dice))
            roll_input = f"Rolled {num_dice}d{dice_sides} → {roll_result}"
            st.chat_message("user").markdown(roll_input)
            st.session_state.messages.append({"role": "user", "content": roll_input})

            with st.spinner("Narramancer is interpreting the result..."):
                response_data = st.session_state.chatbot.interact(
                    player_input=roll_input,
                    session_id=st.session_state.session_id,
                )

            st.session_state.messages.append(
                {"role": "assistant", "content": response_data["text"]}
            )
            update_stats_from_response(response_data)

            # Обновим флаг броска
            roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", response_data["text"])
            if roll_match:
                st.session_state.pending_roll = (
                    int(roll_match.group(1)),
                    int(roll_match.group(2)),
                )
            else:
                st.session_state.pending_roll = None

            st.rerun()

    # 💬 Ввод команды игрока
    player_input = st.chat_input("What do you want to do?")

    if player_input:
        st.session_state.messages.append({"role": "user", "content": player_input})
        with st.spinner("Narramancer is thinking..."):
            response_data = st.session_state.chatbot.interact(
                player_input=player_input,
                session_id=st.session_state.session_id,
            )
        st.session_state.messages.append(
            {"role": "assistant", "content": response_data["text"]}
        )
        update_stats_from_response(response_data)

        # Проверим наличие броска
        roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", response_data["text"])
        if roll_match:
            st.session_state.pending_roll = (
                int(roll_match.group(1)),
                int(roll_match.group(2)),
            )
        else:
            st.session_state.pending_roll = None

        st.rerun()
