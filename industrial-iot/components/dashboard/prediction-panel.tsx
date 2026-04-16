import type { PredictionRisk } from "@/types";
import { Line } from "react-chartjs-2";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { PredictionSnapshotWithTrend } from "@/hooks/use-dashboard-data";

export function PredictionPanel({
  risks,
  snapshot,
}: {
  risks: PredictionRisk[];
  snapshot?: PredictionSnapshotWithTrend | null;
}) {
  const machineHealth = snapshot?.machine_health;
  const trend = snapshot?.trend ?? [];

  return (
    <Card className="h-full">
      <h3 className="text-lg font-semibold text-white">
        Deep Learning Failure Prediction Engine
      </h3>
      <p className="mt-1 text-sm text-slate-400">Current Predictions</p>

      <div className="mt-4 space-y-4">
        {risks.map((risk) => (
          <div key={risk.label}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="text-slate-300">{risk.label}</span>
              <span className="font-medium text-white">{risk.value}%</span>
            </div>
            <Progress
              value={risk.value}
              indicatorClassName={
                risk.value >= 70
                  ? "bg-red-500"
                  : risk.value >= 40
                    ? "bg-amber-500"
                    : "bg-emerald-500"
              }
            />
          </div>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
        <p className="text-slate-400">Algorithm</p>
        <p className="text-right text-slate-100">LSTM + Autoencoder</p>
        <p className="text-slate-400">Input Window</p>
        <p className="text-right text-slate-100">60 sec telemetry</p>
        <p className="text-slate-400">Retrain Frequency</p>
        <p className="text-right text-slate-100">Daily</p>
        <p className="text-slate-400">Confidence Score</p>
        <p className="text-right text-emerald-300">
          {machineHealth?.overall_anomaly_score !== undefined
            ? `${Math.max(0, Math.min(100, Math.round((1 - machineHealth.overall_anomaly_score) * 100)))}%`
            : "92%"}
        </p>
        <p className="text-slate-400">Health Status</p>
        <p className="text-right text-slate-100">{machineHealth?.status ?? "--"}</p>
        <p className="text-slate-400">Overall Health</p>
        <p className="text-right text-slate-100">
          {machineHealth?.overall_health_pct !== undefined ? `${machineHealth.overall_health_pct}%` : "--"}
        </p>
        <p className="text-slate-400">Estimated RUL</p>
        <p className="text-right text-slate-100">
          {machineHealth?.estimated_rul_hours !== undefined ? `${machineHealth.estimated_rul_hours} h` : "--"}
        </p>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
          <p className="mb-2 text-sm text-slate-300">Model Confidence Trend</p>
          <div className="h-44">
            <Line
              data={{
                labels: trend.map((point) => point.timeLabel),
                datasets: [
                  {
                    label: "Confidence %",
                    data: trend.map((point) => point.confidence),
                    borderColor: "#22d3ee",
                    backgroundColor: "rgba(34, 211, 238, 0.15)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 0,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { ticks: { color: "#64748b", maxRotation: 0, autoSkip: true }, grid: { color: "rgba(51,65,85,0.25)" } },
                  y: { min: 0, max: 100, ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                },
              }}
            />
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
          <p className="mb-2 text-sm text-slate-300">Anomaly Score Trend</p>
          <div className="h-44">
            <Line
              data={{
                labels: trend.map((point) => point.timeLabel),
                datasets: [
                  {
                    label: "Anomaly Score %",
                    data: trend.map((point) => point.anomalyScore),
                    borderColor: "#fb7185",
                    backgroundColor: "rgba(251, 113, 133, 0.15)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 0,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: { legend: { display: false } },
                scales: {
                  x: { ticks: { color: "#64748b", maxRotation: 0, autoSkip: true }, grid: { color: "rgba(51,65,85,0.25)" } },
                  y: { min: 0, max: 100, ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                },
              }}
            />
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200">
        {machineHealth?.recommendation ?? "Machine 07 shows abnormal vibration-frequency drift. Recommend inspection within 12 hours."}
      </div>
    </Card>
  );
}
