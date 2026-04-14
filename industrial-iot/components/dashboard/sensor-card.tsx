"use client";

import { Line } from "react-chartjs-2";
import { motion } from "framer-motion";
import type { SensorReading } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function SensorCard({ sensor }: { sensor: SensorReading }) {
  const danger = sensor.value >= sensor.threshold;

  return (
    <motion.div whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
      <Card className="h-full">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">{sensor.name}</h3>
            <p className="text-xs text-slate-400">Anomaly spikes: {sensor.anomalyCount}</p>
          </div>
          <Badge
            className={danger ? "border-red-500/40 bg-red-500/20 text-red-300" : "border-emerald-500/40 bg-emerald-500/20 text-emerald-300"}
          >
            {sensor.value}
            {sensor.unit}
          </Badge>
        </div>

        <div className="h-44">
          <Line
            data={{
              labels: sensor.series.map((_, index) => index),
              datasets: [
                {
                  label: sensor.name,
                  data: sensor.series,
                  borderColor: danger ? "#f87171" : "#22d3ee",
                  backgroundColor: danger
                    ? "rgba(248,113,113,0.16)"
                    : "rgba(34,211,238,0.12)",
                  fill: true,
                  tension: 0.32,
                  pointRadius: 0,
                  borderWidth: 2,
                },
                {
                  label: "Threshold",
                  data: sensor.series.map(() => sensor.threshold),
                  borderColor: "rgba(251,191,36,0.7)",
                  borderDash: [4, 4],
                  pointRadius: 0,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  labels: { color: "#94a3b8", boxWidth: 10 },
                },
              },
              scales: {
                x: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.3)" } },
                y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.3)" } },
              },
            }}
          />
        </div>
      </Card>
    </motion.div>
  );
}
