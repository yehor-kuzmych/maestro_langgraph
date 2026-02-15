from dataclasses import dataclass
from typing import Dict, List, Optional
from .sensor_tracker import SensorType


@dataclass
class Solution:
    description: str
    action: str
    timeframe: str
    consequence: str
    time_until_damage: str
    complexity: int
    is_quick_fix: bool


SOLUTIONS: Dict[SensorType, Dict[str, List[Solution]]] = {
    SensorType.MOISTURE: {
        "too_low": [
            Solution(
                description="Manual watering",
                action="water the plant thoroughly until water drains from the bottom",
                timeframe="immediately",
                consequence="wilting and potential plant death",
                time_until_damage="24 hours",
                complexity=1,
                is_quick_fix=True,
            ),
            Solution(
                description="Check irrigation system",
                action="check the water flow and timer settings on the irrigation system",
                timeframe="within an hour",
                consequence="continued water stress",
                time_until_damage="24-48 hours",
                complexity=2,
                is_quick_fix=False,
            ),
            Solution(
                description="Add mulch",
                action="add a layer of mulch around the plant to retain moisture",
                timeframe="when possible",
                consequence="rapid moisture loss",
                time_until_damage="2-3 days",
                complexity=2,
                is_quick_fix=False,
            ),
        ],
        "too_high": [
            Solution(
                description="Improve drainage",
                action="check drainage holes and let soil dry out before watering again",
                timeframe="immediately",
                consequence="root rot and fungal infections",
                time_until_damage="2-3 days",
                complexity=1,
                is_quick_fix=True,
            ),
            Solution(
                description="Reduce watering frequency",
                action="skip the next scheduled watering",
                timeframe="next watering cycle",
                consequence="oxygen deprivation for roots",
                time_until_damage="3-5 days",
                complexity=1,
                is_quick_fix=True,
            ),
        ],
    },
    SensorType.TEMPERATURE: {
        "too_low": [
            Solution(
                description="Move to warmer spot",
                action="move the plant away from cold windows or drafts",
                timeframe="immediately",
                consequence="cold stress and slowed growth",
                time_until_damage="12-24 hours",
                complexity=1,
                is_quick_fix=True,
            ),
            Solution(
                description="Use heating mat",
                action="place a seedling heating mat under the pot",
                timeframe="within a day",
                consequence="potential root damage",
                time_until_damage="24-48 hours",
                complexity=2,
                is_quick_fix=False,
            ),
        ],
        "too_high": [
            Solution(
                description="Increase airflow",
                action="turn on a fan or open windows for better air circulation",
                timeframe="immediately",
                consequence="heat stress and wilting",
                time_until_damage="6-12 hours",
                complexity=1,
                is_quick_fix=True,
            ),
            Solution(
                description="Move to cooler spot",
                action="move the plant away from direct sunlight or heat sources",
                timeframe="immediately",
                consequence="leaf burn and dehydration",
                time_until_damage="12-24 hours",
                complexity=1,
                is_quick_fix=True,
            ),
        ],
    },
    SensorType.LIGHT: {
        "too_low": [
            Solution(
                description="Move to brighter location",
                action="move the plant closer to a window with indirect sunlight",
                timeframe="when possible",
                consequence="leggy growth and weak stems",
                time_until_damage="1-2 weeks",
                complexity=1,
                is_quick_fix=True,
            ),
            Solution(
                description="Add grow light",
                action="set up a grow light above the plant",
                timeframe="within a few days",
                consequence="poor photosynthesis",
                time_until_damage="2-3 weeks",
                complexity=2,
                is_quick_fix=False,
            ),
        ],
        "too_high": [
            Solution(
                description="Add shade",
                action="move the plant away from direct sunlight or add a sheer curtain",
                timeframe="immediately",
                consequence="leaf burn and bleaching",
                time_until_damage="1-2 days",
                complexity=1,
                is_quick_fix=True,
            ),
        ],
    },
    SensorType.PH: {
        "too_low": [
            Solution(
                description="Add lime",
                action="add a small amount of garden lime to raise pH",
                timeframe="when possible",
                consequence="nutrient lockout",
                time_until_damage="1-2 weeks",
                complexity=2,
                is_quick_fix=False,
            ),
        ],
        "too_high": [
            Solution(
                description="Add sulfur",
                action="add a small amount of sulfur to lower pH",
                timeframe="when possible",
                consequence="nutrient lockout",
                time_until_damage="1-2 weeks",
                complexity=2,
                is_quick_fix=False,
            ),
        ],
    },
}


def get_solutions(sensor_type: SensorType, direction: str, exclude: List[str] = None) -> List[Solution]:
    exclude = exclude or []
    all_solutions = SOLUTIONS.get(sensor_type, {}).get(direction, [])
    return [s for s in all_solutions if s.description not in exclude]


def get_quick_fix(sensor_type: SensorType, direction: str) -> Optional[Solution]:
    solutions = get_solutions(sensor_type, direction)
    for s in solutions:
        if s.is_quick_fix:
            return s
    return solutions[0] if solutions else None
