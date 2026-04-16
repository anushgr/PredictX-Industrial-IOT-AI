"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePredictiveAlerts } from "@/hooks/use-dashboard-data";

export default function PredictiveAlertsPage() {
  const { data = [] } = usePredictiveAlerts();

  return (
    <div className="space-y-6 pb-6">
      <Card>
        <h1 className="text-2xl font-semibold text-white">Predictive Alerts</h1>
        <p className="mt-2 text-sm text-slate-300">
          These are the current predicted failure conditions derived from backend predictions.
        </p>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        {data.length > 0 ? (
          data.map((alert) => (
            <Card key={alert.id}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-white">{alert.machine}</h2>
                  <p className="text-sm text-slate-400">
                    {alert.sensor} · {alert.alertType}
                  </p>
                </div>
                <Badge className={alert.severity === "Critical" ? "border-red-500/40 bg-red-500/15 text-red-300" : "border-amber-500/40 bg-amber-500/15 text-amber-300"}>
                  {alert.severity}
                </Badge>
              </div>
              <p className="mt-4 text-sm text-slate-300">Predicted cause: {alert.predictedCause}</p>
              <p className="mt-2 text-xs text-slate-500">Status: {alert.status}</p>
            </Card>
          ))
        ) : (
          <Card className="border-slate-800 bg-slate-950/70 p-6 text-slate-300 lg:col-span-2">
            No active predictive alerts are available from the backend.
          </Card>
        )}
      </div>
    </div>
  );
}
