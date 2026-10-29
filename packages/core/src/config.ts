import type { AppConfig, HarCleanerConfig, HtmlCleanerConfig } from "./types";

const set = (values: string[]): Set<string> => new Set(values);

export const defaultHtmlConfig = (): HtmlCleanerConfig => ({
  removeTags: set([
    "script", "style", "noscript", "svg", "canvas", "iframe", "template",
    "link", "meta", "source", "picture",
  ]),
  keepAttributes: set([
    "id", "name", "type", "href", "src", "value", "placeholder", "title",
    "role", "alt", "action", "method", "for",
  ]),
  keepAriaAttributes: set(["aria-label", "aria-labelledby", "aria-describedby"]),
  keepDataAttributes: set(["data-testid", "data-test", "data-e2e"]),
  classMode: "semantic",
  removeEmptyNodes: true,
  imageMode: "strip-base64",
  maxAttributeValueLength: 512,
});

export const defaultHarConfig = (): HarCleanerConfig => ({
  keepResourceTypes: set(["document", "xhr", "fetch"]),
  dropResourceTypes: set(["script", "stylesheet", "image", "font", "media", "websocket"]),
  removeCookieHeaders: true,
  removeResponseCookies: true,
  trimJsonArraysTo: 10,
  trimJsonObjectKeysTo: 50,
  trimLongStringsTo: 500,
  maxJsonDepth: 8,
});

export const defaultConfig = (): AppConfig => ({
  html: defaultHtmlConfig(),
  har: defaultHarConfig(),
});
