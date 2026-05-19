"""Tests for deterministic Mnemon eval gates."""

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from teramina.agent.evals.mnemon_eval import (
    FARMER_QUESTION_SET,
    evaluate_answer_set,
    evaluate_memory_answer,
    load_answer_cases,
)


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


def test_load_answer_cases_merges_question_metadata(tmp_path):
    answer_file = tmp_path / "answers.json"
    answer_file.write_text(json.dumps({
        "answers": [
            {
                "id": "feed_less_today",
                "answer": (
                    "Recommendation: reduce feed using live data from active_cycle today. "
                    "Reason: pakan leftover is high in kolam active_cycle today. Confidence: medium."
                ),
            }
        ]
    }))

    cases = load_answer_cases(str(answer_file))

    assert cases[0]["id"] == "feed_less_today"
    assert cases[0]["live_data_required"] is True
    assert cases[0]["expected_time_period"] == "today"


def test_run_mnemon_evals_command_passes_with_complete_json_file(tmp_path, capsys):
    answer_file = tmp_path / "answers.json"
    answer_file.write_text(json.dumps({
        "answers": [
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
            }
        ]
    }))

    call_command("run_mnemon_evals", answers=str(answer_file))

    assert "Mnemon eval: 1/1 passed" in capsys.readouterr().out


def test_run_mnemon_evals_command_fails_when_gate_fails(tmp_path):
    answer_file = tmp_path / "answers.jsonl"
    answer_file.write_text(json.dumps({
        "id": "bad-case",
        "answer": "Recommendation: reduce feed 15%. Reason: pond-a last_cycle. Confidence: medium.",
        "expected_entity_ids": ["pond-a"],
        "expected_time_period": "last_cycle",
        "allowed_numbers": [],
    }))

    with pytest.raises(CommandError, match="Mnemon eval failed"):
        call_command("run_mnemon_evals", answers=str(answer_file))
