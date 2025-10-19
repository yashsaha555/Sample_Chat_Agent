export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function generateDataset() {
  const r = await fetch(`${API}/api/generate-dataset`, { method: "POST" });
  if (!r.ok) throw new Error("Failed to generate dataset");
  return r.json();
}
