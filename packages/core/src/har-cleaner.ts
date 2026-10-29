import { NOTES } from "./constants";
import { defaultHarConfig } from "./config";
import type { CleanResult, HarCleanerConfig, HarDocument } from "./types";

const requestHeadersToDrop = new Set(["accept-encoding", "accept-language", "priority", "cookie"]);
const responseHeadersToDrop = new Set(["etag", "expires", "last-modified", "server", "date", "set-cookie"]);

export function cleanHar(har: HarDocument, overrides?: Partial<HarCleanerConfig>): CleanResult<HarDocument> {
  const config = { ...defaultHarConfig(), ...overrides };
  const log = har.log ?? {};
  const entries = Array.isArray(log.entries) ? log.entries : [];
  const cleanedEntries = entries.filter((entry) => shouldKeepEntry(entry, config)).map((entry) => cleanEntry(entry, config));
  return {
    content: {
      _xrazor_note: NOTES.file,
      log: { pages: cleanPages(Array.isArray(log.pages) ? log.pages : []), entries: cleanedEntries },
    },
    warnings: [],
  };
}

export function cleanHarText(raw: string, overrides?: Partial<HarCleanerConfig>): CleanResult<string> {
  const result = cleanHar(JSON.parse(raw) as HarDocument, overrides);
  return { warnings: result.warnings, content: JSON.stringify(result.content, null, 2) };
}

function shouldKeepEntry(entry: Record<string, any>, config: HarCleanerConfig): boolean {
  const type = resourceType(entry);
  if (config.keepResourceTypes.has(type)) return true;
  if (config.dropResourceTypes.has(type)) return false;
  const mime = mimeType(entry);
  return !/^(image|font|video|audio)\//.test(mime) && /^(application\/json|text\/(html|plain))/.test(mime);
}

function cleanEntry(entry: Record<string, any>, config: HarCleanerConfig): Record<string, any> {
  const request = entry.request ?? {};
  const response = entry.response ?? {};
  const cleaned: Record<string, any> = {
    _resourceType: resourceType(entry),
    request: { method: request.method ?? "GET", url: request.url ?? "" },
    response: { status: response.status ?? "" },
  };
  const query = cleanQuery(request.queryString);
  if (Object.keys(query).length) cleaned.request.query = query;
  const headers = cleanHeaders(request.headers, false, config);
  if (Object.keys(headers).length) cleaned.request.headers = headers;
  const responseHeaders = cleanHeaders(response.headers, true, config);
  if (Object.keys(responseHeaders).length) cleaned.response.headers = responseHeaders;
  if (request.postData) cleaned.request.postData = cleanPostData(request.postData, config);
  if (response.content) cleaned.response.content = cleanContent(response.content, config);
  return cleaned;
}

function cleanPages(pages: Array<Record<string, any>>): Array<Record<string, any>> {
  return pages.map((page) => {
    const result: Record<string, any> = {};
    if (page.id) result.id = page.id;
    if (page.title) result.title = page.title;
    return result;
  }).filter((page) => Object.keys(page).length > 0);
}

function cleanHeaders(headers: unknown, response: boolean, config: HarCleanerConfig): Record<string, string> {
  const result: Record<string, string> = {};
  if (!Array.isArray(headers)) return result;
  for (const header of headers) {
    const name = String(header?.name ?? "").toLowerCase();
    if (!name || name.startsWith("sec-ch-") || name.startsWith("sec-fetch-") || name.startsWith(":")) continue;
    if (response && config.removeResponseCookies && responseHeadersToDrop.has(name)) continue;
    if (!response && config.removeCookieHeaders && requestHeadersToDrop.has(name)) continue;
    result[name] = String(header?.value ?? "");
  }
  return result;
}

function cleanQuery(query: unknown): Record<string, string> {
  const result: Record<string, string> = {};
  if (!Array.isArray(query)) return result;
  for (const item of query) if (item?.name) result[String(item.name)] = String(item.value ?? "");
  return result;
}

function cleanPostData(data: Record<string, any>, config: HarCleanerConfig): Record<string, any> {
  const result: Record<string, any> = {};
  const mime = String(data.mimeType ?? "");
  if (mime) result.mimeType = mime;
  if (Array.isArray(data.params) && data.params.length) result.params = data.params.filter((item: any) => item?.name).map((item: any) => ({ name: String(item.name), value: String(item.value ?? "") }));
  if (typeof data.text === "string") result[mime.includes("json") ? "json" : "text"] = mime.includes("json") ? trimJsonText(data.text, config) : trimString(data.text, config);
  return result;
}

function cleanContent(content: Record<string, any>, config: HarCleanerConfig): Record<string, any> {
  const mime = String(content.mimeType ?? "").toLowerCase();
  const result: Record<string, any> = {};
  if (mime) result.mimeType = mime;
  if (/^(image|font|video|audio)\//.test(mime)) return { ...result, text: NOTES.removedBinary };
  if (typeof content.text !== "string") return result;
  if (mime.includes("json")) result.json = trimJsonText(content.text, config);
  else if (looksLikeBase64(content.text)) result.text = NOTES.filteredBase64;
  else result.text = trimString(content.text, config);
  return result;
}

function trimJsonText(raw: string, config: HarCleanerConfig): unknown {
  try { return trimJsonValue(JSON.parse(raw), 0, config); }
  catch { return raw.length > config.trimLongStringsTo ? NOTES.truncatedJson : raw; }
}

function trimJsonValue(value: unknown, depth: number, config: HarCleanerConfig): unknown {
  if (depth >= config.maxJsonDepth) return NOTES.truncatedJson;
  if (Array.isArray(value)) {
    const items = value.slice(0, config.trimJsonArraysTo).map((item) => trimJsonValue(item, depth + 1, config));
    if (value.length > items.length) items.push({ _xrazor: { message: NOTES.truncatedJson, original_item_count: value.length, kept_item_count: items.length } });
    return items;
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value).slice(0, config.trimJsonObjectKeysTo);
    const result: Record<string, unknown> = Object.fromEntries(entries.map(([key, item]) => [key, trimJsonValue(item, depth + 1, config)]));
    if (Object.keys(value).length > entries.length) result._xrazor = { message: NOTES.truncatedJson, original_key_count: Object.keys(value).length, kept_key_count: entries.length };
    return result;
  }
  return typeof value === "string" ? trimString(value, config) : value;
}

function trimString(value: string, config: HarCleanerConfig): string { return value.length > config.trimLongStringsTo ? NOTES.trimmedLongText : value; }
function looksLikeBase64(value: string): boolean { return value.length >= 256 && !/[{[< \n\t]/.test(value); }
function mimeType(entry: Record<string, any>): string {
  const direct = String(entry.response?.content?.mimeType ?? "").toLowerCase();
  if (direct) return direct;
  const header = entry.response?.headers?.find((item: any) => String(item?.name ?? "").toLowerCase() === "content-type");
  return String(header?.value ?? "").toLowerCase();
}
function resourceType(entry: Record<string, any>): string {
  const explicit = String(entry._resourceType ?? "").toLowerCase().trim();
  if (explicit) return explicit;
  const mime = mimeType(entry);
  const method = String(entry.request?.method ?? "GET").toUpperCase();
  const url = String(entry.request?.url ?? "").toLowerCase();
  const status = Number(entry.response?.status ?? 0);
  if (mime.startsWith("text/html")) return "document";
  if (mime.startsWith("application/json") || url.includes("/api/")) return "xhr";
  if (/^(image|font|video|audio)\//.test(mime)) return "binary";
  if (mime.startsWith("text/css")) return "stylesheet";
  if (mime.includes("javascript")) return "script";
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && status >= 0) return "fetch";
  return "other";
}
