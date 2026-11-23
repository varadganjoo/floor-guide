"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Status = "checking" | "connected" | "offline";

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");
  const controllerRef = useRef<AbortController | null>(null);

  const checkConnection = useCallback(() => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    const timeout = setTimeout(() => controller.abort(), 5000);

    void fetch("/api/health", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Health check failed");
        const data: unknown = await response.json();
        if (
          typeof data !== "object" ||
          data === null ||
          !("status" in data) ||
          data.status !== "ok"
        ) {
          throw new Error("Unexpected health response");
        }
      })
      .then(() => {
        if (controllerRef.current === controller) setStatus("connected");
      })
      .catch(() => {
        if (controllerRef.current === controller) setStatus("offline");
      })
      .finally(() => clearTimeout(timeout));
  }, []);

  useEffect(() => {
    checkConnection();
    return () => {
      controllerRef.current?.abort();
      controllerRef.current = null;
    };
  }, [checkConnection]);

  return (
    <section className="connection" aria-label="Backend connection">
      <div role="status" aria-live="polite">
        <span className={`dot ${status}`} aria-hidden="true" />
        <strong>
          {status === "checking"
            ? "Checking backend…"
            : status === "connected"
              ? "Backend connected"
              : "Backend unavailable"}
        </strong>
        <p>
          {status === "connected"
            ? "Your frontend and API are ready to work together."
            : status === "checking"
              ? "Connecting to your API."
              : "Start the backend, then check the connection again."}
        </p>
      </div>
      <button
        onClick={() => {
          setStatus("checking");
          checkConnection();
        }}
        disabled={status === "checking"}
      >
        Check connection <span aria-hidden="true">↗</span>
      </button>
    </section>
  );
}
