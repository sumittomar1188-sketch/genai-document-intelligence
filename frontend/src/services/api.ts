import type { AskResponse, UploadResponse } from "../types/api";

function getApiBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

  if (!baseUrl) {
    throw new Error(
      "The backend URL is not configured. Set VITE_API_BASE_URL and restart the frontend.",
    );
  }

  return baseUrl.replace(/\/+$/, "");
}

async function readResponse<T>(response: Response): Promise<T> {
  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : `The backend returned an error (${response.status}).`;
    throw new Error(detail);
  }

  if (payload === null || typeof payload !== "object") {
    throw new Error("The backend returned an unexpected response.");
  }

  return payload as T;
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiBaseUrl()}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  const result = await readResponse<UploadResponse>(response);

  if (
    result.status !== "success" ||
    !result.saved_filename ||
    typeof result.chunks_processed !== "number" ||
    typeof result.chunks_stored !== "number"
  ) {
    throw new Error("The backend did not confirm that the document was stored.");
  }

  return result;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${getApiBaseUrl()}/questions/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const result = await readResponse<AskResponse>(response);

  if (
    typeof result.question !== "string" ||
    typeof result.answer !== "string" ||
    !Array.isArray(result.sources)
  ) {
    throw new Error("The backend returned an unexpected answer format.");
  }

  return result;
}
