import type { ImageUploadResponse } from "../types";

const API_BASE = "http://localhost:8000/api/v1";

export async function uploadImage(
  file: File,
  sessionId?: string
): Promise<ImageUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const url = new URL(`${API_BASE}/uploads/image`);
  if (sessionId) {
    url.searchParams.append("session_id", sessionId);
  }

  const response = await fetch(url.toString(), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload image");
  }

  return response.json();
}

export async function fetchImageFromUrl(
  imageUrl: string,
  sessionId: string
): Promise<ImageUploadResponse> {
  const response = await fetch(`${API_BASE}/uploads/image-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: imageUrl,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch image");
  }

  return response.json();
}

export async function cleanupSession(sessionId: string): Promise<number> {
  const response = await fetch(`${API_BASE}/uploads/session/${sessionId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Failed to cleanup session");
  }

  const result = await response.json();
  return result.deleted_count;
}
