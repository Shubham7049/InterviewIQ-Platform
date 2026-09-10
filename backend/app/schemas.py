from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models import (
    InterviewConfig,
    Question,
    AnswerEvaluation,
    AdaptiveDecision,
    AssessmentReport,
)


class StartInterviewRequest(InterviewConfig):
    """Request payload to initiate a new adaptive interview session."""
    pass


class StartInterviewResponse(BaseModel):
    """Response returned upon successfully initializing an interview session."""
    interview_id: str = Field(..., description="Unique interview session ID")
    thread_id: str = Field(..., description="LangGraph checkpoint thread ID")
    status: str = Field(default="in_progress", description="Current interview status")
    current_question_number: int = Field(default=1, description="Index of current question")
    total_questions: int = Field(..., description="Configured total number of questions")
    question: Question = Field(..., description="The first generated interview question")


class SubmitAnswerRequest(BaseModel):
    """Request payload containing the candidate's answer."""
    answer: str = Field(..., min_length=1, description="Candidate's technical answer")


class SubmitAnswerResponse(BaseModel):
    """Response returned after evaluating an answer and determining the next step."""
    interview_id: str = Field(..., description="Unique interview session ID")
    is_completed: bool = Field(..., description="Whether the interview is now complete")
    current_question_number: int = Field(..., description="Question number just evaluated")
    total_questions: int = Field(..., description="Configured total number of questions")
    evaluation: AnswerEvaluation = Field(..., description="Structured evaluation of submitted answer")
    adaptive_decision: Optional[AdaptiveDecision] = Field(None, description="Adaptive decision that led to next question or finish")
    next_question: Optional[Question] = Field(None, description="Next interview question (null if completed)")
    report: Optional[AssessmentReport] = Field(None, description="Final assessment report (null if interview still active)")


class InterviewSummaryResponse(BaseModel):
    """Summary of an interview session."""
    interview_id: str
    thread_id: str
    status: str
    current_question_number: int
    configuration: Dict[str, Any]
    created_at: str
    updated_at: str


class ReportResponse(BaseModel):
    """Response containing the final assessment report."""
    interview_id: str
    status: str
    report: AssessmentReport
