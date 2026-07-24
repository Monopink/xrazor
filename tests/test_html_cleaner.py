from __future__ import annotations

from xrazor.cleaners.html_cleaner import HtmlCleaner
from xrazor.models.config import HtmlCleanerConfig

from xrazor.cleaners.html_cleaner import HtmlCleaner


def test_html_cleaner_removes_script_and_rewrites_base64_src() -> None:
    cleaner = HtmlCleaner()
    raw = """
    <html>
      <body>
        <script>alert(1)</script>
        <img src="data:image/png;base64,AAAA" alt="sample">
        <div class="content card abcdef123456"> Hello   world </div>
      </body>
    </html>
    """

    result = cleaner.clean(raw)
    assert "<script" not in result.content
    assert '[xrazor]filtered-base64-content' in result.content
    assert "Hello world" in result.content


def test_html_cleaner_supports_image_remove_mode() -> None:
    cleaner = HtmlCleaner(HtmlCleanerConfig(image_mode="remove"))
    raw = '<html><body><img src="https://example.com/a.png" alt="sample"><div>ok</div></body></html>'

    result = cleaner.clean(raw)

    assert "<img" not in result.content
    assert "ok" in result.content


def test_html_cleaner_supports_class_modes() -> None:
    raw = '<html><body><div class="content css-abc123 tux-button__x card hero-banner">x</div></body></html>'

    semantic = HtmlCleaner(HtmlCleanerConfig(class_mode="semantic")).clean(raw).content
    keep_all = HtmlCleaner(HtmlCleanerConfig(class_mode="all")).clean(raw).content
    keep_none = HtmlCleaner(HtmlCleanerConfig(class_mode="none")).clean(raw).content

    assert 'class="hero-banner"' in semantic
    assert 'class="content css-abc123 tux-button__x card hero-banner"' in keep_all
    assert 'class="' not in keep_none
