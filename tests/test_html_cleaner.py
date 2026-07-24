from __future__ import annotations

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
