import { NOTES } from "./constants";
import { defaultHtmlConfig } from "./config";
import type { CleanResult, HtmlCleanerConfig } from "./types";

const whitespace = /\s+/g;
const eventAttribute = /^on[a-z]+$/;
const hashClass = /^(?:[a-f0-9]{6,}|[A-Za-z0-9_-]{12,})$/;
const generatedClasses = [/^css-/, /^e[a-z0-9]{6,}$/, /^[a-z]{2,}\d[a-z0-9]{3,}$/, /.*_v\d+(?:_\d+)*$/];
const semanticSegment = /^[A-Za-z][A-Za-z-]{2,}$/;
const classStopwords = new Set([
  "active", "base", "box", "canary", "card", "center", "component", "container",
  "content", "default", "element", "item", "label", "left", "medium", "primary",
  "right", "small", "text", "tiny", "top", "wrapper",
]);

export function cleanHtmlText(raw: string, config?: Partial<HtmlCleanerConfig>): CleanResult<string> {
  if (typeof DOMParser === "undefined") {
    throw new Error(
      "cleanHtmlText requires a browser DOM environment with DOMParser, NodeFilter, and XMLSerializer",
    );
  }
  const document = new DOMParser().parseFromString(raw, "text/html");
  const result = cleanHtmlDocument(document, config);
  if (typeof XMLSerializer === "undefined") {
    throw new Error(
      "cleanHtmlText requires a browser DOM environment with DOMParser, NodeFilter, and XMLSerializer",
    );
  }
  return {
    ...result,
    content: `<!-- XRazor: ${NOTES.file} -->\n${new XMLSerializer().serializeToString(document)}`,
  };
}

export function cleanHtmlDocument(
  document: Document,
  overrides?: Partial<HtmlCleanerConfig>,
): CleanResult<Document> {
  if (typeof NodeFilter === "undefined") {
    throw new Error(
      "cleanHtmlDocument requires a browser DOM environment with DOMParser, NodeFilter, and XMLSerializer",
    );
  }
  const config = mergeConfig(defaultHtmlConfig(), overrides);
  document.querySelectorAll("*").forEach((element) => {
    if (config.removeTags.has(element.tagName.toLowerCase())) element.remove();
  });

  const walker = document.createTreeWalker(document, NodeFilter.SHOW_ALL);
  const nodes: Node[] = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    if (node.nodeType === Node.COMMENT_NODE) node.parentNode?.removeChild(node);
    if (node.nodeType === Node.TEXT_NODE && node.nodeValue) node.nodeValue = normalizeText(node.nodeValue);
  }

  document.querySelectorAll("*").forEach((element) => cleanAttributes(element, config));
  if (config.removeEmptyNodes) removeEmptyNodes(document);
  return { content: document, warnings: [] };
}

function mergeConfig(base: HtmlCleanerConfig, overrides?: Partial<HtmlCleanerConfig>): HtmlCleanerConfig {
  return { ...base, ...overrides };
}

function cleanAttributes(element: Element, config: HtmlCleanerConfig): void {
  const attributes = Array.from(element.attributes);
  for (const attribute of attributes) {
    const name = attribute.name;
    const lowered = name.toLowerCase();
    if (eventAttribute.test(lowered) || ["style", "tabindex", "draggable", "contenteditable"].includes(lowered)) {
      element.removeAttribute(name);
      continue;
    }
    if (lowered === "class") {
      const value = config.classMode === "none" ? "" : config.classMode === "all" ? attribute.value : filterClasses(attribute.value);
      value ? element.setAttribute(name, value) : element.removeAttribute(name);
      continue;
    }
    if (lowered.startsWith("aria-") && !config.keepAriaAttributes.has(lowered)) {
      element.removeAttribute(name);
      continue;
    }
    if (lowered.startsWith("data-") && !config.keepDataAttributes.has(lowered)) {
      element.removeAttribute(name);
      continue;
    }
    if (!config.keepAttributes.has(lowered) && !config.keepAriaAttributes.has(lowered) && !config.keepDataAttributes.has(lowered)) {
      element.removeAttribute(name);
      continue;
    }
    let value = attribute.value;
    if (lowered === "src" && value.startsWith("data:")) {
      if (element.tagName.toLowerCase() === "img" && config.imageMode === "remove") {
        element.remove();
        return;
      }
      value = config.imageMode === "placeholder" ? NOTES.removedNonEssential : NOTES.filteredBase64;
    }
    if (value.length > config.maxAttributeValueLength) value = NOTES.trimmedLongText;
    element.setAttribute(name, value);
  }
  if (config.imageMode === "remove" && element.tagName.toLowerCase() === "img") element.remove();
}

function filterClasses(value: string): string {
  return value.split(/\s+/).filter((token) => {
    if (!token || generatedClasses.some((pattern) => pattern.test(token))) return false;
    if (hashClass.test(token) && !token.includes("-") && !token.includes("_")) return false;
    if (token.toLowerCase().startsWith("tux-")) return false;
    return token.split(/[-_]/).some((segment) => semanticSegment.test(segment) && !classStopwords.has(segment.toLowerCase()));
  }).join(" ");
}

function normalizeText(value: string): string { return value.replace(whitespace, " ").trim(); }

function removeEmptyNodes(document: Document): void {
  let changed = true;
  while (changed) {
    changed = false;
    for (const element of Array.from(document.querySelectorAll("*")).reverse()) {
      if (["input", "button", "a", "form", "label", "img"].includes(element.tagName.toLowerCase())) continue;
      if (["id", "name", "href", "value", "role", "type"].some((name) => element.hasAttribute(name))) continue;
      if (element.textContent?.trim() || element.children.length) continue;
      element.remove();
      changed = true;
    }
  }
}
