export type ClassMode = "none" | "semantic" | "all";
export type ImageMode = "remove" | "strip-base64" | "placeholder";

export interface HtmlCleanerConfig {
  removeTags: Set<string>;
  keepAttributes: Set<string>;
  keepAriaAttributes: Set<string>;
  keepDataAttributes: Set<string>;
  classMode: ClassMode;
  removeEmptyNodes: boolean;
  imageMode: ImageMode;
  maxAttributeValueLength: number;
}

export interface HarCleanerConfig {
  keepResourceTypes: Set<string>;
  dropResourceTypes: Set<string>;
  removeCookieHeaders: boolean;
  removeResponseCookies: boolean;
  trimJsonArraysTo: number;
  trimJsonObjectKeysTo: number;
  trimLongStringsTo: number;
  maxJsonDepth: number;
}

export interface AppConfig {
  html: HtmlCleanerConfig;
  har: HarCleanerConfig;
}

export interface CleanResult<T> {
  content: T;
  warnings: string[];
}

export interface HarDocument {
  log?: {
    pages?: Array<Record<string, unknown>>;
    entries?: Array<Record<string, any>>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}
