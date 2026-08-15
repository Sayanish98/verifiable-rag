import json
from pathlib import Path

from app.schemas.query import QueryRequest
from app.services.query_service import QueryService


class EvaluationService:
    def __init__(self, query_service: QueryService):
        self.query_service = query_service

    async def run_golden_dataset(self, request_id: str) -> dict:
        dataset_path = Path("evaluations/golden_dataset.json")
        if not dataset_path.exists():
            return {"total": 0, "passed": 0, "results": []}
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
        results = []
        for case in dataset:
            response = await self.query_service.execute(QueryRequest(query=case["question"]), request_id)
            answer = response.answer.lower()
            expected_terms = [term.lower() for term in case.get("expected_answer_contains", [])]
            passed = all(term in answer for term in expected_terms) and bool(response.citations)
            results.append({"question": case["question"], "passed": passed})
        return {"total": len(results), "passed": sum(item["passed"] for item in results), "results": results}

