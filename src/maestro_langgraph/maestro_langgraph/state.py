from typing import TypedDict, Optional, Literal
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    FAREWELL = "farewell"
    QUESTION = "question"
    ACKNOWLEDGMENT = "acknowledgment"
    GENERAL = "general"


class Emotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGER = "anger"
    SURPRISE = "surprise"


class RobotStatus(str, Enum):
    FREE = "free"
    BUSY = "busy"
    PROBLEM = "problem"


class DialogueState(TypedDict, total=False):
    human_message: str
    voice_emotion: str

    robot_busy: bool
    robot_status: str
    has_problem: bool
    notifications: dict

    conversation_history: list

    intent: str
    entities: dict
    search_context: Optional[str]
    context_response: Optional[str]

    response: str
    response_emotion: str
    prosody: tuple
    should_end_early: bool

    sensor_tracker_state: dict
    issues_to_mention: list
    sensor_context: Optional[str]
    user_response_type: Optional[str]
    pending_issue: Optional[dict]
    improvement_detected: Optional[dict]
    last_suggested_solution: Optional[str]


PROSODY_PRESETS = {
    Emotion.NEUTRAL: (150, 100, 45),
    Emotion.HAPPY: (160, 140, 65),
    Emotion.SAD: (80, 80, 35),
    Emotion.ANGER: (180, 200, 55),
    Emotion.SURPRISE: (200, 80, 65),
}


def get_prosody_for_emotion(emotion: str) -> tuple:
    try:
        return PROSODY_PRESETS[Emotion(emotion)]
    except (ValueError, KeyError):
        return PROSODY_PRESETS[Emotion.NEUTRAL]
