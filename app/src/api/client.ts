const BASE = "/api";

/** Fetch the list of target repos from stem.yaml. */
export async function fetchTargets(): Promise<string[]> {
  const res = await fetch(`${BASE}/targets`);
  if (!res.ok) {
    throw new Error(`Failed to fetch targets: ${res.statusText}`);
  }
  return res.json();
}

/** Start an assessment job. Returns the job ID. */
export async function startAssess(
  repo: string,
  model: string = "claude-sonnet-4.6",
): Promise<string> {
  const params = new URLSearchParams({ repo, model });
  const res = await fetch(`${BASE}/assess?${params.toString()}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to start assessment: ${res.statusText}`);
  }
  const data = await res.json();
  return data.job_id;
}

/** Subscribe to the SSE stream for an assessment job. */
export function subscribeAssess(
  jobId: string,
  onMessage: (data: unknown) => void,
  onError?: (err: Event) => void,
): EventSource {
  const es = new EventSource(`${BASE}/assess/${jobId}/stream`);
  es.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      onMessage(parsed);
    } catch {
      // ignore malformed events
    }
  };
  if (onError) {
    es.onerror = onError;
  }
  return es;
}
