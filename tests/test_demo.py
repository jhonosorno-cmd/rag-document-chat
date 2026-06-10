from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_load_demo_questions_returns_list(tmp_path):
    questions_file = tmp_path / "preguntas.txt"
    questions_file.write_text("¿Pregunta uno?\n¿Pregunta dos?\n\n¿Pregunta tres?\n", encoding="utf-8")

    from chat import load_demo_questions_from_path
    result = load_demo_questions_from_path(questions_file)
    assert result == ["¿Pregunta uno?", "¿Pregunta dos?", "¿Pregunta tres?"]


def test_load_demo_questions_empty_file(tmp_path):
    questions_file = tmp_path / "preguntas.txt"
    questions_file.write_text("", encoding="utf-8")

    from chat import load_demo_questions_from_path
    result = load_demo_questions_from_path(questions_file)
    assert result == []


def test_load_demo_questions_missing_file(tmp_path):
    from chat import load_demo_questions_from_path
    result = load_demo_questions_from_path(tmp_path / "no_existe.txt")
    assert result == []
