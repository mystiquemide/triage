const TARGET_RPC_URL = "https://studio.genlayer.com/api";

export default async function handler(request, response) {
  response.setHeader("Access-Control-Allow-Origin", "*");
  response.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  response.setHeader("Access-Control-Allow-Headers", "content-type");

  if (request.method === "OPTIONS") {
    response.status(204).end();
    return;
  }

  if (request.method !== "POST") {
    response.status(405).json({ error: "Method not allowed" });
    return;
  }

  try {
    const upstream = await fetch(TARGET_RPC_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: typeof request.body === "string" ? request.body : JSON.stringify(request.body),
    });

    const text = await upstream.text();
    response.status(upstream.status);
    response.setHeader("content-type", upstream.headers.get("content-type") || "application/json");
    response.send(text);
  } catch (error) {
    response.status(502).json({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "GenLayer RPC proxy request failed",
        data: error?.message || String(error),
      },
      id: null,
    });
  }
}
