import type { Run } from "./api";

export type Pending = { conversationId: string; path: string; body: Record<string, unknown>; previousRunId?: string | null };

export function operationSettled(operation: Pending, run: Run | null) {
  if (!run || run.status === "failed" || run.status === "running") return false;
  if (operation.path.endsWith("/messages")) return run.id !== operation.previousRunId;
  if (operation.path.endsWith("/resume")) return run.id === operation.body.turn_id && (run.status === "completed" || run.version > Number(operation.body.version));
  return operation.path.endsWith("/cancel") && run.status === "cancelled";
}

export function isSendKey(event: { key: string; shiftKey: boolean; isComposing: boolean; keyCode: number }) {
  return event.key === "Enter" && !event.shiftKey && !event.isComposing && event.keyCode !== 229;
}
