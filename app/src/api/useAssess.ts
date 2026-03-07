import { useState, useCallback, useRef } from "react";
import type { AssessEvent } from "./types";
import { startAssess, subscribeAssess } from "./client";

export interface UseAssessResult {
  events: AssessEvent[];
  result: string | null;
  isRunning: boolean;
  error: string | null;
  run: (repo: string, model?: string) => void;
}

/** Hook that starts an assessment and streams events in real time. */
export function useAssess(): UseAssessResult {
  const [events, setEvents] = useState<AssessEvent[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const run = useCallback((repo: string, model?: string) => {
    // Reset state
    setEvents([]);
    setResult(null);
    setError(null);
    setIsRunning(true);

    // Close any previous event source
    esRef.current?.close();

    startAssess(repo, model)
      .then((jobId) => {
        const es = subscribeAssess(
          jobId,
          (data) => {
            const event = data as AssessEvent;
            if (event.type === "done") {
              setResult(event.result);
              setIsRunning(false);
              es.close();
            } else if (event.type === "error") {
              setError(event.message);
              setIsRunning(false);
              es.close();
            } else {
              setEvents((prev) => [...prev, event]);
            }
          },
          () => {
            setError("Connection to server lost.");
            setIsRunning(false);
          },
        );
        esRef.current = es;
      })
      .catch((err) => {
        setError(String(err));
        setIsRunning(false);
      });
  }, []);

  return { events, result, isRunning, error, run };
}
