# 🎲🧙‍♂️ **Narramancer** — Your AI Dungeon Master

> **Streamlit web app** powered by LLMs for creating adventures and guiding solo role-playing games, inspired by **Dungeons & Dragons**.

---

## 🧠 **Core Idea**

**Narramancer** is an AI game master designed to lead players through immersive, interactive adventures. It acts as storyteller and guide, generating dynamic narratives and interpreting dice rolls with character attributes in mind.

### 🎯 **Target Audience**

- **TTRPG beginners** looking for a simple, low-barrier way to start playing.
- **Story lovers** who want to co-create adventures with an AI.
- **Solo players** who enjoy RPGs without needing a human DM.
- **D&D fans** who miss their game master.
- **Content creators** looking for inspiration for their own worlds and stories.

---

## ✨ **Key Features**

- **Manual dice rolls**: players roll the dice themselves via the web interface.
- **Automatic attribute modifiers**: outcomes consider your character’s abilities.
- **Personalized storytelling**: the AI generates unique adventures based on your choices.
- **Multi-session support**: game progress and context are stored between sessions.
- **Simple, no-login UI**: available directly in the browser via Streamlit.

---

## 🛠️ **Tech Stack**

- **LLM API**: [`mistralai`](https://github.com/mistralai/mistral-src)
- **LangChain**: for prompt management and chat history context.
- **SQLAlchemy**: database interaction.
- **SQLite**: stores chat and game session data.
- **dotenv**: environment variable management.
- **Streamlit**: front-end for interaction and story progression.

---

## 🧩 **Implementation Details**

### 💡 **Data Management**

- **Chat history** is stored in SQLite, maintaining context between sessions.
- **Conversation chain** powered by `LangChain`, incorporates past interactions.
- **Embeddings** are generated using the Mistral API to keep game responses contextual.

### 🎲 **Prompting & Dice Mechanics**

- Dice roll format: `[roll:XdY]`, where X is the number of dice, Y is the number of sides.
- When the AI prompts for a roll, the player enters the result manually.
- **Attribute modifiers** affect the result silently. If (roll + (attribute - 10)/2) > 10, the action is considered successful.

### ⚔️ **Combat & Health**

- Player HP is reduced when damage is taken. If HP falls below 0, the character dies.
- Healing is possible through potions, magic, or rest. After each encounter, the app updates the player’s status.

---

## 🚀 **Deployment**

- Hosted using Streamlit
- Interaction happens fully in the browser. Players read the story, respond to prompts, and enter dice rolls in the Streamlit interface.

To run locally:

```bash
$ git clone https://github.com/yourusername/narramancer-streamlit
$ cd narramancer-streamlit
$ python -m venv .venv
$ source .venv/bin/activate   # On Windows: .venv\Scripts\activate
$ pip install -r requirements.txt
$ streamlit run app.py
```

---

## 🎯 Roadmap Ideas

1. Add data for monsters, spells, and items from D&D with images via the [D&amp;D 5e API](https://www.dnd5eapi.co).
2. Include six-sided dice (d6) for combat mechanics.
3. Integrate image generation with a neural network to render custom locations.
4. Add level-up mechanics and stat progression.
5. Improve party-based gameplay (currently optimized for solo play).
