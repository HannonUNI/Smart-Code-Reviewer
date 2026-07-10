import tempfile
import unittest
from pathlib import Path

import reviewer
from external_tools import ReviewConfig, collect_python_files


class CollectPythonFilesTests(unittest.TestCase):
    def test_defaults_are_used_when_no_config_is_provided(self):
        config = reviewer.ReviewConfig()
        self.assertEqual(config.max_function_lines, 30)
        self.assertEqual(config.max_function_args, 5)
        self.assertEqual(config.complexity_threshold, 10)
        self.assertEqual(config.maintainability_low_threshold, 40.0)
        self.assertEqual(config.maintainability_very_low_threshold, 20.0)
        self.assertEqual(config.flake8_max_line_length, 120)

    def test_skips_venv_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            good_file = root / "good.py"
            good_file.write_text("value = 1\n", encoding="utf-8")

            venv_dir = root / ".venv"
            venv_dir.mkdir()
            ignored_file = venv_dir / "ignored.py"
            ignored_file.write_text("value = 2\n", encoding="utf-8")

            nested_dir = root / "src"
            nested_dir.mkdir()
            nested_file = nested_dir / "module.py"
            nested_file.write_text("value = 3\n", encoding="utf-8")

            ignored_by_gitignore_dir = root / "build"
            ignored_by_gitignore_dir.mkdir()
            ignored_by_gitignore_file = ignored_by_gitignore_dir / "ignored_build.py"
            ignored_by_gitignore_file.write_text("value = 4\n", encoding="utf-8")

            (root / ".gitignore").write_text("build\n", encoding="utf-8")

            files = sorted(str(path) for path in collect_python_files(root))

            self.assertEqual(files, [str(good_file), str(nested_file)])


if __name__ == "__main__":
    unittest.main()
