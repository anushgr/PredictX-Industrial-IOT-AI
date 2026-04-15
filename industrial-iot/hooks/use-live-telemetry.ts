"use client";

import { useEffect, useState } from "react";
import { sensors } from "@/lib/mock-data";
import type { SensorReading } from "@/types";

function randomWalk(value: number, drift = 0) {
  const next = value + (Math.random() - 0.5) * 2 + drift;
  return Number(next.toFixed(2));
}

export function useLiveTelemetry() {
  const [liveSensors, setLiveSensors] = useState<SensorReading[]>([]);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Initialize with mock data on first render (client-side only)
    setLiveSensors(sensors);
    setIsHydrated(true);

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

    const interval = setInterval(() => {
      setLiveSensors((prev) =>
        prev.map((sensor) => {
          const value = randomWalk(sensor.value, sensor.id === "temp" ? 0.08 : 0);
          const nextSeries = [...sensor.series.slice(-19), value];
          return {
            ...sensor,
            value,
            anomalyCount:
              sensor.threshold > 0 && value > sensor.threshold
                ? sensor.anomalyCount + 1
                : sensor.anomalyCount,
            series: nextSeries,
          };
        }),
      );
    }, 2500);

    return () => {
      closed = true;
      clearInterval(interval);
      ws?.close();
    };
  }, []);

  // Return empty array during hydration to match server render
  return isHydrated ? liveSensors : [];
}
