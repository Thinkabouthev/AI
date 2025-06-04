import json
import os
import pytest
from pathlib import Path
from pydantic import ValidationError
from scripts.generate_notes import Note

@pytest.fixture
def load_notes():
    # Look for exam_notes.json in the project root directory
    file_path = Path(__file__).parent.parent / "exam_notes.json"
    if not file_path.exists():
        pytest.skip("exam_notes.json not found. Run generate_notes.py first.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_notes_count(load_notes):
    assert len(load_notes) == 10, "There should be exactly 10 notes."

def test_note_structure(load_notes):
    for item in load_notes:
        try:
            note = Note(**item)
        except ValidationError as e:
            pytest.fail(f"Validation failed for item: {item}\nError: {e}")

def test_fields_are_not_empty(load_notes):
    for item in load_notes:
        note = Note(**item)
        assert note.heading.strip(), "Note heading must not be empty."
        assert note.summary.strip(), "Note summary must not be empty."

def test_id_range(load_notes):
    ids = [note['id'] for note in load_notes]
    assert sorted(ids) == list(range(1, 11)), "IDs must be sequential from 1 to 10"

def test_summary_length(load_notes):
    for item in load_notes:
        note = Note(**item)
        assert len(note.summary) <= 150, f"Summary exceeds 150 characters: {note.summary}"

def test_page_ref_format(load_notes):
    for item in load_notes:
        note = Note(**item)
        if note.page_ref is not None:
            assert isinstance(note.page_ref, int), "Page reference must be an integer"
            assert note.page_ref > 0, "Page reference must be positive"

def test_unique_headings(load_notes):
    headings = [note['heading'] for note in load_notes]
    assert len(set(headings)) == len(headings), "All note headings must be unique"

def test_note_model():
    # Test Note model validation
    with pytest.raises(ValidationError):
        Note(id=0, heading="Test", summary="Test")  # ID too low
    
    with pytest.raises(ValidationError):
        Note(id=11, heading="Test", summary="Test")  # ID too high
    
    with pytest.raises(ValidationError):
        Note(id=1, heading="", summary="Test")  # Empty heading
    
    with pytest.raises(ValidationError):
        Note(id=1, heading="Test", summary="")  # Empty summary
    
    # Test valid note
    note = Note(id=1, heading="Test", summary="Test", page_ref=42)
    assert note.id == 1
    assert note.heading == "Test"
    assert note.summary == "Test"
    assert note.page_ref == 42