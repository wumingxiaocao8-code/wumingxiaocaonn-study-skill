import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inspect_book_structure = load_module(
    "inspect_book_structure", "scripts/inspect_book_structure.py"
)
split_markdown_book = load_module("split_markdown_book", "scripts/split_markdown_book.py")


class InspectBookStructureTests(unittest.TestCase):
    def test_counts_section_and_subsection_text_in_chapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "book.md"
            book.write_text(
                "\n".join(
                    [
                        "# Chapter 1",
                        "intro",
                        "## Section 1",
                        "section text",
                        "### Detail 1",
                        "detail text",
                        "# Chapter 2",
                        "tail",
                    ]
                ),
                encoding="utf-8",
            )

            result = inspect_book_structure.inspect_book(str(book))

        self.assertEqual(result["chapter_count"], 2)
        chapter = result["chapters"][0]
        self.assertEqual(chapter["char_count"], len("intro") + len("section text") + len("detail text"))
        self.assertEqual(chapter["sections"][0]["char_count"], len("section text") + len("detail text"))
        self.assertEqual(chapter["sections"][0]["subsections"][0]["char_count"], len("detail text"))

    def test_long_section_text_drives_module_suggestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "book.md"
            book.write_text("# Long Chapter\nintro\n## Large Section\n" + ("x" * 9000), encoding="utf-8")

            result = inspect_book_structure.inspect_book(str(book))
            modules = inspect_book_structure.suggest_modules(result)

        self.assertGreater(result["chapters"][0]["char_count"], 8000)
        self.assertEqual(modules[0]["title"], "Long Chapter")
        self.assertGreater(modules[0]["char_count"], 8000)

    def test_cli_handles_non_gbk_characters_in_readme(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "inspect_book_structure.py"), "README.md"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("suggested_modules", completed.stdout)


class SplitMarkdownBookTests(unittest.TestCase):
    def test_split_preserves_chapters_without_sections_and_chapter_preface(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "book.md"
            output_dir = tmp_path / "chapters"
            source.write_text(
                "\n".join(
                    [
                        "# Chapter 1",
                        "intro one",
                        "# Chapter 2",
                        "preface two",
                        "## Section 2",
                        "body two",
                    ]
                ),
                encoding="utf-8",
            )

            result = split_markdown_book.split_book(str(source), str(output_dir))

            self.assertEqual(result["count"], 3)
            files = {p.name: p.read_text(encoding="utf-8") for p in output_dir.glob("*.md")}

        self.assertIn("Chapter 1.md", files)
        self.assertIn("Chapter 2 - 概述.md", files)
        self.assertIn("Chapter 2 - Section 2.md", files)
        self.assertIn("intro one", files["Chapter 1.md"])
        self.assertIn("preface two", files["Chapter 2 - 概述.md"])
        self.assertIn("body two", files["Chapter 2 - Section 2.md"])

    def test_split_rejects_output_outside_current_workspace(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "book.md"
            source.write_text("# Chapter\nbody", encoding="utf-8")
            outside = Path(tempfile.gettempdir()) / "reading_split_outside_workspace"

            result = split_markdown_book.split_book(str(source), str(outside))

        self.assertIn("error", result)
        self.assertIn("outside current workspace", result["error"])


if __name__ == "__main__":
    unittest.main()
