from typing import Literal, Optional
from langgraph.graph import StateGraph, END

from .state import DialogueState, Intent, RobotStatus, Emotion, get_prosody_for_emotion
from .chains import DialogueChains
from .sensor_tracker import SensorTracker, UserResponseType, SensorType, THRESHOLDS
from .solutions import get_solutions, get_quick_fix


_chains: DialogueChains = None

_tracker: SensorTracker = None


def get_chains() -> DialogueChains:
    global _chains
    if _chains is None:
        _chains = DialogueChains()
    return _chains


def set_chains(chains: DialogueChains):
    global _chains
    _chains = chains


def get_tracker() -> SensorTracker:
    global _tracker
    if _tracker is None:
        _tracker = SensorTracker()
    return _tracker


def set_tracker(tracker: SensorTracker):
    global _tracker
    _tracker = tracker


def check_context_node(state: DialogueState) -> DialogueState:
    chains = get_chains()

    robot_busy = state.get("robot_busy", False)
    notifications = state.get("notifications", {})
    message = state.get("human_message", "")

    status = chains.determine_robot_status(robot_busy, notifications)

    context_response = None
    should_end_early = False

    if status == RobotStatus.BUSY.value:
        context_response = chains.generate_busy_response(message)
        should_end_early = True

    elif status == RobotStatus.PROBLEM.value:
        context_response = chains.generate_problem_response(message, notifications)
        should_end_early = False

    return {
        **state,
        "robot_status": status,
        "context_response": context_response,
        "should_end_early": should_end_early,
    }


def classify_intent_node(state: DialogueState) -> DialogueState:
    chains = get_chains()
    message = state.get("human_message", "")

    intent = chains.classify_intent(message)

    return {**state, "intent": intent}


def check_search_node(state: DialogueState) -> DialogueState:
    chains = get_chains()

    message = state.get("human_message", "")
    intent = state.get("intent", Intent.GENERAL.value)

    search_context = None

    if chains.should_search(message, intent):
        search_context = chains.search_web(message)

    return {**state, "search_context": search_context}


def generate_response_node(state: DialogueState) -> DialogueState:
    chains = get_chains()

    context_response = state.get("context_response")
    if context_response:
        return {**state, "response": context_response}

    message = state.get("human_message", "")
    voice_emotion = state.get("voice_emotion", "neutral")
    history = state.get("conversation_history", [])
    search_context = state.get("search_context")

    response = chains.generate_response(
        message=message,
        emotion=voice_emotion,
        history=history,
        search_context=search_context,
    )

    return {**state, "response": response}


def determine_emotion_node(state: DialogueState) -> DialogueState:
    chains = get_chains()
    robot_status = state.get("robot_status", RobotStatus.FREE.value)

    if robot_status == RobotStatus.BUSY.value:
        emotion = Emotion.NEUTRAL.value
    elif robot_status == RobotStatus.PROBLEM.value:
        emotion = Emotion.SAD.value
    else:
        message = state.get("human_message", "")
        response = state.get("response", "")
        emotion = chains.detect_emotion(message, response)

    prosody = get_prosody_for_emotion(emotion)

    return {**state, "response_emotion": emotion, "prosody": prosody}


def update_history_node(state: DialogueState) -> DialogueState:
    history = state.get("conversation_history", [])
    message = state.get("human_message", "")
    response = state.get("response", "")

    history = list(history)
    history.append(("Human", message))
    history.append(("Plantroid", response))

    if len(history) > 10:
        history = history[-10:]

    return {**state, "conversation_history": history}


def process_sensor_issues_node(state: DialogueState) -> DialogueState:
    tracker = get_tracker()

    if state.get("sensor_tracker_state"):
        tracker.load_state(state["sensor_tracker_state"])

    notifications = state.get("notifications", {})
    improvement = None

    for sensor_name, values in notifications.items():
        try:
            if isinstance(values, (list, tuple)) and len(values) > 0:
                value = float(str(values[0]).replace("%", "").replace("°C", "").replace("lux", "").strip())
            else:
                value = float(str(values).replace("%", "").replace("°C", "").replace("lux", "").strip())

            result = tracker.process_notification(sensor_name, value)
            if result and result.severity.value == "optimal":
                improvement = result
        except (ValueError, TypeError):
            continue

    issues = tracker.get_issues_to_mention()

    return {
        **state,
        "sensor_tracker_state": tracker.to_state(),
        "issues_to_mention": [i.to_dict() for i in issues],
        "improvement_detected": improvement.to_dict() if improvement else None,
    }


def check_user_response_node(state: DialogueState) -> DialogueState:
    tracker = get_tracker()
    chains = get_chains()

    pending = tracker.get_pending_issue()
    if not pending:
        return {**state, "user_response_type": None, "pending_issue": None}

    message = state.get("human_message", "")
    issue_desc = f"{pending.sensor_type.value} is {pending.direction.replace('_', ' ')}"

    response_type = chains.classify_user_response(message, issue_desc)
    tracker.record_user_response(response_type)

    return {
        **state,
        "user_response_type": response_type.value,
        "pending_issue": pending.to_dict(),
        "sensor_tracker_state": tracker.to_state(),
    }


def integrate_sensor_response_node(state: DialogueState) -> DialogueState:
    chains = get_chains()
    tracker = get_tracker()

    base_response = state.get("response", "")
    user_response_type = state.get("user_response_type")
    issues = state.get("issues_to_mention", [])
    pending = state.get("pending_issue")
    improvement = state.get("improvement_detected")

    if improvement:
        response = chains.generate_celebration_response(
            base_response=base_response,
            sensor_type=improvement["sensor_type"],
            previous_value=improvement.get("current_value", 0),
            current_value=0,
        )
        return {**state, "response": response, "response_emotion": "happy"}

    if user_response_type == UserResponseType.DEFERRED.value and pending:
        sensor_type = SensorType(pending["sensor_type"])
        quick_fix = get_quick_fix(sensor_type, pending["direction"])

        response = chains.generate_deferred_response(
            message=state.get("human_message", ""),
            issue=pending,
            quick_fix={"action": quick_fix.action, "time_until_damage": quick_fix.time_until_damage} if quick_fix else None,
        )
        tracker.clear_pending_issue()
        return {**state, "response": response, "sensor_tracker_state": tracker.to_state()}

    if user_response_type == UserResponseType.COMMITTED.value:
        tracker.clear_pending_issue()
        return {
            **state,
            "response": base_response + " Thank you, I appreciate your help!",
            "sensor_tracker_state": tracker.to_state(),
        }

    if issues:
        issue = issues[0]
        sensor_type = SensorType(issue["sensor_type"])
        solutions = get_solutions(sensor_type, issue["direction"], issue.get("solutions_suggested", []))
        solution = solutions[0] if solutions else None

        response = chains.generate_sensor_integrated_response(
            base_response=base_response,
            issue=issue,
            solution={"action": solution.action} if solution else None,
        )

        if issue["sensor_type"] in tracker.active_issues:
            tracker.record_mention(
                tracker.active_issues[issue["sensor_type"]],
                [solution.description] if solution else []
            )

        return {
            **state,
            "response": response,
            "last_suggested_solution": solution.description if solution else None,
            "sensor_tracker_state": tracker.to_state(),
        }

    return state


def route_after_context(state: DialogueState) -> Literal["busy_response", "normal_flow"]:
    should_end_early = state.get("should_end_early", False)

    if should_end_early:
        return "busy_response"
    return "normal_flow"


def route_after_intent(state: DialogueState) -> Literal["search", "respond"]:
    chains = get_chains()
    message = state.get("human_message", "")
    intent = state.get("intent", "")

    if chains.should_search(message, intent):
        return "search"
    return "respond"


def build_dialogue_graph() -> StateGraph:
    graph = StateGraph(DialogueState)

    graph.add_node("check_context", check_context_node)
    graph.add_node("process_sensors", process_sensor_issues_node)
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("check_user_response", check_user_response_node)
    graph.add_node("check_search", check_search_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("integrate_sensors", integrate_sensor_response_node)
    graph.add_node("determine_emotion", determine_emotion_node)
    graph.add_node("update_history", update_history_node)

    graph.set_entry_point("check_context")

    graph.add_conditional_edges(
        "check_context",
        route_after_context,
        {
            "busy_response": "generate_response",
            "normal_flow": "process_sensors",
        }
    )

    graph.add_edge("process_sensors", "classify_intent")
    graph.add_edge("classify_intent", "check_user_response")
    graph.add_edge("check_user_response", "check_search")
    graph.add_edge("check_search", "generate_response")
    graph.add_edge("generate_response", "integrate_sensors")
    graph.add_edge("integrate_sensors", "determine_emotion")
    graph.add_edge("determine_emotion", "update_history")
    graph.add_edge("update_history", END)

    return graph.compile()


def process_message(
    message: str,
    voice_emotion: str = "neutral",
    history: list = None,
    robot_busy: bool = False,
    notifications: dict = None,
    sensor_tracker_state: dict = None,
) -> DialogueState:
    initial_state: DialogueState = {
        "human_message": message,
        "voice_emotion": voice_emotion,
        "conversation_history": history or [],
        "robot_busy": robot_busy,
        "has_problem": bool(notifications),
        "notifications": notifications or {},
        "search_context": None,
        "sensor_tracker_state": sensor_tracker_state or {},
        "issues_to_mention": [],
        "user_response_type": None,
        "pending_issue": None,
        "improvement_detected": None,
        "last_suggested_solution": None,
    }

    graph = build_dialogue_graph()

    final_state = graph.invoke(initial_state)

    return final_state
