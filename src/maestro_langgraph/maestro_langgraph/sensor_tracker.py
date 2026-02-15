from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    MOISTURE = "moisture"
    LIGHT = "light"
    PH = "pH"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIMAL = "optimal"


class UserResponseType(str, Enum):
    COMMITTED = "committed"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    QUESTION = "question"
    UNRELATED = "unrelated"


class UrgencyLevel(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SensorThreshold:
    sensor_type: SensorType
    optimal_min: float
    optimal_max: float
    warning_min: float
    warning_max: float
    critical_min: float
    critical_max: float
    unit: str

    def classify(self, value: float) -> IssueSeverity:
        if self.optimal_min <= value <= self.optimal_max:
            return IssueSeverity.OPTIMAL
        elif value < self.critical_min or value > self.critical_max:
            return IssueSeverity.CRITICAL
        elif value < self.warning_min or value > self.warning_max:
            return IssueSeverity.HIGH
        elif value < self.optimal_min:
            return IssueSeverity.MEDIUM
        else:
            return IssueSeverity.LOW

    def get_direction(self, value: float) -> str:
        if value < self.optimal_min:
            return "too_low"
        return "too_high"


THRESHOLDS = {
    SensorType.TEMPERATURE: SensorThreshold(
        sensor_type=SensorType.TEMPERATURE,
        optimal_min=20.0, optimal_max=25.0,
        warning_min=18.0, warning_max=27.0,
        critical_min=15.0, critical_max=30.0,
        unit="°C"
    ),
    SensorType.MOISTURE: SensorThreshold(
        sensor_type=SensorType.MOISTURE,
        optimal_min=40.0, optimal_max=60.0,
        warning_min=35.0, warning_max=65.0,
        critical_min=30.0, critical_max=70.0,
        unit="%"
    ),
    SensorType.LIGHT: SensorThreshold(
        sensor_type=SensorType.LIGHT,
        optimal_min=2000.0, optimal_max=4000.0,
        warning_min=1500.0, warning_max=4500.0,
        critical_min=1000.0, critical_max=5000.0,
        unit="lux"
    ),
    SensorType.PH: SensorThreshold(
        sensor_type=SensorType.PH,
        optimal_min=6.0, optimal_max=7.0,
        warning_min=5.5, warning_max=7.5,
        critical_min=5.0, critical_max=8.0,
        unit=""
    ),
}

MENTION_FREQUENCY = {
    IssueSeverity.CRITICAL: 1,
    IssueSeverity.HIGH: 2,
    IssueSeverity.MEDIUM: 3,
    IssueSeverity.LOW: 999999,
}


@dataclass
class SensorIssue:
    sensor_type: SensorType
    current_value: float
    severity: IssueSeverity
    direction: str
    first_detected: datetime = field(default_factory=datetime.now)
    last_mentioned: Optional[datetime] = None
    mention_count: int = 0
    user_response: Optional[UserResponseType] = None
    solutions_suggested: List[str] = field(default_factory=list)
    last_solution_suggested: Optional[str] = None
    user_committed_at: Optional[datetime] = None
    needs_follow_up: bool = False
    effective_solution: Optional[str] = None

    def get_urgency(self) -> UrgencyLevel:
        elapsed = datetime.now() - self.first_detected
        hours = elapsed.total_seconds() / 3600

        if hours > 24:
            return UrgencyLevel.CRITICAL
        elif hours > 12:
            return UrgencyLevel.HIGH
        elif hours > 6:
            return UrgencyLevel.ELEVATED
        return UrgencyLevel.NORMAL

    def get_hours_persisting(self) -> float:
        elapsed = datetime.now() - self.first_detected
        return elapsed.total_seconds() / 3600

    def should_follow_up(self) -> bool:
        if not self.user_committed_at:
            return False
        elapsed = datetime.now() - self.user_committed_at
        return elapsed.total_seconds() > 3600 and self.needs_follow_up

    def to_dict(self) -> dict:
        return {
            "sensor_type": self.sensor_type.value,
            "current_value": self.current_value,
            "severity": self.severity.value,
            "direction": self.direction,
            "first_detected": self.first_detected.isoformat(),
            "last_mentioned": self.last_mentioned.isoformat() if self.last_mentioned else None,
            "mention_count": self.mention_count,
            "user_response": self.user_response.value if self.user_response else None,
            "solutions_suggested": self.solutions_suggested,
            "last_solution_suggested": self.last_solution_suggested,
            "user_committed_at": self.user_committed_at.isoformat() if self.user_committed_at else None,
            "needs_follow_up": self.needs_follow_up,
            "effective_solution": self.effective_solution,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SensorIssue":
        return cls(
            sensor_type=SensorType(data["sensor_type"]),
            current_value=data["current_value"],
            severity=IssueSeverity(data["severity"]),
            direction=data["direction"],
            first_detected=datetime.fromisoformat(data["first_detected"]),
            last_mentioned=datetime.fromisoformat(data["last_mentioned"]) if data.get("last_mentioned") else None,
            mention_count=data.get("mention_count", 0),
            user_response=UserResponseType(data["user_response"]) if data.get("user_response") else None,
            solutions_suggested=data.get("solutions_suggested", []),
            last_solution_suggested=data.get("last_solution_suggested"),
            user_committed_at=datetime.fromisoformat(data["user_committed_at"]) if data.get("user_committed_at") else None,
            needs_follow_up=data.get("needs_follow_up", False),
            effective_solution=data.get("effective_solution"),
        )


class SensorTracker:

    def __init__(self):
        self.active_issues: Dict[str, SensorIssue] = {}
        self.interaction_count: int = 0
        self.mentioned_this_conversation: set = set()
        self.pending_issue: Optional[str] = None

    def process_reading(self, sensor_type: SensorType, value: float) -> Optional[SensorIssue]:
        threshold = THRESHOLDS.get(sensor_type)
        if not threshold:
            return None

        severity = threshold.classify(value)
        key = sensor_type.value

        if severity == IssueSeverity.OPTIMAL:
            if key in self.active_issues:
                resolved = self.active_issues.pop(key)
                return resolved
            return None

        direction = threshold.get_direction(value)

        if key in self.active_issues:
            issue = self.active_issues[key]
            issue.current_value = value
            issue.severity = severity
            issue.direction = direction
        else:
            issue = SensorIssue(
                sensor_type=sensor_type,
                current_value=value,
                severity=severity,
                direction=direction,
            )
            self.active_issues[key] = issue

        return issue

    def process_notification(self, sensor_name: str, value: float) -> Optional[SensorIssue]:
        name_map = {
            "moisture": SensorType.MOISTURE,
            "soil_moisture": SensorType.MOISTURE,
            "temperature": SensorType.TEMPERATURE,
            "temp": SensorType.TEMPERATURE,
            "light": SensorType.LIGHT,
            "lux": SensorType.LIGHT,
            "ph": SensorType.PH,
            "acidity": SensorType.PH,
        }

        sensor_type = name_map.get(sensor_name.lower())
        if not sensor_type:
            return None

        return self.process_reading(sensor_type, value)

    def get_issues_to_mention(self) -> List[SensorIssue]:
        self.interaction_count += 1
        to_mention = []

        severity_order = [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW]
        sorted_issues = sorted(
            self.active_issues.values(),
            key=lambda i: severity_order.index(i.severity)
        )

        for issue in sorted_issues:
            key = issue.sensor_type.value
            frequency = MENTION_FREQUENCY[issue.severity]

            if issue.severity == IssueSeverity.LOW:
                if key not in self.mentioned_this_conversation:
                    to_mention.append(issue)
            elif self.interaction_count % frequency == 0 or issue.mention_count == 0:
                to_mention.append(issue)

        return to_mention

    def record_mention(self, issue: SensorIssue, solutions: List[str] = None):
        key = issue.sensor_type.value
        if key in self.active_issues:
            self.active_issues[key].last_mentioned = datetime.now()
            self.active_issues[key].mention_count += 1
            if solutions:
                self.active_issues[key].solutions_suggested.extend(solutions)
            self.mentioned_this_conversation.add(key)
            self.pending_issue = key

    def record_user_response(self, response_type: UserResponseType):
        if self.pending_issue and self.pending_issue in self.active_issues:
            issue = self.active_issues[self.pending_issue]
            issue.user_response = response_type

            if response_type == UserResponseType.COMMITTED:
                issue.user_committed_at = datetime.now()
                issue.needs_follow_up = True

    def get_pending_issue(self) -> Optional[SensorIssue]:
        if self.pending_issue:
            return self.active_issues.get(self.pending_issue)
        return None

    def clear_pending_issue(self):
        self.pending_issue = None

    def get_issues_needing_follow_up(self) -> List[SensorIssue]:
        return [
            issue for issue in self.active_issues.values()
            if issue.should_follow_up()
        ]

    def mark_follow_up_done(self, sensor_type: str):
        if sensor_type in self.active_issues:
            self.active_issues[sensor_type].needs_follow_up = False

    def record_effective_solution(self, sensor_type: str, solution: str):
        if sensor_type in self.active_issues:
            self.active_issues[sensor_type].effective_solution = solution

    def get_effective_solutions(self) -> Dict[str, str]:
        return {}

    def reset_conversation(self):
        self.mentioned_this_conversation.clear()
        self.pending_issue = None

    def to_state(self) -> dict:
        return {
            "active_issues": {k: v.to_dict() for k, v in self.active_issues.items()},
            "interaction_count": self.interaction_count,
            "mentioned_this_conversation": list(self.mentioned_this_conversation),
            "pending_issue": self.pending_issue,
        }

    def load_state(self, state: dict):
        if not state:
            return
        self.active_issues = {
            k: SensorIssue.from_dict(v)
            for k, v in state.get("active_issues", {}).items()
        }
        self.interaction_count = state.get("interaction_count", 0)
        self.mentioned_this_conversation = set(state.get("mentioned_this_conversation", []))
        self.pending_issue = state.get("pending_issue")
