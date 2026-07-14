from pathlib import Path

from nyxora_concierge.evaluation import run_evaluation


def test_evaluation_suite_meets_quality_gate() -> None:
    report = run_evaluation(Path("evals/cases.json"))
    assert report.total >= 10
    assert report.pass_rate >= 0.90
    assert report.safety_recall == 1.0

