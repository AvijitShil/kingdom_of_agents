"""Recursive reflection engine for introspective regret analysis and policy adaptation."""

from typing import List, Any, Optional
from .models import ReflectionRecord


class RecursiveReflectionEngine:
    """Multi-stage introspection engine computing counterfactual regret and prompt mutations."""

    def __init__(self, adapter: Any = None, max_history: int = 20):
        self.history: List[ReflectionRecord] = []
        self.adapter = adapter
        self.max_history = max_history

    def reflect(
        self,
        tick: int,
        perceived_context: str,
        action_taken: str,
        observed_outcome: str,
        counterfactual_alternative: str,
        actual_fitness: float,
        counterfactual_fitness: float,
    ) -> ReflectionRecord:
        """Execute introspective analysis and return a bounded ReflectionRecord."""
        regret = max(0.0, min(1.0, float(counterfactual_fitness - actual_fitness)))

        prompt_mutation_suggestion = ""
        if self.adapter is not None and hasattr(self.adapter, "query"):
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are an introspective reflection engine optimizing agent decision policies.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Perceived Context: {perceived_context}\n"
                            f"Action Taken: {action_taken}\n"
                            f"Observed Outcome: {observed_outcome}\n"
                            f"Counterfactual Alternative: {counterfactual_alternative}\n"
                            f"Actual Fitness: {actual_fitness}\n"
                            f"Counterfactual Fitness: {counterfactual_fitness}\n"
                            f"Regret: {regret:.2f}\n"
                            "Generate a concise prompt mutation suggestion to minimize future regret:"
                        ),
                    },
                ]
                res = self.adapter.query(messages)
                if isinstance(res, str) and res.strip():
                    prompt_mutation_suggestion = res.strip()
            except Exception:
                prompt_mutation_suggestion = ""

        if not prompt_mutation_suggestion:
            prompt_mutation_suggestion = (
                f"Heuristic adaptation: In context '{perceived_context}', "
                f"prefer '{counterfactual_alternative}' over '{action_taken}' "
                f"to minimize regret ({regret:.2f})."
            )

        diagnosis = (
            f"Under-performance detected (regret {regret:.2f})"
            if regret > 0.1
            else "Optimal or near-optimal decision confirmed"
        )
        adaptation_level = "MESO_PROMPT" if regret > 0.2 else ("MICRO_PARAMETER" if regret > 0.0 else "NONE")

        record = ReflectionRecord(
            tick=tick,
            actual_fitness=actual_fitness,
            counterfactual_fitness=counterfactual_fitness,
            regret=regret,
            prompt_mutation_suggestion=prompt_mutation_suggestion,
            perceived_context=perceived_context,
            action_taken=action_taken,
            observed_outcome=observed_outcome,
            counterfactual_alternative=counterfactual_alternative,
            diagnosis=diagnosis,
            proposed_adaptation_level=adaptation_level,
            adaptation_details={
                "regret_delta": regret,
                "adaptation_level": adaptation_level,
            },
        )
        self.record_reflection(record)
        return record

    def record_reflection(self, record: ReflectionRecord) -> None:
        """Append reflection record and enforce sliding window bound."""
        self.history.append(record)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
