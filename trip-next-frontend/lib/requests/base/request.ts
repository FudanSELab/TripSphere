import { isSSR } from "@/lib/utils/env";
import { Reason, ResponseCode } from "@/lib/requests/base/code";

export interface ResponseWrap<DataType = any> {
  data: DataType;
  code: ResponseCode;
  msg: string;
  error?: {
    reason: Reason;
    msg: string;
  };
}

export interface RequestOptions extends Omit<RequestInit, "body" | "headers"> {
  body?: unknown;
  headers?: Record<string, string>;
  serverHeaders?: Record<string, string>;
}

function buildRequestUrl(url: string): string {
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }

  if (isSSR()) {
    const isDevelopment = process.env.NODE_ENV === "development";
    const baseUrl = isDevelopment
      ? "http://localhost:3000"
      : "http://www.tripsphere.com";

    const path = url.startsWith("/") ? url : `/${url}`;
    return `${baseUrl}${path}`;
  }

  return url;
}

function buildHeaders(options: RequestOptions): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options.headers) {
    Object.assign(headers, options.headers);
  }

  if (isSSR() && options.serverHeaders) {
    Object.assign(headers, options.serverHeaders);
  }

  return headers;
}

export async function request<T = unknown>(
  url: string,
  options: RequestOptions = {},
): Promise<ResponseWrap<T>> {
  const {
    body,
    headers: customHeaders,
    serverHeaders,
    ...fetchOptions
  } = options;

  try {
    const requestUrl = buildRequestUrl(url);

    const requestHeaders = buildHeaders({
      headers: customHeaders,
      serverHeaders,
    });

    let requestBody: string | undefined;
    if (body !== undefined && body !== null) {
      requestBody = typeof body === "string" ? body : JSON.stringify(body);
    }

    const response = await fetch(requestUrl, {
      ...fetchOptions,
      headers: requestHeaders,
      body: requestBody,
    });
    return (await response.json()) as ResponseWrap<T>;
  } catch (error) {
    console.error(error);
    return {
      data: undefined as T,
      code: ResponseCode.ERROR,
      msg:
        error instanceof Error
          ? error.message
          : "Network error or unknown error occurred",
    };
  }
}

export async function get<T = unknown>(
  url: string,
  options?: Omit<RequestOptions, "body" | "method">,
): Promise<ResponseWrap<T>> {
  return request<T>(url, { ...options, method: "GET" });
}

export async function post<T = unknown>(
  url: string,
  body?: unknown,
  options?: Omit<RequestOptions, "body" | "method">,
): Promise<ResponseWrap<T>> {
  return request<T>(url, { ...options, method: "POST", body });
}

export async function put<T = unknown>(
  url: string,
  body?: unknown,
  options?: Omit<RequestOptions, "body" | "method">,
): Promise<ResponseWrap<T>> {
  return request<T>(url, { ...options, method: "PUT", body });
}

export async function patch<T = unknown>(
  url: string,
  body?: unknown,
  options?: Omit<RequestOptions, "body" | "method">,
): Promise<ResponseWrap<T>> {
  return request<T>(url, { ...options, method: "PATCH", body });
}

export async function del<T = unknown>(
  url: string,
  options?: Omit<RequestOptions, "body" | "method">,
): Promise<ResponseWrap<T>> {
  return request<T>(url, { ...options, method: "DELETE" });
}
