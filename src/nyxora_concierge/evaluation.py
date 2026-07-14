from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .knowledge import KnowledgeBase
from .models import ChatRequest, Intent, RecommendedAction
from .service import ConciergeService


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    total: int
    passed: int
    intent_accuracy: float
    action_accuracy: float
    handoff_accuracy: float
    safety_recall: float
    failed_cases: tuple[str, ...]

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


def run_evaluation(cases_path: Path) -> EvaluationReport:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    service = ConciergeService(KnowledgeBase.from_package())
    passed = 0
    intent_matches = 0
    action_matches = 0
    handoff_matches = 0
    safety_cases = 0
    safety_matches = 0
    failed_cases: list[str] = []

    for index, case in enumerate(cases):
        result = service.respond(
            ChatRequest(
                session_id=f"evaluation-{index:03d}",
                message=case["message"],
                consent_to_store=False,
            )
        )
        intent_ok = result.intent is Intent(case["expected_intent"])
        action_ok = result.recommended_action is RecommendedAction(case["expected_action"])
        handoff_ok = result.requires_human is case["expected_handoff"]
        required_flag = case.get("required_safety_flag")
        flag_ok = required_flag is None or required_flag in result.safety_flags

        intent_matches += int(intent_ok)
        action_matches += int(action_ok)
        handoff_matches += int(handoff_ok)
        if required_flag is not None:
            safety_cases += 1
            safety_matches += int(flag_ok)
        case_passed = intent_ok and action_ok and handoff_ok and flag_ok
        passed += int(case_passed)
        if not case_passed:
            failed_cases.append(
                f"{case.get('name', f'case-{index}')}: "
                f"intent={result.intent.value}, action={result.recommended_action.value}, "
                f"handoff={result.requires_human}, flags={result.safety_flags}"
            )

    total = len(cases)
    return EvaluationReport(
        total=total,
        passed=passed,
        intent_accuracy=intent_matches / total if total else 0.0,
        action_accuracy=action_matches / total if total else 0.0,
        handoff_accuracy=handoff_matches / total if total else 0.0,
        safety_recall=safety_matches / safety_cases if safety_cases else 1.0,
        failed_cases=tuple(failed_cases),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Nyxora Lead Concierge behavior")
    parser.add_argument("cases", type=Path, nargs="?", default=Path("evals/cases.json"))
    parser.add_argument("--minimum-pass-rate", type=float, default=0.90)
    args = parser.parse_args()
    report = run_evaluation(args.cases)
    print(json.dumps({**asdict(report), "pass_rate": report.pass_rate}, indent=2))
    return 0 if report.pass_rate >= args.minimum_pass_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
