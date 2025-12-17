from typing import TypedDict, List, Dict, Any, Optional


class TimelineItem(TypedDict, total=False):
    """TimelineItem structure matching frontend TimelineItem interface"""
    # Step definition fields (from workout_steps table)
    id: str
    step_id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    media_url: Optional[str]
    instructions: Optional[str]
    exercise_type: Optional[str]
    estimated_duration_sec: Optional[int]
    
    # Defaults (from workout_steps table)
    default_reps: Optional[int]
    default_duration_sec: Optional[int]
    default_weight_kg: Optional[float]
    default_distance_m: Optional[float]
    
    # Package usage fields (from workout_packages timeline JSONB)
    sets: Optional[List[Dict[str, Any]]]  # List of WorkoutSet dicts
    rest_between_sets_s: Optional[int]
    
    # Override fields (from timeline overrides)
    reps: Optional[int]
    weight_kg: Optional[float]
    distance_m: Optional[float]
    duration_sec: Optional[int]

