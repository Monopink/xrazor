from __future__ import annotations

from pathlib import Path

import typer

from xrazor.cleaners.har_cleaner import HarCleaner
from xrazor.cleaners.html_cleaner import HtmlCleaner
from xrazor.exporters.ai_context import HarAiContextExporter, HtmlAiContextExporter
from xrazor.exporters.har_exporter import HarJsonExporter, HarMarkdownExporter
from xrazor.exporters.html_exporter import HtmlJsonExporter, HtmlMarkdownExporter
from xrazor.models.config import AppConfig

app = typer.Typer(help="XRazor CLI")


def _load_config(config_path: Path | None) -> AppConfig:
    if config_path is None:
        return AppConfig.default()
    return AppConfig.from_toml(config_path)


def _write_output(content: str, output: Path | None) -> None:
    if output is None:
        typer.echo(content)
        return
    output.write_text(content, encoding="utf-8")


def _apply_html_overrides(
    app_config: AppConfig,
    *,
    image_mode: str | None,
    class_mode: str | None,
) -> AppConfig:
    if image_mode is not None:
        app_config.html.image_mode = image_mode
    if class_mode is not None:
        app_config.html.class_mode = class_mode
    return app_config


def _detect_input_kind(input_path: Path, kind: str | None = None) -> str:
    if kind is not None:
        return kind
    suffix = input_path.suffix.lower()
    if suffix == ".har":
        return "har"
    if suffix in {".html", ".htm"}:
        return "html"
    raise typer.BadParameter("Cannot infer input type. Use --kind html|har.")


def _clean_by_kind(input_path: Path, *, kind: str, app_config: AppConfig) -> str:
    raw = input_path.read_text(encoding="utf-8")
    if kind == "html":
        return HtmlCleaner(app_config.html).clean(raw).content
    if kind == "har":
        return HarCleaner(app_config.har).clean(raw).content
    raise typer.BadParameter(f"Unsupported kind: {kind}")


@app.command("clean-html")
def clean_html(
    input_path: Path,
    output: Path | None = typer.Option(None, "--out", "-o"),
    config: Path | None = typer.Option(None, "--config"),
    image_mode: str | None = typer.Option(None, "--image-mode"),
    class_mode: str | None = typer.Option(None, "--class-mode"),
) -> None:
    app_config = _apply_html_overrides(
        _load_config(config),
        image_mode=image_mode,
        class_mode=class_mode,
    )
    cleaner = HtmlCleaner(app_config.html)
    raw = input_path.read_text(encoding="utf-8")
    result = cleaner.clean(raw)
    _write_output(result.content, output)


@app.command("clean-har")
def clean_har(
    input_path: Path,
    output: Path | None = typer.Option(None, "--out", "-o"),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    app_config = _load_config(config)
    cleaner = HarCleaner(app_config.har)
    raw = input_path.read_text(encoding="utf-8")
    result = cleaner.clean(raw)
    _write_output(result.content, output)


@app.command("clean")
def clean(
    input_path: Path,
    output: Path | None = typer.Option(None, "--out", "-o"),
    config: Path | None = typer.Option(None, "--config"),
    kind: str | None = typer.Option(None, "--kind"),
    image_mode: str | None = typer.Option(None, "--image-mode"),
    class_mode: str | None = typer.Option(None, "--class-mode"),
) -> None:
    app_config = _apply_html_overrides(
        _load_config(config),
        image_mode=image_mode,
        class_mode=class_mode,
    )
    detected_kind = _detect_input_kind(input_path, kind)
    cleaned = _clean_by_kind(input_path, kind=detected_kind, app_config=app_config)
    _write_output(cleaned, output)


@app.command("export-html")
def export_html(
    input_path: Path,
    format_name: str = typer.Option("json", "--format"),
    config: Path | None = typer.Option(None, "--config"),
    output: Path | None = typer.Option(None, "--out", "-o"),
    image_mode: str | None = typer.Option(None, "--image-mode"),
    class_mode: str | None = typer.Option(None, "--class-mode"),
) -> None:
    app_config = _apply_html_overrides(
        _load_config(config),
        image_mode=image_mode,
        class_mode=class_mode,
    )
    cleaned = HtmlCleaner(app_config.html).clean(input_path.read_text(encoding="utf-8")).content

    if format_name == "markdown":
        result = HtmlMarkdownExporter().export(cleaned)
    else:
        result = HtmlJsonExporter().export(cleaned)
    _write_output(result.content, output)


@app.command("export-har")
def export_har(
    input_path: Path,
    format_name: str = typer.Option("json", "--format"),
    config: Path | None = typer.Option(None, "--config"),
    output: Path | None = typer.Option(None, "--out", "-o"),
) -> None:
    app_config = _load_config(config)
    cleaned = HarCleaner(app_config.har).clean(input_path.read_text(encoding="utf-8")).content

    if format_name == "markdown":
        result = HarMarkdownExporter().export(cleaned)
    else:
        result = HarJsonExporter().export(cleaned)
    _write_output(result.content, output)


@app.command("export")
def export(
    input_path: Path,
    format_name: str = typer.Option("json", "--format"),
    config: Path | None = typer.Option(None, "--config"),
    output: Path | None = typer.Option(None, "--out", "-o"),
    kind: str | None = typer.Option(None, "--kind"),
    image_mode: str | None = typer.Option(None, "--image-mode"),
    class_mode: str | None = typer.Option(None, "--class-mode"),
) -> None:
    app_config = _apply_html_overrides(
        _load_config(config),
        image_mode=image_mode,
        class_mode=class_mode,
    )
    detected_kind = _detect_input_kind(input_path, kind)
    cleaned = _clean_by_kind(input_path, kind=detected_kind, app_config=app_config)

    if detected_kind == "html":
        result = HtmlMarkdownExporter().export(cleaned) if format_name == "markdown" else HtmlJsonExporter().export(cleaned)
    else:
        result = HarMarkdownExporter().export(cleaned) if format_name == "markdown" else HarJsonExporter().export(cleaned)
    _write_output(result.content, output)


@app.command("context")
def context(
    input_path: Path,
    config: Path | None = typer.Option(None, "--config"),
    output: Path | None = typer.Option(None, "--out", "-o"),
    kind: str | None = typer.Option(None, "--kind"),
    image_mode: str | None = typer.Option(None, "--image-mode"),
    class_mode: str | None = typer.Option(None, "--class-mode"),
) -> None:
    app_config = _apply_html_overrides(
        _load_config(config),
        image_mode=image_mode,
        class_mode=class_mode,
    )
    detected_kind = _detect_input_kind(input_path, kind)
    cleaned = _clean_by_kind(input_path, kind=detected_kind, app_config=app_config)

    if detected_kind == "html":
        result = HtmlAiContextExporter().export(cleaned)
    else:
        result = HarAiContextExporter().export(cleaned)
    _write_output(result.content, output)
