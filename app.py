import streamlit as st
from model.model import DNDChatbot
import random
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки
st.set_page_config(page_title="Narramancer", page_icon="🎲")
st.title("🧙‍♂️🏔️ Narramancer — Your Story Begins")

# Пути к картинкам
dice_image_folder = "data/dice/"


# Функция для отображения картинки кубика
def show_dice_image(roll_result):
    dice_image_path = os.path.join(dice_image_folder, f"{roll_result}.png")
    if os.path.exists(dice_image_path):
        st.image(
            dice_image_path,
            caption=f"Result: {roll_result}",
            width=200
        )
    else:
        st.warning("No image found for this roll result.")


# 🆕 Сайдбар — лист персонажа
def render_sidebar():
    with st.sidebar:
        st.header("📜 Character Sheet")
        if st.session_state.character_created:
            # Уникальные ключи, чтобы избежать конфликтов
            st.text_input(
                "Name",
                st.session_state.get("char_name", ""),
                disabled=True,
                key="sidebar_name_input",
            )
            st.text_input(
                "Class",
                st.session_state.get("char_class", ""),
                disabled=True,
                key="sidebar_class_input",
            )

            # Добавляем кнопку для начала новой игры
            if st.button("Start New Game"):
                # Сброс состояния
                st.session_state.character_created = False
                st.session_state.messages = []
                st.session_state.pending_roll = None
                st.session_state.stats_parsed = False
                st.session_state.initial_story_shown = False
                st.session_state.chatbot = DNDChatbot()
                st.session_state.session_id = "streamlit_session"
                st.rerun()  # Перезагружаем приложение


# Инициализация сессии
if "chatbot" not in st.session_state:
    st.session_state.chatbot = DNDChatbot()
    st.session_state.session_id = "streamlit_session"
    st.session_state.messages = []
    st.session_state.character_created = False
    st.session_state.initial_story_shown = False
    st.session_state.pending_roll = None
    st.session_state.stats_parsed = False
    st.write("🚀 Session initialized")

# Отображаем сайдбар
render_sidebar()

# 🔧 Этап создания персонажа
if not st.session_state.character_created:
    st.subheader("🎭 Create Your Character")

    char_name = st.text_input("Name", value="John", key="create_name_input")
    char_class = st.text_input("Class", value="Rogue", key="create_class_input")
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
                st.write("🧪 RAW response before stats parsing:", response_data)

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

    # Пример использования в основном коде
    if st.session_state.pending_roll:
        num_dice, dice_sides = st.session_state.pending_roll
        if st.button(f"🎲 Roll {num_dice}d{dice_sides}"):
            roll_result = sum(random.randint(1, dice_sides) for _ in range(num_dice))
            roll_input = f"Rolled {num_dice}d{dice_sides} → {roll_result}"

            # Отображаем результат и картинку
            st.chat_message("user").markdown(roll_input)
            st.session_state.messages.append({"role": "user", "content": roll_input})

            # Показываем картинку с результатом
            show_dice_image(roll_result)

            with st.spinner("Narramancer is interpreting the result..."):
                response_data = st.session_state.chatbot.interact(
                    player_input=roll_input,
                    session_id=st.session_state.session_id,
                )

            st.session_state.messages.append(
                {"role": "assistant", "content": response_data["text"]}
            )

            roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", response_data["text"])
            if roll_match:
                st.session_state.pending_roll = (
                    int(roll_match.group(1)),
                    int(roll_match.group(2)),
                )
            else:
                st.session_state.pending_roll = None

            st.rerun()

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

        roll_match = re.search(r"\[roll:(\d+)d(\d+)\]", response_data["text"])
        if roll_match:
            st.session_state.pending_roll = (
                int(roll_match.group(1)),
                int(roll_match.group(2)),
            )
        else:
            st.session_state.pending_roll = None

        st.rerun()
