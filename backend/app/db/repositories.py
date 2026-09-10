from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.connection import get_db


class InterviewRepository:
    """
    Repository abstraction for MongoDB collections:
    - interviews
    - questions
    - evaluations
    - reports

    Transparently falls back to in-memory persistence if MongoDB is not connected
    (allowing tests and local development to run without an active MongoDB server).
    """

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._db_override = db
        # In-memory storage structures for testing / offline fallback
        self._mem_interviews: Dict[str, Dict[str, Any]] = {}
        self._mem_questions: List[Dict[str, Any]] = []
        self._mem_evaluations: List[Dict[str, Any]] = []
        self._mem_reports: Dict[str, Dict[str, Any]] = {}

    @property
    def db(self) -> Optional[AsyncIOMotorDatabase]:
        return self._db_override or get_db()

    # --- Interview Metadata ---

    async def create_interview(
        self,
        interview_id: str,
        thread_id: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        doc = {
            "interview_id": interview_id,
            "thread_id": thread_id,
            "configuration": configuration,
            "status": "in_progress",
            "current_question_number": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.db is not None:
            await self.db["interviews"].insert_one(doc.copy())
        self._mem_interviews[interview_id] = doc
        return doc

    async def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            doc = await self.db["interviews"].find_one({"interview_id": interview_id}, {"_id": 0})
            if doc:
                return doc
        return self._mem_interviews.get(interview_id)

    async def update_interview(self, interview_id: str, update_data: Dict[str, Any]) -> bool:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if self.db is not None:
            await self.db["interviews"].update_one(
                {"interview_id": interview_id},
                {"$set": update_data}
            )
        if interview_id in self._mem_interviews:
            self._mem_interviews[interview_id].update(update_data)
            return True
        return False

    async def list_interviews(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.db is not None:
            cursor = self.db["interviews"].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        return list(self._mem_interviews.values())[-limit:]

    # --- Questions ---

    async def save_question(self, interview_id: str, question_data: Dict[str, Any]) -> str:
        doc = {
            "interview_id": interview_id,
            "question_id": question_data.get("id"),
            "question_data": question_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.db is not None:
            await self.db["questions"].insert_one(doc.copy())
        self._mem_questions.append(doc)
        return question_data.get("id", "")

    async def get_questions_by_interview(self, interview_id: str) -> List[Dict[str, Any]]:
        if self.db is not None:
            cursor = self.db["questions"].find({"interview_id": interview_id}, {"_id": 0})
            return await cursor.to_list(length=100)
        return [q for q in self._mem_questions if q["interview_id"] == interview_id]

    # --- Evaluations ---

    async def save_evaluation(
        self,
        interview_id: str,
        question_id: str,
        evaluation_data: Dict[str, Any],
        candidate_answer: str,
    ) -> str:
        doc = {
            "interview_id": interview_id,
            "question_id": question_id,
            "candidate_answer": candidate_answer,
            "evaluation": evaluation_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.db is not None:
            await self.db["evaluations"].insert_one(doc.copy())
        self._mem_evaluations.append(doc)
        return question_id

    async def get_evaluations_by_interview(self, interview_id: str) -> List[Dict[str, Any]]:
        if self.db is not None:
            cursor = self.db["evaluations"].find({"interview_id": interview_id}, {"_id": 0})
            return await cursor.to_list(length=100)
        return [e for e in self._mem_evaluations if e["interview_id"] == interview_id]

    # --- Reports ---

    async def save_report(self, interview_id: str, report_data: Dict[str, Any]) -> str:
        doc = {
            "interview_id": interview_id,
            "report": report_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.db is not None:
            await self.db["reports"].update_one(
                {"interview_id": interview_id},
                {"$set": doc},
                upsert=True,
            )
        self._mem_reports[interview_id] = doc
        return interview_id

    async def get_report(self, interview_id: str) -> Optional[Dict[str, Any]]:
        if self.db is not None:
            doc = await self.db["reports"].find_one({"interview_id": interview_id}, {"_id": 0})
            if doc:
                return doc.get("report")
        doc = self._mem_reports.get(interview_id)
        return doc.get("report") if doc else None

    # --- Full History ---

    async def get_interview_history(self, interview_id: str) -> Optional[Dict[str, Any]]:
        interview = await self.get_interview(interview_id)
        if not interview:
            return None
        questions = await self.get_questions_by_interview(interview_id)
        evaluations = await self.get_evaluations_by_interview(interview_id)
        report = await self.get_report(interview_id)

        return {
            "interview": interview,
            "questions": questions,
            "evaluations": evaluations,
            "report": report,
        }
