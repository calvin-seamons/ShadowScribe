import pytest
import shutil
import pickle
from pathlib import Path
from src.rag.character.character_manager import CharacterManager
from src.rag.character.character_types import create_empty_character

@pytest.fixture
def temp_character_manager():
    """Fixture to provide a CharacterManager with a temporary directory."""
    test_dir = Path("test_knowledge_base_fix")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    manager = CharacterManager(save_directory=str(test_dir))
    yield manager

    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)

def test_save_json_format(temp_character_manager):
    """Test that characters are saved as JSON files."""
    manager = temp_character_manager
    char = create_empty_character("JsonChar", "Elf", "Wizard")
    filepath = manager.save_character(char)

    path = Path(filepath)
    assert path.suffix == ".json", f"Expected .json extension, got {path.suffix}"
    assert path.exists(), "File was not created"

    # Verify content is JSON
    with open(path, 'r') as f:
        content = f.read()
        assert content.startswith('{'), "File content does not look like JSON"

def test_load_json_character(temp_character_manager):
    """Test loading a character saved in JSON format."""
    manager = temp_character_manager
    char = create_empty_character("JsonChar", "Elf", "Wizard")
    manager.save_character(char)

    loaded_char = manager.load_character("JsonChar")
    assert loaded_char.character_base.name == "JsonChar"

def test_load_legacy_pkl_character(temp_character_manager):
    """Test backward compatibility for loading legacy PKL files."""
    manager = temp_character_manager
    test_dir = manager.save_directory

    legacy_char = create_empty_character("LegacyChar", "Dwarf", "Cleric")
    legacy_path = test_dir / "LegacyChar.pkl"

    # Create a legacy pickle file manually
    with open(legacy_path, 'wb') as f:
        pickle.dump(legacy_char, f)

    loaded_legacy = manager.load_character("LegacyChar")
    assert loaded_legacy.character_base.name == "LegacyChar"

def test_delete_character_removes_files(temp_character_manager):
    """Test deleting characters removes both JSON and PKL files."""
    manager = temp_character_manager
    test_dir = manager.save_directory

    # Create JSON file
    char_json = create_empty_character("JsonChar", "Elf", "Wizard")
    manager.save_character(char_json)

    # Create PKL file
    char_pkl = create_empty_character("LegacyChar", "Dwarf", "Cleric")
    with open(test_dir / "LegacyChar.pkl", 'wb') as f:
        pickle.dump(char_pkl, f)

    # Delete JSON char
    assert manager.delete_character("JsonChar") is True
    assert not (test_dir / "JsonChar.json").exists()

    # Delete PKL char
    assert manager.delete_character("LegacyChar") is True
    assert not (test_dir / "LegacyChar.pkl").exists()

def test_list_saved_characters(temp_character_manager):
    """Test listing characters works for both formats."""
    manager = temp_character_manager
    test_dir = manager.save_directory

    manager.save_character(create_empty_character("Char1", "Human", "Fighter"))

    with open(test_dir / "Char2.pkl", 'wb') as f:
        pickle.dump(create_empty_character("Char2", "Elf", "Rogue"), f)

    chars = manager.list_saved_characters()
    assert "Char1" in chars
    assert "Char2" in chars
    assert len(chars) == 2
