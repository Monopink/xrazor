from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class HtmlCleanerConfig(BaseModel):
    remove_tags: set[str] = Field(
        default_factory=lambda: {
            "script",
            "style",
            "noscript",
            "svg",
            "canvas",
            "iframe",
            "template",
            "link",
            "meta",
            "source",
            "picture",
        }
    )
    keep_attributes: set[str] = Field(
        default_factory=lambda: {
            "id",
            "name",
            "type",
            "href",
            "src",
            "value",
            "placeholder",
            "title",
            "role",
            "alt",
            "action",
            "method",
            "for",
        }
    )
    keep_aria_attributes: set[str] = Field(
        default_factory=lambda: {"aria-label", "aria-labelledby", "aria-describedby"}
    )
    keep_data_attributes: set[str] = Field(
        default_factory=lambda: {"data-testid", "data-test", "data-e2e"}
    )
    class_mode: str = "semantic"
    remove_empty_nodes: bool = True
    image_mode: str = "strip-base64"
    max_attribute_value_length: int = 512


class HarCleanerConfig(BaseModel):
    keep_resource_types: set[str] = Field(default_factory=lambda: {"document", "xhr", "fetch"})
    drop_resource_types: set[str] = Field(
        default_factory=lambda: {"script", "stylesheet", "image", "font", "media", "websocket"}
    )
    remove_cookie_headers: bool = True
    remove_response_cookies: bool = True
    trim_json_arrays_to: int = 10
    trim_json_object_keys_to: int = 50
    trim_long_strings_to: int = 500
    max_json_depth: int = 8


class AppConfig(BaseModel):
    html: HtmlCleanerConfig = Field(default_factory=HtmlCleanerConfig)
    har: HarCleanerConfig = Field(default_factory=HarCleanerConfig)

    @classmethod
    def default(cls) -> "AppConfig":
        return cls()

    @classmethod
    def from_toml(cls, path: Path) -> "AppConfig":
        import tomllib

        with path.open("rb") as file:
            data = tomllib.load(file)
        return cls.model_validate(data)
