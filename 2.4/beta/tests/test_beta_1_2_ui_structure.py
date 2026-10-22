from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_ui_modules_exist():
    for name in ["theme.py", "components.py", "layout.py"]:
        assert (ROOT / "ui" / name).exists()

def test_play_explore_learn_are_in_app():
    text = (ROOT / "app.py").read_text()
    assert 'view == "Play"' in text
    assert 'view == "Explore"' in text
    assert 'view == "Learn"' in text
    assert 'render_home' in text

def test_sprint_does_not_modify_backend_files_by_ui_import():
    text = (ROOT / "game_backend.py").read_text()
    assert "from ui" not in text
