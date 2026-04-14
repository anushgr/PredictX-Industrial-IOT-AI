import type { PredictionRisk } from "@/types";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export function PredictionPanel({ risks }: { risks: PredictionRisk[] }) {
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
        <p className="text-right text-emerald-300">92%</p>
      </div>

      <div className="mt-5 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200">
        Machine 07 shows abnormal vibration-frequency drift. Recommend inspection within 12 hours.
      </div>
    </Card>
  );
}
