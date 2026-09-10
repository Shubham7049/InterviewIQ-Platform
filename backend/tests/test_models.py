import json
import pytest
from pydantic import ValidationError

from app.models import (
    InterviewConfig,
    Question,
    AnswerEvaluation,
    AdaptiveDecision,
    AssessmentReport,
)


def test_interview_config_creation():
    """Verify InterviewConfig can be created with valid parameters."""
    config = InterviewConfig(
        role="Senior Backend Engineer",
        experience="senior",
        interview_type="technical",
        topics=["Distributed Systems", "Concurrency", "PostgreSQL"],
        difficulty="hard",
        number_of_questions=5,
    )
    assert config.role == "Senior Backend Engineer"
    assert config.experience == "senior"
    assert config.interview_type == "technical"
    assert len(config.topics) == 3
    assert config.difficulty == "hard"
    assert config.number_of_questions == 5


def test_interview_config_invalid_rejected():
    """Verify invalid configuration raises ValidationError."""
    # Invalid: number_of_questions = 0 (ge=1 required)
    with pytest.raises(ValidationError):
        InterviewConfig(
            role="Backend Dev",
            topics=["Python"],
            number_of_questions=0,
        )

    # Invalid: number_of_questions > 20 (le=20 required)
    with pytest.raises(ValidationError):
        InterviewConfig(
            role="Backend Dev",
            topics=["Python"],
            number_of_questions=25,
        )

    # Invalid: empty topics list (min_length=1 required)
    with pytest.raises(ValidationError):
        InterviewConfig(
            role="Backend Dev",
            topics=[],
            number_of_questions=5,
        )

    # Invalid: invalid experience level
    with pytest.raises(ValidationError):
        InterviewConfig(
            role="Backend Dev",
            experience="intern_level",  # Not in literal
            topics=["Python"],
            number_of_questions=5,
        )


def test_question_validation():
    """Verify Question validates correctly with expected fields."""
    q = Question(
        id="q1",
        topic="OOP",
        difficulty="medium",
        question_type="conceptual",
        question_text="Explain polymorphism with an example.",
        expected_concepts=[
            "compile-time polymorphism",
            "runtime polymorphism",
            "virtual functions",
        ],
    )
    assert q.id == "q1"
    assert q.topic == "OOP"
    assert q.difficulty == "medium"
    assert q.question_type == "conceptual"
    assert len(q.expected_concepts) == 3

    # Invalid question: missing required question_text
    with pytest.raises(ValidationError):
        Question(
            id="q2",
            topic="OOP",
            difficulty="easy",
            question_text="",  # min_length=5
        )


def test_answer_evaluation_score_ranges():
    """Verify AnswerEvaluation enforces 0.0 to 10.0 score bounds."""
    # Valid evaluation
    eval_obj = AnswerEvaluation(
        correctness_score=8.5,
        technical_depth_score=8.0,
        completeness_score=9.0,
        communication_score=7.5,
        overall_score=8.2,
        strengths=["Clear explanation of method overriding"],
        weaknesses=["Did not mention compile-time polymorphism"],
        missing_concepts=["overloading"],
        feedback="Good conceptual grasp, but remember both forms of polymorphism.",
        follow_up_required=False,
    )
    assert eval_obj.overall_score == 8.2

    # Invalid: score > 10.0
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            correctness_score=11.0,
            technical_depth_score=8.0,
            completeness_score=9.0,
            communication_score=7.5,
            overall_score=8.0,
            feedback="Good",
        )

    # Invalid: score < 0.0
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            correctness_score=-1.0,
            technical_depth_score=8.0,
            completeness_score=9.0,
            communication_score=7.5,
            overall_score=8.0,
            feedback="Bad",
        )


def test_adaptive_decision_allowed_actions():
    """Verify AdaptiveDecision enforces permitted adaptive actions."""
    # Valid action: increase_difficulty
    decision = AdaptiveDecision(
        action="increase_difficulty",
        next_topic="Distributed Locking",
        next_difficulty="hard",
        reason="Candidate scored 9/10 on concurrency fundamentals.",
    )
    assert decision.action == "increase_difficulty"
    assert decision.next_difficulty == "hard"

    # Valid action: finish
    finish_decision = AdaptiveDecision(
        action="finish",
        reason="All planned questions have been answered.",
    )
    assert finish_decision.action == "finish"
    assert finish_decision.next_topic is None

    # Invalid action not in allowed Literal
    with pytest.raises(ValidationError):
        AdaptiveDecision(
            action="restart_interview",
            reason="Invalid action",
        )


def test_assessment_report_json_serialization():
    """Verify AssessmentReport serializes to JSON and deserializes correctly."""
    report = AssessmentReport(
        interview_id="session_abc_123",
        overall_score=8.4,
        topic_scores={
            "System Design": 8.0,
            "Concurrency": 9.0,
            "Database Optimization": 8.2,
        },
        strengths=["Deep knowledge of async event loops", "Strong architectural intuition"],
        weaknesses=["Slightly vague on distributed consensus edge cases"],
        recommended_topics=["Raft consensus protocol", "Distributed transaction isolation"],
        communication_summary="Structured, concise, and articulate responses.",
        technical_summary="Demonstrates solid senior-level backend architectural competencies.",
        hiring_readiness="Ready",
        final_summary="Strong candidate with high probability of succeeding in a senior backend role.",
    )

    # Serialize to JSON string
    json_str = report.model_dump_json()
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["interview_id"] == "session_abc_123"
    assert data["overall_score"] == 8.4
    assert data["hiring_readiness"] == "Ready"

    # Deserialize back to model (round-trip)
    reconstituted = AssessmentReport.model_validate_json(json_str)
    assert reconstituted.interview_id == report.interview_id
    assert reconstituted.overall_score == report.overall_score
    assert reconstituted.topic_scores == report.topic_scores


def test_full_model_roundtrip_deserialization():
    """Verify dictionary to model deserialization and serialization integrity."""
    raw_dict = {
        "role": "Full Stack Engineer",
        "experience": "mid",
        "interview_type": "mixed",
        "topics": ["React", "FastAPI", "PostgreSQL"],
        "difficulty": "medium",
        "number_of_questions": 6,
    }
    config = InterviewConfig.model_validate(raw_dict)
    dumped = config.model_dump()
    assert dumped["role"] == raw_dict["role"]
    assert dumped["number_of_questions"] == 6
