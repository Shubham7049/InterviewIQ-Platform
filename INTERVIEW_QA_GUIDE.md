# InterviewIQ — Technical Interview & Architecture Q&A Guide

A concise engineering reference explaining the architectural design, Agentic AI principles, and system design behind **InterviewIQ**.

---

### 1. What InterviewIQ Does
InterviewIQ is an adaptive, agentic technical assessment platform. Given a candidate's target role, seniority level, focus topics, and desired question count, it dynamically conducts a technical interview: generating targeted questions, evaluating answers across technical and communication dimensions, adjusting difficulty and topics in response to demonstrated performance, and synthesizing a comprehensive final assessment report.

---

### 2. Why Agentic AI Instead of a Simple Chatbot?
A standard chatbot simply appends conversational turns to an LLM context window without stateful assessment logic or goal orientation. InterviewIQ is **Agentic** because:
- It maintains an explicit, deterministic state machine controlling the assessment lifecycle.
- It dynamically takes autonomous actions based on evaluation feedback (e.g., escalating difficulty, probing identified knowledge gaps, or concluding the session).
- It produces typed data contracts at every step rather than unconstrained conversational text.

---

### 3. Why LangGraph?
LangGraph models LLM workflows as cyclic, stateful computational graphs:
- **State as First-Class**: Provides clean state management (`InterviewState`) with checkpointing and state versioning.
- **Conditional Routing**: Enables deterministic branches (e.g. `should_continue` vs `finish`) without brittle prompt instructions.
- **Interruptibility (Human-in-the-Loop)**: Supports natively pausing graph execution while waiting for external human input (the candidate's answer) and resuming seamlessly.

---

### 4. The 5-Node Architecture
The core LangGraph workflow is organized into 5 focused nodes:
1. **`planner`**: Analyzes candidate profile and target role to create an initial interview plan and baseline topics.
2. **`question_generator`**: Crafts non-repetitive, context-aware technical questions matching current topic and difficulty.
3. **`evaluator`**: Objectively grades answers across correctness, technical depth, completeness, and communication (0–10 scale).
4. **`adaptive_decision`**: Analyzes evaluation trends to decide the next action (`increase_difficulty`, `decrease_difficulty`, `change_topic`, `follow_up`, or `finish`).
5. **`report_generator`**: Compiles the cumulative interview trajectory into an executive assessment report with actionable feedback.

---

### 5. Why Candidate Answering is an External Interaction
In LangGraph, nodes represent internal automated transformations. Candidate answering is **human-in-the-loop**:
- The graph executes up to `question_generator` and yields the question.
- Graph execution halts via LangGraph's native `interrupt()` while the candidate reads, thinks, and submits their answer.
- The submission resumes the thread via `Command(resume=answer)` directly into the `evaluator` node.
- Treating answering as an external event prevents unnecessary LLM polling, saves token costs, and mirrors real-world async workflows.

---

### 6. Why Structured Pydantic Outputs?
- **Deterministic Reliability**: Guarantees that LLM outputs conform to strict schemas (`AnswerEvaluation`, `AdaptiveDecision`, `AssessmentReport`) via `.with_structured_output()`.
- **Downstream Safety**: Eliminates JSON parsing crashes, guarantees score numeric bounds (0–10), and ensures clean ingestion by frontend components and database models.

---

### 7. Separation of Deterministic Rules vs. LLM Reasoning
To maintain system predictability:
- **Deterministic Business Logic (Python)**: Hard limits such as maximum question count (`questions_asked >= number_of_questions`), session termination checks, and score averages are strictly computed in Python code.
- **LLM Reasoning**: Cognitive tasks such as identifying nuanced conceptual misconceptions, determining which weak topic to test next, and formulating technical questions are delegated to the LLM.
- **Rule of Thumb**: Never ask an LLM to count iterations or enforce invariant business boundaries that code can guarantee with 100% precision.

---

### 8. Why Groq?
- **Ultra-Low Latency Inference**: Groq LPUs deliver hundreds of tokens per second, cutting node execution to sub-second or near-instant response times.
- **Candidate Experience**: Long LLM evaluation delays break the flow of an interactive interview. Low latency makes the adaptive loop feel fluid and realistic.

---

### 9. How FastAPI Coordinates with LangGraph Checkpoints (`thread_id`)
HTTP is stateless, but an interview is multi-turn and stateful. InterviewIQ bridges this cleanly:
- When a candidate starts an interview (`POST /api/interviews/start`), FastAPI assigns a unique `interview_id` which acts as the LangGraph `thread_id`.
- The graph streams until pausing at `interrupt()` with Question 1.
- State is preserved in the checkpointer (`MemorySaver` or durable store).
- When the candidate submits an answer (`POST /api/interviews/{id}/answer`), FastAPI retrieves the session, attaches `thread_id`, and resumes execution with `Command(resume=candidate_answer)`.
- No graph state is lost between HTTP requests, and no duplicate graphs are spawned.

---

### 10. Separation of Persistence: MongoDB vs. LangGraph Checkpointing
- **LangGraph Checkpointer**: Responsible solely for short-term graph runtime state (current node, active call stack, memory snapshots required to resume suspended threads).
- **MongoDB Collections**: Responsible for long-term, durable business documents:
  - `interviews`: High-level session metadata, configuration, timestamps, and status (`in_progress`, `completed`).
  - `questions`: Audit trail of questions asked per interview.
  - `evaluations`: Detailed multi-dimensional scores, strengths, weaknesses, and feedback.
  - `reports`: Final synthesized executive scorecards.
- Decoupling runtime execution from analytical persistence allows either system to be upgraded, queried, or scaled independently.

---

### 11. Security & Anti-Tampering Safeguards
- **Zero Exposure of Secrets**: API keys (`GROQ_API_KEY`, `LANGCHAIN_API_KEY`) and database credentials are read from server environment variables and never returned in API responses.
- **Server-Side Invariants**: The candidate client cannot pass its own score, skip questions, or manipulate adaptive difficulty. Scores and transitions are strictly computed on the backend.
- **Strict Hard Bounds**: If a candidate configures 3 questions, the backend deterministically terminates the session at 3 questions regardless of any client payloads or LLM output.

---

### 12. Candidate UI & Agentic AI Presentation Best Practices
- **Visibility of Adaptive Behavior without Leaking Reasoning**: The candidate experience explicitly communicates when the AI is calibrating the next question based on performance (*"Your response has been evaluated. The next question is being selected based on your performance..."*), without exposing raw internal prompts, chain-of-thought, or graph checkpoints.
- **Client-Side State Isolation**: The React frontend relies strictly on clean typed API response contracts (`POST /api/interviews/start`, `POST /api/interviews/{id}/answer`, `GET /api/interviews/{id}/report`). All evaluation logic, score aggregation, and report generation remain strictly backend-driven.

