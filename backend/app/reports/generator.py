"""
Report Generator & Exporter

Generates PDF, CSV, and JSON reports for evaluation runs.
Calculates overall AI safety scores and actionable recommendations.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EvaluationReportData:
    evaluation_id: str
    name: str
    overall_score: float
    accuracy_score: float
    hallucination_rate: float
    faithfulness_score: float
    retrieval_score: float
    security_score: float
    latency_p50_ms: float
    total_cost_usd: float
    total_questions: int
    completed_questions: int
    recommendations: list[str]


class ReportGenerator:
    """Enterprise report generator for evaluation exports."""

    @staticmethod
    def generate_recommendations(data: EvaluationReportData) -> list[str]:
        recs = []
        if data.hallucination_rate > 0.15:
            recs.append("High Hallucination Rate detected (>15%). Consider tightening system prompt constraints and increasing context relevance threshold.")
        if data.retrieval_score < 0.70:
            recs.append("Suboptimal Retrieval Quality (<70%). Upgrade embedding model or re-chunk documents with overlapping windows.")
        if data.security_score < 0.85:
            recs.append("Security Vulnerability Detected (<85%). Implement input/output guardrails for prompt injection and PII leakage.")
        if data.latency_p50_ms > 3000:
            recs.append("High P50 Latency (>3000ms). Optimize vector DB index search parameters and enable prompt streaming.")
        if not recs:
            recs.append("System performing within target operational benchmarks. Continue routine version regression tracking.")
        return recs

    @classmethod
    def generate_json_report(cls, data: EvaluationReportData, results: list[dict[str, Any]]) -> str:
        report_payload = {
            "title": f"Enterprise RAG Evaluation Report - {data.name}",
            "evaluation_id": data.evaluation_id,
            "metrics": {
                "overall_score": data.overall_score,
                "accuracy_score": data.accuracy_score,
                "hallucination_rate": data.hallucination_rate,
                "faithfulness_score": data.faithfulness_score,
                "retrieval_score": data.retrieval_score,
                "security_score": data.security_score,
                "latency_p50_ms": data.latency_p50_ms,
                "total_cost_usd": data.total_cost_usd,
            },
            "recommendations": cls.generate_recommendations(data),
            "results_summary": {
                "total_questions": data.total_questions,
                "completed_questions": data.completed_questions,
            },
            "detailed_results": results,
        }
        return json.dumps(report_payload, indent=2)

    @classmethod
    def generate_csv_report(cls, results: list[dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Question ID", "Question Text", "Response Text", "Overall Score", "Status", "Latency (ms)"])
        for r in results:
            writer.writerow([
                r.get("question_id", ""),
                r.get("question_text", ""),
                r.get("response_text", ""),
                r.get("overall_score", ""),
                r.get("status", ""),
                r.get("latency_ms", ""),
            ])
        return output.getvalue()
