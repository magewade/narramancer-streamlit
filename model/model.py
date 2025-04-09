import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
import re 
import random 
# Загрузка переменных окружения
load_dotenv()

# Класс для управления чат-ботом D&D
class DNDChatbot:
    def __init__(self):
        # Получение API ключа
        self.api_key = os.getenv("MISTRAL_API_KEY")

        # Инициализация языковой модели
        self.llm = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.7,  # Немного повышенная температура для креативности
            )

        # Системный промпт для D&D бота
        self.system_prompt = """Ты Narramancer - мастер для настольной ролевой игры похожей на Dungeons & Dragons. 
        Твои задачи:
        - Создавать увлекательные и динамичные сюжетные повороты
        - Описывать окружение, персонажей и события
        - Помогать игрокам погрузиться в мир приключений
        - Следить за правилами и механикой игры
        - Ты не решаешь за игрока что ему делать и говорить, каждый раз когда история подводит к этому, предлагать несколько вариантов или написать самостоятельно
        - Если игрок должен бросить кубик, не делай это сам. Вместо этого вставь в текст: {{roll:1d20}}, где X — количество кубиков, Y — число граней (например, {{roll:1d20}}). Narramancer покажет игроку кнопку для броска.
        - Если действие требует броска кубика (например, инициативы, ловкости и т.д.), используй специальный шаблон вида: {{roll:1d20}} или {{roll:2d6}}
        - После вставки {{roll:XdY}} не продолжай рассказ, пока игрок не бросил кубик
        - Не предлагай варианты развития событий или действий до получения результата броска
        - После броска кубика ты можешь продолжить историю в зависимости от результата
        - Быть справедливым и создавать захватывающую историю
        - Игрок начинает с введения своего персонажа, если он начинает с чего-то другого, предложи ему создать персонажа
        - Попытайся влезть в лимит в 4000 символов за одно сообщение (можно меньше, но не больше)

        Веди себя как опытный рассказчик и организатор приключений."""

        # Словарь для хранения истории чатов
        self.chat_histories = {}

        # Создание цепочки обработки
        self.chain = self.create_chain()

    def create_chain(self):
        """Создание цепочки обработки с историей сообщений"""
        # Создание шаблона чата
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{player_input}"),
        ])

        # Основная цепочка с добавлением переменной roll
        from langchain_core.runnables import RunnablePassthrough

        base_chain = (
            RunnablePassthrough.assign(roll=lambda x: x.get('roll', ''))
            | prompt 
            | self.llm 
            | StrOutputParser()
        )

        # Создание цепочки с историей
        return RunnableWithMessageHistory(
            base_chain,
            self.get_session_history,
            input_messages_key="player_input",
            history_messages_key="chat_history",
            additional_variables=["roll"]  # Добавляем roll как дополнительную переменную
        )

    def interact(self, player_input: str, session_id: str = "default_session", roll: str = None):
        """Взаимодействие с чат-ботом с обработкой бросков кубика"""
        try:
            # Проверка наличия формата броска кубика
            roll_match = re.search(r'\{roll:(\d+)d(\d+)\}', player_input)
            
            if roll_match:
                # Извлечение параметров броска
                num_dice = int(roll_match.group(1))
                dice_sides = int(roll_match.group(2))
                
                # Если результат броска не передан, генерируем его
                if roll is None:
                    roll_result = sum(random.randint(1, dice_sides) for _ in range(num_dice))
                else:
                    roll_result = int(roll)
                
                # Заменяем метку броска на результат
                modified_input = player_input.replace(
                    roll_match.group(0), 
                    f"(Бросок {num_dice}d{dice_sides}: {roll_result})"
                )
                
                # Выполнение запроса с сохранением истории
                response = self.chain.invoke(
                    {
                        "player_input": modified_input,
                        "roll": str(roll_result)
                    }, 
                    {"configurable": {"session_id": session_id}}
                )
                
                return response
            
            else:
                # Обычный режим без броска
                response = self.chain.invoke(
                    {"player_input": player_input}, 
                    {"configurable": {"session_id": session_id}}
                )
                return response
        
        except Exception as e:
            return f"Произошла ошибка: {e}"
        
    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """Получение или создание истории сообщений для сессии"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = InMemoryChatMessageHistory()
        return self.chat_histories[session_id]

    def interact(self, player_input: str, session_id: str = "default_session"):
        """Взаимодействие с чат-ботом"""
        try:
            # Выполнение запроса с сохранением истории
            response = self.chain.invoke(
                {"player_input": player_input}, 
                {"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            return f"Произошла ошибка: {e}"
