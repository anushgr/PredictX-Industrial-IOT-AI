"use client";

import { useMemo } from "react";
import { AlertTriangle, Gauge, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MachineCard } from "@/components/dashboard/machine-card";
import { SensorCard } from "@/components/dashboard/sensor-card";
import { PredictionPanel } from "@/components/dashboard/prediction-panel";
import { useLiveTelemetry } from "@/hooks/use-live-telemetry";
import { useMachines, usePredictions } from "@/hooks/use-dashboard-data";

export default function Home() {
  const liveSensors = useLiveTelemetry();
  const { data: machines = [], isLoading: machinesLoading } = useMachines();
  const { data: predictions = [] } = usePredictions();

  const machine = machines[0];
  const topSensor = useMemo(() => {
    return liveSensors.find((sensor) => sensor.id === "vibration") ?? liveSensors[0];
  }, [liveSensors]);

  return (
    <div className="space-y-6 pb-6">
      <Card className="overflow-hidden border-cyan-500/20 bg-gradient-to-r from-slate-900 via-slate-900/95 to-cyan-950/25">
        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
              Single machine monitoring mode
            </div>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white md:text-4xl">
              Conveyor-07 predictive maintenance dashboard
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              This view now focuses on one machine only. All live data is coming from the backend dummy JSON source and is limited to sound, vibration, and temperature telemetry.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs text-slate-500">Machine Status</p>
              <p className="mt-1 text-xl font-semibold text-white">{machine?.status ?? "Loading"}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs text-slate-500">Failure Probability</p>
              <p className="mt-1 text-xl font-semibold text-red-300">
                {machine ? `${machine.failureProbability}%` : "--"}
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs text-slate-500">Live Sensor</p>
              <p className="mt-1 text-xl font-semibold text-cyan-300">{topSensor?.name ?? "Loading"}</p>
            </div>
          </div>
        </div>
      </Card>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Machine Overview</h2>
              <p className="text-sm text-slate-400">Single asset view for Conveyor-07</p>
            </div>
            {machine && <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-300">Backend synced</Badge>}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {machinesLoading ? (
              <Skeleton className="h-[260px] w-full sm:col-span-2" />
            ) : machine ? (
              <MachineCard machine={machine} />
            ) : (
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-5 text-sm text-slate-300 sm:col-span-2">
                No machine data available from backend.
              </div>
            )}
          </div>
        </Card>

        <PredictionPanel risks={predictions} />
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Live Sensor Telemetry</h2>
            <p className="text-sm text-slate-400">Sound, vibration, and temperature only</p>
          </div>
          <Button variant="outline" size="sm">
            <Gauge className="mr-2 h-4 w-4" />
            Refreshing from backend
          </Button>
        </div>
        <div className="grid gap-4 xl:grid-cols-3">
          {liveSensors.slice(0, 3).map((sensor) => (
            <SensorCard key={sensor.id} sensor={sensor} />
          ))}
        </div>
      </section>

      <Card className="border-amber-500/30 bg-amber-500/10 text-amber-100">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-300" />
          <div>
            <p className="font-medium">Inspection recommended within 12 hours.</p>
            <p className="mt-1 text-sm text-amber-100/80">
              The backend dummy data currently indicates a vibration-driven risk pattern on Conveyor-07.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
