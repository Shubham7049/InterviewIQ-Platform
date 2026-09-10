from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Allowed values definitions
ExperienceLevel = Literal["entry", "mid", "senior", "lead"]
DifficultyLevel = Literal["easy", "medium", "hard"]
InterviewType = Literal["technical", "system_design", "coding", "mixed"]
AdaptiveAction = Literal[
    "follow_up",
    "increase_difficulty",
    "decrease_difficulty",
    "same_difficulty",
    "change_topic",
    "finish",
]


class InterviewConfig(BaseModel):
    """
    Candidate configuration for setting up the interview session.
    """
    role: str = Field(..., min_length=2, max_length=100, description="Target job role (e.g. Senior Backend Engineer)")
    experience: ExperienceLevel = Field(default="mid", description="Experience level: entry, mid, senior, or lead")
    interview_type: InterviewType = Field(default="technical", description="Interview focus: technical, system_design, coding, or mixed")
    topics: List[str] = Field(..., min_length=1, description="List of technical topics to assess")
    difficulty: DifficultyLevel = Field(default="medium", description="Initial difficulty: easy, medium, or hard")
    number_of_questions: int = Field(default=5, ge=1, le=20, description="Total number of questions (1-20)")

    @field_validator("experience", mode="before")
    @classmethod
    def normalize_experience(cls, v: Any) -> str:
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("fresher", "junior", "intern"):
                return "entry"
            return val
        return v

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalize_difficulty(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("interview_type", mode="before")
    @classmethod
    def normalize_interview_type(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().lower().replace(" ", "_")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "Senior Backend Engineer",
                "experience": "senior",
                "interview_type": "technical",
                "topics": ["System Design", "Concurrency", "Database Optimization"],
                "difficulty": "medium",
                "number_of_questions": 5,
            }
        }
    )


class Question(BaseModel):
    """
    Model representing an interview question generated for the candidate.
    """
    id: str = Field(..., description="Unique question identifier, e.g. q1")
    topic: str = Field(..., min_length=1, description="Subject area or topic of this question")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level of the question: easy, medium, or hard")
    question_type: str = Field(default="conceptual", description="Type of question (e.g., conceptual, scenario, architectural)")
    question_text: str = Field(..., min_length=5, description="The interview question presented to the candidate")
    expected_concepts: List[str] = Field(default_factory=list, description="Core technical concepts expected in a strong answer")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "q1",
                "topic": "OOP",
                "difficulty": "medium",
                "question_type": "conceptual",
                "question_text": "Explain polymorphism with an example.",
                "expected_concepts": [
                    "compile-time polymorphism",
                    "runtime polymorphism",
                    "virtual functions",
                ],
            }
        }
    )


class AnswerEvaluation(BaseModel):
    """
    Structured evaluation of a candidate's answer produced by the Evaluator node.
    All scores are constrained between 0.0 and 10.0.
    """
    correctness_score: float = Field(..., ge=0.0, le=10.0, description="Factual and technical correctness (0-10)")
    technical_depth_score: float = Field(..., ge=0.0, le=10.0, description="Depth of technical explanation and edge-case awareness (0-10)")
    completeness_score: float = Field(..., ge=0.0, le=10.0, description="How completely all parts of the question were answered (0-10)")
    communication_score: float = Field(..., ge=0.0, le=10.0, description="Clarity, structure, and conciseness of communication (0-10)")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Weighted aggregate score for this answer (0-10)")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified in the answer")
    weaknesses: List[str] = Field(default_factory=list, description="Specific knowledge gaps or inaccuracies identified")
    missing_concepts: List[str] = Field(default_factory=list, description="Expected technical concepts that the candidate omitted")
    feedback: str = Field(..., description="Constructive, actionable technical feedback for the candidate")
    follow_up_required: bool = Field(default=False, description="Whether a follow-up question is recommended to clarify gaps")


class AdaptiveDecision(BaseModel):
    """
    Adaptive routing decision produced after evaluating the candidate's answer.
    Captures LLM reasoning (topic choice, difficulty adjustment) while enabling
    deterministic business logic (e.g. max questions check) to override/enforce boundaries.
    """
    action: AdaptiveAction = Field(
        ...,
        description="Next adaptive action: follow_up, increase_difficulty, decrease_difficulty, same_difficulty, change_topic, finish"
    )
    next_topic: Optional[str] = Field(None, description="Next topic to target based on candidate strengths/weaknesses")
    next_difficulty: Optional[DifficultyLevel] = Field(None, description="Adjusted difficulty level for the next question")
    reason: str = Field(..., min_length=3, description="Justification for the chosen adaptive action")


class AssessmentReport(BaseModel):
    """
    Comprehensive structured assessment report synthesized at the conclusion of an interview.
    """
    interview_id: str = Field(..., description="Unique interview session identifier / thread_id")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Final aggregate performance score (0-10)")
    topic_scores: Dict[str, float] = Field(default_factory=dict, description="Average score mapped by topic area")
    strengths: List[str] = Field(default_factory=list, description="Primary technical strengths demonstrated across the interview")
    weaknesses: List[str] = Field(default_factory=list, description="Identified areas of deficiency or gaps")
    recommended_topics: List[str] = Field(default_factory=list, description="Suggested topics for further study and improvement")
    communication_summary: str = Field(..., description="Synthesis of communication clarity and articulation")
    technical_summary: str = Field(..., description="Synthesis of overall technical proficiency")
    hiring_readiness: str = Field(..., description="Overall hiring readiness (e.g. 'Ready', 'Needs Improvement', 'Strong Hire')")
    final_summary: str = Field(..., description="Executive summary of the candidate's interview performance")
