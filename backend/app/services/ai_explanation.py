import logging
from typing import Dict, Any

logger = logging.getLogger("ai-explanation")


class HybridAIExplanationEngine:
    """Generates structured incident root-cause explanations with a deterministic NO-AI fallback."""

    @staticmethod
    def generate_incident_explanation(
        flag_key: str,
        environment_name: str,
        score: float,
        factors: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Produces structured, transparent explanation of rollout risk and incidents."""
        affected_services = factors.get("affected_services", ["api-gateway"])
        error_rate = factors.get("error_rate", 0.0)
        p95_ms = factors.get("p95_ms", 0.0)

        # Deterministic analysis
        summary = (
            f"Rollout of flag '{flag_key}' in '{environment_name}' generated an elevated risk score of {score}/100. "
            f"Observed error rate reached {error_rate*100:.1f}% with p95 response times of {p95_ms}ms across services: "
            f"{', '.join(affected_services)}."
        )

        recommendations = [
            f"Verify upstream dependency health in {affected_services[0] if affected_services else 'target service'}.",
            "Inspect recent commit AST references for unhandled fallback paths.",
            "Maintain rollback state until error rate returns beneath the 1.0% safety threshold.",
        ]

        return {
            "flag_key": flag_key,
            "environment": environment_name,
            "risk_score": score,
            "summary": summary,
            "affected_services": affected_services,
            "recommended_actions": recommendations,
            "ai_mode": "DETERMINISTIC_HYBRID_ENGINE",
            "is_authoritative": False,
            "advisory_only": True,
        }
