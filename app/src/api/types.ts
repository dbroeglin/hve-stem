/** Types for SSE events from the assess stream. */

export interface StatusEvent {
  type: "status";
  message: string;
}

export interface ReasoningEvent {
  type: "reasoning";
  message: string;
}

export interface ToolEvent {
  type: "tool";
  tool: string;
  detail: string;
}

export interface PermissionEvent {
  type: "permission";
  kind: string;
  detail: string;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export interface DoneEvent {
  type: "done";
  status: "completed" | "failed";
  result: string | null;
}

export type AssessEvent =
  | StatusEvent
  | ReasoningEvent
  | ToolEvent
  | PermissionEvent
  | ErrorEvent
  | DoneEvent;
