"""EvolutionaryAgent extending BaseAgent with ideological alignment, reflection, and dynamic switching."""

from typing import List, Dict, Any, Optional
from agents.base import BaseAgent
from knowledge_base.models import IdeologicalProfile
from knowledge_base.retriever import CorpusRetriever
from .models import ReflectionRecord
from .fitness import FitnessMetrics
from .switcher import CategorySwitchManager
from .reflection import RecursiveReflectionEngine
from .prompt_optimizer import PromptOptimizer


class ActionString(str):
    """Action outcome string that provides dual compatibility as a str and as a dict."""

    def __new__(cls, content: str, agent_id: str = "", name: str = "", clan: str = ""):
        instance = super().__new__(cls, content)
        instance.agent_id = agent_id
        instance.name = name
        instance.clan = clan
        instance.action_text = content
        return instance

    def __getitem__(self, item: Any) -> Any:
        if item in ("agent_id", "name", "clan", "action_text"):
            return getattr(self, item)
        return super().__getitem__(item)

    def get(self, item: str, default: Any = None) -> Any:
        if item in ("agent_id", "name", "clan", "action_text"):
            return getattr(self, item)
        return default


class EvolutionaryAgent(BaseAgent):
    """Autonomous agent possessing ideological alignment, fitness tracking, and recursive adaptation."""

    def __init__(
        self,
        name: str,
        clan: str,
        role: str,
        ideology: Optional[IdeologicalProfile] = None,
        initial_category_id: Optional[str] = None,
        retriever: Optional[CorpusRetriever] = None,
        switch_manager: Optional[CategorySwitchManager] = None,
        reflection_engine: Optional[RecursiveReflectionEngine] = None,
        adapter: Any = None,
        budget: int = 1000,
        system_prompt: str = "",
    ):
        super().__init__(name=name, clan=clan, role=role, system_prompt=system_prompt, budget=budget)
        self.retriever = retriever
        self.adapter = adapter

        # Resolve ideology
        if ideology is not None:
            self.ideology: Optional[IdeologicalProfile] = ideology
        elif initial_category_id and retriever is not None:
            self.ideology = retriever.get_ideology(initial_category_id)
        elif retriever is not None:
            categories = retriever.list_all_categories()
            self.ideology = retriever.get_ideology(categories[0]) if categories else None
        else:
            self.ideology = None

        # Wire switcher
        if switch_manager is not None:
            self.switch_manager = switch_manager
            if self.switch_manager.agent is None:
                self.switch_manager.agent = self
        else:
            self.switch_manager = CategorySwitchManager(agent=self, retriever=retriever)

        # Wire reflection engine
        if reflection_engine is not None:
            self.reflection_engine = reflection_engine
        else:
            self.reflection_engine = RecursiveReflectionEngine(adapter=adapter)

        # Evolutionary state
        self.fitness_history: List[FitnessMetrics] = []
        self.reflection_history: List[ReflectionRecord] = []
        self.is_on_probation: bool = False
        self.last_switch_tick: int = -999
        self.generation: int = 1

    def build_prompt(self, current_task: str) -> List[Dict[str, str]]:
        """Construct prompt conditioned on active ideology, memory, and reflection lessons."""
        system_content = PromptOptimizer.synthesize_system_prompt(
            agent_name=self.name,
            clan=self.clan,
            role=self.role,
            base_system_prompt=self.system_prompt,
            ideology=self.ideology,
            reflection_history=self.reflection_history,
            max_reflections=3,
        )

        messages = [
            {"role": "system", "content": system_content},
        ]

        if self.memory:
            recent_events = "\n".join([f"- {m['event']}" for m in self.memory[-3:]])
            messages.append({"role": "user", "content": f"Recent Society Context:\n{recent_events}"})

        messages.append({"role": "user", "content": current_task})
        return messages

    def act(self, current_task: str) -> ActionString:
        """Execute decision turn: formulate prompt, query adapter or synthesize ideological action."""
        messages = self.build_prompt(current_task)
        action_text = ""

        if self.adapter is not None and hasattr(self.adapter, "query"):
            try:
                res = self.adapter.query(messages)
                if isinstance(res, str) and res.strip():
                    action_text = res.strip()
            except Exception:
                action_text = ""

        if not action_text:
            ideology_name = self.ideology.title if self.ideology else "Pragmatic Baseline"
            action_text = f"[{ideology_name}] Decided action response to: {current_task}"

        return ActionString(
            action_text,
            agent_id=self.agent_id,
            name=self.name,
            clan=self.clan,
        )

    def step(self, tick: int, society_context: Optional[Dict[str, Any]] = None) -> ActionString:
        """Execute complete evolutionary lifecycle turn."""
        society_context = society_context or {}

        # 1. Perception
        event_summary = society_context.get("summary", f"Tick {tick} societal state update.")
        self.perceive(event_summary)

        # 2. Action
        task = society_context.get("task", f"Execute responsibilities for tick {tick}.")
        action = self.act(task)

        # 3. Fitness evaluation
        if "metrics" in society_context and isinstance(society_context["metrics"], FitnessMetrics):
            metrics = society_context["metrics"]
        else:
            metrics = FitnessMetrics(
                wealth=society_context.get("wealth", 0.5),
                security=society_context.get("security", 0.5),
                reputation=society_context.get("reputation", 0.5),
                fairness=society_context.get("fairness", 0.5),
                compliance=society_context.get("compliance", 0.5),
                tick=tick,
            )
            if self.ideology and hasattr(self.ideology, "utility_weights"):
                metrics.compute_composite(self.ideology.utility_weights)
        self.fitness_history.append(metrics)

        # 4. Introspective reflection
        if self.reflection_engine is not None:
            actual_f = metrics.composite_score
            counterfactual_f = society_context.get("counterfactual_fitness", actual_f)
            rec = self.reflection_engine.reflect(
                tick=tick,
                perceived_context=event_summary,
                action_taken=str(action),
                observed_outcome=society_context.get("outcome", "Action registered in ledger."),
                counterfactual_alternative=society_context.get("counterfactual_alternative", "Alternative doctrine"),
                actual_fitness=actual_f,
                counterfactual_fitness=counterfactual_f,
            )
            self.reflection_history.append(rec)

        # 5. Probation or switch evaluation
        if self.switch_manager is not None:
            if self.is_on_probation:
                self.switch_manager.check_probation(tick)
            elif "candidate_ideology" in society_context:
                cand = society_context["candidate_ideology"]
                cand_exp = society_context.get("candidate_expected_fitness", 0.8)
                if self.switch_manager.evaluate_switch(cand, cand_exp, current_tick=tick):
                    self.switch_manager.execute_switch(cand, current_tick=tick)

        return action
