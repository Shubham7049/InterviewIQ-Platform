import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from app.models import Question, AssessmentReport
from app.schemas import (
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    InterviewSummaryResponse,
    ReportResponse,
)
from app.db.repositories import InterviewRepository
from app.graph.interview_graph import create_interview_graph

logger = logging.getLogger("interviewiq.api")

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])

# Shared in-memory checkpointer & graph instance for application runtime
_checkpointer = MemorySaver()
_default_graph = create_interview_graph(checkpointer=_checkpointer)
_default_repo = InterviewRepository()


def get_repository() -> InterviewRepository:
    """Dependency provider for InterviewRepository."""
    return _default_repo


def get_graph():
    """Dependency provider for compiled LangGraph instance."""
    return _default_graph


@router.post("/start", response_model=StartInterviewResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    request: StartInterviewRequest,
    repo: InterviewRepository = Depends(get_repository),
    graph = Depends(get_graph),
):
    """
    Start a new adaptive interview session.
    Initializes session in MongoDB, executes planner, generates Question 1,
    and returns initial question to the client.
    """
    try:
        interview_id = f"int_{uuid.uuid4().hex[:12]}"
        thread_id = interview_id

        # 1. Initialize MongoDB record
        await repo.create_interview(
            interview_id=interview_id,
            thread_id=thread_id,
            configuration=request.model_dump(),
        )

        # 2. Run graph up to first interrupt
        initial_state = {
            "interview_id": interview_id,
            "interview_config": request,
        }
        thread_config = {"configurable": {"thread_id": thread_id}}

        # Stream graph until pause at question_generator interrupt
        for _ in graph.stream(initial_state, thread_config):
            pass

        snapshot = graph.get_state(thread_config)
        if not snapshot.tasks or not snapshot.tasks[0].interrupts:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Graph failed to pause for first question input.",
            )

        payload = snapshot.tasks[0].interrupts[0].value
        question_data = payload.get("question", {})
        question = Question(**question_data)

        # 3. Save first question in MongoDB
        await repo.save_question(interview_id, question.model_dump())

        return StartInterviewResponse(
            interview_id=interview_id,
            thread_id=thread_id,
            status="in_progress",
            current_question_number=1,
            total_questions=request.number_of_questions,
            question=question,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error starting interview: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(exc)}",
        )


@router.post("/{interview_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    interview_id: str,
    request: SubmitAnswerRequest,
    repo: InterviewRepository = Depends(get_repository),
    graph = Depends(get_graph),
):
    """
    Submit candidate answer for the current question.
    Resumes the LangGraph thread, evaluates answer, triggers adaptive decision,
    and returns next question or final report.
    """
    # 1. Validate interview existence and state
    interview = await repo.get_interview(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    if interview.get("status") == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Interview '{interview_id}' is already completed.",
        )

    answer_text = request.answer.strip()
    if not answer_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer text cannot be empty.",
        )

    thread_id = interview.get("thread_id", interview_id)
    thread_config = {"configurable": {"thread_id": thread_id}}

    try:
        # 2. Resume graph with candidate's answer
        res = graph.invoke(Command(resume=answer_text), thread_config)

        # 3. Save evaluation to MongoDB
        current_q = res.get("current_question")
        current_eval = res.get("current_evaluation")
        q_id = current_q.id if current_q else "q_unknown"

        if current_eval:
            await repo.save_evaluation(
                interview_id=interview_id,
                question_id=q_id,
                evaluation_data=current_eval.model_dump(),
                candidate_answer=answer_text,
            )

        total_questions = interview["configuration"]["number_of_questions"]
        questions_asked = res.get("questions_asked", 1)

        # 4. Check if interview completed
        if res.get("report") is not None:
            report: AssessmentReport = res["report"]
            await repo.save_report(interview_id, report.model_dump())
            await repo.update_interview(interview_id, {
                "status": "completed",
                "current_question_number": questions_asked,
            })

            return SubmitAnswerResponse(
                interview_id=interview_id,
                is_completed=True,
                current_question_number=questions_asked,
                total_questions=total_questions,
                evaluation=current_eval,
                adaptive_decision=res.get("adaptive_decision"),
                next_question=None,
                report=report,
            )

        # 5. Interview continues: extract next question from paused graph
        snapshot = graph.get_state(thread_config)
        next_question = None
        if snapshot.tasks and snapshot.tasks[0].interrupts:
            payload = snapshot.tasks[0].interrupts[0].value
            next_q_data = payload.get("question", {})
            next_question = Question(**next_q_data)
            await repo.save_question(interview_id, next_question.model_dump())
            await repo.update_interview(interview_id, {
                "current_question_number": questions_asked + 1,
            })

        return SubmitAnswerResponse(
            interview_id=interview_id,
            is_completed=False,
            current_question_number=questions_asked,
            total_questions=total_questions,
            evaluation=current_eval,
            adaptive_decision=res.get("adaptive_decision"),
            next_question=next_question,
            report=None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error evaluating answer for {interview_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(exc)}",
        )


@router.get("/{interview_id}/report", response_model=ReportResponse)
async def get_interview_report(
    interview_id: str,
    repo: InterviewRepository = Depends(get_repository),
):
    """
    Retrieve the final structured assessment report for a completed interview.
    """
    interview = await repo.get_interview(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    if interview.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview '{interview_id}' is still in progress. Final report is not generated yet.",
        )

    report_data = await repo.get_report(interview_id)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report data for interview '{interview_id}' not found.",
        )

    return ReportResponse(
        interview_id=interview_id,
        status="completed",
        report=AssessmentReport(**report_data),
    )


@router.get("/{interview_id}", response_model=InterviewSummaryResponse)
async def get_interview_details(
    interview_id: str,
    repo: InterviewRepository = Depends(get_repository),
):
    """
    Retrieve metadata and status for a specific interview session.
    """
    interview = await repo.get_interview(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview '{interview_id}' not found.",
        )

    return InterviewSummaryResponse(**interview)


@router.get("", response_model=List[InterviewSummaryResponse])
async def list_recent_interviews(
    limit: int = 20,
    repo: InterviewRepository = Depends(get_repository),
):
    """
    List recent interview sessions.
    """
    interviews = await repo.list_interviews(limit=min(limit, 50))
    return [InterviewSummaryResponse(**i) for i in interviews]
