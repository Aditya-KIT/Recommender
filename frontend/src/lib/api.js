const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export async function sendChat(messages) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    let detail = "Failed to reach backend API";
    try {
      const err = await response.json();
      if (err.detail) detail = err.detail;
    } catch {}
    throw new Error(detail);
  }

  return response.json();
}
