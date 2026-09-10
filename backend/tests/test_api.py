import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from app.main import app
from app.api.interviews import get_graph, get_repository
from app.db.repositories import InterviewRepository
from app.graph.interview_graph import create_interview_graph
from app.models import (
    Question,
    AnswerEvaluation,
    AdaptiveDecision,
    AssessmentReport,
)
from tests.test_agent_flow import MockChatLLM


@pytest.fixture
def test_setup():
    """Sets up an isolated test repository and mock graph with dependency overrides."""
    repo = InterviewRepository()
    mock_llm = MockChatLLM()
    checkpointer = MemorySaver()
    graph = create_interview_graph(checkpointer=checkpointer, llm=mock_llm)

    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_graph] = lambda: graph

    client = TestClient(app)
    yield client, repo, graph

    app.dependency_overrides.clear()


def test_health_endpoint(test_setup):
    """Verify /health returns 200 OK."""
    client, _, _ = test_setup
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_docs_and_openapi_endpoints(test_setup):
    """Verify /docs and /openapi.json return 200 OK."""
    client, _, _ = test_setup
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200
    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    assert "InterviewIQ API" in openapi_resp.json()["info"]["title"]


def test_start_interview_valid(test_setup):
    """
    POST /api/interviews/start
    -> valid request -> interview created -> first question returned
    """
    client, repo, _ = test_setup
    payload = {
        "role": "Software Developer",
        "experience": "mid",
        "interview_type": "technical",
        "topics": ["OOP", "DSA", "DBMS"],
        "difficulty": "medium",
        "number_of_questions": 3,
    }
    resp = client.post("/api/interviews/start", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert "interview_id" in data
    assert data["status"] == "in_progress"
    assert data["current_question_number"] == 1
    assert data["total_questions"] == 3
    assert "question" in data
    assert data["question"]["id"] == "q_1"
    assert len(data["question"]["question_text"]) > 5


def test_start_interview_invalid_config(test_setup):
    """
    POST /api/interviews/start
    -> invalid configuration (e.g. number_of_questions = 0) -> validation error (422)
    """
    client, _, _ = test_setup
    invalid_payload = {
        "role": "Developer",
        "topics": ["Python"],
        "number_of_questions": 0,  # Invalid: ge=1 required
    }
    resp = client.post("/api/interviews/start", json=invalid_payload)
    assert resp.status_code == 422


def test_answer_flow_next_question_and_completion(test_setup):
    """
    POST /api/interviews/{id}/answer
    -> answer accepted -> graph resumes -> next question OR completion returned
    """
    client, _, _ = test_setup

    # 1. Start a 2-question interview
    start_resp = client.post("/api/interviews/start", json={
        "role": "Backend Developer",
        "experience": "mid",
        "interview_type": "technical",
        "topics": ["OOP", "System Design"],
        "difficulty": "medium",
        "number_of_questions": 2,
    })
    assert start_resp.status_code == 201
    interview_id = start_resp.json()["interview_id"]

    # 2. Answer Question 1 -> should yield Question 2
    ans1_resp = client.post(f"/api/interviews/{interview_id}/answer", json={
        "answer": "Polymorphism enables treating derived classes through a common base interface."
    })
    assert ans1_resp.status_code == 200
    ans1_data = ans1_resp.json()
    assert not ans1_data["is_completed"]
    assert ans1_data["current_question_number"] == 1
    assert ans1_data["evaluation"]["overall_score"] > 0
    assert ans1_data["next_question"] is not None
    assert ans1_data["next_question"]["id"] == "q_2"

    # 3. Answer Question 2 -> hits maximum question limit -> completes and yields report
    ans2_resp = client.post(f"/api/interviews/{interview_id}/answer", json={
        "answer": "In microservices, CQRS separates read and write data models for scalability."
    })
    assert ans2_resp.status_code == 200
    ans2_data = ans2_resp.json()
    assert ans2_data["is_completed"]
    assert ans2_data["next_question"] is None
    assert ans2_data["report"] is not None
    assert ans2_data["report"]["overall_score"] > 0


def test_answer_unknown_interview_404(test_setup):
    """
    POST /api/interviews/{id}/answer
    -> unknown interview ID -> 404
    """
    client, _, _ = test_setup
    resp = client.post("/api/interviews/unknown_id_999/answer", json={
        "answer": "Some answer"
    })
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_answer_submitted_after_completion_409(test_setup):
    """
    POST /api/interviews/{id}/answer
    -> answer submitted after completion -> 409 conflict
    """
    client, _, _ = test_setup

    # 1. Start a 1-question interview
    start_resp = client.post("/api/interviews/start", json={
        "role": "QA Engineer",
        "experience": "entry",
        "interview_type": "technical",
        "topics": ["Testing"],
        "difficulty": "easy",
        "number_of_questions": 1,
    })
    interview_id = start_resp.json()["interview_id"]

    # 2. Answer Q1 -> completes
    ans1_resp = client.post(f"/api/interviews/{interview_id}/answer", json={
        "answer": "Unit tests verify individual components in isolation."
    })
    assert ans1_resp.status_code == 200
    assert ans1_resp.json()["is_completed"]

    # 3. Submit another answer -> must return 409 Conflict
    ans2_resp = client.post(f"/api/interviews/{interview_id}/answer", json={
        "answer": "Another superfluous answer."
    })
    assert ans2_resp.status_code == 409
    assert "already completed" in ans2_resp.json()["detail"].lower()


def test_get_report_completed_and_in_progress(test_setup):
    """
    GET /api/interviews/{id}/report
    -> returns 400 when still in progress
    -> returns 200 with report when completed
    """
    client, _, _ = test_setup

    # 1. Start interview
    start_resp = client.post("/api/interviews/start", json={
        "role": "DevOps Engineer",
        "experience": "senior",
        "interview_type": "technical",
        "topics": ["CI/CD"],
        "difficulty": "hard",
        "number_of_questions": 1,
    })
    interview_id = start_resp.json()["interview_id"]

    # 2. Request report before answering -> 400 Bad Request
    in_prog_resp = client.get(f"/api/interviews/{interview_id}/report")
    assert in_prog_resp.status_code == 400
    assert "in progress" in in_prog_resp.json()["detail"].lower()

    # 3. Answer and complete
    client.post(f"/api/interviews/{interview_id}/answer", json={
        "answer": "CI/CD automates integration testing and zero-downtime canary deployment."
    })

    # 4. Request report after completion -> 200 OK
    rep_resp = client.get(f"/api/interviews/{interview_id}/report")
    assert rep_resp.status_code == 200
    data = rep_resp.json()
    assert data["interview_id"] == interview_id
    assert data["status"] == "completed"
    assert "overall_score" in data["report"]
    assert "strengths" in data["report"]


def test_maximum_question_limit_enforced(test_setup):
    """
    Verify that number_of_questions = 3 can never result in question 4.
    """
    client, _, _ = test_setup

    start_resp = client.post("/api/interviews/start", json={
        "role": "SRE",
        "experience": "mid",
        "interview_type": "technical",
        "topics": ["Observability", "Linux"],
        "difficulty": "medium",
        "number_of_questions": 3,
    })
    interview_id = start_resp.json()["interview_id"]

    # Turn 1
    t1 = client.post(f"/api/interviews/{interview_id}/answer", json={"answer": "Ans 1"})
    assert not t1.json()["is_completed"]
    assert t1.json()["next_question"]["id"] == "q_2"

    # Turn 2
    t2 = client.post(f"/api/interviews/{interview_id}/answer", json={"answer": "Ans 2"})
    assert not t2.json()["is_completed"]
    assert t2.json()["next_question"]["id"] == "q_3"

    # Turn 3 (final question)
    t3 = client.post(f"/api/interviews/{interview_id}/answer", json={"answer": "Ans 3"})
    assert t3.json()["is_completed"]
    assert t3.json()["next_question"] is None
    assert t3.json()["report"] is not None

    # Check interview details: current_question_number should be 3, never 4
    detail_resp = client.get(f"/api/interviews/{interview_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["current_question_number"] == 3
    assert detail_resp.json()["status"] == "completed"


def test_list_recent_interviews(test_setup):
    """Verify GET /api/interviews lists registered sessions."""
    client, _, _ = test_setup
    resp = client.get("/api/interviews")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
