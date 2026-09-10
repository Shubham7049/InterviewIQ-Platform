from typing import TypedDict, List, Dict, Optional, Any
from app.models import (
    InterviewConfig,
    Question,
    AnswerEvaluation,
    AdaptiveDecision,
    AssessmentReport,
    DifficultyLevel,
)


class InterviewState(TypedDict):
    """
    Complete state representation for the InterviewIQ LangGraph workflow.
    Designed for stateful execution, pause/resume checkpointing, and history tracking.
    """
    # Session Identity
    interview_id: str

    # Configuration & Strategy
    interview_config: InterviewConfig
    interview_plan: List[str]  # Planned topic sequence
    plan_strategy: Optional[str]  # Architectural strategy overview

    # Active Step Tracking
    current_topic: str
    current_difficulty: DifficultyLevel
    current_question_number: int
    questions_asked: int

    # Active Turn Data
    current_question: Optional[Question]
    current_answer: Optional[str]
    current_evaluation: Optional[AnswerEvaluation]
    adaptive_decision: Optional[AdaptiveDecision]

    # Historical Trajectory
    question_history: List[Question]
    answer_history: List[Dict[str, Any]]
    evaluation_history: List[AnswerEvaluation]
    weaknesses_identified: List[str]
    strengths_identified: List[str]

    # Final Report
    report: Optional[AssessmentReport]
