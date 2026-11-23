import { RunInspector } from "@/components/run-inspector";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Observability · Floor Guide" };

export default async function Observability({ searchParams }: { searchParams: Promise<{ run?: string | string[] }> }) {
  const { run } = await searchParams;
  return <RunInspector initialRunId={typeof run === "string" ? run : null} />;
}
