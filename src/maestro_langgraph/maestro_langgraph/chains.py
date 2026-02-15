from typing import Optional, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools import DuckDuckGoSearchRun

from .prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    EMOTION_DETECTION_PROMPT,
    ROBOT_PERSONA,
    BUSY_RESPONSE_PROMPT,
    PROBLEM_ANNOUNCEMENT_PROMPT,
    format_notifications,
    USER_RESPONSE_CLASSIFICATION_PROMPT,
    SENSOR_INTEGRATED_RESPONSE_PROMPT,
    DEFERRED_RESPONSE_PROMPT,
    IMPROVEMENT_CELEBRATION_PROMPT,
)
from .state import Intent, Emotion, RobotStatus
from .sensor_tracker import UserResponseType, SensorType, THRESHOLDS
from .solutions import get_solutions, get_quick_fix


DEFAULT_MODEL = "qwen2:0.5b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_LMSTUDIO_URL = "http://localhost:1234/v1"

BackendType = Literal["ollama", "lmstudio"]


def create_llm(
    backend: BackendType = "ollama",
    model_name: str = DEFAULT_MODEL,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
):
    if backend == "lmstudio":
        from langchain_openai import ChatOpenAI

        url = base_url or DEFAULT_LMSTUDIO_URL

        return ChatOpenAI(
            base_url=url,
            api_key="lm-studio",
            model=model_name or "local-model",
            temperature=temperature,
        )
    else:
        from langchain_ollama import ChatOllama

        url = base_url or DEFAULT_OLLAMA_URL
        return ChatOllama(
            model=model_name,
            base_url=url,
            temperature=temperature,
        )


class DialogueChains:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,
        backend: BackendType = "ollama",
    ):
        self.model_name = model_name
        self.backend = backend
        self.base_url = base_url

        self.llm = create_llm(
            backend=backend,
            model_name=model_name,
            base_url=base_url,
            temperature=0.7,
        )

        self.search_tool = DuckDuckGoSearchRun()

        self._setup_chains()

    def _setup_chains(self):
        intent_prompt = ChatPromptTemplate.from_template(INTENT_CLASSIFICATION_PROMPT)
        self.intent_chain = intent_prompt | self.llm | StrOutputParser()

        response_prompt = ChatPromptTemplate.from_messages([
            ("system", ROBOT_PERSONA),
            ("human", RESPONSE_GENERATION_PROMPT),
        ])
        self.response_chain = response_prompt | self.llm | StrOutputParser()

        emotion_prompt = ChatPromptTemplate.from_template(EMOTION_DETECTION_PROMPT)
        self.emotion_chain = emotion_prompt | self.llm | StrOutputParser()

        busy_prompt = ChatPromptTemplate.from_template(BUSY_RESPONSE_PROMPT)
        self.busy_chain = busy_prompt | self.llm | StrOutputParser()

        problem_prompt = ChatPromptTemplate.from_template(PROBLEM_ANNOUNCEMENT_PROMPT)
        self.problem_chain = problem_prompt | self.llm | StrOutputParser()

        user_response_prompt = ChatPromptTemplate.from_template(USER_RESPONSE_CLASSIFICATION_PROMPT)
        self.user_response_chain = user_response_prompt | self.llm | StrOutputParser()

        sensor_response_prompt = ChatPromptTemplate.from_template(SENSOR_INTEGRATED_RESPONSE_PROMPT)
        self.sensor_response_chain = sensor_response_prompt | self.llm | StrOutputParser()

        deferred_prompt = ChatPromptTemplate.from_template(DEFERRED_RESPONSE_PROMPT)
        self.deferred_chain = deferred_prompt | self.llm | StrOutputParser()

        celebration_prompt = ChatPromptTemplate.from_template(IMPROVEMENT_CELEBRATION_PROMPT)
        self.celebration_chain = celebration_prompt | self.llm | StrOutputParser()

    def classify_intent(self, message: str) -> str:
        try:
            result = self.intent_chain.invoke({"message": message})
            intent = result.strip().lower()

            valid_intents = [i.value for i in Intent]
            if intent in valid_intents:
                return intent

            if any(g in intent for g in ["greet", "hello", "hi"]):
                return Intent.GREETING.value
            if any(f in intent for f in ["farewell", "bye", "goodbye", "quit"]):
                return Intent.FAREWELL.value
            if any(q in intent for q in ["question", "ask", "what", "who", "how", "search"]):
                return Intent.QUESTION.value
            if any(a in intent for a in ["acknowledge", "yes", "no", "ok"]):
                return Intent.ACKNOWLEDGMENT.value

            return Intent.GENERAL.value

        except Exception as e:
            print(f"Intent classification error: {e}")
            return Intent.GENERAL.value

    def search_web(self, query: str) -> str:
        try:
            results = self.search_tool.invoke(query)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return f"I couldn't search for that right now."

    def generate_response(
        self,
        message: str,
        emotion: str = "neutral",
        history: Optional[list] = None,
        search_context: Optional[str] = None,
    ) -> str:
        try:
            history_str = ""
            if history:
                for role, msg in history[-5:]:
                    history_str += f"{role}: {msg}\n"

            context_str = ""
            if search_context:
                context_str = f"\n\nRelevant information from web search:\n{search_context}\n"

            result = self.response_chain.invoke({
                "message": message + context_str,
                "emotion": emotion,
                "history": history_str or "No previous conversation.",
            })
            return result.strip()

        except Exception as e:
            print(f"Response generation error: {e}")
            return "I'm having trouble responding right now."

    def detect_emotion(self, user_message: str, robot_response: str) -> str:
        try:
            result = self.emotion_chain.invoke({
                "user_message": user_message,
                "robot_response": robot_response,
            })
            emotion = result.strip().lower()

            valid_emotions = [e.value for e in Emotion]
            if emotion in valid_emotions:
                return emotion

            if "happ" in emotion or "joy" in emotion:
                return Emotion.HAPPY.value
            if "sad" in emotion:
                return Emotion.SAD.value
            if "ang" in emotion:
                return Emotion.ANGER.value
            if "surpr" in emotion:
                return Emotion.SURPRISE.value

            return Emotion.NEUTRAL.value

        except Exception as e:
            print(f"Emotion detection error: {e}")
            return Emotion.NEUTRAL.value

    def should_search(self, message: str, intent: str) -> bool:
        if intent == Intent.QUESTION.value:
            search_triggers = [
                "what is", "who is", "who was", "what was",
                "tell me about", "search for", "look up",
                "find", "how to", "where is", "when did",
            ]
            msg_lower = message.lower()
            return any(trigger in msg_lower for trigger in search_triggers)
        return False

    def generate_busy_response(self, message: str) -> str:
        try:
            result = self.busy_chain.invoke({"message": message})
            return result.strip()
        except Exception as e:
            print(f"Busy response generation error: {e}")
            return "I'm sorry, I'm currently busy with a task. Please wait a moment."

    def generate_problem_response(self, message: str, notifications: dict) -> str:
        try:
            problems_text = format_notifications(notifications)
            result = self.problem_chain.invoke({
                "message": message,
                "problems": problems_text,
            })
            return result.strip()
        except Exception as e:
            print(f"Problem response generation error: {e}")
            return "I've detected some issues with the soil that need attention."

    def determine_robot_status(
        self,
        robot_busy: bool,
        notifications: dict,
    ) -> str:
        if robot_busy:
            return RobotStatus.BUSY.value
        elif notifications:
            return RobotStatus.PROBLEM.value
        else:
            return RobotStatus.FREE.value

    def classify_user_response(self, message: str, issue_description: str) -> UserResponseType:
        try:
            result = self.user_response_chain.invoke({
                "message": message,
                "issue_description": issue_description,
            })
            response = result.strip().lower()

            mapping = {
                "committed": UserResponseType.COMMITTED,
                "deferred": UserResponseType.DEFERRED,
                "rejected": UserResponseType.REJECTED,
                "question": UserResponseType.QUESTION,
                "unrelated": UserResponseType.UNRELATED,
            }
            return mapping.get(response, UserResponseType.UNRELATED)
        except Exception as e:
            print(f"User response classification error: {e}")
            return UserResponseType.UNRELATED

    def generate_sensor_integrated_response(
        self,
        base_response: str,
        issue: dict,
        solution: dict,
    ) -> str:
        try:
            sensor_type = SensorType(issue["sensor_type"])
            threshold = THRESHOLDS[sensor_type]

            result = self.sensor_response_chain.invoke({
                "base_response": base_response,
                "sensor_type": issue["sensor_type"],
                "value": issue["current_value"],
                "unit": threshold.unit,
                "optimal_min": threshold.optimal_min,
                "optimal_max": threshold.optimal_max,
                "direction": "too low" if issue["direction"] == "too_low" else "too high",
                "severity": issue["severity"],
                "action": solution["action"] if solution else "check on it",
                "outcome": f"get it back to optimal levels ({threshold.optimal_min}-{threshold.optimal_max}{threshold.unit})",
            })
            return result.strip()
        except Exception as e:
            print(f"Sensor integrated response error: {e}")
            return base_response

    def generate_deferred_response(
        self,
        message: str,
        issue: dict,
        quick_fix: dict,
    ) -> str:
        try:
            sensor_type = SensorType(issue["sensor_type"])
            threshold = THRESHOLDS[sensor_type]

            result = self.deferred_chain.invoke({
                "sensor_type": issue["sensor_type"],
                "value": issue["current_value"],
                "unit": threshold.unit,
                "optimal_min": threshold.optimal_min,
                "optimal_max": threshold.optimal_max,
                "message": message,
                "time_until_damage": quick_fix["time_until_damage"] if quick_fix else "soon",
                "quick_fix_action": quick_fix["action"] if quick_fix else "a quick check",
            })
            return result.strip()
        except Exception as e:
            print(f"Deferred response error: {e}")
            return "I understand. Just keep an eye on it when you can."

    def generate_celebration_response(
        self,
        base_response: str,
        sensor_type: str,
        previous_value: float,
        current_value: float,
    ) -> str:
        try:
            result = self.celebration_chain.invoke({
                "base_response": base_response,
                "sensor_type": sensor_type,
                "previous_value": previous_value,
                "current_value": current_value,
            })
            return result.strip()
        except Exception as e:
            print(f"Celebration response error: {e}")
            return base_response
