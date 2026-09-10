import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt

from app.models import (
    InterviewConfig,
    Question,
    AnswerEvaluation,
    AdaptiveDecision,
    AssessmentReport,
    DifficultyLevel,
)
from app.graph.state import InterviewState
from app.llm import get_llm
from app.prompts import (
    PLANNER_SYSTEM_PROMPT,
    PLANNER_USER_PROMPT,
    QUESTION_GENERATOR_SYSTEM_PROMPT,
    QUESTION_GENERATOR_USER_PROMPT,
    EVALUATOR_SYSTEM_PROMPT,
    EVALUATOR_USER_PROMPT,
    ADAPTIVE_DECISION_SYSTEM_PROMPT,
    ADAPTIVE_DECISION_USER_PROMPT,
    REPORT_GENERATOR_SYSTEM_PROMPT,
    REPORT_GENERATOR_USER_PROMPT,
)


class InterviewNodes:
    """
    Encapsulates all 5 LangGraph node implementations for InterviewIQ.
    Accepts an optional LLM instance to enable easy testing and mocking.
    """

    def __init__(self, llm=None):
        self._llm = llm

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def planner(self, state: InterviewState) -> Dict[str, Any]:
        """
        Planner Node: Analyzes candidate configuration and creates an initial interview strategy
        and topic progression plan. Does NOT generate actual interview questions.
        """
        config: InterviewConfig = state["interview_config"]

        # Deterministic baseline: distribute topics across the planned question count
        topic_count = len(config.topics)
        fallback_sequence = [
            config.topics[i % topic_count] for i in range(config.number_of_questions)
        ]

        strategy_summary = (
            f"Structured technical assessment for {config.role} ({config.experience} level) "
            f"covering {', '.join(config.topics)} starting at {config.difficulty} difficulty."
        )
        topic_sequence = fallback_sequence

        # If LLM is available, allow it to refine the plan
        try:
            prompt_sys = PLANNER_SYSTEM_PROMPT.format(
                role=config.role,
                experience=config.experience,
                difficulty=config.difficulty,
            )
            prompt_user = PLANNER_USER_PROMPT.format(
                role=config.role,
                experience=config.experience,
                interview_type=config.interview_type,
                topics=", ".join(config.topics),
                difficulty=config.difficulty,
                number_of_questions=config.number_of_questions,
            )
            response = self.llm.invoke([
                SystemMessage(content=prompt_sys),
                HumanMessage(content=prompt_user),
            ])
            # Attempt parsing JSON response if model returned text
            content = response.content if hasattr(response, "content") else str(response)
            if "{" in content and "}" in content:
                json_str = content[content.find("{"):content.rfind("}") + 1]
                data = json.loads(json_str)
                if "topic_sequence" in data and isinstance(data["topic_sequence"], list):
                    topic_sequence = data["topic_sequence"][:config.number_of_questions]
                if "strategy_summary" in data:
                    strategy_summary = data["strategy_summary"]
        except Exception:
            # Safely fall back to deterministic plan
            pass

        initial_topic = topic_sequence[0] if topic_sequence else config.topics[0]

        return {
            "interview_plan": topic_sequence,
            "plan_strategy": strategy_summary,
            "current_topic": initial_topic,
            "current_difficulty": config.difficulty,
            "current_question_number": 1,
            "questions_asked": 0,
            "question_history": [],
            "answer_history": [],
            "evaluation_history": [],
            "weaknesses_identified": [],
            "strengths_identified": [],
            "report": None,
        }

    def question_generator(self, state: InterviewState) -> Dict[str, Any]:
        """
        Question Generator Node:
        1. Formulates exactly ONE technical question tailored to the candidate's
           current topic, difficulty, role, experience, and past weaknesses.
        2. Pauses graph execution via interrupt() to await candidate's answer externally.
        3. Resumes when candidate submits an answer.
        """
        config: InterviewConfig = state["interview_config"]
        topic = state.get("current_topic") or config.topics[0]
        difficulty = state.get("current_difficulty") or config.difficulty
        q_num = state.get("current_question_number", state.get("questions_asked", 0) + 1)
        q_id = f"q_{q_num}"

        # Format past context to avoid question duplication
        past_questions_summary = "\n".join(
            [f"- [{q.difficulty}] ({q.topic}): {q.question_text}" for q in state.get("question_history", [])]
        ) or "None (this is the first question)."

        past_weaknesses_summary = "\n".join(
            [f"- {w}" for w in state.get("weaknesses_identified", [])]
        ) or "None recorded yet."

        sys_prompt = QUESTION_GENERATOR_SYSTEM_PROMPT.format(
            role=config.role,
            experience=config.experience,
            topic=topic,
            difficulty=difficulty,
            interview_type=config.interview_type,
        )

        user_prompt = QUESTION_GENERATOR_USER_PROMPT.format(
            question_number=q_num,
            question_id=q_id,
            role=config.role,
            experience=config.experience,
            topic=topic,
            difficulty=difficulty,
            interview_type=config.interview_type,
            previous_questions=past_questions_summary,
            previous_weaknesses=past_weaknesses_summary,
        )

        # Structured output generation
        structured_llm = self.llm.with_structured_output(Question)
        question: Question = structured_llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Overwrite ID, topic, and difficulty to guarantee schema consistency
        question = Question(
            id=q_id,
            topic=topic,
            difficulty=difficulty,
            question_type=question.question_type or "conceptual",
            question_text=question.question_text,
            expected_concepts=question.expected_concepts or [],
        )

        # PAUSE GRAPH EXECUTION (Human-in-the-Loop)
        # Yields the generated question and halts until candidate submits an answer
        candidate_answer = interrupt({
            "type": "candidate_answer_required",
            "question": question.model_dump(),
            "interview_id": state.get("interview_id"),
        })

        return {
            "current_question": question,
            "current_answer": str(candidate_answer),
            "question_history": state.get("question_history", []) + [question],
            "answer_history": state.get("answer_history", []) + [{
                "question_id": question.id,
                "answer": str(candidate_answer),
            }],
            "questions_asked": state.get("questions_asked", 0) + 1,
        }

    def evaluator(self, state: InterviewState) -> Dict[str, Any]:
        """
        Evaluator Node: Objectively assesses candidate's answer against the question
        and its expected concepts, producing a structured AnswerEvaluation.
        """
        config: InterviewConfig = state["interview_config"]
        question: Question = state["current_question"]
        candidate_answer: str = state.get("current_answer", "")

        sys_prompt = EVALUATOR_SYSTEM_PROMPT.format(
            role=config.role,
            experience=config.experience,
        )

        user_prompt = EVALUATOR_USER_PROMPT.format(
            topic=question.topic,
            difficulty=question.difficulty,
            question_type=question.question_type,
            question_text=question.question_text,
            expected_concepts=", ".join(question.expected_concepts),
            candidate_answer=candidate_answer,
        )

        structured_llm = self.llm.with_structured_output(AnswerEvaluation)
        evaluation: AnswerEvaluation = structured_llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt),
        ])

        return {
            "current_evaluation": evaluation,
            "evaluation_history": state.get("evaluation_history", []) + [evaluation],
            "weaknesses_identified": state.get("weaknesses_identified", []) + evaluation.weaknesses,
            "strengths_identified": state.get("strengths_identified", []) + evaluation.strengths,
        }

    def adaptive_decision(self, state: InterviewState) -> Dict[str, Any]:
        """
        Adaptive Decision Node: Combines deterministic Python business rules
        (e.g., maximum question count limit) with LLM reasoning to determine
        the next adaptive step (difficulty change, topic pivot, follow-up, or finish).
        """
        config: InterviewConfig = state["interview_config"]
        questions_asked = state.get("questions_asked", 0)
        max_questions = config.number_of_questions

        # --- DETERMINISTIC RULE 1: Question Limit Reached ---
        if questions_asked >= max_questions:
            decision = AdaptiveDecision(
                action="finish",
                reason=f"Interview question limit reached ({questions_asked}/{max_questions}). Proceeding to final assessment report.",
            )
            return {"adaptive_decision": decision}

        # --- LLM REASONING: Determine Next Adaptive Action ---
        latest_eval: Optional[AnswerEvaluation] = state.get("current_evaluation")
        current_topic = state.get("current_topic", config.topics[0])
        current_diff = state.get("current_difficulty", config.difficulty)

        history_summary = []
        for i, ev in enumerate(state.get("evaluation_history", []), 1):
            q_topic = state["question_history"][i - 1].topic if i - 1 < len(state["question_history"]) else "General"
            history_summary.append(f"Q{i} ({q_topic}): Score {ev.overall_score}/10, Weaknesses: {', '.join(ev.weaknesses) or 'None'}")
        history_text = "\n".join(history_summary) or "No prior questions."

        sys_prompt = ADAPTIVE_DECISION_SYSTEM_PROMPT
        user_prompt = ADAPTIVE_DECISION_USER_PROMPT.format(
            role=config.role,
            experience=config.experience,
            topics=", ".join(config.topics),
            current_topic=current_topic,
            current_difficulty=current_diff,
            questions_asked=questions_asked,
            total_questions=max_questions,
            latest_score=latest_eval.overall_score if latest_eval else "N/A",
            latest_strengths=", ".join(latest_eval.strengths) if latest_eval else "None",
            latest_weaknesses=", ".join(latest_eval.weaknesses) if latest_eval else "None",
            latest_missing=", ".join(latest_eval.missing_concepts) if latest_eval else "None",
            follow_up_recommended=latest_eval.follow_up_required if latest_eval else False,
            history_summary=history_text,
        )

        structured_llm = self.llm.with_structured_output(AdaptiveDecision)
        decision: AdaptiveDecision = structured_llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt),
        ])

        # --- DETERMINISTIC OVERRIDE: Prevent early finish if quota remains and action is invalid ---
        if decision.action == "finish" and questions_asked < max_questions:
            decision.action = "change_topic"
            decision.reason += " (Overridden: Continuing to meet configured question count)."

        # Determine next difficulty
        next_difficulty: DifficultyLevel = current_diff
        if decision.action == "increase_difficulty":
            next_difficulty = "hard" if current_diff in ("medium", "hard") else "medium"
        elif decision.action == "decrease_difficulty":
            next_difficulty = "easy" if current_diff in ("medium", "easy") else "medium"
        elif decision.next_difficulty:
            next_difficulty = decision.next_difficulty

        # Determine next topic
        next_topic = current_topic
        if decision.action == "change_topic":
            if decision.next_topic and decision.next_topic in config.topics:
                next_topic = decision.next_topic
            else:
                # Cycle to next topic in interview plan
                plan = state.get("interview_plan", config.topics)
                next_idx = questions_asked % len(plan)
                next_topic = plan[next_idx]
        elif decision.action == "follow_up":
            # Keep same topic for follow-up probe
            next_topic = current_topic
        elif decision.next_topic and decision.next_topic in config.topics:
            next_topic = decision.next_topic

        return {
            "adaptive_decision": decision,
            "current_topic": next_topic,
            "current_difficulty": next_difficulty,
            "current_question_number": questions_asked + 1,
        }

    def report_generator(self, state: InterviewState) -> Dict[str, Any]:
        """
        Report Generator Node: Synthesizes the full interview trajectory into
        a comprehensive, structured AssessmentReport.
        """
        config: InterviewConfig = state["interview_config"]
        history = []
        for i, q in enumerate(state.get("question_history", [])):
            ans_dict = state["answer_history"][i] if i < len(state.get("answer_history", [])) else {"answer": "N/A"}
            ev = state["evaluation_history"][i] if i < len(state.get("evaluation_history", [])) else None
            score_str = f"{ev.overall_score}/10" if ev else "Not evaluated"
            feedback_str = ev.feedback if ev else "None"
            history.append(
                f"Question {i+1} [{q.difficulty}] ({q.topic}): {q.question_text}\n"
                f"Answer: {ans_dict.get('answer')}\n"
                f"Score: {score_str}\n"
                f"Feedback: {feedback_str}\n"
            )

        session_history_str = "\n---\n".join(history)

        sys_prompt = REPORT_GENERATOR_SYSTEM_PROMPT
        user_prompt = REPORT_GENERATOR_USER_PROMPT.format(
            interview_id=state.get("interview_id", "session_unknown"),
            role=config.role,
            experience=config.experience,
            interview_type=config.interview_type,
            session_history=session_history_str,
        )

        structured_llm = self.llm.with_structured_output(AssessmentReport)
        report: AssessmentReport = structured_llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt),
        ])

        # Guarantee matching interview_id
        report.interview_id = state.get("interview_id", "session_unknown")

        return {"report": report}


def route_after_decision(state: InterviewState) -> str:
    """
    Conditional routing function evaluated after `adaptive_decision`.
    Guarantees deterministic exit when question limit is reached.
    """
    decision: Optional[AdaptiveDecision] = state.get("adaptive_decision")
    questions_asked = state.get("questions_asked", 0)
    max_questions = state["interview_config"].number_of_questions

    # Invariant: Never exceed configured maximum questions
    if questions_asked >= max_questions:
        return "finish"

    if decision and decision.action == "finish":
        return "finish"

    return "continue"
