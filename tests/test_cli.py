from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from xrazor.cli import app

runner = CliRunner()


def test_clean_command_detects_html(tmp_path: Path) -> None:
    input_file = tmp_path / "page.html"
    input_file.write_text("<html><body><script>x</script><div>ok</div></body></html>", encoding="utf-8")

    result = runner.invoke(app, ["clean", str(input_file)])

    assert result.exit_code == 0
    assert "<script" not in result.stdout
    assert "XRazor" in result.stdout


def test_context_command_detects_har(tmp_path: Path) -> None:
    input_file = tmp_path / "page.har"
    input_file.write_text(
        '{"log":{"entries":[{"_resourceType":"xhr","request":{"method":"GET","url":"https://example.com/api","headers":[]},"response":{"status":200,"headers":[],"content":{"mimeType":"application/json","text":"{\\"ok\\":true}"}}}]}}',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["context", str(input_file)])

    assert result.exit_code == 0
    assert "Important APIs:" in result.stdout
    assert "https://example.com/api" in result.stdout


def test_context_command_filters_generic_html_labels(tmp_path: Path) -> None:
    input_file = tmp_path / "page.html"
    input_file.write_text(
        '<html><body><button></button><div role="button"></div><button aria-label="Save"></button></body></html>',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["context", str(input_file)])

    assert result.exit_code == 0
    assert "- Save" in result.stdout
    assert "- button" not in result.stdout
    assert "- div" not in result.stdout


def test_context_command_includes_headings_and_stats(tmp_path: Path) -> None:
    input_file = tmp_path / "page.html"
    input_file.write_text(
        """
        <html><body>
        <h1 data-e2e="user-title">Ms.Vi</h1>
        <strong data-e2e="followers-count">62K</strong>
        <button aria-label="Follow">Follow</button>
        </body></html>
        """,
        encoding="utf-8",
    )

    result = runner.invoke(app, ["context", str(input_file)])

    assert result.exit_code == 0
    assert "Important headings:" in result.stdout
    assert "- Ms.Vi" in result.stdout
    assert "Visible stats:" in result.stdout
    assert "- followers: 62K" in result.stdout
