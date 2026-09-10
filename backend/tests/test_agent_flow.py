import os
import sys
import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from app.models import (
    InterviewConfig,
    Question,
    AnswerEvaluation,
    AdaptiveDecision,
    AssessmentReport,
)
from app.graph.state import InterviewState
from app.graph.interview_graph import create_interview_graph


class MockStructuredRunnable:
    """Mock runnable that returns pre-configured Pydantic objects for with_structured_output."""
    def __init__(self, output_factory):
        self.output_factory = output_factory

    def invoke(self, messages, **kwargs):
        if callable(self.output_factory):
            return self.output_factory(messages)
        return self.output_factory


class MockChatLLM:
    """
    Mock LLM supporting .with_structured_output() and .invoke()
    for deterministic testing of LangGraph nodes without live API keys.
    """
    def __init__(
        self,
        question_output: Optional[Question] = None,
        eval_output: Optional[AnswerEvaluation] = None,
        adaptive_output: Optional[AdaptiveDecision] = None,
        report_output: Optional[AssessmentReport] = None,
    ):
        self.question_output = question_output or Question(
            id="q_1",
            topic="OOP",
            difficulty="medium",
            question_type="conceptual",
            question_text="Explain the difference between composition and inheritance in software architecture.",
            expected_concepts=["loose coupling", "has-a vs is-a", "code reusability", "flexibility"],
        )
        self.eval_output = eval_output or AnswerEvaluation(
            correctness_score=8.5,
            technical_depth_score=8.0,
            completeness_score=8.5,
            communication_score=8.0,
            overall_score=8.3,
            strengths=["Clear articulation of loose coupling"],
            weaknesses=["Could have provided a concrete UML or design pattern example"],
            missing_concepts=["strategy pattern"],
            feedback="Strong explanation of OOP design principles.",
            follow_up_required=False,
        )
        self.adaptive_output = adaptive_output or AdaptiveDecision(
            action="same_difficulty",
            next_topic="DSA",
            next_difficulty="medium",
            reason="Candidate demonstrated solid baseline competency.",
        )
        self.report_output = report_output or AssessmentReport(
            interview_id="test_session",
            overall_score=8.3,
            topic_scores={"OOP": 8.5, "DSA": 8.1},
            strengths=["Strong object-oriented design intuition"],
            weaknesses=["Minor hesitation on behavioral patterns"],
            recommended_topics=["Design Patterns", "Concurrency"],
            communication_summary="Clear and concise articulation.",
            technical_summary="Demonstrated solid competency.",
            hiring_readiness="Ready",
            final_summary="Recommended for next round.",
        )

    def invoke(self, messages, **kwargs):
        # Used by planner for initial plan text
        mock_resp = MagicMock()
        mock_resp.content = '{"strategy_summary": "Mock strategy", "topic_sequence": ["OOP", "DSA"]}'
        return mock_resp

    def with_structured_output(self, schema):
        if schema == Question:
            return MockStructuredRunnable(self.question_output)
        elif schema == AnswerEvaluation:
            return MockStructuredRunnable(self.eval_output)
        elif schema == AdaptiveDecision:
            return MockStructuredRunnable(self.adaptive_output)
        elif schema == AssessmentReport:
            return MockStructuredRunnable(self.report_output)
        return MockStructuredRunnable(self.eval_output)


def test_graph_compilation():
    """Verify that create_interview_graph constructs and compiles a valid LangGraph StateGraph."""
    mock_llm = MockChatLLM()
    graph = create_interview_graph(checkpointer=MemorySaver(), llm=mock_llm)
    assert graph is not None
    assert hasattr(graph, "stream")
    assert hasattr(graph, "invoke")


def test_full_agent_flow_with_interrupt_and_resume():
    """
    Test end-to-end execution of the interview graph with human-in-the-loop:
    1. START -> planner -> question_generator -> interrupt (awaits answer)
    2. Resume with Command(resume="candidate answer")
    3. evaluator -> adaptive_decision -> routes to finish/report when question limit is reached
    """
    mock_llm = MockChatLLM()
    graph = create_interview_graph(checkpointer=MemorySaver(), llm=mock_llm)

    config = InterviewConfig(
        role="Backend Developer",
        experience="mid",
        interview_type="technical",
        topics=["OOP", "DSA"],
        difficulty="medium",
        number_of_questions=1,  # Single question test
    )

    initial_state = {
        "interview_id": "session_test_01",
        "interview_config": config,
    }

    thread = {"configurable": {"thread_id": "session_test_01"}}

    # Run up to first interrupt
    events = list(graph.stream(initial_state, thread))
    state = graph.get_state(thread)

    # Verify that the graph paused at question_generator
    assert len(state.tasks) > 0
    assert len(state.tasks[0].interrupts) > 0
    interrupt_payload = state.tasks[0].interrupts[0].value
    assert interrupt_payload["type"] == "candidate_answer_required"
    assert "question" in interrupt_payload

    # Resume with candidate's answer
    candidate_answer = "Composition creates a has-a relationship, whereas inheritance creates an is-a relationship."
    res = graph.invoke(Command(resume=candidate_answer), thread)

    # Verify final completed state
    assert res["questions_asked"] == 1
    assert len(res["evaluation_history"]) == 1
    assert res["report"] is not None
    assert res["report"].overall_score == 8.3


def test_scenario_a_strong_candidate_increases_difficulty():
    """Scenario A: Strong answer (score >= 8.5) triggers increase_difficulty."""
    strong_eval = AnswerEvaluation(
        correctness_score=9.5,
        technical_depth_score=9.0,
        completeness_score=9.5,
        communication_score=9.0,
        overall_score=9.3,
        strengths=["Deep understanding of virtual memory and TLB"],
        weaknesses=[],
        missing_concepts=[],
        feedback="Exceptional response.",
        follow_up_required=False,
    )
    strong_decision = AdaptiveDecision(
        action="increase_difficulty",
        next_topic="Operating Systems",
        next_difficulty="hard",
        reason="Candidate scored 9.3/10; escalating to hard difficulty.",
    )

    mock_llm = MockChatLLM(eval_output=strong_eval, adaptive_output=strong_decision)
    graph = create_interview_graph(checkpointer=MemorySaver(), llm=mock_llm)

    config = InterviewConfig(
        role="Systems Engineer",
        experience="senior",
        interview_type="technical",
        topics=["Operating Systems"],
        difficulty="medium",
        number_of_questions=2,
    )

    thread = {"configurable": {"thread_id": "session_strong"}}
    list(graph.stream({"interview_id": "session_strong", "interview_config": config}, thread))

    # Answer Q1
    res = graph.invoke(Command(resume="TLB caches virtual to physical address translations."), thread)

    # Next difficulty must have escalated to 'hard'
    state = graph.get_state(thread)
    assert state.values["current_difficulty"] == "hard"
    assert state.values["adaptive_decision"].action == "increase_difficulty"


def test_scenario_b_weak_candidate_decreases_difficulty():
    """Scenario B: Weak answer (score < 5.0) triggers decrease_difficulty."""
    weak_eval = AnswerEvaluation(
        correctness_score=3.0,
        technical_depth_score=2.0,
        completeness_score=3.0,
        communication_score=4.0,
        overall_score=3.0,
        strengths=[],
        weaknesses=["Confused process memory layout with disk caching"],
        missing_concepts=["stack vs heap", "paging"],
        feedback="Candidate struggled with fundamental memory layout.",
        follow_up_required=False,
    )
    weak_decision = AdaptiveDecision(
        action="decrease_difficulty",
        next_topic="Operating Systems",
        next_difficulty="easy",
        reason="Candidate struggled on medium question (score 3.0/10); lowering to easy.",
    )

    mock_llm = MockChatLLM(eval_output=weak_eval, adaptive_output=weak_decision)
    graph = create_interview_graph(checkpointer=MemorySaver(), llm=mock_llm)

    config = InterviewConfig(
        role="Junior Developer",
        experience="entry",
        interview_type="technical",
        topics=["Operating Systems"],
        difficulty="medium",
        number_of_questions=2,
    )

    thread = {"configurable": {"thread_id": "session_weak"}}
    list(graph.stream({"interview_id": "session_weak", "interview_config": config}, thread))

    # Answer Q1
    res = graph.invoke(Command(resume="I am not very sure how memory works."), thread)

    # Next difficulty must have dropped to 'easy'
    state = graph.get_state(thread)
    assert state.values["current_difficulty"] == "easy"
    assert state.values["adaptive_decision"].action == "decrease_difficulty"


def test_scenario_c_weak_topic_targeted_again():
    """Scenario C: Repeated weakness in a topic (e.g. DBMS) causes adaptive node to target DBMS again."""
    dbms_decision = AdaptiveDecision(
        action="change_topic",
        next_topic="DBMS",
        next_difficulty="medium",
        reason="Candidate has demonstrated repeated gaps in B-tree indexing; probing DBMS again.",
    )

    mock_llm = MockChatLLM(adaptive_output=dbms_decision)
    graph = create_interview_graph(checkpointer=MemorySaver(), llm=mock_llm)

    config = InterviewConfig(
        role="Backend Developer",
        experience="mid",
        interview_type="technical",
        topics=["OOP", "DBMS", "DSA"],
        difficulty="medium",
        number_of_questions=3,
    )

    thread = {"configurable": {"thread_id": "session_dbms"}}
    list(graph.stream({"interview_id": "session_dbms", "interview_config": config}, thread))

    # Answer Q1
    res = graph.invoke(Command(resume="Indexes use trees."), thread)

    state = graph.get_state(thread)
    assert state.values["current_topic"] == "DBMS"
    assert "B-tree" in state.values["adaptive_decision"].reason


def test_scenario_d_maximum_questions_enforced_by_python_logic():
    """
    Scenario D: Deterministic invariant test.
    Even if LLM adaptive decision tries to 'continue' or 'same_difficulty',
    when questions_asked >= number_of_questions, the Python business logic
    strictly overrides it with 'finish' and routes to report_generator -> END.
    """
    # LLM mistakenly tries to continue
    rogue_continue_decision = AdaptiveDecision(
        action="same_difficulty",
        next_topic="OOP",
        next_difficulty="medium",
        reason="LLM wanting to keep asking questions indefinitely.",
    )

    mock_llm = MockChatLLM(adaptive_output=rogue_continue_decision)
    graph = create_interview_graph(checkpointer=MemorySaver(), llm=mock_llm)

    config = InterviewConfig(
        role="Backend Engineer",
        experience="mid",
        interview_type="technical",
        topics=["OOP"],
        difficulty="medium",
        number_of_questions=2,  # Hard limit: 2 questions
    )

    thread = {"configurable": {"thread_id": "session_max_limit"}}
    list(graph.stream({"interview_id": "session_max_limit", "interview_config": config}, thread))

    # Turn 1: Submit Answer 1
    graph.invoke(Command(resume="Answer 1"), thread)

    # Turn 2: Submit Answer 2 (hits maximum limit of 2)
    final_res = graph.invoke(Command(resume="Answer 2"), thread)

    # Verification:
    # 1. Exactly 2 questions asked
    assert final_res["questions_asked"] == 2
    # 2. Decision strictly overridden to 'finish'
    assert final_res["adaptive_decision"].action == "finish"
    # 3. Report was generated and interview completed
    assert final_res["report"] is not None
    assert final_res["report"].interview_id == "session_max_limit"


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY environment variable not set")
def test_live_groq_integration():
    """
    Live integration test against Groq's llama-3.3-70b-versatile.
    Executes a single-turn live interview cycle when GROQ_API_KEY is configured.
    """
    graph = create_interview_graph(checkpointer=MemorySaver())
    config = InterviewConfig(
        role="Junior Python Developer",
        experience="entry",
        interview_type="technical",
        topics=["Python Fundamentals"],
        difficulty="easy",
        number_of_questions=1,
    )
    thread = {"configurable": {"thread_id": "session_live_groq"}}
    list(graph.stream({"interview_id": "session_live_groq", "interview_config": config}, thread))

    state = graph.get_state(thread)
    assert len(state.tasks) > 0
    question_data = state.tasks[0].interrupts[0].value["question"]
    assert len(question_data["question_text"]) > 5

    res = graph.invoke(Command(resume="In Python, a list is mutable while a tuple is immutable."), thread)
    assert res["questions_asked"] == 1
    assert res["report"] is not None
    assert res["report"].overall_score >= 0.0


def run_interactive_cli():
    """Interactive CLI test harness allowing a developer to conduct a live simulated interview."""
    print("\n" + "=" * 60)
    print(" InterviewIQ — Interactive CLI Test Harness (Phase 2)")
    print("=" * 60)

    role = input("Enter Role [Software Developer]: ").strip() or "Software Developer"
    exp = input("Enter Experience Level (entry/mid/senior/lead) [entry]: ").strip() or "entry"
    topics_in = input("Enter Topics comma-separated [OOP, DSA]: ").strip() or "OOP, DSA"
    topics = [t.strip() for t in topics_in.split(",") if t.strip()]
    num_q = int(input("Number of Questions (1-5) [2]: ").strip() or "2")

    config = InterviewConfig(
        role=role,
        experience=exp,
        interview_type="technical",
        topics=topics,
        difficulty="medium",
        number_of_questions=num_q,
    )

    has_api_key = bool(os.getenv("GROQ_API_KEY"))
    if has_api_key:
        print("\n[INFO] Real GROQ_API_KEY detected. Using live Groq LLM!")
        llm = None  # Uses default get_llm()
    else:
        print("\n[INFO] No GROQ_API_KEY found. Running with Mock LLM for simulation.")
        llm = MockChatLLM()

    graph = create_interview_graph(checkpointer=MemorySaver(), llm=llm)
    session_id = "cli_session_01"
    thread = {"configurable": {"thread_id": session_id}}

    print("\n🚀 Initializing Interview Planner & Generating Question 1...")
    events = list(graph.stream({"interview_id": session_id, "interview_config": config}, thread))

    for q_idx in range(1, num_q + 1):
        state = graph.get_state(thread)
        tasks = state.tasks
        if not tasks or not tasks[0].interrupts:
            break

        question_data = tasks[0].interrupts[0].value["question"]
        print(f"\n" + "-" * 50)
        print(f"🤖 AI Interviewer [Question {q_idx}/{num_q}] [{question_data['difficulty'].upper()}] ({question_data['topic']}):")
        print(f"   {question_data['question_text']}")
        print("-" * 50)

        answer = input("\n👤 Your Answer: ").strip()
        while not answer:
            answer = input("Please provide an answer: ").strip()

        print("\n⏳ Evaluating answer & calculating adaptive routing...")
        result = graph.invoke(Command(resume=answer), thread)

        eval_data = result.get("current_evaluation")
        if eval_data:
            print(f"📊 Evaluator Score: {eval_data.overall_score}/10")
            print(f"💡 Feedback: {eval_data.feedback}")

        decision = result.get("adaptive_decision")
        if decision and decision.action != "finish":
            print(f"🔄 Adaptive Action: {decision.action} (Next Topic: {decision.next_topic}, Difficulty: {decision.next_difficulty})")
            print(f"   Reason: {decision.reason}")

    state = graph.get_state(thread)
    final_report = state.values.get("report")
    if final_report:
        print("\n" + "=" * 60)
        print("🎯 FINAL ASSESSMENT REPORT")
        print("=" * 60)
        print(f"Overall Score: {final_report.overall_score}/10")
        print(f"Hiring Readiness: {final_report.hiring_readiness}")
        print(f"Topic Scores: {final_report.topic_scores}")
        print(f"Strengths: {', '.join(final_report.strengths)}")
        print(f"Growth Areas: {', '.join(final_report.weaknesses)}")
        print(f"Executive Summary: {final_report.final_summary}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    run_interactive_cli()
