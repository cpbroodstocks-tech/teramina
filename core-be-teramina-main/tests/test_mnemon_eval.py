"""Tests for deterministic Mnemon eval gates."""

from teramina.agent.evals.mnemon_eval import FARMER_QUESTION_SET, evaluate_answer_set, evaluate_memory_answer


def test_farmer_question_set_covers_planned_eval_questions():
    questions = {case["question"] for case in FARMER_QUESTION_SET}

    assert "What happened last time DO was low?" in questions
    assert "What does this farmer usually do before harvest?" in questions
    assert "Which pond has the most recurring water quality issues?" in questions
    assert "Should I feed less today?" in questions
    assert "Why are you recommending harvest next week?" in questions


def test_evaluate_memory_answer_rejects_invented_numbers():
    result = evaluate_memory_answer(
        "Recommendation: reduce feed 15%. Reason: pond-a last_cycle. Confidence: medium.",
        {
            "expected_entity_ids": ["pond-a"],
            "expected_time_period": "last_cycle",
            "allowed_numbers": [],
        },
    )

    assert result["passed"] is False
    assert result["checks"]["no_invented_numbers"] is False
    assert result["invented_numbers"] == ["15"]


def test_evaluate_answer_set_passes_complete_answers():
    result = evaluate_answer_set([
        {
            "id": "case-1",
            "answer": (
                "Recommendation: reduce feed using live data from active_cycle today. "
                "Reason: pakan leftover is high in kolam active_cycle today. Confidence: medium."
            ),
            "expected_entity_ids": ["active_cycle"],
            "expected_time_period": "today",
            "allowed_numbers": [],
            "live_data_required": True,
            "requires_indonesian": True,
        },
        {
            "id": "case-2",
            "answer": (
                "Recommendation: use the corrected preference for farmer historical. "
                "Reason: corrected memory says harvest preference changed. Confidence: high."
            ),
            "expected_entity_ids": ["farmer"],
            "expected_time_period": "historical",
            "allowed_numbers": [],
            "requires_correction_handling": True,
        },
    ])

    assert result["passed"] is True
    assert result["passed_count"] == 2
