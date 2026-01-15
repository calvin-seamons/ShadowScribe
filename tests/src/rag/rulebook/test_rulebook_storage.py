import pytest
import os
import json
import numpy as np
from pathlib import Path
from src.rag.rulebook.rulebook_storage import RulebookStorage
from src.rag.rulebook.rulebook_types import RulebookSection, RulebookCategory

@pytest.fixture
def temp_storage(tmp_path):
    # Initialize storage with a temporary path
    storage = RulebookStorage(storage_path=str(tmp_path))
    return storage

def test_json_serialization(temp_storage):
    # Create a dummy section
    section = RulebookSection(
        id="test-section",
        title="Test Section",
        level=1,
        content="This is a test content.",
        categories=[RulebookCategory.COMBAT],
        vector=[0.1, 0.2, 0.3]  # List
    )
    temp_storage.sections["test-section"] = section
    temp_storage.category_index[RulebookCategory.COMBAT].add("test-section")

    # Save to JSON
    temp_storage.save_to_disk("test_storage.json")

    # Verify file exists
    json_path = temp_storage.storage_path / "test_storage.json"
    assert json_path.exists()

    # Load from JSON
    new_storage = RulebookStorage(storage_path=str(temp_storage.storage_path))
    success = new_storage.load_from_disk("test_storage.json")
    assert success

    # Verify content
    loaded_section = new_storage.sections["test-section"]
    assert loaded_section.title == "Test Section"
    assert isinstance(loaded_section.vector, np.ndarray)
    assert np.allclose(loaded_section.vector, np.array([0.1, 0.2, 0.3]))
    assert RulebookCategory.COMBAT in loaded_section.categories

def test_numpy_vector_serialization(temp_storage):
    # Create a dummy section with numpy vector
    section = RulebookSection(
        id="numpy-section",
        title="Numpy Section",
        level=1,
        content="Content",
        categories=[RulebookCategory.SPELLCASTING],
        vector=np.array([0.4, 0.5, 0.6])
    )
    temp_storage.sections["numpy-section"] = section

    # Save to JSON
    temp_storage.save_to_disk("numpy_storage.json")

    # Load back
    new_storage = RulebookStorage(storage_path=str(temp_storage.storage_path))
    new_storage.load_from_disk("numpy_storage.json")

    # Verify vector became numpy array again
    loaded_vector = new_storage.sections["numpy-section"].vector
    assert isinstance(loaded_vector, np.ndarray)
    assert np.allclose(loaded_vector, np.array([0.4, 0.5, 0.6]))

def test_legacy_load_fail(temp_storage):
    # Ensure attempting to load a non-existent file fails gracefully
    success = temp_storage.load_from_disk("non_existent.json")
    assert not success
