from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import InterviewState
from app.graph.nodes import InterviewNodes, route_after_decision


def create_interview_graph(checkpointer=None, llm=None):
    """
    Constructs and compiles the InterviewIQ LangGraph workflow.

    Workflow topology:
    START -> planner -> question_generator -> (interrupt) -> evaluator -> adaptive_decision
                                ^                                              |
                                |------------- continue -----------------------|
                                                                               |
                                                                             finish -> report_generator -> END

    Args:
        checkpointer: Optional LangGraph checkpointer. Defaults to MemorySaver() for local execution.
        llm: Optional LLM instance (enables mock injection for deterministic tests).
    """
    nodes = InterviewNodes(llm=llm)
    builder = StateGraph(InterviewState)

    # 1. Register the 5 primary nodes
    builder.add_node("planner", nodes.planner)
    builder.add_node("question_generator", nodes.question_generator)
    builder.add_node("evaluator", nodes.evaluator)
    builder.add_node("adaptive_decision", nodes.adaptive_decision)
    builder.add_node("report_generator", nodes.report_generator)

    # 2. Add sequential transitions
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "question_generator")
    builder.add_edge("question_generator", "evaluator")
    builder.add_edge("evaluator", "adaptive_decision")

    # 3. Add conditional routing after adaptive decision
    builder.add_conditional_edges(
        "adaptive_decision",
        route_after_decision,
        {
            "continue": "question_generator",
            "finish": "report_generator",
        },
    )

    # 4. Final transition to END
    builder.add_edge("report_generator", END)

    # 5. Attach Checkpointer (Default: MemorySaver)
    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)
