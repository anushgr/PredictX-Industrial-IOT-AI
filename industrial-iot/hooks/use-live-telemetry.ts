"use client";

import { useEffect, useState } from "react";
import type { SensorReading } from "@/types";

export function useLiveTelemetry() {
  const [liveSensors, setLiveSensors] = useState<SensorReading[]>([]);

  useEffect(() => {
    let closed = false;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket("ws://localhost:8000/ws/telemetry");
      ws.onmessage = (event) => {
        if (closed) return;
        const payload = JSON.parse(event.data) as SensorReading[];
        if (Array.isArray(payload)) setLiveSensors(payload);
      };
      ws.onerror = () => {
        ws?.close();
      };
    } catch {
      ws = null;
    }

    return () => {
      closed = true;
      ws?.close();
    };
  }, []);

  return liveSensors;
}
