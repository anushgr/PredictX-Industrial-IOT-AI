"use client";

import { Card } from "@/components/ui/card";
import { SensorCard } from "@/components/dashboard/sensor-card";
import { useLiveTelemetry } from "@/hooks/use-live-telemetry";

export default function LiveMonitoringPage() {
  const sensors = useLiveTelemetry();

  return (
    <div className="space-y-6 pb-6">
      <Card>
        <h1 className="text-2xl font-semibold text-white">Live Monitoring</h1>
        <p className="mt-2 text-sm text-slate-300">
          Conveyor-07 telemetry only. Sound, vibration, and temperature are updated from the backend.
        </p>
      </Card>
      <div className="grid gap-4 xl:grid-cols-3">
        {sensors.length > 0 ? (
          sensors.map((sensor) => <SensorCard key={sensor.id} sensor={sensor} />)
        ) : (
          <Card className="xl:col-span-3 border-slate-800 bg-slate-950/70 p-6 text-slate-300">
            No live telemetry received from the backend yet.
          </Card>
        )}
      </div>
    </div>
  );
}
