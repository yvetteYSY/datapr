from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_markdown_links import find_broken_links, main, markdown_files


ROOT = Path(__file__).parent.parent


class MarkdownLinkTest(unittest.TestCase):
    def test_covers_required_repository_markdown(self) -> None:
        expected = {
            ROOT / "README.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "ROADMAP.md",
            ROOT / "CHANGELOG.md",
            *(ROOT / "docs").rglob("*.md"),
        }

        self.assertEqual(expected, set(markdown_files(ROOT)))
        self.assertEqual([], find_broken_links(ROOT))

    def test_accepts_supported_relative_link_shapes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "examples").mkdir()
            (root / "docs/a file.md").touch()
            (root / "docs/name_(v1).md").touch()
            (root / "README.md").write_text(
                """[Directory](examples)
[Encoded](docs/a%20file.md#details)
[Parentheses](docs/name_(v1).md)
[Titled](docs/a%20file.md "Guide")
""",
                encoding="utf-8",
            )

            self.assertEqual([], find_broken_links(root))

    def test_ignores_external_links_and_in_page_anchors(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                """[HTTP](https://example.com/missing.md)
[Protocol relative](//example.com/missing.md)
[Email](mailto:docs@example.com)
[Section](#overview)
[Query only](?plain=1)
""",
                encoding="utf-8",
            )

            self.assertEqual([], find_broken_links(root))

    def test_checks_linked_images_and_reference_definitions(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                """[![Badge](https://example.com/badge.svg)](missing-badge-target.md)
[Guide][guide]

[guide]: missing-reference.md "Guide"
""",
                encoding="utf-8",
            )

            self.assertEqual(
                [
                    "README.md: missing-badge-target.md",
                    "README.md: missing-reference.md",
                ],
                find_broken_links(root),
            )

    def test_ignores_links_in_code_and_comments(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                """`[Inline code](missing-inline.md)`

```markdown
[Fenced code](missing-fenced.md)
```

<!-- [Comment](missing-comment.md) -->
""",
                encoding="utf-8",
            )

            self.assertEqual([], find_broken_links(root))

    def test_ignores_incomplete_or_escaped_link_syntax(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                """\\[Escaped](missing-escaped.md)
prose](missing-opener.md)
[Missing close](missing-closing.md
""",
                encoding="utf-8",
            )

            self.assertEqual([], find_broken_links(root))

    def test_reports_source_and_target_in_deterministic_order(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "README.md").write_text(
                "[Missing root](missing-root.md)\n", encoding="utf-8"
            )
            (root / "docs/guide.md").write_text(
                "[Missing nested](missing-nested.md#section)\n", encoding="utf-8"
            )

            self.assertEqual(
                [
                    "README.md: missing-root.md",
                    "docs/guide.md: missing-nested.md#section",
                ],
                find_broken_links(root),
            )

    def test_rejects_targets_outside_the_repository(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "repository"
            root.mkdir()
            (Path(directory) / "outside.md").touch()
            (root / "README.md").write_text(
                "[Outside](../outside.md)\n", encoding="utf-8"
            )

            self.assertEqual(
                ["README.md: ../outside.md"],
                find_broken_links(root),
            )

    def test_command_reports_source_and_target(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "[Missing](docs/missing.md)\n", encoding="utf-8"
            )
            stderr = StringIO()

            with redirect_stderr(stderr):
                result = main(["--root", str(root)])

            self.assertEqual(1, result)
            self.assertIn(
                "broken Markdown link: README.md: docs/missing.md",
                stderr.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
